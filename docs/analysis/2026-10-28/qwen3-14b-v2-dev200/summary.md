# Eval: qwen3-14b-v2-dev200

Command: `python -m scripts.eval --split train --subset dev200 --topic qwen3-14b-v2-dev200 --workers 16`

Model: `Qwen/Qwen3-14B-FP8`

Config: `split=train`, `subset=dev200`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.455** on 200 questions: 134 correct, 43 wrong, 23 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 23 |
| correct | 134 |
| wrong_type | 3 |
| wrong_value | 40 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 1.0 | 2 | 0 | 0 |
| date | 10 | 0.8 | 8 | 0 | 2 |
| list | 8 | 0.125 | 4 | 3 | 1 |
| number | 130 | 0.4692 | 91 | 30 | 9 |
| percent | 40 | 0.425 | 26 | 9 | 5 |
| string | 6 | 0.3333 | 3 | 1 | 2 |
| unanswerable | 4 | 0.0 | 0 | 0 | 4 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.455 | 134 | 43 | 23 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.885 |
| selective_accuracy | 0.7571 |
| oracle_at_k | None |
| top_accuracy | 0.738 |
| agreement_auroc | 0.5341 |
| repair_rate | 0.0 |
| unanswerable_precision | None |
| unanswerable_recall | 0.0 |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.445 |
| 0.05 | 0.455 |
| 0.1 | 0.455 |
| 0.15 | 0.455 |
| 0.2 | 0.455 |
| 0.25 | 0.455 |
| 0.3 | 0.455 |
| 0.35 | 0.455 |
| 0.4 | 0.455 |
| 0.45 | 0.455 |
| 0.5 | 0.455 |
| 0.55 | 0.455 |
| 0.6 | 0.455 |
| 0.65 | 0.455 |
| 0.7 | 0.455 |
| 0.75 | 0.435 |
| 0.8 | 0.435 |
| 0.85 | 0.425 |
| 0.9 | 0.425 |
| 0.95 | 0.02 |
| 1.0 | 0.0 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 164 questions fit in 6 h
- LLM time share of wall time: 0.9985
- LLM calls: 636 (0 failed); questions over the 4-step limit: 6
- tokens: 8823859 prompt, 600629 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 26270.279 | 131.3514 | 128.342 | 183.772 | 200.412 | 247.136 |
| llm seconds | 200 | 26231.7669 | 131.1588 | 128.2664 | 183.6411 | 200.198 | 247.0228 |
| ingest seconds | 200 | 8.5481 | 0.0427 | 0.0149 | 0.0804 | 0.1874 | 0.7262 |
| llm calls | 200 | 636.0 | 3.18 | 3.0 | 4.0 | 4.0 | 5.0 |
| llm steps | 200 | 636.0 | 3.18 | 3.0 | 4.0 | 4.0 | 5.0 |
| prompt tokens | 200 | 8823859.0 | 44119.295 | 40849.0 | 59755.0 | 68117.0 | 77485.0 |
| completion tokens | 200 | 600629.0 | 3003.145 | 2803.0 | 4149.0 | 4752.0 | 6776.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 636 | 22223.6267 | 34.9428 | 33.3398 | 52.9799 | 60.6366 | 101.4459 |
| latency (s) | 636 | 26231.7669 | 41.2449 | 39.4625 | 61.001 | 68.9412 | 113.2179 |
| decode tokens/s | 636 | 114386.1444 | 179.8524 | 155.4534 | 293.8232 | 353.2067 | 833.6378 |
| prompt tokens | 636 | 8823859.0 | 13873.9921 | 13498.0 | 16974.0 | 17749.0 | 20609.0 |
| completion tokens | 636 | 600629.0 | 944.3852 | 857.0 | 1562.0 | 1819.0 | 3516.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 200 | 2.8025 | 0.014 | 0.0114 | 0.0255 | 0.0376 | 0.0738 |
| progress | 200 | 9.3559 | 0.0468 | 0.0468 | 0.0661 | 0.0759 | 0.0936 |
| schema | 200 | 11.39 | 0.057 | 0.0275 | 0.1458 | 0.1732 | 0.4329 |
| thought_queries | 200 | 9237.5702 | 46.1879 | 41.8703 | 69.9559 | 81.18 | 113.2184 |
| thought_results | 200 | 7733.3336 | 38.6667 | 31.4249 | 62.8192 | 95.8538 | 132.2855 |
| thought_schema | 200 | 9264.6053 | 46.323 | 46.308 | 60.8703 | 64.813 | 92.4607 |
