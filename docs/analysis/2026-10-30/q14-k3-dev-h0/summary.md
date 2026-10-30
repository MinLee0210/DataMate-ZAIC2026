# Eval: q14-k3-dev-h0

Command: `python -m scripts.eval --split train --subset /workspace/dev_h0.txt --topic q14-k3-dev-h0 --workers 16`

Model: `Qwen/Qwen3-14B-FP8`

Config: `split=train`, `subset=/workspace/dev_h0.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.53** on 100 questions: 76 correct, 23 wrong, 1 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 1 |
| correct | 76 |
| wrong_type | 1 |
| wrong_value | 22 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| date | 7 | 0.4286 | 5 | 2 | 0 |
| list | 3 | 0.3333 | 2 | 1 | 0 |
| number | 66 | 0.5303 | 50 | 15 | 1 |
| percent | 23 | 0.5652 | 18 | 5 | 0 |
| string | 1 | 1.0 | 1 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.53 | 76 | 23 | 1 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.99 |
| selective_accuracy | 0.7677 |
| oracle_at_k | None |
| top_accuracy | 0.7677 |
| agreement_auroc | 0.6779 |
| repair_rate | 0.0 |
| unanswerable_precision | None |
| unanswerable_recall | None |
| errors | 0 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.53 |
| 0.05 | 0.53 |
| 0.1 | 0.53 |
| 0.15 | 0.53 |
| 0.2 | 0.53 |
| 0.25 | 0.53 |
| 0.3 | 0.53 |
| 0.35 | 0.57 |
| 0.4 | 0.57 |
| 0.45 | 0.57 |
| 0.5 | 0.57 |
| 0.55 | 0.57 |
| 0.6 | 0.57 |
| 0.65 | 0.57 |
| 0.7 | 0.46 |
| 0.75 | 0.46 |
| 0.8 | 0.46 |
| 0.85 | 0.46 |
| 0.9 | 0.46 |
| 0.95 | 0.46 |
| 1.0 | 0.46 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 53 questions fit in 6 h
- LLM time share of wall time: 0.9989
- LLM calls: 930 (0 failed); questions over the 4-step limit: 100
- tokens: 13424169 prompt, 909859 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 40311.824 | 403.1182 | 387.384 | 545.603 | 581.416 | 650.361 |
| llm seconds | 100 | 40268.0995 | 402.681 | 387.108 | 544.0635 | 581.1996 | 650.047 |
| ingest seconds | 100 | 7.9162 | 0.0792 | 0.0173 | 0.2472 | 0.4201 | 0.9375 |
| llm calls | 100 | 930.0 | 9.3 | 9.0 | 10.0 | 10.0 | 12.0 |
| llm steps | 100 | 930.0 | 9.3 | 9.0 | 10.0 | 10.0 | 12.0 |
| prompt tokens | 100 | 13424169.0 | 134241.69 | 127968.0 | 172857.0 | 177130.0 | 212748.0 |
| completion tokens | 100 | 909859.0 | 9098.59 | 8872.0 | 11712.0 | 12675.0 | 16616.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 930 | 13048.4653 | 14.0306 | 13.003 | 26.4016 | 30.4596 | 47.5216 |
| latency (s) | 930 | 40268.0995 | 43.299 | 40.9858 | 67.1293 | 75.9194 | 115.1429 |
| decode tokens/s | 930 | 31553.3545 | 33.9283 | 33.3968 | 37.5363 | 39.4214 | 77.4671 |
| prompt tokens | 930 | 13424169.0 | 14434.5903 | 14055.0 | 17609.0 | 18061.0 | 20920.0 |
| completion tokens | 930 | 909859.0 | 978.343 | 887.0 | 1637.0 | 1922.0 | 3527.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 100 | 3.4814 | 0.0348 | 0.0303 | 0.0603 | 0.0702 | 0.1566 |
| progress | 100 | 14.6056 | 0.1461 | 0.1252 | 0.1816 | 0.194 | 2.2631 |
| schema | 100 | 13.4867 | 0.1349 | 0.0673 | 0.3483 | 0.4522 | 0.8172 |
| thought_queries | 100 | 14596.8617 | 145.9686 | 142.0333 | 200.1072 | 216.5599 | 316.7031 |
| thought_results | 100 | 10664.8461 | 106.6485 | 94.3819 | 168.3651 | 196.3047 | 266.5329 |
| thought_schema | 100 | 15008.5471 | 150.0855 | 147.2678 | 192.7029 | 208.2352 | 251.9353 |
