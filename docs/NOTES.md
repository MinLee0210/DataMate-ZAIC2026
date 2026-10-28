# Decisions log

Newest at the top. Record *why*, not just *what*.

## 2026-10-28 - Experiment tracking on W&B; hold-out split; duplicate order lines
- W&B project `octoopt/zaic2026-datamate`. `scripts/devfree/wandb_report.py` reads what the eval
  wrote (`docs/analysis/<date>/<topic>/metrics.json`, `summary.md`) and logs PA, right / wrong /
  abstain, per answer type, the PA-vs-tau curve, timings and tokens; `test` logs a public or
  private test run (counts and timings only, never the predictions, plus the leaderboard PA when
  known). Nothing in `src/` or `scripts/eval.py` imports wandb (extra `tracking`). Pod runs are
  copied to the Mac and reported from there, so the W&B key never goes to the pod.
- `metrics.json` now records the run's config (model, pipeline, thinking, subset, workers, k,
  tau), the per-type table and the tau curve; each eval keeps its own `trace.jsonl` in its run dir.
- Hold-out (`scripts/splits.py`): one business per shop type, never used for training, datagen or
  retrieval: biz_102 (grocery), biz_106 (cafe), biz_114 (building materials), biz_120 (pharmacy),
  biz_125 (small), biz_130 (restaurant); 554 questions. `--subset holdout` / `holdout200`.
- Ingest (version 4): duplicate lines of an order are dropped (rulebook §8: equal in every cell =
  export error, counts once). Found in 6 train businesses; it explains the revenue answers about
  1-4 % too high (biz_128 "hôm nay": 40,228,500 with duplicates, 39,793,500 = gold without).
- `business-metrics` skill: SQL recipes (status folding, whole-order exclusion on returns, line
  totals, base units, rounding, shares, growth, customers, debt). DuckDB `strip_accents` keeps
  `đ`, so folding also replaces `đ` with `d`.

## 2026-10-27 - Ready for a GPU pod: context length, thinking, run scripts
- Prompt sizes with the Qwen3 tokenizer: system prompt (template, skills, rulebook) 7.6k tokens
  on train and 8.8k on public_test; the step-1 user prompt up to 10.7k (train) and 14.5k
  (public_test, dev_005). Later steps add results and thoughts, so about 28k. With thinking this
  is above Qwen3's native 32768, and vLLM rejects a request whose prompt + max_tokens exceed
  `max-model-len`.
- `scripts/vllm.sh`: every setting is an env variable; `MAX_MODEL_LEN` 49152 with static YaRN
  (factor = length / 32768, as the Qwen3 card describes), prefix caching on, `QUANTIZATION` and
  `KV_CACHE_DTYPE` for one 48 GB GPU (`TP=1 QUANTIZATION=fp8`). Defaults stay for 2× RTX 5090.
- `scripts/infer.sh` now runs dataAgent with thinking on its reasoning steps, 8 workers,
  `ANALYZE_MAX_TOKENS` 12288 (all overridable).
- A thinking block cut off by max_tokens is dropped before JSON parsing, so a JSON-like line in
  the thinking is never read as the answer.
- `scripts/pod/` (setup.sh, README.md): copy, set up, serve, smoke test, dev200, public_test,
  rerun. `scripts/export.py` exports any run's submission in the portal format.
- Open: greedy decoding (temperature 0) in thinking mode can loop (the Qwen3 card recommends
  sampling); kept for determinism, to be checked on the pod by the share of cut-off replies.
- Why: the user will provide a pod (A40) for the first legal public_test run, then 2× RTX 5090.

## 2026-10-27 - Ingest fixes from error analysis; messy-data skill; CA with thinking
- Four ingest errors made tables wrong (details and affected businesses:
  [notes/2026-10-27/data-errors/notes.md](notes/2026-10-27/data-errors/notes.md)): dot thousands
  read as decimals, money shorthand (`25k`, `1,5tr`) left as text, tables split by month or part,
  grouped exports with blank parent cells. All four are fixed in ingest, deterministically.
  `INGEST_VERSION` (now 3) is part of the cache key.
- The same knowledge is a skill (`assets/skills/messy-data`): what ingest cleaned, and how to
  check and fix the rest in SQL or pandas, for cases ingest does not catch.
- CA pipeline with thinking on every step (old ingest): PA 0.55 (122/12/66), 23 s/question. Only
  12 wrong out of 134 answered (91 %): with thinking, the last THOUGHT abstains when unsure.
- `python_exec.py` moved to `src/modules/`.

## 2026-10-27 - CA pipeline: the reasoning loop of Google's Conversational Analytics API
- New `PIPELINE=ca` (`src/services/qa/ca.py`), built on the CA-API message types (REST reference,
  `Message`): `SchemaMessage` → `TextMessage THOUGHT` → `PROGRESS` (sample field values) →
  `DataMessage` (named query → SQL → named `DataResult`) → `THOUGHT` on the results →
  `AnalysisMessage` (Python over named results, `dataResultNames`) or one more `DataMessage` →
  `FINAL_RESPONSE`. Errors are recoverable and shown to the next THOUGHT, as in CA-API.
  Reference trace: a CA-API response stream on Looker data (user's work file, not copied here).
- Bounded for the competition: at most 4 LLM steps (THOUGHT 1 schema, THOUGHT 2 queries,
  THOUGHT 3 results, THOUGHT 4 only after an analysis or extra query). PROGRESS is deterministic
  (`modules/context/sampling.py`): distinct counts, top values, min/max, and the number of rows
  after the as-of date. The final value is formatted in code from the named result.
- Differences from CA-API: no charts, no natural-language answer, no clarifying questions, and the
  last THOUGHT may abstain (CA-API has no abstain; PA punishes a wrong answer).
- Python analysis runs in `src/modules/python_exec.py`: AST check (no imports, dunder or private
  names, file or reflection builtins), `results`, `pd` and a read-only `query()`, timeout.
- The vote pipeline stays as `PIPELINE=vote` (default until the CA run is measured).
- Why: user request, to follow CA-API instead of a self-designed pipeline. The vote pipeline went
  straight from question to SQL; the intent step of CA-API's QueryData had been trimmed.
- Same day, vote pipeline with an analysis step shared by the k candidates (`ANALYZE=true`):
  PA 0.335 vs 0.35 without it. The candidates agree more (9 abstain instead of 36), so wrong
  answers rose from 47 to 62. A shared analysis removes the diversity the vote relies on.
  With thinking on for that analysis call only (`ANALYZE_EXTRA_BODY={"thinking": {"type":
  "enabled"}}`): PA 0.52 (143/39/18), at 15.3 s/question instead of 5.8. Thinking is the gain,
  not the extra step. The 6 h budget on the target GPU must be checked before keeping it.
- Code layout: `LLMUsage` moved to `src/models/llm.py`; prompt and skill file IO
  (`load_prompt_template`, `render`, `list_skills`, `load_skill`) moved from `modules/agents/` to
  `src/utils/assets.py` (file IO only, no agent logic).

## 2026-10-27 - Split rulebook in the system prompt; threaded batch runner
- The split's `rulebook.md` (`/data/rulebook.md` at inference) is now appended to the SQL agent's
  system prompt (`assets/prompt_templates/rulebook.md`, `SQLAgent(rulebook=...)`). Before this, no
  code passed the rulebook to the model, and `business-metrics` was still a TODO.
- Why: public_test scored PA -0.169 (about 211 right, 380 wrong). Its rulebook has 3 shop types
  that are not in train (mother & baby, motorbike repair, phone shop) and many "most/best"
  definitions (khách sộp nhất, giờ cao điểm, nhà cung cấp chính, ...). Without them the k
  candidates agree on the same wrong definition, so voting cannot catch it. Reading the rulebook
  at inference is allowed: it is part of the input.
- Cost: about 22.6k characters, so about 26k prompt tokens per call instead of about 13k. It sits
  at the end of the system prompt, so the shared prefix stays cacheable (DeepSeek, vLLM prefix
  cache). To check on the pod: Qwen3-14B has a 32k native context (about 40k with its config), so
  rulebook + schema + question must fit. If they do not, keep the general sections plus the
  business's shop-type section.
- `python -m src --workers N` (`WORKERS`, `make eval WORKERS=8`) runs questions on N threads. Every
  business is ingested first, one at a time. Each thread has its own QAService (LLM client, usage
  records, DuckDB connections). Writes are locked and fsynced per line. With N > 1 the line order
  follows decision order, not the questions file; the score is by id, and answers do not depend
  on N (temperature 0, fixed seeds per candidate).

## 2026-10-27 - Exception: public_test run on the DeepSeek API
- The user asked for a public_test submission before the GPU pod is ready, so public_test (1,000
  questions) was run once through the hosted DeepSeek API (`deepseek-flash`). This breaks hard rule 3
  in CLAUDE.md ("never run third-party APIs on public_test") by the user's explicit decision. It
  sends the public_test questions and data excerpts to a third party.
- Nothing from this run is used for tuning, training or few-shot examples. The score is a
  reference for the pipeline only and does not reflect the final ≤15B offline model.
- Why: the first upload was the train dev200 file by mistake and scored 0.0000, because none of its
  ids are in public_test.

## 2026-10-27 - Submission exports in data/results/<date>/<topic>/
- `make eval` now also writes the run's submission to
  `data/results/<yyyy-mm-dd>/<topic>/submission.jsonl`, the same date/topic layout as
  `docs/analysis/`. Each line is re-serialized and its answer is format-checked with the scorer's
  `check_format`. A bad line stops the export, so a broken file is never written.
- Lines follow the portal's Submission example (challenge.zalo.ai/portal/datamate, read through its
  public `config-detail` API on 2026-10-27): value types are `{"id", "type", "answer"}`,
  unanswerable is `{"id", "type": "unanswerable", "reason": "<Vietnamese text>"}` and abstain is
  `{"id", "type": "abstain"}`. Neither of the last two has an `answer` key
  (`SubmissionLine.record()`). The portal accepts only `.jsonl` files of at most 5 MB.
- Why: user request, so that every run leaves a file in the challenge format that can be uploaded or
  compared directly.

## 2026-10-26 - Planned feature: charts in the demo app
- The demo app will draw a chart next to the answer, as Google's CA-API does. The challenge does
  not ask for this; it is a product feature for the app's interface.
- Scope: `app/` and `POST /ask` only. The batch path and `submission.jsonl` stay chart-free, so
  inference time and determinism are unchanged.
- Not built yet. Design notes are in SUGGESTIONS.md (S18) and the task is PLAN.md T18.

## 2026-10-26 - MAX_REPAIRS 2 → 5
- The default `max_repairs` is now 5 (`MAX_REPAIRS` in `.env` overrides it). A question takes at
  most 1 + 5 = 6 LLM steps, which exceeds the "at most 4 LLM steps" workflow rule in CLAUDE.md.
  Repairs run only for failed candidates (bad JSON, SQL error, wrong result shape); a question
  whose candidates all run takes 1 step as before.
- Why: user request, to give failing candidates more chances before they count against
  agreement. To check: the eval's `llm_steps` and `over_4` rows show how often questions go past
  4 steps, and the seconds per question show whether the 6 h budget still holds.

## 2026-10-26 - Time handling follows rulebook §2 (T1)
- `timeparse.py` now ends "tuần này / tháng này / quý này / năm nay" on `as_of_date`, not on the
  period end, and handles "từ đầu năm" as 01/01 → today. A quarter without a year uses this year
  only when it does not start after today. Why: rulebook §2 defines these as periods to the end of
  today, and the old resolver returned future days that the data excludes anyway; the agent was
  being told to filter on ranges that did not match the rulebook.
- "tháng này so với tháng trước" now caps the previous month at the same day number as today
  (month end when that day does not exist). Why: §2 compares windows with the same number of days;
  the old whole-previous-month range gave the comparison a different denominator.
- Tết is resolved from the split's `calendar.csv` through `LunarCalendar` (23 tháng Chạp of lunar
  Y−1 to 10 tháng Giêng of lunar Y), and "trước Tết" is the same number of days immediately before.
  The calendar is loaded once in `QAService` from `IngestService.calendar` and passed to the graph,
  so no date is hard-coded and no network is needed. Why: lunar dates cannot be computed from the
  solar date alone, and the rulebook names `calendar.csv` as the source.
- `time-expressions/SKILL.md` is rewritten row by row from §2: future rows have not happened (with
  the cancel/return exception), comparison operators exclude or include N, the shifts are fixed
  clock windows, and "đến hết ngày X" is a balance counted from the start of the data.
- Tests cover every T1 row; the Tết tests build a four-row `calendar.csv` fixture, so the suite
  stays offline and deterministic.

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
