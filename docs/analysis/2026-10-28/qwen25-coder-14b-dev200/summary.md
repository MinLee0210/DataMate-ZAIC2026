# Eval: qwen25-coder-14b-dev200

Command: `python -m scripts.eval --split train --subset dev200 --topic qwen25-coder-14b-dev200 --workers 16`

Model: `Qwen/Qwen2.5-Coder-14B-Instruct`

Config: `split=train`, `subset=dev200`, `pipeline=ca`, `thinking=False`, `analyze_extra_body=`, `analyze_max_tokens=4096`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8013/v1`

**PA 0.0** on 200 questions: 82 correct, 82 wrong, 36 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 36 |
| correct | 82 |
| wrong_type | 4 |
| wrong_value | 78 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 0 | 0 | 2 |
| date | 10 | 0.6 | 7 | 1 | 2 |
| list | 8 | -0.25 | 2 | 4 | 2 |
| number | 130 | 0.1231 | 68 | 52 | 10 |
| percent | 40 | -0.45 | 3 | 21 | 16 |
| string | 6 | 0.0 | 2 | 2 | 2 |
| unanswerable | 4 | -0.5 | 0 | 2 | 2 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.0 | 82 | 82 | 36 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.82 |
| selective_accuracy | 0.5 |
| oracle_at_k | None |
| top_accuracy | 0.4882 |
| agreement_auroc | 0.5283 |
| repair_rate | 0.0 |
| unanswerable_precision | None |
| unanswerable_recall | 0.0 |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | -0.02 |
| 0.05 | 0.0 |
| 0.1 | 0.0 |
| 0.15 | 0.0 |
| 0.2 | 0.0 |
| 0.25 | 0.0 |
| 0.3 | 0.0 |
| 0.35 | 0.0 |
| 0.4 | 0.0 |
| 0.45 | 0.0 |
| 0.5 | 0.0 |
| 0.55 | 0.005 |
| 0.6 | 0.005 |
| 0.65 | 0.005 |
| 0.7 | 0.005 |
| 0.75 | 0.005 |
| 0.8 | 0.005 |
| 0.85 | 0.005 |
| 0.9 | 0.005 |
| 0.95 | 0.0 |
| 1.0 | 0.0 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 365 questions fit in 6 h
- LLM time share of wall time: 0.997
- LLM calls: 651 (0 failed); questions over the 4-step limit: 6
- tokens: 9016377 prompt, 129559 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 11807.214 | 59.0361 | 57.0 | 81.414 | 90.584 | 113.81 |
| llm seconds | 200 | 11772.2652 | 58.8613 | 56.782 | 81.3184 | 90.4523 | 113.5659 |
| ingest seconds | 200 | 7.7599 | 0.0388 | 0.0147 | 0.0693 | 0.1578 | 0.71 |
| llm calls | 200 | 651.0 | 3.255 | 3.0 | 4.0 | 4.0 | 5.0 |
| llm steps | 200 | 649.0 | 3.245 | 3.0 | 4.0 | 4.0 | 5.0 |
| prompt tokens | 200 | 9016377.0 | 45081.885 | 41909.0 | 59525.0 | 68925.0 | 99583.0 |
| completion tokens | 200 | 129559.0 | 647.795 | 590.0 | 925.0 | 1096.0 | 1377.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 651 | 5392.6165 | 8.2836 | 8.1135 | 12.2337 | 13.1929 | 14.8576 |
| latency (s) | 651 | 11772.2652 | 18.0834 | 17.5848 | 25.2268 | 28.3666 | 45.5651 |
| decode tokens/s | 651 | 13876.0683 | 21.315 | 20.3307 | 26.8399 | 29.7869 | 76.5504 |
| prompt tokens | 651 | 9016377.0 | 13850.0415 | 13467.0 | 17134.0 | 18190.0 | 21189.0 |
| completion tokens | 651 | 129559.0 | 199.0154 | 192.0 | 325.0 | 368.0 | 743.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 200 | 2.436 | 0.0122 | 0.0096 | 0.0249 | 0.028 | 0.0406 |
| progress | 200 | 8.8526 | 0.0443 | 0.0388 | 0.0716 | 0.0799 | 0.2289 |
| schema | 200 | 10.8812 | 0.0544 | 0.0292 | 0.1388 | 0.1663 | 0.3722 |
| thought_queries | 200 | 4144.942 | 20.7247 | 20.0891 | 27.4762 | 30.352 | 45.5656 |
| thought_results | 200 | 3631.8061 | 18.159 | 14.5331 | 34.2785 | 40.0807 | 63.0462 |
| thought_schema | 200 | 3997.8522 | 19.9893 | 19.4374 | 27.5479 | 29.7075 | 42.6729 |
