# Hold-out exposure log

The hold-out (scripts/splits.py) estimates how the pipeline does on shops it has never been
tuned on. Every time hold-out questions are scored, or their errors are read, it loses some of
that value. Log each opening here, append only. Do not swap the hold-out because a score is low.

Rules:
- Choose models, prompts and thresholds on the development folds (`scripts/calibrate.py`,
  cross-fitted). Score the hold-out only at a checkpoint, with the candidate already fixed.
- Reading hold-out errors to change the pipeline makes later hold-out scores no longer blind:
  say so in the entry.
- dev200 mixes hold-out and development businesses; scoring dev200 also touches the hold-out
  (about 29 % of its questions in v2), logged as "dev200 overlap".

| # | Date, time (VN) | Hold-out | Run (topic) | Purpose | Errors read? | Blind afterwards? |
|---|---|---|---|---|---|---|
| 1 | 2026-10-27 to 2026-10-28 | v1 and v2 | every dev200 run so far (baseline … qwen3-5090-ca-thinking) | development scoring, before any hold-out existed | yes: dev200 errors were analysed, which include hold-out v2 businesses (biz_102, 103, 104, 121, 122, 117, 129, 125) | v2 is **not pristine**: its businesses appeared in dev200 error analysis |
| 2 | 2026-10-28 16:31 | v1 (biz_102, 106, 114, 120, 125, 130) | qwen35-9b-v2-holdout200, gemma4-12b-v2-holdout200 | model comparison | no | v1 retired the same day (family leakage) |
| 3 | 2026-10-28 17:00 | v2 (58 questions inside dev200) | `scripts/calibrate.py` on qwen35-9b-v2-dev200 and gemma4-12b-v2-dev200 | threshold check printed hold-out PA (0.43 / 0.45; 0.36 / 0.43) | no | yes (scores only, no error reading) |
| 4 | 2026-10-28 19:40 | v2 (58 questions inside dev200) | `scripts/calibrate.py` on qwen35-9b-k3-dev200-h0/h1 (E1) | threshold check printed hold-out PA (no gate 0.517, tau 0.35 0.586) | no | yes (scores only) |

Notes:
- v2 holds out whole schema families. Its businesses were already part of dev200 analysis on
  2026-10-27/28 (entry 1), so treat v2 as "seen format, never tuned on directly", not as fully
  new shops. From now on: no error analysis on v2 businesses.
