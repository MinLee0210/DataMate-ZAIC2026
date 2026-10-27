# CLAUDE.md — DataMate (Zalo AI Challenge 2026)

Vietnamese natural-language QA over messy tabular data (CSV/XLSX/SQLite), built on
LakoreAI/ai-app-project-template. Competition spec: docs/PROJECT.md. Hypotheses and method: docs/RESEARCH.md.
Read both before any non-trivial change.

## Hard rules (competition compliance, never violate)
1. Final inference is fully offline. The only allowed LLM endpoint at inference is a local vLLM server
   (`LLM_BASE_URL=http://127.0.0.1:...`). `src/config.py` must raise if `FINAL_MODE=1` and the base URL is not local.
2. Third-party APIs are allowed only in `scripts/datagen/` and `scripts/devfree/`. Nothing in `src/` imports them.
3. Never run third-party APIs or external models on public_test or private_test. Use train data and self-generated data only.
4. Never hard-code answers or branch on `business_id` or question `id`.
5. All models used at inference total ≤ 15B params (MoE counts all experts), weights public before 2026-10-01.
   Every model is declared in docs/MODELS.md before it is used.
6. `/data` is read-only. Temp files go to `$WORK_DIR` (default `/tmp/datamate`).
7. Append and flush each answer to `/result/submission.jsonl` as soon as it is decided. A timeout keeps only written lines.
8. Determinism: fixed seeds, temperature 0, fixed batch size and vLLM settings. Upload vs rerun PA must differ ≤ 0.03.

## Two phases, one code path
| Phase | `LLM_BASE_URL` | `LLM_MODEL` | Use |
|---|---|---|---|
| dev_free | hosted provider (OpenAI-compatible) | the TARGET open model | pipeline, flow, ingest, context |
| dev_free (datagen) | any strong model | teacher | `scripts/datagen/` only, train businesses only |
| dev_constraint / final | `http://127.0.0.1:8001/v1` (vLLM) | TARGET model | latency, tau, determinism, Docker |
Never tune prompts, thresholds or `tau` on a model other than the target.

## Architecture in this template
```
src/
├── __main__.py            batch entrypoint: python -m src --data /data --out /result
├── config.py              + llm_base_url, llm_model, seed, final_mode, data_dir, result_dir, tau, k
├── models/                Question, Answer (typed union), SubmissionLine, SchemaCard
├── services/qa/           service.py: one question end to end; utils/
├── services/ingest/       service.py: business package → DuckDB + context, cached per business
├── modules/
│   ├── llm.py             OpenAI SDK with base_url (API or local vLLM), seed, temperature 0
│   ├── agents/sql_agent.py    BaseAgent: plan → SQL/Python; prompt_template = "sql_agent"
│   ├── ingest/            header detection, multi-sheet, merged cells, type inference
│   ├── context/           auto-authored context: schema card, entity dict, glossary
│   ├── semantic/          rulebook → DuckDB views/macros (valid_orders, revenue, cogs, overdue_debt, ...)
│   └── decide/            vote over executed results → answer | abstain | unanswerable
├── utils/                 deterministic helpers, never import modules/
│   ├── format.py          typed answer formatting and rounding
│   ├── timeparse.py       as_of_date, relative expressions, lunar calendar (deterministic)
│   ├── text.py            fold (accent/case folding)
│   └── health.py, logger.py
├── evaluate/              official PA scorer (rulebook §9), used by scripts/eval.py only
├── data/duckdb.py         DuckDB DataSource (connect/ping/close)
├── routes/                keep /health; optional POST /ask for manual debugging only
└── assets/
    ├── prompt_templates/  sql_agent.md, repair.md, verifier.md
    └── skills/            authored context as skills: time-expressions, ranking-rules,
                           business-metrics, unanswerable, answer-types
scripts/
├── infer.sh               start vLLM, wait for it, run python -m src
├── eval.py                eval runner (scores with src/evaluate/), writes docs/analysis/<date>/<topic>/
├── datagen/  devfree/     API allowed here, never imported by src/
```
Remove the Postgres/Milvus datasources and their compose services. They are not used.

## Commands
- `make install` — `uv sync`
- `make ingest SPLIT=train` — build DuckDB + context cache per business
- `make eval SUBSET=dev200` — run on a fixed dev subset and score PA
- `make eval-full` — full train split (slow, run overnight)
- `make vllm` — start the local vLLM server with pinned settings
- `make docker-build && make rerun-check` — build the image, run it twice, diff the outputs
- `make test lint fmt`

## Workflow rules
- No claimed improvement without a `make eval SUBSET=dev200` run.
  `scripts/eval.py` writes results to `docs/analysis/<yyyy-mm-dd>/<topic>/summary.md` and appends a row to
  docs/EXPERIMENTS.md. Do not copy numbers by hand.
- Every eval reports PA, #correct/#wrong/#abstain, and breakdowns by answer type and question category.
  A change to `decide/` also reports the PA-vs-tau curve.
- Record design decisions in docs/NOTES.md, newest at the top, with the why.
- Prefer deterministic Python over the LLM for time parsing, formatting, rounding and entity normalization.
- At most 4 LLM steps per question.
- Prompts live in `assets/prompt_templates/`; rulebook knowledge lives in `assets/skills/`. No prompts in code.
- Skills and semantic views must be generic across businesses. Nothing keyed on a specific business.

## Code conventions
Python 3.12, `uv`, ruff (line 100, rules E F I B UP). Type hints everywhere.
Tests need no network and no GPU: fake the LLM as in the template. Unit tests are required for
`utils/timeparse.py`, `utils/format.py`, `evaluate/` (scorer) and `modules/decide/`. No notebooks in `src/`.

## Don't
- Don't look for, infer or store test answers.
- Don't add a model without updating docs/MODELS.md and the parameter budget.
- Don't swallow exceptions: log them and abstain.
