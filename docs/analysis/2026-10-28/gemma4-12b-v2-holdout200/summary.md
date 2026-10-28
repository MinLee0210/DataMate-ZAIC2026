# Eval: gemma4-12b-v2-holdout200

Command: `python -m scripts.eval --split train --subset holdout200 --topic gemma4-12b-v2-holdout200 --workers 10`

Model: `google/gemma-4-12B-it`

Config: `split=train`, `subset=holdout200`, `pipeline=ca`, `thinking=False`, `analyze_extra_body=`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=10`, `llm_base_url=http://127.0.0.1:8013/v1`

**PA 0.505** on 200 questions: 138 correct, 37 wrong, 25 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 25 |
| correct | 138 |
| wrong_type | 15 |
| wrong_value | 22 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 0 | 0 | 2 |
| date | 6 | 0.3333 | 4 | 2 | 0 |
| list | 15 | 0.2667 | 8 | 4 | 3 |
| number | 126 | 0.5556 | 90 | 20 | 16 |
| percent | 38 | 0.5 | 27 | 8 | 3 |
| string | 4 | -0.5 | 1 | 3 | 0 |
| table | 1 | 0.0 | 0 | 0 | 1 |
| unanswerable | 8 | 1.0 | 8 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.505 | 138 | 37 | 25 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.875 |
| selective_accuracy | 0.7886 |
| oracle_at_k | None |
| top_accuracy | 0.7886 |
| agreement_auroc | 0.5791 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.5 |
| unanswerable_recall | 1.0 |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.505 |
| 0.05 | 0.505 |
| 0.1 | 0.505 |
| 0.15 | 0.505 |
| 0.2 | 0.505 |
| 0.25 | 0.505 |
| 0.3 | 0.505 |
| 0.35 | 0.505 |
| 0.4 | 0.505 |
| 0.45 | 0.505 |
| 0.5 | 0.505 |
| 0.55 | 0.505 |
| 0.6 | 0.505 |
| 0.65 | 0.505 |
| 0.7 | 0.505 |
| 0.75 | 0.505 |
| 0.8 | 0.505 |
| 0.85 | 0.505 |
| 0.9 | 0.505 |
| 0.95 | 0.505 |
| 1.0 | 0.505 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 390 questions fit in 6 h
- LLM time share of wall time: 0.9983
- LLM calls: 626 (0 failed); questions over the 4-step limit: 0
- tokens: 8532291 prompt, 253909 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 11068.414 | 55.3421 | 47.867 | 75.58 | 93.845 | 432.865 |
| llm seconds | 200 | 11049.1009 | 55.2455 | 47.8033 | 75.4017 | 93.8095 | 432.7738 |
| ingest seconds | 200 | 2.2048 | 0.011 | 0.0001 | 0.0255 | 0.0529 | 0.3162 |
| llm calls | 200 | 626.0 | 3.13 | 3.0 | 4.0 | 4.0 | 5.0 |
| llm steps | 200 | 624.0 | 3.12 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 200 | 8532291.0 | 42661.455 | 36734.0 | 51930.0 | 67091.0 | 77739.0 |
| completion tokens | 200 | 253909.0 | 1269.545 | 1060.0 | 1801.0 | 2098.0 | 12057.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 626 | 2401.2415 | 3.8358 | 3.8516 | 5.3884 | 5.8541 | 7.947 |
| latency (s) | 626 | 11049.1009 | 17.6503 | 15.8543 | 24.6384 | 29.5721 | 352.7033 |
| decode tokens/s | 626 | 19383.6907 | 30.9644 | 29.6022 | 37.1394 | 42.3509 | 95.5052 |
| prompt tokens | 626 | 8532291.0 | 13629.8578 | 12411.0 | 17035.0 | 17277.0 | 18907.0 |
| completion tokens | 626 | 253909.0 | 405.6054 | 346.0 | 566.0 | 736.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 200 | 2.9586 | 0.0148 | 0.0127 | 0.0256 | 0.0331 | 0.113 |
| progress | 200 | 4.9101 | 0.0246 | 0.0002 | 0.0589 | 0.0731 | 0.093 |
| schema | 200 | 6.7905 | 0.034 | 0.0103 | 0.116 | 0.1396 | 0.1702 |
| thought_queries | 200 | 4477.2429 | 22.3862 | 16.7175 | 31.5154 | 39.0172 | 371.6615 |
| thought_results | 200 | 2943.0106 | 14.7151 | 12.6692 | 26.3144 | 34.6486 | 48.464 |
| thought_schema | 200 | 3630.4538 | 18.1523 | 17.4398 | 23.988 | 26.659 | 50.9846 |
