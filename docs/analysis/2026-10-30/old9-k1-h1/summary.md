# Eval: old9-k1-h1

Command: `python -m scripts.eval --split train --subset /workspace/dev_h1.txt --topic old9-k1-h1 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h1.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.55** on 100 questions: 74 correct, 19 wrong, 7 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 7 |
| correct | 74 |
| wrong_type | 3 |
| wrong_value | 16 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 1.0 | 2 | 0 | 0 |
| date | 3 | 1.0 | 3 | 0 | 0 |
| list | 5 | -0.2 | 2 | 3 | 0 |
| number | 64 | 0.6094 | 49 | 10 | 5 |
| percent | 17 | 0.3529 | 11 | 5 | 1 |
| string | 5 | 0.6 | 4 | 1 | 0 |
| unanswerable | 4 | 0.75 | 3 | 0 | 1 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.55 | 74 | 19 | 7 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.93 |
| selective_accuracy | 0.7957 |
| oracle_at_k | None |
| top_accuracy | 0.7895 |
| agreement_auroc | 0.5847 |
| repair_rate | 0.0 |
| unanswerable_precision | 1.0 |
| unanswerable_recall | 0.75 |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.55 |
| 0.05 | 0.55 |
| 0.1 | 0.55 |
| 0.15 | 0.55 |
| 0.2 | 0.55 |
| 0.25 | 0.55 |
| 0.3 | 0.55 |
| 0.35 | 0.55 |
| 0.4 | 0.55 |
| 0.45 | 0.55 |
| 0.5 | 0.55 |
| 0.55 | 0.55 |
| 0.6 | 0.55 |
| 0.65 | 0.55 |
| 0.7 | 0.55 |
| 0.75 | 0.53 |
| 0.8 | 0.53 |
| 0.85 | 0.52 |
| 0.9 | 0.52 |
| 0.95 | 0.35 |
| 1.0 | 0.01 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 400 questions fit in 6 h
- LLM time share of wall time: 0.995
- LLM calls: 323 (0 failed); questions over the 4-step limit: 0
- tokens: 4542577 prompt, 399707 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5391.445 | 53.9144 | 45.637 | 82.52 | 106.357 | 176.617 |
| llm seconds | 100 | 5364.2293 | 53.6423 | 45.5553 | 82.2259 | 106.1452 | 176.4436 |
| ingest seconds | 100 | 7.4743 | 0.0747 | 0.0196 | 0.1673 | 0.4101 | 0.8149 |
| llm calls | 100 | 323.0 | 3.23 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 321.0 | 3.21 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4542577.0 | 45425.77 | 42831.0 | 60384.0 | 61473.0 | 82348.0 |
| completion tokens | 100 | 399707.0 | 3997.07 | 3299.0 | 5812.0 | 7568.0 | 15947.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 323 | 152.1637 | 0.4711 | 0.3584 | 0.7262 | 0.9911 | 3.3682 |
| latency (s) | 323 | 5364.2293 | 16.6075 | 14.1146 | 24.6678 | 28.5201 | 114.9316 |
| decode tokens/s | 323 | 24682.307 | 76.4158 | 74.7599 | 82.6719 | 87.2348 | 137.2647 |
| prompt tokens | 323 | 4542577.0 | 14063.7059 | 13686.0 | 17191.0 | 19718.0 | 21362.0 |
| completion tokens | 323 | 399707.0 | 1237.483 | 1038.0 | 1865.0 | 2179.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 99 | 1.312 | 0.0133 | 0.0123 | 0.0236 | 0.0284 | 0.0435 |
| progress | 99 | 5.8336 | 0.0589 | 0.052 | 0.0909 | 0.1332 | 0.1486 |
| schema | 99 | 6.4162 | 0.0648 | 0.0304 | 0.1746 | 0.2265 | 0.319 |
| thought_queries | 99 | 1543.6762 | 15.5927 | 12.665 | 25.8406 | 27.6792 | 68.3765 |
| thought_results | 99 | 2110.4343 | 21.3175 | 15.6282 | 37.5736 | 47.6022 | 129.2781 |
| thought_schema | 99 | 1671.1033 | 16.8798 | 15.6023 | 24.9438 | 29.2916 | 48.082 |
