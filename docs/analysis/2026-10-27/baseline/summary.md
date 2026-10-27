# Eval: baseline

Command: `python -m scripts.eval --split train --subset dev200 --topic baseline`

Model: `deepseek-flash`

**PA 0.09** on 200 questions: 92 correct, 74 wrong, 34 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 34 |
| correct | 92 |
| wrong_type | 1 |
| wrong_value | 73 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 1 | 1 | 0 |
| date | 10 | 0.8 | 8 | 0 | 2 |
| list | 8 | 0.0 | 2 | 2 | 4 |
| number | 130 | 0.0462 | 60 | 54 | 16 |
| percent | 40 | 0.0 | 14 | 14 | 12 |
| string | 6 | 0.0 | 3 | 3 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.09 | 92 | 74 | 34 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.83 |
| selective_accuracy | 0.5542 |
| oracle_at_k | 0.54 |
| top_accuracy | 0.5226 |
| agreement_auroc | 0.556 |
| repair_rate | 0.095 |
| unanswerable_precision | 1.0 |
| unanswerable_recall | 1.0 |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.045 |
| 0.05 | 0.045 |
| 0.1 | 0.045 |
| 0.15 | 0.045 |
| 0.2 | 0.045 |
| 0.25 | 0.045 |
| 0.3 | 0.045 |
| 0.35 | 0.075 |
| 0.4 | 0.075 |
| 0.45 | 0.075 |
| 0.5 | 0.075 |
| 0.55 | 0.075 |
| 0.6 | 0.075 |
| 0.65 | 0.075 |
| 0.7 | 0.09 |
| 0.75 | 0.09 |
| 0.8 | 0.09 |
| 0.85 | 0.09 |
| 0.9 | 0.09 |
| 0.95 | 0.09 |
| 1.0 | 0.09 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 3962 questions fit in 6 h
- LLM time share of wall time: 0.9841
- LLM calls: 683 (0 failed); questions over the 4-step limit: 5
- tokens: 8222678 prompt, 109146 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 1090.314 | 5.4516 | 4.715 | 7.332 | 9.199 | 23.315 |
| llm seconds | 200 | 1072.993 | 5.365 | 4.641 | 7.0967 | 9.1296 | 23.2512 |
| ingest seconds | 200 | 1.0371 | 0.0052 | 0.0001 | 0.0095 | 0.0329 | 0.1159 |
| llm calls | 200 | 683.0 | 3.415 | 3.0 | 3.0 | 6.0 | 18.0 |
| llm steps | 200 | 242.0 | 1.21 | 1.0 | 1.0 | 2.0 | 6.0 |
| prompt tokens | 200 | 8222678.0 | 41113.39 | 36212.0 | 66117.0 | 68904.0 | 342535.0 |
| completion tokens | 200 | 109146.0 | 545.73 | 456.0 | 868.0 | 1024.0 | 2344.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 683 | 583.0663 | 0.8537 | 0.8472 | 1.0928 | 1.1861 | 2.2316 |
| latency (s) | 683 | 1072.993 | 1.571 | 1.5167 | 2.0599 | 2.2132 | 3.11 |
| decode tokens/s | 683 | 150752.348 | 220.7209 | 220.8296 | 253.0964 | 259.4859 | 1402.5157 |
| prompt tokens | 683 | 8222678.0 | 12039.06 | 8753.0 | 22024.0 | 22887.0 | 24103.0 |
| completion tokens | 683 | 109146.0 | 159.8038 | 145.0 | 247.0 | 296.0 | 489.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| decide | 200 | 0.0101 | 0.0001 | 0.0 | 0.0001 | 0.0001 | 0.0002 |
| execute | 200 | 2.9267 | 0.0146 | 0.0122 | 0.0238 | 0.0316 | 0.0647 |
| generate | 200 | 944.6418 | 4.7232 | 4.5436 | 5.9506 | 6.3052 | 8.3785 |
| prepare | 200 | 12.4354 | 0.0622 | 0.0477 | 0.1617 | 0.1772 | 0.2376 |
| repair | 19 | 128.4942 | 6.7629 | 4.4111 | 18.5918 | 19.9239 | 19.9239 |
