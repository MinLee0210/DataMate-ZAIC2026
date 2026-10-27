# Eval: ca

Command: `python -m scripts.eval --split train --subset dev200 --topic ca --workers 8`

Model: `deepseek-flash`

**PA 0.43** on 200 questions: 140 correct, 54 wrong, 6 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 6 |
| correct | 140 |
| wrong_type | 1 |
| wrong_value | 53 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 1 | 1 | 0 |
| date | 10 | 0.9 | 9 | 0 | 1 |
| list | 8 | 0.0 | 4 | 4 | 0 |
| number | 130 | 0.5077 | 96 | 30 | 4 |
| percent | 40 | 0.15 | 23 | 17 | 0 |
| string | 6 | 0.1667 | 3 | 2 | 1 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.43 | 140 | 54 | 6 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.97 |
| selective_accuracy | 0.7216 |
| oracle_at_k | None |
| top_accuracy | 0.7216 |
| agreement_auroc | 0.5 |
| repair_rate | 0.0 |
| unanswerable_precision | 1.0 |
| unanswerable_recall | 1.0 |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.43 |
| 0.05 | 0.43 |
| 0.1 | 0.43 |
| 0.15 | 0.43 |
| 0.2 | 0.43 |
| 0.25 | 0.43 |
| 0.3 | 0.43 |
| 0.35 | 0.43 |
| 0.4 | 0.43 |
| 0.45 | 0.43 |
| 0.5 | 0.43 |
| 0.55 | 0.43 |
| 0.6 | 0.43 |
| 0.65 | 0.43 |
| 0.7 | 0.43 |
| 0.75 | 0.43 |
| 0.8 | 0.43 |
| 0.85 | 0.43 |
| 0.9 | 0.43 |
| 0.95 | 0.43 |
| 1.0 | 0.43 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 2928 questions fit in 6 h
- LLM time share of wall time: 0.9784
- LLM calls: 618 (0 failed); questions over the 4-step limit: 0
- tokens: 11657903 prompt, 200221 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 1475.408 | 7.377 | 7.054 | 9.2 | 9.981 | 17.554 |
| llm seconds | 200 | 1443.4809 | 7.2174 | 6.9075 | 9.0143 | 9.8297 | 17.2181 |
| ingest seconds | 200 | 6.1833 | 0.0309 | 0.0135 | 0.0744 | 0.1367 | 0.4485 |
| llm calls | 200 | 618.0 | 3.09 | 3.0 | 3.0 | 4.0 | 4.0 |
| llm steps | 200 | 617.0 | 3.085 | 3.0 | 3.0 | 4.0 | 4.0 |
| prompt tokens | 200 | 11657903.0 | 58289.515 | 54562.0 | 85534.0 | 89468.0 | 122879.0 |
| completion tokens | 200 | 200221.0 | 1001.105 | 926.0 | 1370.0 | 1558.0 | 4663.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 618 | 532.9565 | 0.8624 | 0.8387 | 1.1454 | 1.2581 | 1.6499 |
| latency (s) | 618 | 1443.4809 | 2.3357 | 2.1569 | 3.618 | 3.8538 | 11.9571 |
| decode tokens/s | 618 | 131016.6186 | 212.001 | 210.6041 | 250.9605 | 262.9618 | 373.7908 |
| prompt tokens | 618 | 11657903.0 | 18863.9207 | 18144.0 | 28507.0 | 29315.0 | 31243.0 |
| completion tokens | 618 | 200221.0 | 323.9822 | 304.0 | 587.0 | 643.0 | 4096.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 199 | 2.067 | 0.0104 | 0.0065 | 0.0183 | 0.0272 | 0.1038 |
| progress | 199 | 6.8931 | 0.0346 | 0.0282 | 0.0505 | 0.0741 | 0.319 |
| schema | 199 | 14.4104 | 0.0724 | 0.0467 | 0.186 | 0.2134 | 0.4201 |
| thought_queries | 199 | 464.4605 | 2.334 | 2.1393 | 3.4328 | 3.7545 | 5.5837 |
| thought_results | 199 | 328.4786 | 1.6506 | 1.4044 | 2.107 | 3.8541 | 7.7607 |
| thought_schema | 199 | 636.0891 | 3.1964 | 3.2127 | 3.8891 | 4.2132 | 4.822 |
