# Eval: gemma4-12b-ca-nothink

Command: `python -m scripts.eval --split train --subset dev200 --topic gemma4-12b-ca-nothink --workers 16`

Model: `google/gemma-4-12B-it`

Config: `split=train`, `subset=dev200`, `pipeline=ca`, `thinking=False`, `analyze_extra_body=`, `analyze_max_tokens=4096`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8013/v1`

**PA 0.0** on 200 questions: 0 correct, 0 wrong, 200 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 200 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 0 | 0 | 2 |
| date | 10 | 0.0 | 0 | 0 | 10 |
| list | 8 | 0.0 | 0 | 0 | 8 |
| number | 130 | 0.0 | 0 | 0 | 130 |
| percent | 40 | 0.0 | 0 | 0 | 40 |
| string | 6 | 0.0 | 0 | 0 | 6 |
| unanswerable | 4 | 0.0 | 0 | 0 | 4 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.0 | 0 | 0 | 200 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.0 |
| selective_accuracy | None |
| oracle_at_k | None |
| top_accuracy | None |
| agreement_auroc | None |
| repair_rate | 0.0 |
| unanswerable_precision | None |
| unanswerable_recall | 0.0 |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.0 |
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
| 0.55 | 0.0 |
| 0.6 | 0.0 |
| 0.65 | 0.0 |
| 0.7 | 0.0 |
| 0.75 | 0.0 |
| 0.8 | 0.0 |
| 0.85 | 0.0 |
| 0.9 | 0.0 |
| 0.95 | 0.0 |
| 1.0 | 0.0 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 481 questions fit in 6 h
- LLM time share of wall time: 0.9956
- LLM calls: 600 (0 failed); questions over the 4-step limit: 0
- tokens: 8350178 prompt, 224937 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 8962.914 | 44.8146 | 41.521 | 65.453 | 71.506 | 93.787 |
| llm seconds | 200 | 8923.7131 | 44.6186 | 41.4848 | 65.3362 | 71.2791 | 93.457 |
| ingest seconds | 200 | 8.9249 | 0.0446 | 0.0154 | 0.071 | 0.1891 | 0.762 |
| llm calls | 200 | 600.0 | 3.0 | 3.0 | 3.0 | 3.0 | 4.0 |
| llm steps | 200 | 598.0 | 2.99 | 3.0 | 3.0 | 3.0 | 3.0 |
| prompt tokens | 200 | 8350178.0 | 41750.89 | 40832.0 | 51497.0 | 53756.0 | 80095.0 |
| completion tokens | 200 | 224937.0 | 1124.685 | 1065.0 | 1673.0 | 1808.0 | 2252.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 600 | 936.7026 | 1.5612 | 1.3967 | 2.4946 | 3.1125 | 12.9747 |
| latency (s) | 600 | 8923.7131 | 14.8729 | 14.0655 | 22.9525 | 27.8843 | 50.9882 |
| decode tokens/s | 600 | 17496.5996 | 29.161 | 28.2327 | 34.4265 | 36.9997 | 94.7775 |
| prompt tokens | 600 | 8350178.0 | 13916.9633 | 13665.0 | 17193.0 | 18266.0 | 21454.0 |
| completion tokens | 600 | 224937.0 | 374.895 | 350.0 | 560.0 | 700.0 | 1345.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 199 | 3.3526 | 0.0168 | 0.0129 | 0.0352 | 0.0398 | 0.0933 |
| progress | 199 | 8.2882 | 0.0416 | 0.0457 | 0.0796 | 0.0863 | 0.4238 |
| schema | 199 | 11.9229 | 0.0599 | 0.0338 | 0.1588 | 0.1989 | 0.4731 |
| thought_queries | 199 | 3413.4687 | 17.1531 | 15.4894 | 28.3275 | 34.547 | 50.9887 |
| thought_results | 199 | 2093.9466 | 10.5223 | 9.756 | 17.0201 | 18.6227 | 29.9711 |
| thought_schema | 199 | 3401.4395 | 17.0927 | 16.2003 | 24.4013 | 27.1738 | 49.1766 |
