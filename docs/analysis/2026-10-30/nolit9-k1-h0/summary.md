# Eval: nolit9-k1-h0

Command: `python -m scripts.eval --split train --subset /workspace/dev_h0.txt --topic nolit9-k1-h0 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h0.txt`, `pipeline=malt`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.46** on 100 questions: 67 correct, 21 wrong, 12 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 12 |
| correct | 67 |
| wrong_type | 3 |
| wrong_value | 18 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| date | 7 | 0.5714 | 5 | 1 | 1 |
| list | 3 | 0.0 | 1 | 1 | 1 |
| number | 66 | 0.5152 | 46 | 12 | 8 |
| percent | 23 | 0.3043 | 14 | 7 | 2 |
| string | 1 | 1.0 | 1 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.46 | 67 | 21 | 12 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.88 |
| selective_accuracy | 0.7614 |
| oracle_at_k | None |
| top_accuracy | 0.7614 |
| agreement_auroc | 0.623 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.0 |
| unanswerable_recall | None |
| errors | 2 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.46 |
| 0.05 | 0.46 |
| 0.1 | 0.46 |
| 0.15 | 0.46 |
| 0.2 | 0.46 |
| 0.25 | 0.46 |
| 0.3 | 0.46 |
| 0.35 | 0.46 |
| 0.4 | 0.46 |
| 0.45 | 0.46 |
| 0.5 | 0.46 |
| 0.55 | 0.46 |
| 0.6 | 0.46 |
| 0.65 | 0.46 |
| 0.7 | 0.46 |
| 0.75 | 0.45 |
| 0.8 | 0.45 |
| 0.85 | 0.45 |
| 0.9 | 0.48 |
| 0.95 | 0.41 |
| 1.0 | 0.0 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 371 questions fit in 6 h
- LLM time share of wall time: 0.9956
- LLM calls: 324 (0 failed); questions over the 4-step limit: 0
- tokens: 4635983 prompt, 433444 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5819.26 | 58.1926 | 50.801 | 78.591 | 107.96 | 305.851 |
| llm seconds | 100 | 5793.8585 | 57.9386 | 50.4575 | 78.3128 | 107.8467 | 305.6329 |
| ingest seconds | 100 | 5.8772 | 0.0588 | 0.0193 | 0.1427 | 0.2496 | 0.721 |
| llm calls | 100 | 324.0 | 3.24 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 320.0 | 3.2 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4635983.0 | 46359.83 | 43352.0 | 60788.0 | 65085.0 | 73747.0 |
| completion tokens | 100 | 433444.0 | 4334.44 | 3674.0 | 6179.0 | 7698.0 | 22509.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 324 | 136.3631 | 0.4209 | 0.3558 | 0.6781 | 0.8367 | 1.9882 |
| latency (s) | 324 | 5793.8585 | 17.8823 | 14.9024 | 25.8891 | 33.95 | 142.0142 |
| decode tokens/s | 324 | 24949.6264 | 77.005 | 75.4432 | 83.0176 | 88.8415 | 137.5115 |
| prompt tokens | 324 | 4635983.0 | 14308.5895 | 13916.0 | 17432.0 | 18009.0 | 20733.0 |
| completion tokens | 324 | 433444.0 | 1337.7901 | 1091.0 | 1887.0 | 2488.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 98 | 1.3722 | 0.014 | 0.0121 | 0.0249 | 0.0351 | 0.071 |
| progress | 98 | 6.1544 | 0.0628 | 0.0559 | 0.1015 | 0.1251 | 0.1514 |
| schema | 98 | 7.1591 | 0.0731 | 0.0382 | 0.1689 | 0.3931 | 0.4765 |
| thought_queries | 98 | 1526.545 | 15.577 | 13.1626 | 24.9296 | 33.9219 | 44.1224 |
| thought_results | 98 | 2164.4746 | 22.0865 | 15.6253 | 34.4442 | 47.5324 | 277.9912 |
| thought_schema | 98 | 2028.6301 | 20.7003 | 17.117 | 33.952 | 36.7058 | 161.9374 |
