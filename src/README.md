# src/

The DataMate package. The competition runs `python -m src` (`__main__.py`, batch). `src/__init__.py`
also builds a FastAPI app with `/health` and `/ask`, used for debugging and, later, by the demo UI
in `app/`. Run it with `make run` (`APP_HOST`, `APP_PORT`, `APP_RELOAD` from `.env`).

```
src/
├── __main__.py      batch: questions → QAService → submission.jsonl (append + fsync) + trace
├── config.py        Settings (pydantic-settings, reads .env); FINAL_MODE=1 needs a local LLM URL
├── models/          Question, Answer, SubmissionLine, SchemaCard
├── data/            DuckDBSource (read-only, guarded queries), layout.py (dataset paths)
├── modules/         shared building blocks, no I/O policy of their own
├── services/        ingest (package → DuckDB + context), qa (LangGraph pipeline)
├── routes/          /health, /ask (debugging, demo UI)
├── utils/           colored logger
└── assets/          prompt_templates/, skills/, semantic/
```

## Flow

`__main__` / `routes` → `services/<name>/service.py` → `modules/` + `data/` + `utils/`.
A service does not define modules; it composes the shared ones.

`services/qa/graph.py` is the per-question LangGraph:
`prepare` (time ranges, entity links; no LLM) → `generate` (k prompt variants, 1 step) → `execute`
(DuckDB) → `repair` on failures (≤ `max_repairs` steps) → `decide` (vote, tau).

## Rules that apply here (from CLAUDE.md)

- Nothing in `src/` imports a third-party API client other than the OpenAI-compatible `LLM`, which
  points at a local vLLM server in final mode.
- No prompts in code: prompts are in `assets/prompt_templates/`, rulebook knowledge in `assets/skills/`.
- Nothing keyed on a `business_id` or question `id`.
- Any failure in a question is logged and becomes `abstain`.

## Logging

```python
from src.utils import get_logger

logger = get_logger(__name__)
```
