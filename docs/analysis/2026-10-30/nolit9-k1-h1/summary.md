# Eval: nolit9-k1-h1

Command: `python -m scripts.eval --split train --subset /workspace/dev_h1.txt --topic nolit9-k1-h1 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h1.txt`, `pipeline=malt`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.49** on 100 questions: 69 correct, 20 wrong, 11 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 11 |
| correct | 69 |
| wrong_type | 7 |
| wrong_value | 13 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | -0.5 | 0 | 1 | 1 |
| date | 3 | 0.3333 | 2 | 1 | 0 |
| list | 5 | -0.2 | 2 | 3 | 0 |
| number | 64 | 0.5938 | 47 | 9 | 8 |
| percent | 17 | 0.2941 | 10 | 5 | 2 |
| string | 5 | 0.6 | 4 | 1 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.49 | 69 | 20 | 11 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.89 |
| selective_accuracy | 0.7753 |
| oracle_at_k | None |
| top_accuracy | 0.75 |
| agreement_auroc | 0.6222 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.5714 |
| unanswerable_recall | 1.0 |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.46 |
| 0.05 | 0.49 |
| 0.1 | 0.49 |
| 0.15 | 0.49 |
| 0.2 | 0.49 |
| 0.25 | 0.49 |
| 0.3 | 0.49 |
| 0.35 | 0.49 |
| 0.4 | 0.49 |
| 0.45 | 0.49 |
| 0.5 | 0.49 |
| 0.55 | 0.49 |
| 0.6 | 0.49 |
| 0.65 | 0.49 |
| 0.7 | 0.49 |
| 0.75 | 0.47 |
| 0.8 | 0.47 |
| 0.85 | 0.47 |
| 0.9 | 0.45 |
| 0.95 | 0.4 |
| 1.0 | 0.01 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 389 questions fit in 6 h
- LLM time share of wall time: 0.9945
- LLM calls: 328 (0 failed); questions over the 4-step limit: 0
- tokens: 4652177 prompt, 396744 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5549.177 | 55.4918 | 45.475 | 80.921 | 98.531 | 220.655 |
| llm seconds | 100 | 5518.5502 | 55.1855 | 45.3335 | 80.3477 | 98.3228 | 220.1766 |
| ingest seconds | 100 | 7.3506 | 0.0735 | 0.022 | 0.2035 | 0.3252 | 0.775 |
| llm calls | 100 | 328.0 | 3.28 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 326.0 | 3.26 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4652177.0 | 46521.77 | 44066.0 | 60872.0 | 70104.0 | 84065.0 |
| completion tokens | 100 | 396744.0 | 3967.44 | 3273.0 | 5863.0 | 7453.0 | 15461.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 328 | 153.6004 | 0.4683 | 0.3852 | 0.8863 | 1.1522 | 1.6242 |
| latency (s) | 328 | 5518.5502 | 16.8248 | 13.9069 | 25.6414 | 31.857 | 147.4025 |
| decode tokens/s | 328 | 24605.961 | 75.0182 | 72.8553 | 82.7914 | 90.0892 | 137.2287 |
| prompt tokens | 328 | 4652177.0 | 14183.4665 | 13865.0 | 17390.0 | 19854.0 | 21944.0 |
| completion tokens | 328 | 396744.0 | 1209.5854 | 1015.0 | 1827.0 | 2291.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 99 | 1.5755 | 0.0159 | 0.013 | 0.0312 | 0.039 | 0.0621 |
| progress | 99 | 8.2147 | 0.083 | 0.0666 | 0.125 | 0.1585 | 0.7185 |
| schema | 99 | 6.3771 | 0.0644 | 0.0332 | 0.1757 | 0.2192 | 0.5221 |
| thought_queries | 99 | 1618.8294 | 16.3518 | 12.6725 | 26.2977 | 29.5661 | 164.7622 |
| thought_results | 99 | 2000.0744 | 20.2028 | 15.9204 | 29.8704 | 44.3912 | 169.0349 |
| thought_schema | 99 | 1866.2434 | 18.8509 | 16.2554 | 32.1736 | 35.5062 | 66.2634 |
