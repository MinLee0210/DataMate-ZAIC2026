# Eval: lang-en-dev200

Command: `python -m scripts.eval --split train --subset dev200 --topic lang-en-dev200 --workers 14`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=dev200`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=14`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.38** on 200 questions: 128 correct, 52 wrong, 20 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 20 |
| correct | 128 |
| wrong_type | 15 |
| wrong_value | 37 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 1 | 1 | 0 |
| date | 10 | 0.2 | 5 | 3 | 2 |
| list | 8 | -0.25 | 2 | 4 | 2 |
| number | 130 | 0.4692 | 91 | 30 | 9 |
| percent | 40 | 0.225 | 22 | 13 | 5 |
| string | 6 | 0.3333 | 3 | 1 | 2 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.38 | 128 | 52 | 20 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.9 |
| selective_accuracy | 0.7111 |
| oracle_at_k | None |
| top_accuracy | 0.7088 |
| agreement_auroc | 0.6367 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.3333 |
| unanswerable_recall | 1.0 |
| errors | 4 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.38 |
| 0.05 | 0.38 |
| 0.1 | 0.38 |
| 0.15 | 0.38 |
| 0.2 | 0.38 |
| 0.25 | 0.38 |
| 0.3 | 0.38 |
| 0.35 | 0.38 |
| 0.4 | 0.38 |
| 0.45 | 0.38 |
| 0.5 | 0.38 |
| 0.55 | 0.38 |
| 0.6 | 0.38 |
| 0.65 | 0.38 |
| 0.7 | 0.38 |
| 0.75 | 0.375 |
| 0.8 | 0.375 |
| 0.85 | 0.375 |
| 0.9 | 0.375 |
| 0.95 | 0.34 |
| 1.0 | -0.005 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 402 questions fit in 6 h
- LLM time share of wall time: 0.9968
- LLM calls: 650 (0 failed); questions over the 4-step limit: 0
- tokens: 9250508 prompt, 802996 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 10740.295 | 53.7015 | 47.173 | 78.504 | 93.281 | 226.217 |
| llm seconds | 200 | 10706.2954 | 53.5315 | 47.0413 | 77.9877 | 93.0905 | 226.0929 |
| ingest seconds | 200 | 6.3885 | 0.0319 | 0.0117 | 0.0592 | 0.139 | 0.5862 |
| llm calls | 200 | 650.0 | 3.25 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 200 | 642.0 | 3.21 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 200 | 9250508.0 | 46252.54 | 42813.0 | 61389.0 | 69502.0 | 84391.0 |
| completion tokens | 200 | 802996.0 | 4014.98 | 3508.0 | 5702.0 | 6938.0 | 16898.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 650 | 279.8968 | 0.4306 | 0.3524 | 0.6512 | 0.8325 | 4.3552 |
| latency (s) | 650 | 10706.2954 | 16.4712 | 14.2548 | 23.3712 | 28.8662 | 137.9114 |
| decode tokens/s | 650 | 50266.8833 | 77.3337 | 76.8091 | 82.6075 | 84.6069 | 130.5633 |
| prompt tokens | 650 | 9250508.0 | 14231.5508 | 13860.0 | 17356.0 | 18487.0 | 21691.0 |
| completion tokens | 650 | 802996.0 | 1235.3785 | 1072.0 | 1785.0 | 2109.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 196 | 2.5875 | 0.0132 | 0.0109 | 0.0246 | 0.0302 | 0.1594 |
| progress | 196 | 9.4846 | 0.0484 | 0.0409 | 0.0682 | 0.0897 | 0.4199 |
| schema | 196 | 9.6061 | 0.049 | 0.0213 | 0.1303 | 0.1649 | 0.3635 |
| thought_queries | 196 | 2976.2518 | 15.185 | 13.1481 | 23.5196 | 27.1678 | 66.5014 |
| thought_results | 195 | 3924.1766 | 20.124 | 15.1852 | 34.0907 | 43.8688 | 161.6884 |
| thought_schema | 196 | 3652.1159 | 18.6332 | 15.979 | 25.9813 | 34.7525 | 158.9124 |
