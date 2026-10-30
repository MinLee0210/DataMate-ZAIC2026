# Eval: lit9-k1-h0

Command: `python -m scripts.eval --split train --subset /workspace/dev_h0.txt --topic lit9-k1-h0 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h0.txt`, `pipeline=malt`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.52** on 100 questions: 71 correct, 19 wrong, 10 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 10 |
| correct | 71 |
| wrong_type | 2 |
| wrong_value | 17 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| date | 7 | 0.5714 | 5 | 1 | 1 |
| list | 3 | 0.3333 | 2 | 1 | 0 |
| number | 66 | 0.4848 | 46 | 14 | 6 |
| percent | 23 | 0.6087 | 17 | 3 | 3 |
| string | 1 | 1.0 | 1 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.52 | 71 | 19 | 10 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.9 |
| selective_accuracy | 0.7889 |
| oracle_at_k | None |
| top_accuracy | 0.7889 |
| agreement_auroc | 0.6219 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.0 |
| unanswerable_recall | None |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.52 |
| 0.05 | 0.52 |
| 0.1 | 0.52 |
| 0.15 | 0.52 |
| 0.2 | 0.52 |
| 0.25 | 0.52 |
| 0.3 | 0.52 |
| 0.35 | 0.52 |
| 0.4 | 0.52 |
| 0.45 | 0.52 |
| 0.5 | 0.52 |
| 0.55 | 0.52 |
| 0.6 | 0.52 |
| 0.65 | 0.52 |
| 0.7 | 0.52 |
| 0.75 | 0.51 |
| 0.8 | 0.51 |
| 0.85 | 0.52 |
| 0.9 | 0.53 |
| 0.95 | 0.43 |
| 1.0 | 0.0 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 356 questions fit in 6 h
- LLM time share of wall time: 0.9909
- LLM calls: 332 (0 failed); questions over the 4-step limit: 0
- tokens: 4766591 prompt, 444565 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 6057.852 | 60.5785 | 51.295 | 85.895 | 102.005 | 196.41 |
| llm seconds | 100 | 6002.7174 | 60.0272 | 50.317 | 85.6262 | 100.9118 | 196.1823 |
| ingest seconds | 100 | 6.8408 | 0.0684 | 0.0202 | 0.1184 | 0.2044 | 0.9608 |
| llm calls | 100 | 332.0 | 3.32 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 330.0 | 3.3 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4766591.0 | 47665.91 | 46028.0 | 63519.0 | 69715.0 | 81306.0 |
| completion tokens | 100 | 444565.0 | 4445.65 | 3740.0 | 6461.0 | 7648.0 | 16150.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 332 | 159.9273 | 0.4817 | 0.3589 | 0.6946 | 1.0221 | 3.8963 |
| latency (s) | 332 | 6002.7174 | 18.0805 | 14.7765 | 27.3994 | 33.3987 | 141.9382 |
| decode tokens/s | 332 | 25536.5156 | 76.9172 | 75.7527 | 81.3445 | 85.6308 | 134.0224 |
| prompt tokens | 332 | 4766591.0 | 14357.2018 | 13971.0 | 17470.0 | 18251.0 | 20863.0 |
| completion tokens | 332 | 444565.0 | 1339.0512 | 1095.0 | 2053.0 | 2528.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 99 | 28.2071 | 0.2849 | 0.2464 | 0.5267 | 0.7022 | 0.8474 |
| progress | 99 | 6.3398 | 0.064 | 0.057 | 0.1066 | 0.1187 | 0.1786 |
| schema | 99 | 6.7751 | 0.0684 | 0.0413 | 0.1879 | 0.2261 | 0.5087 |
| thought_queries | 99 | 1595.6826 | 16.118 | 13.9298 | 26.0184 | 29.2894 | 39.4994 |
| thought_results | 99 | 2243.4632 | 22.6612 | 15.9006 | 43.3626 | 47.3588 | 155.8322 |
| thought_schema | 99 | 2124.9059 | 21.4637 | 16.8842 | 32.995 | 38.7057 | 156.8994 |
