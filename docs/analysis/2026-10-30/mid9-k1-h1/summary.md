# Eval: mid9-k1-h1

Command: `python -m scripts.eval --split train --subset /workspace/dev_h1.txt --topic mid9-k1-h1 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h1.txt`, `pipeline=malt`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.4** on 100 questions: 65 correct, 25 wrong, 10 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 10 |
| correct | 65 |
| wrong_type | 6 |
| wrong_value | 19 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 1 | 1 | 0 |
| date | 3 | 1.0 | 3 | 0 | 0 |
| list | 5 | -0.6 | 1 | 4 | 0 |
| number | 64 | 0.5156 | 45 | 12 | 7 |
| percent | 17 | 0.1176 | 8 | 6 | 3 |
| string | 5 | 0.2 | 3 | 2 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.4 | 65 | 25 | 10 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.9 |
| selective_accuracy | 0.7222 |
| oracle_at_k | None |
| top_accuracy | 0.7222 |
| agreement_auroc | 0.5846 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.6667 |
| unanswerable_recall | 1.0 |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.4 |
| 0.05 | 0.4 |
| 0.1 | 0.4 |
| 0.15 | 0.4 |
| 0.2 | 0.4 |
| 0.25 | 0.4 |
| 0.3 | 0.4 |
| 0.35 | 0.4 |
| 0.4 | 0.4 |
| 0.45 | 0.4 |
| 0.5 | 0.4 |
| 0.55 | 0.4 |
| 0.6 | 0.4 |
| 0.65 | 0.39 |
| 0.7 | 0.39 |
| 0.75 | 0.4 |
| 0.8 | 0.4 |
| 0.85 | 0.4 |
| 0.9 | 0.4 |
| 0.95 | 0.3 |
| 1.0 | 0.01 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 378 questions fit in 6 h
- LLM time share of wall time: 0.995
- LLM calls: 327 (0 failed); questions over the 4-step limit: 0
- tokens: 4605676 prompt, 418512 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5702.988 | 57.0299 | 47.675 | 79.094 | 107.138 | 205.335 |
| llm seconds | 100 | 5674.3531 | 56.7435 | 46.9661 | 78.1416 | 106.892 | 205.147 |
| ingest seconds | 100 | 7.4168 | 0.0742 | 0.0203 | 0.2476 | 0.3503 | 0.7652 |
| llm calls | 100 | 327.0 | 3.27 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 325.0 | 3.25 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4605676.0 | 46056.76 | 44006.0 | 60743.0 | 61564.0 | 83378.0 |
| completion tokens | 100 | 418512.0 | 4185.12 | 3492.0 | 5679.0 | 7771.0 | 15271.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 327 | 157.8752 | 0.4828 | 0.3642 | 0.7749 | 1.1966 | 3.5505 |
| latency (s) | 327 | 5674.3531 | 17.3528 | 14.0311 | 27.2329 | 31.5894 | 142.412 |
| decode tokens/s | 327 | 25045.7345 | 76.5925 | 75.3537 | 83.0619 | 90.2014 | 136.9081 |
| prompt tokens | 327 | 4605676.0 | 14084.6361 | 13750.0 | 17171.0 | 19718.0 | 21550.0 |
| completion tokens | 327 | 418512.0 | 1279.8532 | 1045.0 | 2019.0 | 2319.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 99 | 1.6365 | 0.0165 | 0.0127 | 0.03 | 0.0448 | 0.0988 |
| progress | 99 | 6.5396 | 0.0661 | 0.0561 | 0.1219 | 0.1381 | 0.2424 |
| schema | 99 | 6.7772 | 0.0685 | 0.0351 | 0.1745 | 0.234 | 0.4994 |
| thought_queries | 99 | 1544.6323 | 15.6023 | 12.9001 | 26.4193 | 30.5252 | 66.1546 |
| thought_results | 99 | 2073.697 | 20.9464 | 15.5128 | 31.8786 | 45.2776 | 172.3295 |
| thought_schema | 99 | 2022.3881 | 20.4282 | 16.3397 | 30.3339 | 38.5702 | 152.0508 |
