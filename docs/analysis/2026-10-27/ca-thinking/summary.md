# Eval: ca-thinking

Command: `python -m scripts.eval --split train --subset dev200 --topic ca-thinking --workers 8`

Model: `deepseek-flash`

**PA 0.55** on 200 questions: 122 correct, 12 wrong, 66 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 66 |
| correct | 122 |
| wrong_value | 12 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.5 | 1 | 0 | 1 |
| date | 10 | 0.6 | 6 | 0 | 4 |
| list | 8 | 0.5 | 4 | 0 | 4 |
| number | 130 | 0.6 | 83 | 5 | 42 |
| percent | 40 | 0.375 | 21 | 6 | 13 |
| string | 6 | 0.3333 | 3 | 1 | 2 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.55 | 122 | 12 | 66 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.67 |
| selective_accuracy | 0.9104 |
| oracle_at_k | None |
| top_accuracy | 0.9104 |
| agreement_auroc | 0.5 |
| repair_rate | 0.0 |
| unanswerable_precision | 1.0 |
| unanswerable_recall | 1.0 |
| errors | 59 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.55 |
| 0.05 | 0.55 |
| 0.1 | 0.55 |
| 0.15 | 0.55 |
| 0.2 | 0.55 |
| 0.25 | 0.55 |
| 0.3 | 0.55 |
| 0.35 | 0.55 |
| 0.4 | 0.55 |
| 0.45 | 0.55 |
| 0.5 | 0.55 |
| 0.55 | 0.55 |
| 0.6 | 0.55 |
| 0.65 | 0.55 |
| 0.7 | 0.55 |
| 0.75 | 0.55 |
| 0.8 | 0.55 |
| 0.85 | 0.55 |
| 0.9 | 0.55 |
| 0.95 | 0.55 |
| 1.0 | 0.55 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 935 questions fit in 6 h
- LLM time share of wall time: 0.9935
- LLM calls: 614 (0 failed); questions over the 4-step limit: 0
- tokens: 11613229 prompt, 842226 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 4618.127 | 23.0906 | 21.054 | 36.323 | 46.039 | 68.279 |
| llm seconds | 200 | 4588.1662 | 22.9408 | 20.9033 | 36.0914 | 45.9185 | 67.9101 |
| ingest seconds | 200 | 6.0552 | 0.0303 | 0.0102 | 0.0701 | 0.0977 | 0.4274 |
| llm calls | 200 | 614.0 | 3.07 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 200 | 522.0 | 2.61 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 200 | 11613229.0 | 58066.145 | 54258.0 | 86013.0 | 93249.0 | 122058.0 |
| completion tokens | 200 | 842226.0 | 4211.13 | 3828.0 | 6878.0 | 8502.0 | 13031.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 614 | 528.8266 | 0.8613 | 0.8453 | 1.1268 | 1.2906 | 1.6815 |
| latency (s) | 614 | 4588.1662 | 7.4726 | 5.8574 | 16.7683 | 20.3415 | 25.0072 |
| decode tokens/s | 614 | 129014.4658 | 210.1213 | 209.226 | 235.7966 | 244.4422 | 293.1012 |
| prompt tokens | 614 | 11613229.0 | 18914.0537 | 17457.0 | 28440.0 | 29421.0 | 31393.0 |
| completion tokens | 614 | 842226.0 | 1371.7036 | 1069.0 | 3243.0 | 4096.0 | 4096.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| analysis | 2 | 0.0022 | 0.0011 | 0.001 | 0.0012 | 0.0012 | 0.0012 |
| data | 141 | 1.7324 | 0.0123 | 0.0089 | 0.0235 | 0.0344 | 0.0879 |
| progress | 141 | 4.0274 | 0.0286 | 0.024 | 0.0427 | 0.0462 | 0.2058 |
| schema | 141 | 8.4632 | 0.06 | 0.0312 | 0.1668 | 0.177 | 0.3093 |
| thought_queries | 141 | 1008.765 | 7.1544 | 5.9971 | 12.8079 | 17.1437 | 18.6011 |
| thought_results | 141 | 749.5302 | 5.3158 | 2.5579 | 12.2157 | 15.4727 | 35.9829 |
| thought_schema | 141 | 1071.2688 | 7.5977 | 6.4873 | 13.4839 | 14.8359 | 20.2388 |
