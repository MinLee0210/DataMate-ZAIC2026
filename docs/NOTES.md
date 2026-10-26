# Decisions log

Newest at the top. Record *why*, not just *what*.

## 2026-10-26 - Extra metrics: tokens, TTFT, latency, diagnostics
- `LLM.complete` records one `LLMUsage` per call: prompt and completion tokens, time to first token,
  latency and error. `QAService` puts them in the trace as `llm`, with `timings` (seconds per graph
  node) and `ingest_s`. `src/evaluate/metrics.py` computes efficiency and diagnostics from the
  trace, and `scripts/eval.py` reports them and writes `metrics.json`.
  Why: inference time is the official tie-break and the private run has a 6 h limit; tokens and
  TTFT show where time goes. Coverage, oracle@k and the agreement AUROC show whether abstention
  or generation is the bottleneck.
- Replies are streamed by default (`LLM_STREAM=true`) to measure TTFT; the generated output is
  the same either way. Checked on the HF router (Qwen3-14B via deepinfra): usage arrives in the
  last chunk.

## 2026-10-26 - modules/ = agent core, utils/ = deterministic helpers
- `modules/` keeps what defines the agent's behaviour: `ingest/`, `context/`, `semantic/`,
  `agents/` + `llm.py`, `decide/`.
- Moved to `utils/` as single files: `format.py`, `timeparse.py`, `health.py` (HealthModule, no
  longer a `BaseModules`), and `text.py` (`fold`, moved out of `context/entities.py`).
  Why: these are deterministic, fixed by the spec or the rulebook, and are not where the agent's
  quality is tuned. `utils/` never imports `modules/`, so `fold` had to leave `context/`.
- The PA scorer is its own top-level package, `src/evaluate/`, outside both. Why: it judges the
  pipeline's output and the pipeline never imports it.

## 2026-10-26 - Official scorer (now src/evaluate/)
- The scorer moved from `scripts/eval.py` to `src/evaluate/` and follows rulebook §9
  strictly. Why: the old scorer was lenient where the official one is strict, so local PA was
  too high. It accepted numbers given as strings, rounded both sides to 2 dp, let number and
  percent swap, and accepted `"true"`. It also scored tables as ordered lists and ignored `alias`.
- `load_gold` keeps `alias`. The formatter writes tables as `{"columns", "rows"}`.
  Why: the old list-of-rows table was a wrong format, so every table answer scored −1.
- Check: all train gold answers, and their alias forms, score PA 1.0 with the new scorer.
- The eval summary adds a "by verdict" count (`wrong_type` / `bad_format` / `wrong_value`).

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
