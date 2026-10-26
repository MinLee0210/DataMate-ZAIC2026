# Decisions log

Newest at the top. Record *why*, not just *what*.

## 2026-10-26 - App settings, demo UI later
- `APP_NAME`, `APP_VERSION`, `APP_HOST`, `APP_PORT`, `APP_RELOAD`, `LOG_LEVEL` are settings (`.env`).
  `scripts/entrypoints.sh` reads only the `APP_*` keys from `.env`. Why: one place for config, and
  sourcing the whole `.env` in bash would break on JSON values such as `LLM_EXTRA_BODY`.
- `app/` will hold a simple demo UI, built after `src/` is done, on top of `POST /ask`. Why: the
  batch path stays the competition entrypoint; the UI reuses the same `QAService`.

## 2026-10-26 - Template → DataMate data agent
Details: [system design review](notes/2026-10-26/system-design/review.md),
[research report](reports/2026-10-26/data-agent-research/report.md).
- Inference is a bounded **LangGraph** `StateGraph` (prepare → generate → execute → repair ≤ 2 →
  decide), not a deepagents loop. Why: the 4-LLM-step rule and the 0.03 PA rerun rule need a known
  step count and low variance.
- **deepagents** is used only in `scripts/datagen/teacher.py` (train split only). It reads the same
  `src/assets/skills/` through a read-only virtual filesystem. Why: open exploration helps data
  generation, and APIs are allowed there; it also keeps the teacher and the inference agent on one
  rulebook.
- k candidates come from **prompt variants at temperature 0** with per-candidate seeds. Why: rule 8
  forbids sampling, and voting still needs diversity.
- The vote is on **executed, typed, normalized answers**; failed candidates count against
  agreement; answer only if agreement ≥ tau. Why: PA rewards abstaining when P(correct) ≤ 0.5, and
  agreement is execution-grounded.
- **Time and entities are resolved in Python** before the LLM. Why: deterministic, testable, and a
  frequent failure mode of small models.
- Ingest: **number locale decided per column**, day-first dates, merged cells filled, header row
  scored by distinct text cells, SQLite read with stdlib. Why: Vietnamese spreadsheets; the DuckDB
  sqlite extension downloads at first use and fails offline.
- Generated SQL: one SELECT (sqlglot), read-only DuckDB without external access, a timeout and a row
  cap. Why: model output is untrusted input.
- Removed Postgres, Milvus, `/chat` and docker-compose. Kept `/health`; added `/ask` for debugging.
  Why: the competition is a batch job; no vector store fits the parameter budget.
- One code path for both phases: `LLM_BASE_URL` points to OpenRouter (dev_free) or local vLLM.
  `FINAL_MODE=1` refuses non-local URLs.
- Dataset layout is a guess isolated in `src/data/layout.py`. Fix it when the data is downloaded.
- The Dockerfile (vLLM base + weights + `infer.sh`) is a draft: not built, vLLM tag not pinned for
  RTX 5090.

## 2026-10-26 - Layered backend, settings, tests
- Services call shared modules in `src/modules/` (LLM, agents, health); they do not own a `modules/` folder.
- `src/` layers: `routes/` -> `services/<name>/` -> `modules/` + `data/` + `utils/`;
  request/response schemas in `models/`. Why: routes stay thin; services compose reusable parts.
- Health is a `HealthModule` (registry of probes) so any source can be added later.
- Settings via `pydantic-settings` (reads `.env`). Why: typed config, no manual `export`.
- Each agent's prompt is `src/assets/prompt_templates/<agent>.md` (loaded by `BaseAgent`, no prompts in code).
- Skills live in `src/assets/skills/<name>/SKILL.md` and are part of agents: `BaseAgent` loads the skills
  it is given and builds its `system_prompt`.
