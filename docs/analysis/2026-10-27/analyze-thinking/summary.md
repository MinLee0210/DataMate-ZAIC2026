# Eval: analyze-thinking

Command: `python -m scripts.eval --split train --subset dev200 --topic analyze-thinking --workers 8`

Model: `deepseek-flash`

**PA 0.52** on 200 questions: 143 correct, 39 wrong, 18 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 18 |
| correct | 143 |
| wrong_value | 39 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 1 | 1 | 0 |
| date | 10 | 0.9 | 9 | 0 | 1 |
| list | 8 | 0.375 | 5 | 2 | 1 |
| number | 130 | 0.5846 | 97 | 21 | 12 |
| percent | 40 | 0.25 | 23 | 13 | 4 |
| string | 6 | 0.3333 | 4 | 2 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.52 | 143 | 39 | 18 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.91 |
| selective_accuracy | 0.7857 |
| oracle_at_k | 0.76 |
| top_accuracy | 0.7538 |
| agreement_auroc | 0.578 |
| repair_rate | 0.105 |
| unanswerable_precision | 1.0 |
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
| 0.35 | 0.5 |
| 0.4 | 0.5 |
| 0.45 | 0.5 |
| 0.5 | 0.5 |
| 0.55 | 0.5 |
| 0.6 | 0.5 |
| 0.65 | 0.5 |
| 0.7 | 0.52 |
| 0.75 | 0.52 |
| 0.8 | 0.52 |
| 0.85 | 0.52 |
| 0.9 | 0.52 |
| 0.95 | 0.52 |
| 1.0 | 0.52 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 1411 questions fit in 6 h
- LLM time share of wall time: 0.9918
- LLM calls: 880 (0 failed); questions over the 4-step limit: 5
- tokens: 16647460 prompt, 471393 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 3061.045 | 15.3052 | 13.056 | 24.141 | 29.123 | 58.754 |
| llm seconds | 200 | 3035.8336 | 15.1792 | 12.9447 | 23.9089 | 28.5961 | 58.507 |
| ingest seconds | 200 | 4.9323 | 0.0247 | 0.0099 | 0.0576 | 0.0765 | 0.3051 |
| llm calls | 200 | 880.0 | 4.4 | 4.0 | 5.0 | 7.0 | 19.0 |
| llm steps | 200 | 241.0 | 1.205 | 1.0 | 2.0 | 2.0 | 6.0 |
| prompt tokens | 200 | 16647460.0 | 83237.3 | 82422.0 | 115557.0 | 130594.0 | 331649.0 |
| completion tokens | 200 | 471393.0 | 2356.965 | 1938.0 | 4167.0 | 4838.0 | 11259.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 880 | 773.5422 | 0.879 | 0.8502 | 1.1475 | 1.2572 | 2.0631 |
| latency (s) | 880 | 3035.8336 | 3.4498 | 1.8675 | 8.0132 | 11.6895 | 25.283 |
| decode tokens/s | 880 | 208689.9304 | 237.1476 | 241.8549 | 276.8475 | 286.6531 | 517.1849 |
| prompt tokens | 880 | 16647460.0 | 18917.5682 | 15448.0 | 28852.0 | 29810.0 | 31277.0 |
| completion tokens | 880 | 471393.0 | 535.6739 | 230.0 | 1365.0 | 2037.0 | 4096.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| analyze | 200 | 1834.3719 | 9.1719 | 7.606 | 15.7138 | 20.4881 | 25.2832 |
| decide | 200 | 0.0058 | 0.0 | 0.0 | 0.0001 | 0.0001 | 0.0001 |
| execute | 200 | 4.4974 | 0.0225 | 0.0154 | 0.038 | 0.0686 | 0.1964 |
| generate | 200 | 1048.6008 | 5.243 | 4.9011 | 7.1275 | 7.9169 | 10.2826 |
| prepare | 200 | 13.9967 | 0.07 | 0.0429 | 0.1708 | 0.1892 | 0.623 |
| repair | 21 | 153.0384 | 7.2875 | 4.8375 | 17.0756 | 18.5096 | 22.9446 |
