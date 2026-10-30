# Eval: d1k-old-h1

Command: `python -m scripts.eval --split train --subset /workspace/d1k_h1.txt --topic d1k-old-h1 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/d1k_h1.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.436** on 500 questions: 333 correct, 115 wrong, 52 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 52 |
| correct | 333 |
| wrong_type | 21 |
| wrong_value | 94 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 5 | 0.0 | 1 | 1 | 3 |
| date | 22 | 0.5909 | 17 | 4 | 1 |
| list | 32 | -0.25 | 9 | 17 | 6 |
| number | 317 | 0.4385 | 213 | 74 | 30 |
| percent | 98 | 0.551 | 71 | 17 | 10 |
| string | 13 | 0.6923 | 11 | 2 | 0 |
| table | 2 | 0.5 | 1 | 0 | 1 |
| unanswerable | 11 | 0.9091 | 10 | 0 | 1 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 500 | 0.436 | 333 | 115 | 52 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.896 |
| selective_accuracy | 0.7433 |
| oracle_at_k | None |
| top_accuracy | 0.7433 |
| agreement_auroc | 0.625 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.7692 |
| unanswerable_recall | 0.9091 |
| errors | 14 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.436 |
| 0.05 | 0.436 |
| 0.1 | 0.436 |
| 0.15 | 0.436 |
| 0.2 | 0.436 |
| 0.25 | 0.436 |
| 0.3 | 0.436 |
| 0.35 | 0.436 |
| 0.4 | 0.436 |
| 0.45 | 0.436 |
| 0.5 | 0.436 |
| 0.55 | 0.436 |
| 0.6 | 0.436 |
| 0.65 | 0.438 |
| 0.7 | 0.438 |
| 0.75 | 0.436 |
| 0.8 | 0.436 |
| 0.85 | 0.436 |
| 0.9 | 0.428 |
| 0.95 | 0.352 |
| 1.0 | 0.012 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 500; at the mean pace, 365 questions fit in 6 h
- LLM time share of wall time: 0.9967
- LLM calls: 1632 (0 failed); questions over the 4-step limit: 0
- tokens: 23352989 prompt, 2138531 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 500 | 29586.15 | 59.1723 | 49.331 | 80.532 | 121.298 | 367.408 |
| llm seconds | 500 | 29489.7589 | 58.9795 | 49.1459 | 80.3918 | 121.0927 | 367.2902 |
| ingest seconds | 500 | 15.1493 | 0.0303 | 0.0094 | 0.0548 | 0.0829 | 0.7807 |
| llm calls | 500 | 1632.0 | 3.264 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 500 | 1605.0 | 3.21 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 500 | 23352989.0 | 46705.978 | 43843.0 | 62388.0 | 68890.0 | 83031.0 |
| completion tokens | 500 | 2138531.0 | 4277.062 | 3531.0 | 5893.0 | 8658.0 | 26254.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 1632 | 691.1724 | 0.4235 | 0.3659 | 0.6461 | 0.7575 | 5.8033 |
| latency (s) | 1632 | 29489.7589 | 18.0697 | 14.793 | 25.4983 | 31.6237 | 145.0546 |
| decode tokens/s | 1632 | 121734.8979 | 74.5925 | 74.3061 | 79.2821 | 81.1955 | 136.8557 |
| prompt tokens | 1632 | 23352989.0 | 14309.4295 | 13992.0 | 17326.0 | 18229.0 | 21741.0 |
| completion tokens | 1632 | 2138531.0 | 1310.3744 | 1071.0 | 1846.0 | 2308.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 486 | 7.5345 | 0.0155 | 0.013 | 0.0267 | 0.0357 | 0.2526 |
| progress | 486 | 30.536 | 0.0628 | 0.0567 | 0.0986 | 0.1215 | 0.3078 |
| schema | 486 | 26.6607 | 0.0549 | 0.0304 | 0.1457 | 0.178 | 0.6354 |
| thought_queries | 486 | 7840.6343 | 16.133 | 13.9011 | 24.0427 | 28.675 | 174.7306 |
| thought_results | 486 | 10425.5009 | 21.4516 | 15.8339 | 35.5837 | 45.6371 | 192.5534 |
| thought_schema | 486 | 10003.2721 | 20.5829 | 16.6952 | 28.1051 | 35.419 | 192.505 |
