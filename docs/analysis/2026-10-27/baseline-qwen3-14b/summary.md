# Eval: baseline

Command: `python -m scripts.eval --split train --subset dev200 --topic baseline`

**PA -0.01** on 200 questions: 40 correct, 42 wrong, 118 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 118 |
| correct | 40 |
| wrong_type | 2 |
| wrong_value | 40 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | -0.5 | 0 | 1 | 1 |
| date | 10 | 0.5 | 5 | 0 | 5 |
| list | 8 | -0.125 | 1 | 2 | 5 |
| number | 130 | -0.0692 | 25 | 34 | 71 |
| percent | 40 | 0.05 | 5 | 3 | 32 |
| string | 6 | -0.1667 | 1 | 2 | 3 |
| unanswerable | 4 | 0.75 | 3 | 0 | 1 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | -0.01 | 40 | 42 | 118 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.41 |
| selective_accuracy | 0.4878 |
| oracle_at_k | 0.3568 |
| top_accuracy | 0.2825 |
| agreement_auroc | 0.7508 |
| repair_rate | 0.425 |
| unanswerable_precision | 0.6 |
| unanswerable_recall | 0.75 |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | -0.385 |
| 0.05 | -0.385 |
| 0.1 | -0.385 |
| 0.15 | -0.385 |
| 0.2 | -0.385 |
| 0.25 | -0.385 |
| 0.3 | -0.385 |
| 0.35 | -0.245 |
| 0.4 | -0.245 |
| 0.45 | -0.245 |
| 0.5 | -0.245 |
| 0.55 | -0.245 |
| 0.6 | -0.245 |
| 0.65 | -0.245 |
| 0.7 | -0.01 |
| 0.75 | -0.01 |
| 0.8 | -0.01 |
| 0.85 | -0.01 |
| 0.9 | -0.01 |
| 0.95 | -0.01 |
| 1.0 | -0.01 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 870 questions fit in 6 h
- LLM time share of wall time: 0.9451
- LLM calls: 1283 (1 failed); questions over the 4-step limit: 44
- tokens: 16362541 prompt, 253463 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 4963.652 | 24.8183 | 12.826 | 57.941 | 84.894 | 218.902 |
| llm seconds | 200 | 4690.9236 | 23.4546 | 11.3444 | 57.1303 | 84.7491 | 218.6247 |
| ingest seconds | 200 | 242.4188 | 1.2121 | 0.0002 | 3.6282 | 8.6647 | 28.3427 |
| llm calls | 200 | 1283.0 | 6.415 | 3.0 | 18.0 | 18.0 | 18.0 |
| llm steps | 200 | 484.0 | 2.42 | 1.0 | 6.0 | 6.0 | 6.0 |
| prompt tokens | 200 | 16362541.0 | 81812.705 | 53112.0 | 200264.0 | 314058.0 | 457184.0 |
| completion tokens | 200 | 253463.0 | 1267.315 | 546.0 | 3127.0 | 4742.0 | 13794.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 1282 | 1203.9038 | 0.9391 | 0.8343 | 1.3126 | 2.02 | 4.0997 |
| latency (s) | 1283 | 4690.9236 | 3.6562 | 3.1253 | 5.6431 | 6.5495 | 18.7831 |
| decode tokens/s | 1282 | 94739.9971 | 73.9002 | 74.7344 | 82.3897 | 84.274 | 161.6677 |
| prompt tokens | 1282 | 16362541.0 | 12763.2925 | 12016.0 | 22896.0 | 24611.0 | 25765.0 |
| completion tokens | 1282 | 253463.0 | 197.709 | 159.0 | 328.0 | 390.0 | 1024.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| decide | 199 | 0.0615 | 0.0003 | 0.0001 | 0.0006 | 0.001 | 0.0108 |
| execute | 199 | 10.6257 | 0.0534 | 0.0236 | 0.118 | 0.1626 | 1.1671 |
| generate | 199 | 2054.9487 | 10.3264 | 9.4803 | 15.5094 | 17.5944 | 44.8911 |
| prepare | 199 | 16.4244 | 0.0825 | 0.0586 | 0.1791 | 0.2006 | 1.9714 |
| repair | 85 | 2611.8087 | 30.7272 | 21.1213 | 74.3711 | 80.703 | 200.2711 |
