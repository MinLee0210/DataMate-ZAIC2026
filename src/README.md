# src/

The DataMate package. The competition runs `python -m src` (`__main__.py`, batch). `src/__init__.py`
also builds a FastAPI app with `/health` and `/ask`, used for debugging and, later, by the demo UI
in `app/`. Run it with `make run` (`APP_HOST`, `APP_PORT`, `APP_RELOAD` from `.env`).

```
src/
├── __main__.py      batch: questions → QAService → submission.jsonl (append + fsync) + trace
├── config.py        Settings (pydantic-settings, reads .env); FINAL_MODE=1 needs a local LLM URL
├── models/          Question, Answer, SubmissionLine, SchemaCard, LLMUsage
├── data/            DuckDBSource (read-only, guarded queries), layout.py (dataset paths)
├── modules/         agent core: ingest, context, semantic, agents + llm, decide
├── services/        ingest (package → DuckDB + context), qa (dataAgent, vote pipeline)
├── routes/          /health, /ask (debugging, demo UI)
├── utils/           deterministic helpers: format, timeparse, text, assets (prompt and skill
│                    files), health, logger
├── evaluate/        official PA scorer (rulebook §9); used by scripts/eval.py, not by the pipeline
└── assets/          prompt_templates/, skills/, semantic/
```

## Flow

`__main__` / `routes` → `services/<name>/service.py` → `modules/` + `data/` + `utils/`.
A service does not define modules; it composes the shared ones.

What goes where:
- `modules/` holds components whose behaviour *is* the agent's logic. Changing them changes what
  the agent reads, plans or decides: ingest, context, semantic, agents, llm, decide.
- `utils/` holds deterministic helpers with fixed, spec-driven behaviour: answer formatting,
  time-expression parsing, text folding, health probes, logging. `utils/` never
  imports from `modules/`.
- `evaluate/` is the official PA scorer. It judges the pipeline's output and is never imported
  by it, so it stays outside both.

Two per-question pipelines, chosen by `PIPELINE`:

- `services/qa/malt.py` (`malt`): dataAgent, a bounded reasoning loop.
  Think on the schema (LLM) → sample the fields it asked for
  (`modules/context/sampling.py`, no LLM) → named data queries (LLM) → DuckDB → think on the
  results (LLM): `final`, `abstain`, a pandas `analysis` (`modules/python_exec.py`) or one more
  `data_query` → think again (LLM) → the chosen result formatted in code. At most 4 LLM steps. Every
  step is in the trace as a message (`thought`, `progress`, `data`, `analysis`,
  `error`, `final`).
- `services/qa/graph.py` (`vote`): a LangGraph: `prepare` (time ranges, entity links; no LLM) →
  optional `analyze` → `generate` (k prompt variants, 1 step) → `execute` (DuckDB) → `repair` on
  failures (≤ `max_repairs` steps) → `decide` (vote, tau).

Both read the same context (`graph.build_context`) and the same system prompt: the agent's
template, the skills, and the split's rulebook.

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
