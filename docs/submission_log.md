# Public leaderboard submissions

Rules (adopted 2026-10-28):
- At most 5 uploads a day. Slots 1-3: one deliberate change each, so a score difference has one
  cause. Slot 4: re-upload the best version (regression check). Slot 5: spare.
- Upload only when the change already helped on **holdout200** (businesses never used for error
  analysis or examples); dev200 overstates public scores (Qwen3-14B: 73 % right on dev200, about
  27 % on public).
- Log every upload here: time (VN), commit, what changed, the file in `data/results/`, PA. Add the
  PA to the W&B run (`leaderboard_pa`).

| # | Date, time (VN) | Code | Model, pipeline | What changed vs. the previous upload | File (`data/results/…`) | Answered / abstain / unanswerable | Public PA |
|---|---|---|---|---|---|---|---|
| 1 | 2026-10-27 | before d29997d | – | uploaded the **train dev200** file by mistake (no public ids) | `2026-10-27/baseline/` | – | 0.0000 |
| 2 | 2026-10-27 ~17:00 | before d29997d | deepseek-flash, vote (k=3) | first public run, no rulebook in the prompt | `2026-10-27/public-test-deepseek/` | 529 / 409 / 62 | -0.169 |
| 3 | 2026-10-27 ~22:30 | before d29997d | deepseek-flash, vote (k=3) | + split rulebook in the system prompt | `2026-10-27/public-test-rulebook/` | 526 / 443 / 31 | -0.023 |
| 4 | 2026-10-28 ~15:40 | 96072ee (working tree) | Qwen3-14B-FP8 on 2x RTX 5090, dataAgent + thinking, ingest v5 | model, pipeline and ingest all changed (several changes at once) | `2026-10-28/public-test-qwen3-5090/` | 793 / 125 / 82 | -0.411 |
| 5 | 2026-10-28 ~16:10 | 96072ee + ingest v7 (working tree) | deepseek-flash, dataAgent + thinking, ingest v7 | model back to deepseek-flash; ingest v6-v7 (macros, merged monthly tables, no money fill-down) | `2026-10-28/public-test-deepseek-v7/` | 881 / 98 / 21 | **+0.104** |
| 6 | 2026-10-28 18:34 (ready) | working tree after 96072ee (ingest v7, dataAgent v2: confidence field, unanswerable evidence, query retries, action inference) | **Qwen3.5-9B** (fp8, 2x RTX 5090), dataAgent + thinking, `presence_penalty` 1.5, k=1, no few-shot, MIN_CONFIDENCE 0.05 | first target-sized model with today's code (vs #4: model Qwen3-14B → Qwen3.5-9B and code v2) | `2026-10-28/public-test-qwen35-9b-k1/` | 855 / 109 / 36 | **-0.259** |
| 7 | 2026-10-28 19:15 (ready) | same as #6 | same as #6 | **+ few-shot** (`FEW_SHOT_K=3`, 101 verified train examples) — the only change vs #6 | `2026-10-28/public-test-qwen35-9b-k1-fewshot/` | 834 / 123 / 43 | **-0.261** |
| 8 | 2026-10-28 ~21:20 (running since 19:45) | same as #6 + money rounding wired into the pipeline | Qwen3.5-9B, dataAgent + thinking, **k=3 self-consistency**, `MIN_CONFIDENCE` 0.35, no few-shot | vs #6: k=1 → k=3 with the agreement gate (dev200 PA 0.415 → 0.520 for k=3; cross-fitted tau 0.35 adds +0.028 on development). Money rounding also changed (affects ~2 answers on #6) | `2026-10-28/public-test-qwen35-9b-k3/` | – | (to upload) |

| 9 | 2026-10-30 | f92ebdd | Qwen3.5-9B k=3 (10-28 run), gate 4 of 5 | agreement gate on the 10-28 k=3 run | `2026-10-28/public-test-qwen35-9b-k3-agree4of5/` | 356 / – / – | **0.066** |
| 10 | 2026-10-30 ~14:30 | f92ebdd | MALT, vote of 8 (k3 + k1 + k1-fewshot + new k3), >= 6 votes | ensemble of 4 runs | `2026-10-30/public-test-ensemble-v6/` | 465 / – / – | 0.030 |
| 11 | 2026-10-30 ~15:10 | f92ebdd | same, >= 7 votes | stricter gate than #10 | `2026-10-30/public-test-ensemble-v7/` | 329 / – / – | **0.084** (best) |
| 12 | 2026-10-30 ~15:45 | f92ebdd | v7 + 41 answers from a borderline third pass (>= 9 of 11 votes) | third pass on 252 questions with variant offset 3 | `2026-10-30/public-test-ensemble-final/` | 370 / – / – | 0.081 |

Pattern on 2026-10-30: fewer answers scored higher (465: 0.030, 356: 0.066, 329: 0.084); the 41 extra answers from the third pass were net -3. Estimated public precision about 63% at 329 answered.

Notes:
- Uploads 2, 3 and 5 sent public_test questions to the hosted DeepSeek API at the user's request
  (exception to CLAUDE.md rule 3, logged in NOTES.md). The final solution runs offline.
- From upload 6 on, change one thing at a time and fill in the commit before uploading.
