# Eval: base9-k1-h1

Command: `python -m scripts.eval --split train --subset /workspace/dev_h1.txt --topic base9-k1-h1 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h1.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.61** on 100 questions: 77 correct, 16 wrong, 7 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 7 |
| correct | 77 |
| wrong_type | 2 |
| wrong_value | 14 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 1.0 | 2 | 0 | 0 |
| date | 3 | 1.0 | 3 | 0 | 0 |
| list | 5 | -0.2 | 2 | 3 | 0 |
| number | 64 | 0.6875 | 51 | 7 | 6 |
| percent | 17 | 0.3529 | 11 | 5 | 1 |
| string | 5 | 0.6 | 4 | 1 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.61 | 77 | 16 | 7 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.93 |
| selective_accuracy | 0.828 |
| oracle_at_k | None |
| top_accuracy | 0.828 |
| agreement_auroc | 0.5747 |
| repair_rate | 0.0 |
| unanswerable_precision | 1.0 |
| unanswerable_recall | 1.0 |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.61 |
| 0.05 | 0.61 |
| 0.1 | 0.61 |
| 0.15 | 0.61 |
| 0.2 | 0.61 |
| 0.25 | 0.61 |
| 0.3 | 0.61 |
| 0.35 | 0.61 |
| 0.4 | 0.61 |
| 0.45 | 0.61 |
| 0.5 | 0.61 |
| 0.55 | 0.61 |
| 0.6 | 0.61 |
| 0.65 | 0.61 |
| 0.7 | 0.61 |
| 0.75 | 0.61 |
| 0.8 | 0.61 |
| 0.85 | 0.61 |
| 0.9 | 0.59 |
| 0.95 | 0.42 |
| 1.0 | 0.02 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 375 questions fit in 6 h
- LLM time share of wall time: 0.9945
- LLM calls: 325 (0 failed); questions over the 4-step limit: 0
- tokens: 4593935 prompt, 410777 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5749.156 | 57.4916 | 47.788 | 87.246 | 106.812 | 214.896 |
| llm seconds | 100 | 5717.328 | 57.1733 | 47.5402 | 86.9564 | 106.6654 | 214.3304 |
| ingest seconds | 100 | 10.5474 | 0.1055 | 0.0284 | 0.3239 | 0.4834 | 1.5997 |
| llm calls | 100 | 325.0 | 3.25 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 323.0 | 3.23 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4593935.0 | 45939.35 | 42276.0 | 61546.0 | 68419.0 | 84025.0 |
| completion tokens | 100 | 410777.0 | 4107.77 | 3452.0 | 6003.0 | 7752.0 | 15254.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 325 | 195.7208 | 0.6022 | 0.4037 | 0.8334 | 1.0262 | 5.6092 |
| latency (s) | 325 | 5717.328 | 17.5918 | 14.4886 | 25.0857 | 29.7409 | 145.9077 |
| decode tokens/s | 325 | 24305.8702 | 74.7873 | 73.475 | 80.05 | 85.0795 | 137.5971 |
| prompt tokens | 325 | 4593935.0 | 14135.1846 | 13840.0 | 17171.0 | 19749.0 | 21615.0 |
| completion tokens | 325 | 410777.0 | 1263.9292 | 1049.0 | 1759.0 | 2113.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 99 | 1.802 | 0.0182 | 0.0135 | 0.0342 | 0.0612 | 0.1575 |
| progress | 99 | 6.6211 | 0.0669 | 0.0583 | 0.1106 | 0.1382 | 0.2336 |
| schema | 99 | 7.2033 | 0.0728 | 0.0405 | 0.2191 | 0.2526 | 0.3671 |
| thought_queries | 99 | 1617.7129 | 16.3405 | 12.8698 | 23.876 | 29.7415 | 111.8571 |
| thought_results | 99 | 1943.9162 | 19.6355 | 15.2002 | 30.5705 | 45.8223 | 165.7013 |
| thought_schema | 99 | 2119.3062 | 21.4071 | 16.8395 | 27.9922 | 36.5989 | 165.8427 |
