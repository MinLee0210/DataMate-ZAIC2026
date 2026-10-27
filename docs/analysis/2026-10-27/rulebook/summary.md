# Eval: rulebook

Command: `python -m scripts.eval --split train --subset dev200 --topic rulebook --workers 8`

Model: `deepseek-flash`

**PA 0.35** on 200 questions: 117 correct, 47 wrong, 36 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 36 |
| correct | 117 |
| wrong_value | 47 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 1 | 1 | 0 |
| date | 10 | 0.6 | 8 | 2 | 0 |
| list | 8 | 0.25 | 4 | 2 | 2 |
| number | 130 | 0.3462 | 77 | 32 | 21 |
| percent | 40 | 0.25 | 19 | 9 | 12 |
| string | 6 | 0.5 | 4 | 1 | 1 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.35 | 117 | 47 | 36 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.82 |
| selective_accuracy | 0.7134 |
| oracle_at_k | 0.65 |
| top_accuracy | 0.64 |
| agreement_auroc | 0.6336 |
| repair_rate | 0.105 |
| unanswerable_precision | 1.0 |
| unanswerable_recall | 1.0 |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.28 |
| 0.05 | 0.28 |
| 0.1 | 0.28 |
| 0.15 | 0.28 |
| 0.2 | 0.28 |
| 0.25 | 0.28 |
| 0.3 | 0.28 |
| 0.35 | 0.305 |
| 0.4 | 0.305 |
| 0.45 | 0.305 |
| 0.5 | 0.305 |
| 0.55 | 0.305 |
| 0.6 | 0.305 |
| 0.65 | 0.305 |
| 0.7 | 0.35 |
| 0.75 | 0.35 |
| 0.8 | 0.35 |
| 0.85 | 0.35 |
| 0.9 | 0.35 |
| 0.95 | 0.35 |
| 1.0 | 0.35 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 3703 questions fit in 6 h
- LLM time share of wall time: 0.9774
- LLM calls: 670 (0 failed); questions over the 4-step limit: 1
- tokens: 12222450 prompt, 124411 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 1166.438 | 5.8322 | 5.169 | 8.631 | 10.056 | 19.081 |
| llm seconds | 200 | 1140.1019 | 5.7005 | 5.0215 | 8.3831 | 9.9446 | 18.9165 |
| ingest seconds | 200 | 5.6989 | 0.0285 | 0.0102 | 0.0724 | 0.1164 | 0.3771 |
| llm calls | 200 | 670.0 | 3.35 | 3.0 | 4.0 | 6.0 | 10.0 |
| llm steps | 200 | 235.0 | 1.175 | 1.0 | 2.0 | 2.0 | 6.0 |
| prompt tokens | 200 | 12222450.0 | 61112.25 | 60132.0 | 85212.0 | 97279.0 | 243616.0 |
| completion tokens | 200 | 124411.0 | 622.055 | 516.0 | 1087.0 | 1367.0 | 1889.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 670 | 595.7255 | 0.8891 | 0.8739 | 1.1327 | 1.2384 | 1.8661 |
| latency (s) | 670 | 1140.1019 | 1.7016 | 1.6226 | 2.2256 | 2.4918 | 3.6206 |
| decode tokens/s | 670 | 150781.5272 | 225.0471 | 225.5363 | 254.4273 | 261.807 | 849.8024 |
| prompt tokens | 670 | 12222450.0 | 18242.4627 | 16084.0 | 28127.0 | 29106.0 | 30303.0 |
| completion tokens | 670 | 124411.0 | 185.6881 | 167.0 | 295.0 | 390.0 | 569.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| decide | 200 | 0.0065 | 0.0 | 0.0 | 0.0001 | 0.0001 | 0.0001 |
| execute | 200 | 4.7439 | 0.0237 | 0.0149 | 0.048 | 0.0925 | 0.1713 |
| generate | 200 | 1026.2993 | 5.1315 | 4.8704 | 6.5065 | 7.2478 | 8.9067 |
| prepare | 200 | 13.5062 | 0.0675 | 0.0448 | 0.1665 | 0.1977 | 0.3383 |
| repair | 21 | 113.9496 | 5.4262 | 4.9944 | 8.9558 | 9.3959 | 12.7281 |
