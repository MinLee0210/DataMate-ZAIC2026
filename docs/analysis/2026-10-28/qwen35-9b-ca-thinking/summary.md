# Eval: qwen35-9b-ca-thinking

Command: `python -m scripts.eval --split train --subset dev200 --topic qwen35-9b-ca-thinking --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=dev200`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.365** on 200 questions: 104 correct, 31 wrong, 65 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 65 |
| correct | 104 |
| wrong_type | 6 |
| wrong_value | 25 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 0 | 0 | 2 |
| date | 10 | 0.5 | 6 | 1 | 3 |
| list | 8 | 0.0 | 3 | 3 | 2 |
| number | 130 | 0.4231 | 77 | 22 | 31 |
| percent | 40 | 0.225 | 13 | 4 | 23 |
| string | 6 | 0.6667 | 5 | 1 | 0 |
| unanswerable | 4 | 0.0 | 0 | 0 | 4 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.365 | 104 | 31 | 65 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.675 |
| selective_accuracy | 0.7704 |
| oracle_at_k | None |
| top_accuracy | 0.7704 |
| agreement_auroc | 0.5645 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.0 |
| unanswerable_recall | 0.0 |
| errors | 51 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.365 |
| 0.05 | 0.385 |
| 0.1 | 0.385 |
| 0.15 | 0.385 |
| 0.2 | 0.385 |
| 0.25 | 0.385 |
| 0.3 | 0.385 |
| 0.35 | 0.385 |
| 0.4 | 0.385 |
| 0.45 | 0.385 |
| 0.5 | 0.385 |
| 0.55 | 0.385 |
| 0.6 | 0.385 |
| 0.65 | 0.385 |
| 0.7 | 0.385 |
| 0.75 | 0.385 |
| 0.8 | 0.385 |
| 0.85 | 0.385 |
| 0.9 | 0.385 |
| 0.95 | 0.385 |
| 1.0 | 0.385 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 263 questions fit in 6 h
- LLM time share of wall time: 0.9969
- LLM calls: 539 (0 failed); questions over the 4-step limit: 0
- tokens: 7321398 prompt, 1236901 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 16405.716 | 82.0286 | 50.3 | 154.99 | 190.217 | 314.167 |
| llm seconds | 200 | 16354.4257 | 81.7721 | 50.0351 | 154.7647 | 190.0944 | 313.5251 |
| ingest seconds | 200 | 10.3567 | 0.0518 | 0.02 | 0.115 | 0.231 | 0.8266 |
| llm calls | 200 | 539.0 | 2.695 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 200 | 506.0 | 2.53 | 3.0 | 3.0 | 4.0 | 4.0 |
| prompt tokens | 200 | 7321398.0 | 36606.99 | 37584.0 | 53438.0 | 58379.0 | 68336.0 |
| completion tokens | 200 | 1236901.0 | 6184.505 | 3723.0 | 11605.0 | 14397.0 | 23564.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 471 | 5568.3928 | 11.8225 | 10.1208 | 17.0793 | 22.7367 | 82.1527 |
| latency (s) | 539 | 16354.4257 | 30.3422 | 14.7415 | 130.7334 | 135.7681 | 141.8047 |
| decode tokens/s | 471 | 165442.152 | 351.2572 | 299.0787 | 538.3766 | 671.4639 | 2456.6242 |
| prompt tokens | 539 | 7321398.0 | 13583.2987 | 13233.0 | 16712.0 | 17635.0 | 20912.0 |
| completion tokens | 539 | 1236901.0 | 2294.8071 | 1090.0 | 10240.0 | 10240.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 149 | 2.5235 | 0.0169 | 0.0123 | 0.0248 | 0.032 | 0.1609 |
| progress | 149 | 11.5003 | 0.0772 | 0.0713 | 0.1114 | 0.1311 | 0.3761 |
| schema | 149 | 11.7737 | 0.079 | 0.0342 | 0.2463 | 0.3121 | 0.3643 |
| thought_queries | 149 | 2287.4584 | 15.3521 | 13.4155 | 23.116 | 28.7713 | 49.0943 |
| thought_results | 149 | 4540.3969 | 30.4725 | 12.5566 | 72.9245 | 153.1813 | 271.7354 |
| thought_schema | 149 | 2574.4225 | 17.278 | 16.1449 | 24.4024 | 26.6824 | 47.5162 |
