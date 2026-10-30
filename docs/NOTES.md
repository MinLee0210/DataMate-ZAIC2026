# Decisions log

Newest at the top. Record *why*, not just *what*.

## 2026-10-30 - New pod, Vietnamese prompts tested, sample failures, ensemble

- Pod: 2x RTX 5090 (same as the competition machine), one Qwen3.5-9B replica per GPU (fp8 at
  load, ports 8011 / 8012), run from `/workspace/DataMate-ZAIC2026`. Public halves run in two
  processes over `--ids` files (even / odd line of `questions.jsonl`).
- **Vietnamese prompts (`PROMPT_LANG=vi`)**: Vietnamese copies of the dataAgent prompts and skills
  (`prompt_templates/vi/`, `skills/*/SKILL.vi.md`; JSON keys, actions and SQL stay English).
  Same code, dev200, k=1, thinking on, two replicas at the same time. On the 82 questions both
  had finished: **en PA 0.43 (55/20/7), vi PA 0.23 (31/12/39)**. vi used about 2x the completion
  tokens (7.3k vs 3.4k per question) and abstained far more (Vietnamese thinking runs into the
  10,240-token cap). English stays the default; vi is kept for a later test with a larger budget.
  Full en dev200: PA 0.38 (128/52/20), 13 min (last night, other code: 0.415; noise on 200).
- **Bug: one bad sample lost the whole question.** With k=3, an unparseable reply after the retry
  raised out of `MaltPipeline.run`, so the question abstained although the other samples had
  answered: 41 of 1,000 public questions in the 2026-10-28 k=3 run. A failed sample is now an
  abstain vote.
- Label-free look at that run's SQL errors: 704 failed queries in 3,000 samples. Most are the model's
  own mistakes (a column used on the wrong table or alias: `ma_bill` is in `chi_tiet_don`, not
  `don_hang`; invented columns; `x::T` inside `CAST`). The retry hint now names the table that owns
  the column, or the closest real column names (`error_hint`).
- `scripts/ensemble.py`: votes from several runs of one split (every sample of a k>1 trace and
  every k=1 trace is one vote; a missing or failed sample is an abstain vote). On dev (known
  answers; k3 + k1 + k1, 5 votes) precision stays 0.83-0.90 whatever the gate, and PA is highest at
  the loosest gate (2 of 5: 0.595) because dev precision is far above 0.5. Public is not like dev
  (35 % right at k=1), so public files use a stricter gate; two uploads with different gates
  measure what the marginal answers are worth.
- `MALT_VARIANT_OFFSET`: sample i uses approach `(offset + i) % 6`; `malt_variants.md` has 3 new
  approaches (rulebook-first, two independent computations, defensive about the data). Offset 3
  gives three votes that differ from the first three, and stays inside the final solution's rules
  (same model, same code).
- Not measured: the effect of the sample-failure fix and the column hints on PA. They change which
  questions get an answer, not what an answered question says.

## 2026-10-29 - NULL-safe status predicates

- `is_cancelled(NULL)` and `is_returned(NULL)` previously returned SQL NULL. A common valid-order
  predicate using `NOT` on both therefore silently dropped rows with missing status. The macros
  now return false for NULL status, so such rows remain eligible. A regression test executes the
  exact filter over NULL, completed and cancelled orders.
- Bumped `INGEST_VERSION` to 8 because semantic macros are stored in the per-business DuckDB cache.
  This is a verified correctness fix, not a measured PA improvement. A target-model run on a
  clean business-family split is still needed to assess its scoring effect.

## 2026-10-28 - Product architecture review and bounded MALT calls

- Compared the architectures of hosted analytics products in
  [PRODUCT_ARCHITECTURES.md](PRODUCT_ARCHITECTURES.md).
- Their transferable pattern is curated business semantics plus executed queries and isolated
  benchmarks. DataMate's generic semantic layer remains thin, so rulebook metrics are the next
  architecture target.
- Enforced four actual MALT LLM calls per sample, including parse retries. The old failed-query
  path could use five calls; now it abstains after four. This preserves the documented inference
  budget and makes the trace count reflect calls rather than successful thought messages.
- Unit tests establish behavior only. PA and runtime effects require a target-model eval.

## 2026-10-28 (late) - Public k=1 is negative; agreement filters; model check on dev200

- Public results for Qwen3.5-9B:
  - k=1: -0.259 (about 298 right / 557 wrong, 35 % right when answered, vs 73 % on dev200).
  - k=1 + few-shot: -0.261.
  - DeepSeek with the same pipeline got +0.104 (about 54 % right). The pipeline works; the
    9B model is much weaker on the public shops.
  - dev200 and the hold-out both overstate public scores badly.
- Below 50 % right, every extra answer lowers PA, and an all-abstain file scores 0.
  - On dev200 k=3, right-when-answered by votes for the top answer: 3/3 89 %, 2/3 67 %,
    1/3 17 %.
  - Built stricter public variants from the five runs (#1, #2 and #3's three samples), in
    `data/results/2026-10-28/public-test-qwen35-9b-k3-agree*`:

    | Variant | Answered |
    |---|---|
    | agree3 | 386 |
    | agree4of5 | 356 |
    | agree5of5 | 278 |

  - Plan: upload agree4of5 next (no uploads left on 2026-10-28).
- dev200, k=1, today's code:

  | Model | PA |
  |---|---|
  | Qwen3-14B-FP8 | 0.455 |
  | Qwen3.5-9B | 0.415 |
  | Qwen2.5-Coder-14B-Instruct | 0.0 (50 % right when answered) |

  - Drop the coder model.
  - Qwen3-14B is slightly ahead; within noise on 200 questions, and about 1.5x slower.
- Next on a pod: Qwen3-14B with k=3, the E3 skill rules, an eval set closer to public.
  - Nothing overnight: pod cost.

## 2026-10-28 - Self-consistency k=3 wins on dev200 (E1); public #3 uses it; E2 paused

- E1, Qwen3.5-9B, dataAgent + thinking, no few-shot, dev200 in two halves:
  - k=3: 144 right / 40 wrong / 16 abstain, PA **0.520**.
  - k=1 (qwen35-9b-v2-dev200): PA 0.415.
  - Right when answered: 78 %, up from 73 %.
  - Cost: about 3x the time per question.
- With k=3 the agreement between samples is a real signal, unlike self-reported confidence.
  - `scripts/calibrate.py` picks tau 0.35 in all 4 folds.
  - Development PA: 0.521 without the gate, 0.549 cross-fitted.
  - Hold-out check: 0.517 without the gate, 0.586 at tau 0.35.
- Why public #3 is k=3 + tau 0.35: it is the largest measured gain. A 1000-question k=3 run takes
  about 95 min on 2x RTX 5090, which only fits before the 22:00 deadline if E2 stops.
- E2 (k=1 over the rest of the development set) stopped after about 60 questions. It feeds
  cross-fit calibration and few-shot examples; rerun it later, with k=3 now that k=3 is the
  candidate.
- Skill rules written locally from development-only errors, not yet synced or measured (E3):
  - debt collected by payment date, without the checkout payment;
  - effect of a price change;
  - growth direction;
  - status counts through `is_cancelled`;
  - answer shape.

## 2026-10-28 - Bake-off results; self-reported confidence is useless; self-consistency
- From now on no hosted API: every run is a model on the GPU pod (user decision).
- dev200, same code (ingest v7, confidence field, unanswerable evidence, query retries):
  Qwen3.5-9B (thinking, `presence_penalty` 1.5) PA 0.415 (131/48/21, 73 % right when answering);
  Gemma-4-12B (no thinking: with thinking it loops at temperature 0) 0.28 (118/62/20, 66 %).
  Qwen3-14B-FP8 (older code) 0.43. Hold-out v1 numbers (0.645 / 0.505) leak and are not used.
  **Qwen3.5-9B is the main model**: about Qwen3-14B's PA, 5B smaller, faster, cheap KV cache.
- **Self-reported confidence does not separate right from wrong**: Qwen3.5 said 0.9 on 164 of
  179 answers. Cross-fitted threshold: no gain (0.4085 -> 0.4014). The unanswerable-evidence rule
  does help (Gemma 0.2465 -> 0.3169 cross-fitted). Keep MIN_CONFIDENCE at 0.05 (it only drops
  evidence-less unanswerable).
- **Self-consistency** (`CA_SAMPLES`, `CA_MIN_AGREEMENT`): the dataAgent loop runs once per
  approach in `malt_variants.md` (direct; bottom-up from lines; independent pandas check), with
  different seeds; the answer is the majority, `agreement` its share, gated by
  CA_MIN_AGREEMENT. The vote pipeline did this with DeepSeek and reached 91 % right when
  answering. Costs k times the time; measure k = 3 on the folds before using it.
- Running: Qwen3.5-9B on the whole development set (2,131 questions, 4 family folds, two
  replicas on the two GPUs, few-shot off) for cross-fitted calibration and few-shot examples.

## 2026-10-28 - Evaluation protocol from another team's repo; hold-out v2; few-shot BM25
- Read baond12/zalo-ai-challenge-2026-datamate (stage A only: audit, splits, scorer; no agent,
  no score; dev box 1x P100 with a 2,048-token context). Adopted their protocol ideas:
  - **Hold-out by schema family** (`scripts/splits.py`). Several businesses share one export
    template; hold-out v1 (biz_102, 106, 114, 120, 125, 130) had family members in development
    for 4 of 6 businesses. v2 holds out whole families: biz_102, 103, 104, 121, 122 (one
    template across grocery, cafe, pharmacy), biz_117, biz_129, biz_125; 869 questions, all five
    sectors. Families: any transaction table (6+ columns, 1,000+ rows) with Jaccard >= 0.8.
  - **Family-grouped folds** (4) over development and **sector subsets** (`--subset fold2`,
    `sector:pharmacy`, `development200`, `holdout200`).
  - **Cross-fitted threshold** (`scripts/calibrate.py`): MIN_CONFIDENCE is chosen on the other
    folds and scored on the held fold, so the reported PA is not in-sample. Self-reported
    confidence is a score to threshold, not a probability.
  - **Hold-out exposure log** (`docs/holdout_exposure.md`); v2 is "seen format" because its
    businesses were in dev200 error analysis before; no more error analysis on them.
  - Not adopted: stdlib-only ingest without cleaning, P100 / 2,048-token settings.
- **Few-shot examples** (`modules/context/examples.py`, `FEW_SHOT_K`, default 3): BM25 over
  folded questions with numbers masked; verified train SQL only (answer matched the reference),
  never hold-out businesses, never the asking business's family. Built by
  `scripts/datagen/build_examples.py` from eval traces; 101 examples so far.
- `docs/submission_log.md`: every public upload, one change per upload from now on.
- Qwen3.5-9B with `presence_penalty` 1.5 (thinking): 2 failed questions in the first 60 instead
  of 16; the greedy thinking loops are mostly gone.

## 2026-10-28 - Public leaderboard: DeepSeek 0.104, Qwen3-14B -0.411; ingest v7; confidence gate
- Leaderboard PA on public_test (1000 questions):
  - deepseek-flash, dataAgent with thinking, ingest v7: **+0.104** (902 answered, 98 abstain,
    21 unanswerable: about 503 right, 399 wrong, 56 % right when answering). First positive score.
    Run on the hosted API at the user's request (like the earlier exception), 48 threads, 13 min.
  - Qwen3-14B-FP8 on 2x RTX 5090, same pipeline, ingest v5: **-0.411** (875 answered, 125 abstain,
    82 unanswerable: about 232 right, 643 wrong, 27 % right). On train dev200 the same model is
    right 73 % of the time when it answers.
  - So the pipeline works on public data with a stronger model; Qwen3-14B's gap is the model on
    new businesses (plus the two ingest bugs below that the DeepSeek run already had fixed).
- Ingest version 7, two bugs that only hurt public_test:
  - Split tables were merged by month number only (`banhang_t1` = T1/2025 + T1/2026,
    `banhang_t10_2025` separate): the base name now drops period tokens (`_t1`, `_thang05`,
    `_m3`, `_q2`), so dev_002 and dev_005 have one `banhang` table.
  - The fill-down also filled order-level money (`tong_phieu`, dev_004: 18,138 cells), so a sum
    over lines counted each order total once per line. Numeric columns are no longer filled.
- dataAgent (not measured yet):
  - The final step reports `confidence` (0-1). The trace records it as `agreement`, so the eval
    draws PA vs tau; `MIN_CONFIDENCE` gates answers (default 0 until chosen on dev200).
  - "unanswerable" must give `evidence` (the missing concept or the period with the data's first
    and last date); without it, its confidence is 0.
  - Query retries: a failed query's error lists the columns of the tables it named (no LLM); a
    failed extra query earns one more step (at most 5 LLM steps, only when queries fail: about
    3.5 % of public questions); a non-JSON reply in steps 1-2 is asked again once.
- Docker requirements read from the portal's Data tab: `predict.sh` (added at the repo root) and
  per-question logs in `/result/logs/` (now `<out>/logs/questions.jsonl`: id, answer, seconds,
  question, full trace).
- Model bake-off on dev200 (same code as the DeepSeek public run): Qwen3.5-9B with thinking runs
  well; Gemma-4-12B with thinking at temperature 0 loops until the 10,240-token cap on 14 of 16
  questions, so it is measured with thinking off.

## 2026-10-28 - Qwen3 on dev200: right more often, but rarely abstains; fixes for its 50 errors
- dev200 on 2x RTX 5090, Qwen3-14B-FP8, dataAgent with thinking, ingest v5 and today's fixes:
  PA 0.43 (136 right / 50 wrong / 14 abstain), 73 % right when it answers. deepseek-flash, same
  pipeline before today's fixes: PA 0.55 (122 / 12 / 66), 91 %. Qwen3 gets more right (40 that
  DeepSeek skipped) but answers almost everything, so its 50 wrong answers cost more than the
  extra right ones give: a calibration problem, not a solving one.
- The 50 wrong (train, gold known), by cause: money not rounded to whole VND (4: ROUND(x, 2) on an
  average order value); one spelling of a status or of the walk-in customer (about 5: a cancel
  count of 0 with `hủy đơn` and `Đã hủy đơn` in the data; "kl", "lẻ" ranked as top customers);
  unit or scale (about 7: percent 0.66 for 66.01, price per pill vs per box, sum vs average);
  answer shape (4: a table for a list); wrong unanswerable (5); revenue or period off by 1-15 %
  (about 12); question misread (about 8: "số bill" as money, ×19, ×99).
- Fixes (not measured yet):
  - Number answers to money questions are rounded to whole VND, half up
    (`utils.format.is_money_question`, `round_money`, applied in the dataAgent final step).
  - Semantic layer macros in every database (`assets/semantic/text_and_status.sql`): `fold`,
    `is_cancelled`, `is_returned`, `is_walk_in`, for every spelling of a status and of a walk-in
    customer ("hoàn thành" is not a return). The loader used to drop a statement with a comment
    above it, so these are the first statements it ever created. Ingest version 6.
  - business-metrics skill: the macros, units and prices, percent in points, counts of bills.
  - The results prompt checks unit and scale, spellings, shape and plausibility one by one and
    abstains when a check fails.
- Next: dev200 again on the pod with these fixes; then work on abstention (a second, independent
  check of the final answer) if wrong answers stay high.

## 2026-10-28 - First target-model run (A40), stopped at 137/1000; fixes from it
- public_test on Qwen3-14B-FP8, vLLM 0.32 on 1x A40, dataAgent with thinking, 12 workers. Stopped
  at 137 questions (the user moved to 2x RTX 5090). Files: data/results/2026-10-28/
  public-test-qwen3-partial/raw (submission, trace, logs); W&B run 2026-10-28/public-test-qwen3-partial.
- Speed: about 40 s per question at 12 in parallel (about 11 h for 1000 on an A40); 4,465
  completion tokens and 3.4 LLM steps per question; 16k prompt tokens per call; 4 calls cut at the
  10,240 thinking budget. Each reasoning step took 130-165 s under load.
- 47 of 137 abstained, but about 39 of them were not the model's choice: in the final step Qwen3
  wrote the value ("42149500"), an index ("0") or nothing instead of the result's name, and the
  answer was dropped; 7 more were JSON errors (invalid escapes, a missing comma).
  Fixes: `ca.resolve_result` (name, case-insensitive name, index, a result holding that value,
  the only usable result), the prompt lists the result names, invalid escapes are repaired, and a
  JSON error in step 3 is shown to step 4 instead of failing the question. Replaying the traces'
  SQL offline: 22 of the 39 now resolve to a result; the other 17 had a value the model computed
  itself (left as abstain).
- 16 of 137 were "unanswerable" (train: 2.3 %). 4 were dates the model could not parse, others a
  too strict reading ("no column matches the revenue definition"). Ingest now parses mixed dates;
  the results prompt says when a question is not unanswerable (computable measure, spelling,
  date parsing, an empty period inside the data).
- Ingest version 5 also drops subtotal rows and repeated header rows (details in
  notes/2026-10-27/data-errors/notes.md, errors 6-8). Train had text date columns in 6 businesses
  and subtotal rows in 5, unnoticed until now.
- Not measured yet: none of these fixes has a dev200 or public score; the next run is on 2x 5090.

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

## 2026-10-27 - Ingest fixes from error analysis; messy-data skill; MALT with thinking
- Four ingest errors made tables wrong (details and affected businesses:
  [notes/2026-10-27/data-errors/notes.md](notes/2026-10-27/data-errors/notes.md)): dot thousands
  read as decimals, money shorthand (`25k`, `1,5tr`) left as text, tables split by month or part,
  grouped exports with blank parent cells. All four are fixed in ingest, deterministically.
  `INGEST_VERSION` (now 3) is part of the cache key.
- The same knowledge is a skill (`assets/skills/messy-data`): what ingest cleaned, and how to
  check and fix the rest in SQL or pandas, for cases ingest does not catch.
- MALT pipeline with thinking on every step (old ingest): PA 0.55 (122/12/66), 23 s/question. Only
  12 wrong out of 134 answered (91 %): with thinking, the last THOUGHT abstains when unsure.
- `python_exec.py` moved to `src/modules/`.

## 2026-10-27 - MALT: a bounded reasoning loop for the dataAgent
- New `PIPELINE=malt` (`src/services/qa/malt.py`): schema message → THOUGHT → PROGRESS (sample field
  values) → DATA (named query → SQL → named result) → THOUGHT on the results → ANALYSIS (Python over
  named results) or one more DATA → FINAL. Errors are recoverable and shown to the next THOUGHT.
- Bounded for the competition: at most 4 LLM steps (THOUGHT 1 schema, THOUGHT 2 queries,
  THOUGHT 3 results, THOUGHT 4 only after an analysis or extra query). PROGRESS is deterministic
  (`modules/context/sampling.py`): distinct counts, top values, min/max, and the number of rows
  after the as-of date. The final value is formatted in code from the named result.
- No charts, no natural-language answer, no clarifying questions, and the last THOUGHT may abstain
  (PA punishes a wrong answer).
- Python analysis runs in `src/modules/python_exec.py`: AST check (no imports, dunder or private
  names, file or reflection builtins), `results`, `pd` and a read-only `query()`, timeout.
- The vote pipeline stays as `PIPELINE=vote` (default until the MALT run is measured).
- Why: the vote pipeline went straight from question to SQL; an intent and schema step was missing.
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
- The demo app will draw a chart next to the answer, as hosted analytics products do. The challenge does
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
