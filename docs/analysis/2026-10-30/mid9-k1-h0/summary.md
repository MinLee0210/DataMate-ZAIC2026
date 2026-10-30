# Eval: mid9-k1-h0

Command: `python -m scripts.eval --split train --subset /workspace/dev_h0.txt --topic mid9-k1-h0 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h0.txt`, `pipeline=malt`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.52** on 100 questions: 72 correct, 20 wrong, 8 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 8 |
| correct | 72 |
| wrong_type | 2 |
| wrong_value | 18 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| date | 7 | 0.5714 | 5 | 1 | 1 |
| list | 3 | 0.6667 | 2 | 0 | 1 |
| number | 66 | 0.5303 | 49 | 14 | 3 |
| percent | 23 | 0.4348 | 15 | 5 | 3 |
| string | 1 | 1.0 | 1 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.52 | 72 | 20 | 8 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.92 |
| selective_accuracy | 0.7826 |
| oracle_at_k | None |
| top_accuracy | 0.7579 |
| agreement_auroc | 0.6141 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.0 |
| unanswerable_recall | None |
| errors | 3 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.49 |
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
| 0.75 | 0.5 |
| 0.8 | 0.5 |
| 0.85 | 0.5 |
| 0.9 | 0.5 |
| 0.95 | 0.33 |
| 1.0 | -0.01 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 375 questions fit in 6 h
- LLM time share of wall time: 0.9951
- LLM calls: 321 (0 failed); questions over the 4-step limit: 0
- tokens: 4579113 prompt, 433362 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5749.387 | 57.4939 | 50.238 | 81.783 | 95.078 | 207.909 |
| llm seconds | 100 | 5721.1918 | 57.2119 | 49.5238 | 80.905 | 94.9041 | 207.8233 |
| ingest seconds | 100 | 6.8854 | 0.0689 | 0.0161 | 0.1615 | 0.3236 | 0.8548 |
| llm calls | 100 | 321.0 | 3.21 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 316.0 | 3.16 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4579113.0 | 45791.13 | 43039.0 | 60507.0 | 67798.0 | 72637.0 |
| completion tokens | 100 | 433362.0 | 4333.62 | 3625.0 | 6212.0 | 7312.0 | 20480.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 321 | 151.5522 | 0.4721 | 0.3256 | 0.6865 | 1.5585 | 3.7634 |
| latency (s) | 321 | 5721.1918 | 17.823 | 14.7473 | 25.1917 | 34.58 | 142.6776 |
| decode tokens/s | 321 | 24963.4663 | 77.7678 | 76.8908 | 83.3443 | 87.1247 | 131.389 |
| prompt tokens | 321 | 4579113.0 | 14265.1495 | 13989.0 | 17436.0 | 18113.0 | 20970.0 |
| completion tokens | 321 | 433362.0 | 1350.0374 | 1110.0 | 1900.0 | 2533.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 97 | 1.3279 | 0.0137 | 0.0122 | 0.0252 | 0.0307 | 0.0576 |
| progress | 97 | 5.8304 | 0.0601 | 0.0546 | 0.0874 | 0.1016 | 0.2587 |
| schema | 97 | 6.5519 | 0.0675 | 0.0296 | 0.1879 | 0.2923 | 0.3782 |
| thought_queries | 97 | 1547.5718 | 15.9543 | 13.7154 | 25.0327 | 32.4928 | 51.1838 |
| thought_results | 97 | 1698.3616 | 17.5089 | 15.2204 | 26.682 | 36.6336 | 57.4072 |
| thought_schema | 97 | 2056.1466 | 21.1974 | 18.3529 | 33.4256 | 37.7766 | 117.0763 |
