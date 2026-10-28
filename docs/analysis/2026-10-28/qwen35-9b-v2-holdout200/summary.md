# Eval: qwen35-9b-v2-holdout200

Command: `python -m scripts.eval --split train --subset holdout200 --topic qwen35-9b-v2-holdout200 --workers 10`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=holdout200`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=10`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.645** on 200 questions: 159 correct, 30 wrong, 11 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 11 |
| correct | 159 |
| wrong_type | 7 |
| wrong_value | 23 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | -0.5 | 0 | 1 | 1 |
| date | 6 | 0.3333 | 4 | 2 | 0 |
| list | 15 | 0.3333 | 9 | 4 | 2 |
| number | 126 | 0.7302 | 106 | 14 | 6 |
| percent | 38 | 0.5526 | 29 | 8 | 1 |
| string | 4 | 0.5 | 3 | 1 | 0 |
| table | 1 | 1.0 | 1 | 0 | 0 |
| unanswerable | 8 | 0.875 | 7 | 0 | 1 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.645 | 159 | 30 | 11 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.945 |
| selective_accuracy | 0.8413 |
| oracle_at_k | None |
| top_accuracy | 0.8413 |
| agreement_auroc | 0.6644 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.7 |
| unanswerable_recall | 0.875 |
| errors | 2 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.645 |
| 0.05 | 0.655 |
| 0.1 | 0.655 |
| 0.15 | 0.655 |
| 0.2 | 0.655 |
| 0.25 | 0.655 |
| 0.3 | 0.655 |
| 0.35 | 0.655 |
| 0.4 | 0.655 |
| 0.45 | 0.655 |
| 0.5 | 0.655 |
| 0.55 | 0.655 |
| 0.6 | 0.655 |
| 0.65 | 0.655 |
| 0.7 | 0.655 |
| 0.75 | 0.65 |
| 0.8 | 0.65 |
| 0.85 | 0.65 |
| 0.9 | 0.655 |
| 0.95 | 0.445 |
| 1.0 | 0.03 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 307 questions fit in 6 h
- LLM time share of wall time: 0.9983
- LLM calls: 661 (0 failed); questions over the 4-step limit: 3
- tokens: 8887837 prompt, 858047 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 14041.586 | 70.2079 | 57.303 | 101.097 | 128.701 | 399.58 |
| llm seconds | 200 | 14018.3005 | 70.0915 | 57.1171 | 100.9921 | 128.4562 | 399.3419 |
| ingest seconds | 200 | 2.3299 | 0.0116 | 0.0001 | 0.0297 | 0.0501 | 0.3086 |
| llm calls | 200 | 661.0 | 3.305 | 3.0 | 4.0 | 4.0 | 5.0 |
| llm steps | 200 | 637.0 | 3.185 | 3.0 | 4.0 | 4.0 | 5.0 |
| prompt tokens | 200 | 8887837.0 | 44439.185 | 43906.0 | 62979.0 | 67870.0 | 87204.0 |
| completion tokens | 200 | 858047.0 | 4290.235 | 3379.0 | 6376.0 | 8321.0 | 28515.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 652 | 10182.8087 | 15.6178 | 14.3816 | 22.9819 | 27.8905 | 54.9892 |
| latency (s) | 661 | 14018.3005 | 21.2077 | 18.1492 | 28.4677 | 34.9138 | 147.2754 |
| decode tokens/s | 652 | 210986.6262 | 323.5991 | 293.4662 | 496.8077 | 583.5763 | 1008.9141 |
| prompt tokens | 661 | 8887837.0 | 13446.0469 | 12154.0 | 16694.0 | 16911.0 | 18081.0 |
| completion tokens | 661 | 858047.0 | 1298.1044 | 1062.0 | 1786.0 | 2319.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 198 | 2.3652 | 0.0119 | 0.0097 | 0.0215 | 0.0275 | 0.0432 |
| progress | 198 | 8.5888 | 0.0434 | 0.0394 | 0.0604 | 0.0733 | 0.212 |
| schema | 198 | 7.0556 | 0.0356 | 0.0093 | 0.1258 | 0.1476 | 0.2161 |
| thought_queries | 198 | 3784.3337 | 19.1128 | 16.8003 | 25.6525 | 35.6842 | 181.1368 |
| thought_results | 198 | 5378.8007 | 27.1657 | 18.9762 | 46.3607 | 57.9732 | 329.3813 |
| thought_schema | 198 | 4744.8632 | 23.964 | 20.1883 | 34.0829 | 42.0879 | 164.0548 |
