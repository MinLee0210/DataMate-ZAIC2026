# Eval: q14-k3-dev-h1

Command: `python -m scripts.eval --split train --subset /workspace/dev_h1.txt --topic q14-k3-dev-h1 --workers 16`

Model: `Qwen/Qwen3-14B-FP8`

Config: `split=train`, `subset=/workspace/dev_h1.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.46** on 100 questions: 70 correct, 24 wrong, 6 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 6 |
| correct | 70 |
| wrong_type | 2 |
| wrong_value | 22 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 1.0 | 2 | 0 | 0 |
| date | 3 | 1.0 | 3 | 0 | 0 |
| list | 5 | -0.2 | 2 | 3 | 0 |
| number | 64 | 0.5781 | 50 | 13 | 1 |
| percent | 17 | 0.1176 | 9 | 7 | 1 |
| string | 5 | 0.6 | 4 | 1 | 0 |
| unanswerable | 4 | 0.0 | 0 | 0 | 4 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.46 | 70 | 24 | 6 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.94 |
| selective_accuracy | 0.7447 |
| oracle_at_k | None |
| top_accuracy | 0.7447 |
| agreement_auroc | 0.8217 |
| repair_rate | 0.0 |
| unanswerable_precision | None |
| unanswerable_recall | 0.0 |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.46 |
| 0.05 | 0.46 |
| 0.1 | 0.46 |
| 0.15 | 0.46 |
| 0.2 | 0.46 |
| 0.25 | 0.46 |
| 0.3 | 0.46 |
| 0.35 | 0.55 |
| 0.4 | 0.55 |
| 0.45 | 0.55 |
| 0.5 | 0.55 |
| 0.55 | 0.55 |
| 0.6 | 0.55 |
| 0.65 | 0.55 |
| 0.7 | 0.49 |
| 0.75 | 0.49 |
| 0.8 | 0.49 |
| 0.85 | 0.49 |
| 0.9 | 0.49 |
| 0.95 | 0.49 |
| 1.0 | 0.49 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 55 questions fit in 6 h
- LLM time share of wall time: 0.9989
- LLM calls: 937 (0 failed); questions over the 4-step limit: 100
- tokens: 13355003 prompt, 896101 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 38854.729 | 388.5473 | 383.456 | 510.961 | 554.793 | 640.165 |
| llm seconds | 100 | 38812.6095 | 388.1261 | 383.2441 | 510.177 | 553.5323 | 639.7116 |
| ingest seconds | 100 | 7.6155 | 0.0762 | 0.0159 | 0.1609 | 0.5093 | 0.8352 |
| llm calls | 100 | 937.0 | 9.37 | 9.0 | 11.0 | 11.0 | 12.0 |
| llm steps | 100 | 937.0 | 9.37 | 9.0 | 11.0 | 11.0 | 12.0 |
| prompt tokens | 100 | 13355003.0 | 133550.03 | 126437.0 | 171908.0 | 183969.0 | 227779.0 |
| completion tokens | 100 | 896101.0 | 8961.01 | 8350.0 | 12742.0 | 14366.0 | 16573.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 937 | 12539.4114 | 13.3825 | 13.2424 | 22.0783 | 24.4535 | 35.1646 |
| latency (s) | 937 | 38812.6095 | 41.4222 | 38.78 | 62.3552 | 73.8396 | 126.5915 |
| decode tokens/s | 937 | 32258.3323 | 34.4272 | 33.9131 | 38.7092 | 40.7517 | 79.8452 |
| prompt tokens | 937 | 13355003.0 | 14252.9381 | 13884.0 | 17400.0 | 19829.0 | 21471.0 |
| completion tokens | 937 | 896101.0 | 956.3511 | 838.0 | 1617.0 | 2075.0 | 3712.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 100 | 3.2247 | 0.0322 | 0.0293 | 0.052 | 0.0656 | 0.0837 |
| progress | 100 | 14.4842 | 0.1448 | 0.1126 | 0.1895 | 0.2045 | 2.2381 |
| schema | 100 | 11.7123 | 0.1171 | 0.0574 | 0.3146 | 0.3806 | 0.6354 |
| thought_queries | 100 | 13764.9559 | 137.6496 | 134.2047 | 188.1667 | 224.2759 | 306.0779 |
| thought_results | 100 | 10603.0522 | 106.0305 | 98.0099 | 160.1739 | 186.1324 | 244.1413 |
| thought_schema | 100 | 14447.283 | 144.4728 | 141.6179 | 194.5506 | 203.8105 | 271.6732 |
