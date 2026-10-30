# Eval: base9-k1-h0

Command: `python -m scripts.eval --split train --subset /workspace/dev_h0.txt --topic base9-k1-h0 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h0.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.51** on 100 questions: 68 correct, 17 wrong, 15 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 15 |
| correct | 68 |
| wrong_value | 17 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| date | 7 | 0.7143 | 5 | 0 | 2 |
| list | 3 | 0.3333 | 2 | 1 | 0 |
| number | 66 | 0.5455 | 48 | 12 | 6 |
| percent | 23 | 0.3478 | 12 | 4 | 7 |
| string | 1 | 1.0 | 1 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.51 | 68 | 17 | 15 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.85 |
| selective_accuracy | 0.8 |
| oracle_at_k | None |
| top_accuracy | 0.7816 |
| agreement_auroc | 0.7488 |
| repair_rate | 0.0 |
| unanswerable_precision | None |
| unanswerable_recall | None |
| errors | 2 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.49 |
| 0.05 | 0.51 |
| 0.1 | 0.51 |
| 0.15 | 0.51 |
| 0.2 | 0.51 |
| 0.25 | 0.51 |
| 0.3 | 0.51 |
| 0.35 | 0.51 |
| 0.4 | 0.51 |
| 0.45 | 0.51 |
| 0.5 | 0.51 |
| 0.55 | 0.51 |
| 0.6 | 0.51 |
| 0.65 | 0.51 |
| 0.7 | 0.51 |
| 0.75 | 0.53 |
| 0.8 | 0.53 |
| 0.85 | 0.53 |
| 0.9 | 0.54 |
| 0.95 | 0.4 |
| 1.0 | 0.0 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 366 questions fit in 6 h
- LLM time share of wall time: 0.9947
- LLM calls: 331 (0 failed); questions over the 4-step limit: 0
- tokens: 4757302 prompt, 423028 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5901.204 | 59.012 | 51.078 | 90.524 | 109.338 | 154.298 |
| llm seconds | 100 | 5870.0777 | 58.7008 | 50.8184 | 90.2454 | 109.0268 | 154.067 |
| ingest seconds | 100 | 7.7715 | 0.0777 | 0.0231 | 0.161 | 0.4334 | 0.93 |
| llm calls | 100 | 331.0 | 3.31 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 327.0 | 3.27 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4757302.0 | 47573.02 | 45390.0 | 68114.0 | 69110.0 | 84602.0 |
| completion tokens | 100 | 423028.0 | 4230.28 | 3705.0 | 6142.0 | 7500.0 | 12480.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 331 | 192.7532 | 0.5823 | 0.3817 | 0.7511 | 1.1066 | 6.0354 |
| latency (s) | 331 | 5870.0777 | 17.7344 | 15.3337 | 28.837 | 36.1194 | 81.4869 |
| decode tokens/s | 331 | 24885.5292 | 75.1829 | 74.1429 | 81.25 | 88.3141 | 132.5631 |
| prompt tokens | 331 | 4757302.0 | 14372.5136 | 14002.0 | 17477.0 | 18107.0 | 21824.0 |
| completion tokens | 331 | 423028.0 | 1278.0302 | 1102.0 | 2024.0 | 2557.0 | 6200.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 98 | 1.9332 | 0.0197 | 0.0143 | 0.0392 | 0.046 | 0.158 |
| progress | 98 | 7.6659 | 0.0782 | 0.0638 | 0.1131 | 0.1347 | 0.8019 |
| schema | 98 | 7.6747 | 0.0783 | 0.0362 | 0.21 | 0.2617 | 0.5495 |
| thought_queries | 98 | 1625.8442 | 16.5902 | 13.6989 | 26.4803 | 30.4125 | 61.5101 |
| thought_results | 98 | 2081.2932 | 21.2377 | 16.5399 | 36.4111 | 55.6871 | 76.7923 |
| thought_schema | 98 | 2090.5384 | 21.332 | 17.563 | 35.4714 | 41.2182 | 81.5083 |
