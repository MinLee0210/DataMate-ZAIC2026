# Public test: k=1 + confidence gate (semantic layer v1)

Run 2026-11-11 11:12–12:02 VN (50 minutes) on 2× RTX 5090.

## Config

| | |
|---|---|
| Model | `Qwen/Qwen3.5-9B` (9.65B), vLLM 0.33.0 |
| Serving | 2 replicas (one per GPU), `TP=1`, `max_model_len 40960`, `max_num_seqs 24`, prefix caching |
| Pipeline | `PIPELINE=malt`, `MALT_SAMPLES=1`, `MIN_CONFIDENCE=0.6` |
| Type gates | `{"list": 1.0, "boolean": 1.0}` |
| Context | `ANSWER_SHAPE=1`, `PREMISE_CHECK=1`, semantic views (ingest v14) |
| Workers | 40 (20 per replica), `--order business` |
| Data | `public_test`, 1,000 questions |

## Output

`submission.jsonl`: **1,000 lines**, 1,000 unique ids, ids = `questions.jsonl`,
0 unreadable lines, 0 wrong formats.

| type | n |
|---|---|
| number | 441 |
| abstain | 287 |
| percent | 133 |
| string | 51 |
| unanswerable | 45 |
| date | 32 |
| table | 11 |

713 answered, 287 abstained (28.7 %).

## Speed

~20–24 questions/minute on both GPUs (100 % each), mean **75 s/question** at k=1.
The earlier k=3 configuration measured ~390 s/question; at 3,000 private questions it would
exceed the 6-hour limit, while k=1 takes ~1.6 h for 3,000.

## Notes

- No PA: `public_test` has no gold answers. The score comes from the leaderboard upload.
- Reproducibility (rule 8): a 100-question rerun with the same config is running; the match rate
  is recorded in `docs/EXPERIMENTS.md` when it finishes.
- The gate `MALT_MIN_AGREEMENT=0.67` never accepted 2 of 3 votes (0.6667 < 0.67); for k=3 use
  0.66, otherwise every question runs all samples and 2/3 answers abstain.
