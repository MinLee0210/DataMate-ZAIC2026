# Eval: qwen35-9b-v2-dev200

Command: `python -m scripts.eval --split train --subset dev200 --topic qwen35-9b-v2-dev200 --workers 10`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=dev200`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=10`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.415** on 200 questions: 131 correct, 48 wrong, 21 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 21 |
| correct | 131 |
| wrong_type | 8 |
| wrong_value | 40 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | -0.5 | 0 | 1 | 1 |
| date | 10 | 0.7 | 8 | 1 | 1 |
| list | 8 | -0.125 | 3 | 4 | 1 |
| number | 130 | 0.4615 | 88 | 28 | 14 |
| percent | 40 | 0.25 | 23 | 13 | 4 |
| string | 6 | 0.6667 | 5 | 1 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.415 | 131 | 48 | 21 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.895 |
| selective_accuracy | 0.7318 |
| oracle_at_k | None |
| top_accuracy | 0.7318 |
| agreement_auroc | 0.5922 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.5 |
| unanswerable_recall | 1.0 |
| errors | 6 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.415 |
| 0.05 | 0.425 |
| 0.1 | 0.425 |
| 0.15 | 0.425 |
| 0.2 | 0.425 |
| 0.25 | 0.425 |
| 0.3 | 0.425 |
| 0.35 | 0.425 |
| 0.4 | 0.425 |
| 0.45 | 0.425 |
| 0.5 | 0.425 |
| 0.55 | 0.425 |
| 0.6 | 0.425 |
| 0.65 | 0.425 |
| 0.7 | 0.425 |
| 0.75 | 0.425 |
| 0.8 | 0.425 |
| 0.85 | 0.425 |
| 0.9 | 0.425 |
| 0.95 | 0.29 |
| 1.0 | 0.005 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 313 questions fit in 6 h
- LLM time share of wall time: 0.9978
- LLM calls: 661 (0 failed); questions over the 4-step limit: 4
- tokens: 9102447 prompt, 818788 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 13797.188 | 68.9859 | 61.452 | 95.522 | 123.202 | 250.828 |
| llm seconds | 200 | 13767.0154 | 68.8351 | 61.3329 | 95.4247 | 123.1082 | 250.6924 |
| ingest seconds | 200 | 4.22 | 0.0211 | 0.0109 | 0.0497 | 0.0664 | 0.3061 |
| llm calls | 200 | 661.0 | 3.305 | 3.0 | 4.0 | 4.0 | 6.0 |
| llm steps | 200 | 632.0 | 3.16 | 3.0 | 4.0 | 4.0 | 5.0 |
| prompt tokens | 200 | 9102447.0 | 45512.235 | 42174.0 | 60623.0 | 68445.0 | 89740.0 |
| completion tokens | 200 | 818788.0 | 4093.94 | 3575.0 | 6025.0 | 7533.0 | 16541.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 657 | 10551.0484 | 16.0594 | 14.6784 | 23.1856 | 27.7142 | 50.0292 |
| latency (s) | 661 | 13767.0154 | 20.8276 | 18.6648 | 29.2212 | 34.2115 | 141.5397 |
| decode tokens/s | 657 | 212894.005 | 324.0396 | 282.0454 | 483.4172 | 579.6286 | 1306.8559 |
| prompt tokens | 661 | 9102447.0 | 13770.7216 | 13443.0 | 16949.0 | 17847.0 | 21206.0 |
| completion tokens | 661 | 818788.0 | 1238.711 | 1079.0 | 1755.0 | 2146.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 194 | 2.4123 | 0.0124 | 0.0097 | 0.0247 | 0.0311 | 0.0413 |
| progress | 194 | 8.1139 | 0.0418 | 0.0374 | 0.0644 | 0.0707 | 0.0936 |
| schema | 194 | 9.6828 | 0.0499 | 0.0225 | 0.1414 | 0.1794 | 0.358 |
| thought_queries | 194 | 3872.0541 | 19.959 | 17.1392 | 31.1321 | 36.6039 | 59.0194 |
| thought_results | 194 | 4964.3775 | 25.5896 | 20.2741 | 40.5097 | 51.684 | 200.9944 |
| thought_schema | 194 | 4446.9133 | 22.9222 | 20.7094 | 31.9157 | 35.4786 | 159.4924 |
