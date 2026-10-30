# Eval: d1k-old-h0

Command: `python -m scripts.eval --split train --subset /workspace/d1k_h0.txt --topic d1k-old-h0 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/d1k_h0.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.354** on 500 questions: 309 correct, 132 wrong, 59 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 59 |
| correct | 309 |
| wrong_type | 28 |
| wrong_value | 104 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 4 | 0.0 | 1 | 1 | 2 |
| date | 28 | 0.3929 | 18 | 7 | 3 |
| list | 31 | -0.4839 | 7 | 22 | 2 |
| number | 326 | 0.3896 | 207 | 80 | 39 |
| percent | 83 | 0.3855 | 51 | 19 | 13 |
| string | 11 | 0.6364 | 9 | 2 | 0 |
| table | 4 | 0.5 | 3 | 1 | 0 |
| unanswerable | 13 | 1.0 | 13 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 500 | 0.354 | 309 | 132 | 59 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.882 |
| selective_accuracy | 0.7007 |
| oracle_at_k | None |
| top_accuracy | 0.6959 |
| agreement_auroc | 0.625 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.65 |
| unanswerable_recall | 1.0 |
| errors | 7 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.348 |
| 0.05 | 0.354 |
| 0.1 | 0.354 |
| 0.15 | 0.354 |
| 0.2 | 0.354 |
| 0.25 | 0.354 |
| 0.3 | 0.354 |
| 0.35 | 0.354 |
| 0.4 | 0.354 |
| 0.45 | 0.354 |
| 0.5 | 0.354 |
| 0.55 | 0.354 |
| 0.6 | 0.354 |
| 0.65 | 0.354 |
| 0.7 | 0.354 |
| 0.75 | 0.356 |
| 0.8 | 0.356 |
| 0.85 | 0.354 |
| 0.9 | 0.352 |
| 0.95 | 0.266 |
| 1.0 | 0.012 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 500; at the mean pace, 356 questions fit in 6 h
- LLM time share of wall time: 0.9967
- LLM calls: 1638 (0 failed); questions over the 4-step limit: 0
- tokens: 23615635 prompt, 2160680 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 500 | 30303.737 | 60.6075 | 51.233 | 91.814 | 113.536 | 256.808 |
| llm seconds | 500 | 30204.4827 | 60.409 | 50.9139 | 91.4 | 113.427 | 256.3735 |
| ingest seconds | 500 | 13.0111 | 0.026 | 0.0096 | 0.0555 | 0.083 | 0.6534 |
| llm calls | 500 | 1638.0 | 3.276 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 500 | 1624.0 | 3.248 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 500 | 23615635.0 | 47231.27 | 44787.0 | 61448.0 | 68005.0 | 83922.0 |
| completion tokens | 500 | 2160680.0 | 4321.36 | 3660.0 | 6569.0 | 8119.0 | 17982.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 1638 | 702.3991 | 0.4288 | 0.3731 | 0.6831 | 0.8398 | 4.3596 |
| latency (s) | 1638 | 30204.4827 | 18.4399 | 15.4054 | 27.2057 | 35.4311 | 148.6727 |
| decode tokens/s | 1638 | 120465.3726 | 73.5442 | 73.1563 | 78.4928 | 80.1449 | 135.2555 |
| prompt tokens | 1638 | 23615635.0 | 14417.3596 | 14024.0 | 17375.0 | 18482.0 | 21765.0 |
| completion tokens | 1638 | 2160680.0 | 1319.0965 | 1095.0 | 1935.0 | 2514.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| analysis | 1 | 0.0016 | 0.0016 | 0.0016 | 0.0016 | 0.0016 | 0.0016 |
| data | 493 | 8.1053 | 0.0164 | 0.0134 | 0.0281 | 0.0356 | 0.223 |
| progress | 493 | 33.4593 | 0.0679 | 0.0581 | 0.1065 | 0.1249 | 0.8394 |
| schema | 493 | 30.0716 | 0.061 | 0.0332 | 0.1761 | 0.2077 | 0.4568 |
| thought_queries | 493 | 8438.5475 | 17.1167 | 14.247 | 26.9026 | 36.0133 | 88.363 |
| thought_results | 493 | 11218.8764 | 22.7563 | 16.2542 | 37.9862 | 47.8527 | 202.7179 |
| thought_schema | 493 | 10295.1517 | 20.8827 | 17.9591 | 31.5008 | 37.2634 | 176.9428 |
