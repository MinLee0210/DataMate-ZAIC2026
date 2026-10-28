# Plan: next steps (handoff)

Written 2026-10-26 for an agent picking up the work. Each task is self-contained: goal, why, files,
steps, and a check that says when it is done. Do them in order within a milestone unless marked
**parallel**. When a task is finished, tick it here and add a line to docs/NOTES.md.

## Tonight (2026-10-28) after public #2, until 22:00: experiments to lift the score

Agreed with the user: once public #1 (Qwen3.5-9B, k=1) and #2 (+ few-shot) are done, use the
pod (2x RTX 5090, a Qwen3.5-9B replica per GPU) for as many experiments as fit. Pod only, no
hosted API. Each experiment: one change, scored on development folds (never the hold-out v2),
logged to W&B and NOTES.md; Google Chat ping every 100 questions and at the end.

1. [ ] **Resume the train development folds** (k=1, few-shot off; 787 of 2,131 done, partial
   traces in `/tmp/dm-fold*/trace.partial.jsonl`): cross-fitted threshold
   (`scripts/calibrate.py`) and a bigger few-shot store (`scripts/datagen/build_examples.py`,
   from about 100 to about 1,000 verified examples).
2. [ ] **Self-consistency k=3** (`CA_SAMPLES=3`, sync the code to the pod first) on
   `development200`: PA, wrong answers, abstentions, seconds per question; pick
   `CA_MIN_AGREEMENT` by cross-fit. Expected: fewer wrong answers (the vote pipeline reached
   91 % right when answering).
3. [ ] **Few-shot with the bigger store** on `development200`, compared with #2's 101 examples.
4. [ ] **Qwen3-14B-FP8 with today's code** (thinking + `presence_penalty`) on `development200`,
   vs Qwen3.5-9B on the same questions.
5. [ ] Speed knobs if time is short: thinking only in the results step; `ANALYZE_MAX_TOKENS`
   6144; k=2 with early stop when the first two agree.
6. [ ] If one change clearly beats #1/#2 on the folds: **public #3** with that change only
   (`docs/submission_log.md`).

## Next session (2026-10-28): first run on a GPU pod

The user provides a pod (A40, 48 GB) with its SSH config. Goal: the first legal public_test
submission with the target model, and the real dev200 PA of Qwen3-14B. Every number so far is
from hosted `deepseek-flash`. Runbook: [scripts/pod/README.md](../scripts/pod/README.md).

Where we are (2026-10-27): dataAgent (`PIPELINE=ca`) with thinking is the best setup, dev200 PA
0.55 (122 right / 12 wrong / 66 abstain) on deepseek-flash, measured **before** the four ingest
fixes. Public leaderboard: −0.169, then −0.023 (deepseek-flash, vote pipeline + rulebook).

1. [ ] **Get the pod config** from the user: SSH host, port, user, key; GPU, CUDA version, disk,
   internet. Check `nvidia-smi` and the disk (about 100 GB).
2. [ ] **Copy and set up**: rsync the repo and `data/train`, `data/public_test`; write the pod
   `.env` (runbook §2); run `./scripts/pod/setup.sh` (uv, project env, vLLM in `.venv-vllm`,
   weights in `/models/target`, ingest of both splits).
3. [ ] **Start vLLM**: `TP=1 QUANTIZATION=fp8 ./scripts/vllm.sh` in tmux. It is ready when
   `curl 127.0.0.1:8001/v1/models` answers. If YaRN or `--hf-overrides` fails on that vLLM
   version, check the flag name and fix `scripts/vllm.sh`.
4. [ ] **Smoke test** one train question (`notebooks.llm_call --id q_001883280e83`): the answer
   is right, there is a `<think>` block, the reply is parsed, and the time per question is noted.
5. [ ] **dev200 on Qwen3-14B**: `make eval SUBSET=dev200 TOPIC=qwen3-ca-thinking WORKERS=8`.
   Record PA, the share of question errors (cut-off thinking, bad JSON) and seconds per question.
   If more than about 5 % of the questions fail, lower `ANALYZE_MAX_TOKENS` or turn thinking on
   only for the "think on the results" step, then measure again.
6. [ ] **Same dev200 with thinking off** (`ANALYZE_EXTRA_BODY=`) to see what thinking costs in
   time and gives in PA on the target model.
7. [ ] **public_test**: `START_VLLM=0 SPLIT=public_test ... ./scripts/infer.sh`, then
   `scripts.export --topic public-test-qwen3`. Check 1000 lines with the strict checker, then
   the user uploads it.
8. [ ] **Rerun check**: run public_test a second time and diff the two files (rule 8: PA
   difference ≤ 0.03). Count the lines that differ and look at why.
9. [ ] **Time budget**: from steps 5 and 7, estimate the time for the private test on 2x RTX 5090
   (rule 7: 6 h including model loading). Decide whether thinking fits.
10. [ ] Write the results to docs/NOTES.md and EXPERIMENTS.md (eval does the rows), commit and
    push (pre-commit first; `git_acc personal`, then back to `work`).

Later (agreed 2026-10-28): **evaluate two other target models** against Qwen3-14B-FP8, same
pipeline, dev200 + holdout200, on the GPU pod (about 20-25 min and 1 USD each on 2x RTX 5090).
Survey: [reports/2026-10-28/llm-candidates](reports/2026-10-28/llm-candidates/report.md).
11. [ ] `Qwen/Qwen3.5-9B` (9.65B, 2026-02-27, Apache-2.0): thinking on by default, 201 languages.
12. [ ] `google/gemma-4-12B-it` (11.95B, 2026-05-23, Apache-2.0): configurable thinking.
    For each: read the licence file, confirm date and parameter count from `config.json`, check
    vLLM 0.32 support and the chat template's thinking switch (`ANALYZE_EXTRA_BODY` may differ
    from Qwen3's `enable_thinking`), and add the row to docs/MODELS.md **before** running it.

Also open, not blocking the pod run:
- The dev200 run of dataAgent with thinking on the fixed ingest (`ca-thinking-ingest3`) was
  stopped. Re-run it on deepseek-flash if the pod is late, to measure the ingest fixes.
- 66 abstentions out of 200: find which ones the model could answer (error analysis on train).
- Revenue definitions off by 1–4 % (about 20 wrong answers): fill the `business-metrics` skill
  and semantic views from the rulebook (T2, T3).
- Hold-out by business or shop type before any fine-tuning on train (dev200 overlaps train
  businesses).
- Rename `PIPELINE=ca` / `ca.py` / `ca_*.md` to dataAgent if the user wants it.
- The default `PIPELINE` in `src/config.py` is still `vote`; switch to `ca` once the pod results
  confirm it.

## 0. Read first

1. `CLAUDE.md`: hard rules (offline, ≤ 15B, no test answers, no business-specific code,
   determinism, ≤ 4 LLM steps) and workflow rules.
2. `docs/CHALLENGE.md`: the task, answer format and scoring. `data/train/rulebook.md`: the business
   rules, in Vietnamese. **The rulebook is the ground truth for every answer.**
3. `docs/SUGGESTIONS.md`: the backlog. The S-numbers below refer to it.
4. `README.md` and `src/README.md`: architecture and layout.

**State on 2026-10-26.**
- The pipeline runs end to end. It has deterministic ingest, a time resolver and entity linking, a
  LangGraph agent (k candidates, repair, vote) and a formatter.
- The official scorer is in `src/evaluate/`.
- Cost and calibration metrics are in `src/evaluate/metrics.py`.
- `make ingest SPLIT=train` works.
- **No baseline PA exists yet.** The rulebook knowledge is mostly not written into `src/assets/`
  yet.

**Working rules for the agent**
- No improvement counts without `make eval SUBSET=dev200 TOPIC=<name>`. The script writes
  `docs/analysis/<date>/<topic>/` and a row in `docs/EXPERIMENTS.md`. Never copy numbers by hand.
- Tune only on train. Never look at public_test answers (there are none) or private_test. Never use
  a hosted model on public_test or private_test questions, except for the hosted copy of the target
  model in dev_free, which `src/` uses through `LLM_BASE_URL`.
- Skills and semantic views must be generic. Never branch on `business_id` or question `id`.
- Run `make test lint` before every commit. New logic in `utils/` or `modules/decide/` needs unit
  tests, with no network and no GPU.
- Git: this repo is under `.researchs`, so run `git_acc personal` first. The commit email must be
  `minh.leduc.0210@gmail.com`, never the company email; any name is fine. Do not add Claude
  attribution lines. Run `git_acc work` when done. Push only when the user asks.

## Milestone 1 — measured baseline (by 01/11)

### T1. [x] Make time handling match rulebook §2 *(S1, high impact, small)*
**Why.** Number and percent are 82% of train answers, and most of them are bounded by time. The
skill and the resolver currently contradict the rulebook.

**Files.** `src/assets/skills/time-expressions/SKILL.md`, `src/utils/timeparse.py`,
`tests/test_timeparse.py`.

**Fix each of these:**

| Rulebook §2 | Now |
|---|---|
| Files can contain rows dated after `as_of_date`; treat them as not having happened. Exception: an order's cancel/return status is read as written | The skill says such rows "do not exist" |
| "Tuần này / tháng này / quý này / năm nay": from the period start to **the end of today** | `timeparse.py` goes to the end of the period |
| "Từ đầu năm (tới nay)": 01/01 → today | not handled |
| "Tháng M" / "quý Q" with no year: this year if not after today, else the previous year | quarters always use this year |
| "Tháng này so với tháng trước": the previous month uses the **same number of days** (day 1 → the same day number, capped at month end) | not handled |
| "N ngày gần nhất": N days including today | check that it matches |
| "Quá / hơn / trên / dưới N" exclude N; "từ N trở lên" includes N | put in the skill |
| Tết of year Y: solar date of 23 tháng Chạp (lunar Y − 1) → 10 tháng Giêng (lunar Y), from `calendar.csv`. "Trước Tết" = the same number of days just before | not handled: add a resolver rule that reads the calendar |
| Ca sáng 06:00–13:59, ca chiều 14:00–21:59, by the order's creation time | put in the skill |
| "Đến hết ngày X / tính đến hôm nay" asks for a balance (debt, stock): everything from the start of the data to the end of X | put in the skill |

**Done when** each row has a unit test, `make test` passes, and the skill text matches the rulebook.

### T2. Write the rulebook into skills *(S5, high impact, medium)* — **parallel with T1**
**Why.** The agent cannot know "revenue excludes the whole order if anything was returned",
"rank by revenue unless told otherwise", the debt rules or the cost-of-goods rules unless they are
in its context.

**Files.** `src/assets/skills/*/SKILL.md`. Add skills where a topic is large.

**Steps.**
- Fill `business-metrics` from rulebook §1 (orders and revenue), §4 (debt) and §5 (stock, purchases,
  cost of goods). Write each term as *term → Vietnamese synonyms → definition → which semantic
  view implements it* (CA-style glossary).
- Update `ranking-rules` from §3 (customer identity, walk-in customers, service-fee lines, tie
  rules) and the list/table ordering rules in §9.
- Update `unanswerable` from §7. The key point: no data is different from 0.
- Add `shop-types`, one section per §6 shop type. Include the **public_test** types too (baby
  goods, motorbike repair, phone shop). They are in `data/public_test/rulebook.md`, which holds
  rules, not answers, so it may be read.
- Update `answer-types` for money (see T4).
- Keep each skill short. They all go into the prompt, so check prompt tokens in the eval's
  Efficiency section.

**Done when** every rulebook section is covered by a skill, and the T5 baseline shows the effect.

### T3. Semantic layer that takes `as_of_date` *(S6, high impact, medium; after T2)*
**Why.** The rulebook filters (valid order, returned order, the order's period by order date) are
repeated in every query, and a 14B model gets them wrong. They should be defined once.

**Files.** `src/assets/semantic/*.sql`, `src/modules/semantic/views.py`, `business-metrics` skill.

**Steps.**
- Read several train business READMEs and schemas (`$WORK_DIR/ingest/`) to see which column
  roles recur: order id, order date, status, item, quantity, base unit, price, discount.
- Ingest cleans the files but does not rename columns to roles, so first decide how views find
  their columns. Options:
  - **(a)** a deterministic role mapper at ingest (header synonyms → role) that creates standard
    views such as `orders_std` and `order_lines_std`;
  - **(b)** DuckDB table macros whose parameters the LLM fills.

  Prefer (a) where the mapping is reliable, and **record the decision in NOTES.md**.
- Bound time with `as_of_date`, through a macro parameter or a view that filters
  `order_date <= as_of`.
- A statement that does not apply to a business is skipped (`views.py`). Keep statements small.

**Done when** the views exist for most train businesses (log coverage) and dev200 PA on
number/percent rises against the T5 baseline.

### T4. Money is whole VND *(small)* — **parallel**
Rulebook §9: money is a whole number of VND, and an average of money is rounded to the đồng (half
rounds up). Other averages and percents use 2 dp. `src/utils/format.py` rounds every number to 2
dp. Put the rule in `answer-types` so the SQL does `ROUND(x)` for money. Consider a `money` hint
in the plan JSON (the `sql_agent.md` reply format) so the formatter can round to an integer.
**Done when** there are tests for both cases and no `wrong_value` in the eval comes only from
.5 VND.

### T5. Baseline eval and error analysis *(after T1–T4)*
- `make ingest SPLIT=train`, then `make eval SUBSET=dev200 TOPIC=baseline`.
- Write `docs/analysis/<date>/baseline/errors.md`: sort the `wrong_*` and abstain rows from
  `scored.jsonl` into causes (time, entity, metric definition, type or format, join, ingest
  parsing, unanswerable confusion), with counts and 2–3 examples each.
- Read the PA-vs-tau curve and set `TAU` (in `.env` / `src/config.py`) to the best value, noting
  the agreement AUROC.

**Done when** the summary, errors.md and the EXPERIMENTS.md row exist, and the top 3 error causes
are listed in NOTES.md as the next targets.

### T6. First public-test submission *(after T5)*
`uv run python -m src --split public_test --out <dir>`. Check that every line parses with
`src.evaluate.parse_line` and that the type distribution looks like train. Then hand the file to
the user to upload: the agent never uploads. **Done when** the file exists and passes the format
check.

### T7. GPU smoke run *(parallel; needs the GPU machine)*
- Pin a vLLM image that supports RTX 5090 (Blackwell, CUDA ≥ 12.8) in `Dockerfile`; download the
  weights to `models/target`.
- `make vllm`, then run dev200 with `LLM_BASE_URL=http://127.0.0.1:8001/v1`. Compare its PA with
  the hosted run; it should be close.
- Test `VLLM_BATCH_INVARIANT=1` (S17): run twice, then send the k candidates concurrently and
  check the outputs are identical.

**Done when** the seconds per question and the "questions per 6 h" from the Efficiency section are
recorded in NOTES.md.

## Milestone 2 — accuracy and calibration (02/11 – 08/11)

Each task is one dev200 experiment with its own TOPIC, kept only if PA improves.

| ID | Task | Backlog | Notes |
|---|---|---|---|
| T8 | Value search: entity links return table.column, concept type and distance; show the top-n when they are close | S7 | `modules/context/entities.py` |
| T9 | Column synonyms and tags in the schema card; prune the card to linked tables and columns, keeping join keys | S3, S10 | `modules/context/schema_card.py` |
| T10 | Teacher datagen on train: `scripts/datagen/teacher.py` has `DATAGEN_BASE_URL` and `DATAGEN_MODEL` but reads its key from `OPENROUTER_API_KEY` and defaults to OpenRouter; add a `DATAGEN_API_KEY` setting so it can use the HF router. Generate verified (question, SQL, answer) examples and check them against train gold where the questions overlap | S8 prep | train only; API allowed only in `scripts/datagen/` |
| T11 | Retrieve examples by masked intent (time and entities replaced by slots, then BM25), top-3, checked against the schema. Add a "trusted" path for exact template matches | S8, S9 | evaluate leave-business-out |
| T12 | Confidence model (agreement + entity distance + template hit + empty result + repairs) → logistic regression, CV grouped by business. Abstain when candidates disagree because they read the question differently | S14, S11 | `modules/decide/`; report the PA-vs-tau curve |
| T13 | Target-model bake-off: Qwen3-14B against Arctic-Text2SQL-R1-14B, Qwen2.5-Coder-14B and OmniSQL-14B. Check each model card (release date before 2026-10-01, licence, parameter count) and add it to `docs/MODELS.md` **before** running it | S12 | same pipeline, dev200 |

## Milestone 3 — ship (09/11 – 16/11)

| ID | Task | Done when |
|---|---|---|
| T14 | Build Docker with the weights baked in; `make docker-build && make rerun-check` | the image runs with `--network none`; two runs differ by ≤ 0.01 PA on dev |
| T15 | 6 h budget test on a set as large as the expected private test; tune `TIME_BUDGET_S` | the run finishes with ≥ 30% margin; appends survive a kill |
| T16 | Final checks: `docs/MODELS.md` and README declare every model; `FINAL_MODE=1` refuses non-local URLs; no API client imported in `src/` | checklist in NOTES.md |
| — | **16/11 23:59**: the user submits the solution (max 2 uploads, the last counts) | |

## After the competition path — demo app

| ID | Task | Notes |
|---|---|---|
| T17 | Demo UI in `app/` on top of `POST /ask` | after `src/` is done |
| T18 | **Charts in the app** (planned feature, not scored): `/ask` returns a chart spec built from the winning result, with the chart type chosen from the answer type and result shape | see SUGGESTIONS.md S18; the batch path never draws charts |

## Prompt to give another agent

> You are working on the DataMate repo (Zalo AI Challenge 2026). Read `CLAUDE.md`,
> `docs/CHALLENGE.md`, `docs/PLAN.md` and `data/train/rulebook.md` first. Do task **T<n>** from
> `docs/PLAN.md` only. Follow the working rules in §0 of the plan: train data only, generic skills
> and views, `make test lint` green, eval with `make eval SUBSET=dev200 TOPIC=<name>` when the task
> asks for it. When done, tick the task in PLAN.md, add a dated entry to `docs/NOTES.md` with the
> why, and commit with the personal git identity and no Claude attribution. Do not push. Report the
> PA change and anything you could not finish.
