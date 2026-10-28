# Eval: qwen35-9b-k3-dev200-h0

Command: `python -m scripts.eval --split train --subset /tmp/dm-exp/e1_dev200_h0.txt --topic qwen35-9b-k3-dev200-h0 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/tmp/dm-exp/e1_dev200_h0.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.505** on 101 questions: 71 correct, 20 wrong, 10 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 10 |
| correct | 71 |
| wrong_type | 4 |
| wrong_value | 16 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| date | 5 | 0.4 | 3 | 1 | 1 |
| list | 6 | 0.0 | 3 | 3 | 0 |
| number | 65 | 0.4615 | 44 | 14 | 7 |
| percent | 19 | 0.6842 | 15 | 2 | 2 |
| string | 5 | 1.0 | 5 | 0 | 0 |
| unanswerable | 1 | 1.0 | 1 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 101 | 0.505 | 71 | 20 | 10 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.901 |
| selective_accuracy | 0.7802 |
| oracle_at_k | None |
| top_accuracy | 0.7802 |
| agreement_auroc | 0.6975 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.3333 |
| unanswerable_recall | 1.0 |
| errors | 6 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.505 |
| 0.05 | 0.505 |
| 0.1 | 0.505 |
| 0.15 | 0.505 |
| 0.2 | 0.505 |
| 0.25 | 0.505 |
| 0.3 | 0.505 |
| 0.35 | 0.5248 |
| 0.4 | 0.5248 |
| 0.45 | 0.5248 |
| 0.5 | 0.5248 |
| 0.55 | 0.5248 |
| 0.6 | 0.5248 |
| 0.65 | 0.5248 |
| 0.7 | 0.4257 |
| 0.75 | 0.4257 |
| 0.8 | 0.4257 |
| 0.85 | 0.4257 |
| 0.9 | 0.4257 |
| 0.95 | 0.4257 |
| 1.0 | 0.4257 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 101; at the mean pace, 128 questions fit in 6 h
- LLM time share of wall time: 0.9958
- LLM calls: 988 (0 failed); questions over the 4-step limit: 95
- tokens: 14573204 prompt, 1294486 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 101 | 16989.542 | 168.2133 | 150.862 | 242.87 | 330.532 | 545.834 |
| llm seconds | 101 | 16918.6072 | 167.511 | 149.8631 | 242.4385 | 329.6156 | 545.1222 |
| ingest seconds | 101 | 7.9401 | 0.0786 | 0.0272 | 0.2465 | 0.3819 | 0.8669 |
| llm calls | 101 | 988.0 | 9.7822 | 10.0 | 12.0 | 13.0 | 15.0 |
| llm steps | 101 | 938.0 | 9.2871 | 9.0 | 12.0 | 12.0 | 14.0 |
| prompt tokens | 101 | 14573204.0 | 144289.1485 | 137733.0 | 183767.0 | 223164.0 | 307627.0 |
| completion tokens | 101 | 1294486.0 | 12816.6931 | 11506.0 | 18141.0 | 25165.0 | 41507.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 980 | 11964.8244 | 12.209 | 10.6413 | 19.1335 | 23.9213 | 51.5739 |
| latency (s) | 988 | 16918.6072 | 17.1241 | 14.6772 | 24.8114 | 31.4322 | 138.3986 |
| decode tokens/s | 980 | 328882.5497 | 335.5944 | 294.4689 | 496.3212 | 591.4729 | 1727.1137 |
| prompt tokens | 988 | 14573204.0 | 14750.2065 | 14481.0 | 19203.0 | 19972.0 | 21509.0 |
| completion tokens | 988 | 1294486.0 | 1310.2085 | 1113.0 | 1853.0 | 2402.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 95 | 6.3993 | 0.0674 | 0.0564 | 0.1042 | 0.1323 | 0.5879 |
| progress | 95 | 21.977 | 0.2313 | 0.218 | 0.329 | 0.3687 | 0.6622 |
| schema | 95 | 21.5262 | 0.2266 | 0.1275 | 0.5459 | 0.7408 | 1.2433 |
| thought_queries | 95 | 4799.2555 | 50.5185 | 44.6423 | 69.0839 | 78.5291 | 255.3666 |
| thought_results | 95 | 6524.8103 | 68.6822 | 53.3984 | 97.7053 | 122.8011 | 385.4239 |
| thought_schema | 95 | 5239.9174 | 55.157 | 50.4352 | 73.696 | 96.7466 | 192.9061 |
