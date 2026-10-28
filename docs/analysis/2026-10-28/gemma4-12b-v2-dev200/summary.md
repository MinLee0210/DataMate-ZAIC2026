# Eval: gemma4-12b-v2-dev200

Command: `python -m scripts.eval --split train --subset dev200 --topic gemma4-12b-v2-dev200 --workers 10`

Model: `google/gemma-4-12B-it`

Config: `split=train`, `subset=dev200`, `pipeline=ca`, `thinking=False`, `analyze_extra_body=`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=10`, `llm_base_url=http://127.0.0.1:8013/v1`

**PA 0.28** on 200 questions: 118 correct, 62 wrong, 20 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 20 |
| correct | 118 |
| wrong_type | 27 |
| wrong_value | 35 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | -0.5 | 0 | 1 | 1 |
| date | 10 | 0.5 | 7 | 2 | 1 |
| list | 8 | -0.125 | 3 | 4 | 1 |
| number | 130 | 0.4308 | 86 | 30 | 14 |
| percent | 40 | -0.275 | 13 | 24 | 3 |
| string | 6 | 0.6667 | 5 | 1 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.28 | 118 | 62 | 20 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.9 |
| selective_accuracy | 0.6556 |
| oracle_at_k | None |
| top_accuracy | 0.6556 |
| agreement_auroc | 0.6282 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.1818 |
| unanswerable_recall | 1.0 |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.28 |
| 0.05 | 0.35 |
| 0.1 | 0.35 |
| 0.15 | 0.35 |
| 0.2 | 0.35 |
| 0.25 | 0.35 |
| 0.3 | 0.35 |
| 0.35 | 0.35 |
| 0.4 | 0.35 |
| 0.45 | 0.35 |
| 0.5 | 0.35 |
| 0.55 | 0.35 |
| 0.6 | 0.35 |
| 0.65 | 0.35 |
| 0.7 | 0.35 |
| 0.75 | 0.35 |
| 0.8 | 0.35 |
| 0.85 | 0.35 |
| 0.9 | 0.35 |
| 0.95 | 0.35 |
| 1.0 | 0.35 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 402 questions fit in 6 h
- LLM time share of wall time: 0.9974
- LLM calls: 623 (0 failed); questions over the 4-step limit: 0
- tokens: 8754658 prompt, 234587 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 10727.984 | 53.6399 | 50.166 | 79.068 | 87.874 | 123.332 |
| llm seconds | 200 | 10700.3604 | 53.5018 | 50.1261 | 78.7625 | 87.8145 | 123.1972 |
| ingest seconds | 200 | 5.5152 | 0.0276 | 0.0121 | 0.0576 | 0.1025 | 0.3588 |
| llm calls | 200 | 623.0 | 3.115 | 3.0 | 4.0 | 4.0 | 5.0 |
| llm steps | 200 | 621.0 | 3.105 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 200 | 8754658.0 | 43773.29 | 41644.0 | 55553.0 | 64232.0 | 81813.0 |
| completion tokens | 200 | 234587.0 | 1172.935 | 1061.0 | 1793.0 | 1996.0 | 2687.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 623 | 2630.4279 | 4.2222 | 4.0991 | 5.6391 | 6.3768 | 11.3013 |
| latency (s) | 623 | 10700.3604 | 17.1755 | 16.1256 | 24.4668 | 28.7601 | 81.1813 |
| decode tokens/s | 623 | 18687.4389 | 29.9959 | 29.4436 | 35.9204 | 39.0846 | 67.2101 |
| prompt tokens | 623 | 8754658.0 | 14052.4205 | 13760.0 | 17458.0 | 18770.0 | 21471.0 |
| completion tokens | 623 | 234587.0 | 376.5441 | 348.0 | 575.0 | 686.0 | 1866.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 200 | 2.7847 | 0.0139 | 0.0112 | 0.0286 | 0.0333 | 0.058 |
| progress | 200 | 6.321 | 0.0316 | 0.0395 | 0.0637 | 0.0682 | 0.1048 |
| schema | 200 | 9.5442 | 0.0477 | 0.0242 | 0.135 | 0.1469 | 0.3378 |
| thought_queries | 200 | 4045.0905 | 20.2255 | 17.9352 | 30.6888 | 40.7183 | 81.1818 |
| thought_results | 200 | 2892.0781 | 14.4604 | 12.5599 | 23.1492 | 30.2234 | 44.0082 |
| thought_schema | 200 | 3764.7925 | 18.824 | 18.3432 | 24.9938 | 26.3465 | 50.6807 |
