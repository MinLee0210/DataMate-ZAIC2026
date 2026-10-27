# Eval: analyze

Command: `python -m scripts.eval --split train --subset dev200 --topic analyze --workers 8`

Model: `deepseek-flash`

**PA 0.335** on 200 questions: 129 correct, 62 wrong, 9 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 9 |
| correct | 129 |
| wrong_type | 3 |
| wrong_value | 59 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 1 | 1 | 0 |
| date | 10 | 0.9 | 9 | 0 | 1 |
| list | 8 | -0.25 | 3 | 5 | 0 |
| number | 130 | 0.3923 | 87 | 36 | 7 |
| percent | 40 | 0.075 | 21 | 18 | 1 |
| string | 6 | 0.3333 | 4 | 2 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.335 | 129 | 62 | 9 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.955 |
| selective_accuracy | 0.6754 |
| oracle_at_k | 0.645 |
| top_accuracy | 0.645 |
| agreement_auroc | 0.5634 |
| repair_rate | 0.12 |
| unanswerable_precision | 1.0 |
| unanswerable_recall | 1.0 |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.29 |
| 0.05 | 0.29 |
| 0.1 | 0.29 |
| 0.15 | 0.29 |
| 0.2 | 0.29 |
| 0.25 | 0.29 |
| 0.3 | 0.29 |
| 0.35 | 0.295 |
| 0.4 | 0.295 |
| 0.45 | 0.295 |
| 0.5 | 0.295 |
| 0.55 | 0.295 |
| 0.6 | 0.295 |
| 0.65 | 0.295 |
| 0.7 | 0.335 |
| 0.75 | 0.335 |
| 0.8 | 0.335 |
| 0.85 | 0.335 |
| 0.9 | 0.335 |
| 0.95 | 0.335 |
| 1.0 | 0.335 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 2416 questions fit in 6 h
- LLM time share of wall time: 0.9859
- LLM calls: 877 (0 failed); questions over the 4-step limit: 3
- tokens: 16532837 prompt, 236374 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 1787.704 | 8.9385 | 8.092 | 11.686 | 14.617 | 29.488 |
| llm seconds | 200 | 1762.489 | 8.8124 | 7.9557 | 11.5939 | 14.5086 | 29.2628 |
| ingest seconds | 200 | 4.8197 | 0.0241 | 0.0099 | 0.0628 | 0.0792 | 0.3456 |
| llm calls | 200 | 877.0 | 4.385 | 4.0 | 5.0 | 7.0 | 12.0 |
| llm steps | 200 | 242.0 | 1.21 | 1.0 | 2.0 | 2.0 | 6.0 |
| prompt tokens | 200 | 16532837.0 | 82664.185 | 82300.0 | 115334.0 | 122545.0 | 303032.0 |
| completion tokens | 200 | 236374.0 | 1181.87 | 1058.0 | 1704.0 | 2113.0 | 5441.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 877 | 742.3556 | 0.8465 | 0.8315 | 1.067 | 1.1805 | 1.8017 |
| latency (s) | 877 | 1762.489 | 2.0097 | 1.6863 | 3.3611 | 3.6986 | 5.4052 |
| decode tokens/s | 877 | 210050.8216 | 239.5106 | 239.6141 | 278.0728 | 286.8332 | 342.7541 |
| prompt tokens | 877 | 16532837.0 | 18851.5815 | 17252.0 | 28702.0 | 29630.0 | 30847.0 |
| completion tokens | 877 | 236374.0 | 269.5257 | 199.0 | 537.0 | 593.0 | 901.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| analyze | 200 | 666.2236 | 3.3311 | 3.2855 | 3.9604 | 4.2847 | 5.4053 |
| decide | 200 | 0.0061 | 0.0 | 0.0 | 0.0001 | 0.0001 | 0.0001 |
| execute | 200 | 4.5538 | 0.0228 | 0.014 | 0.039 | 0.083 | 0.218 |
| generate | 200 | 962.2526 | 4.8113 | 4.6091 | 6.057 | 6.7315 | 9.6736 |
| prepare | 200 | 13.3519 | 0.0668 | 0.0425 | 0.1734 | 0.19 | 0.358 |
| repair | 24 | 134.1838 | 5.591 | 4.3127 | 9.6212 | 13.3966 | 15.6914 |
