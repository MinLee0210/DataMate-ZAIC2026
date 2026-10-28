# Eval: qwen3-5090-ca-thinking

Command: `python -m scripts.eval --split train --subset dev200 --topic qwen3-5090-ca-thinking --workers 10`

Model: `Qwen/Qwen3-14B`

Config: `split=train`, `subset=dev200`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=10`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.43** on 200 questions: 136 correct, 50 wrong, 14 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 14 |
| correct | 136 |
| wrong_type | 7 |
| wrong_value | 43 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.5 | 1 | 0 | 1 |
| date | 10 | 0.7 | 8 | 1 | 1 |
| list | 8 | -0.25 | 3 | 5 | 0 |
| number | 130 | 0.4308 | 89 | 33 | 8 |
| percent | 40 | 0.425 | 27 | 10 | 3 |
| string | 6 | 0.5 | 4 | 1 | 1 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 200 | 0.43 | 136 | 50 | 14 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.93 |
| selective_accuracy | 0.7312 |
| oracle_at_k | None |
| top_accuracy | 0.7312 |
| agreement_auroc | 0.5 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.5 |
| unanswerable_recall | 1.0 |
| errors | 1 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.43 |
| 0.05 | 0.43 |
| 0.1 | 0.43 |
| 0.15 | 0.43 |
| 0.2 | 0.43 |
| 0.25 | 0.43 |
| 0.3 | 0.43 |
| 0.35 | 0.43 |
| 0.4 | 0.43 |
| 0.45 | 0.43 |
| 0.5 | 0.43 |
| 0.55 | 0.43 |
| 0.6 | 0.43 |
| 0.65 | 0.43 |
| 0.7 | 0.43 |
| 0.75 | 0.43 |
| 0.8 | 0.43 |
| 0.85 | 0.43 |
| 0.9 | 0.43 |
| 0.95 | 0.43 |
| 1.0 | 0.43 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 200; at the mean pace, 161 questions fit in 6 h
- LLM time share of wall time: 0.9988
- LLM calls: 631 (0 failed); questions over the 4-step limit: 0
- tokens: 8492153 prompt, 632407 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 200 | 26699.776 | 133.4989 | 117.672 | 206.813 | 234.963 | 427.236 |
| llm seconds | 200 | 26668.2259 | 133.3411 | 117.5283 | 206.7136 | 234.7776 | 427.1053 |
| ingest seconds | 200 | 4.0047 | 0.02 | 0.0108 | 0.0518 | 0.063 | 0.2185 |
| llm calls | 200 | 631.0 | 3.155 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 200 | 630.0 | 3.15 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 200 | 8492153.0 | 42460.765 | 39928.0 | 57148.0 | 59812.0 | 78694.0 |
| completion tokens | 200 | 632407.0 | 3162.035 | 2758.0 | 4650.0 | 5678.0 | 12392.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 631 | 539.4171 | 0.8549 | 0.7705 | 1.4665 | 1.8043 | 3.9876 |
| latency (s) | 631 | 26668.2259 | 42.2634 | 36.9949 | 71.3831 | 87.3858 | 337.7133 |
| decode tokens/s | 631 | 15315.4202 | 24.2717 | 24.1907 | 26.6766 | 27.5328 | 33.9725 |
| prompt tokens | 631 | 8492153.0 | 13458.2456 | 13088.0 | 16591.0 | 17677.0 | 20731.0 |
| completion tokens | 631 | 632407.0 | 1002.2298 | 860.0 | 1698.0 | 2116.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 199 | 2.2938 | 0.0115 | 0.0095 | 0.021 | 0.0287 | 0.0602 |
| progress | 199 | 8.8915 | 0.0447 | 0.0437 | 0.0705 | 0.0782 | 0.1047 |
| schema | 199 | 10.8566 | 0.0546 | 0.0262 | 0.157 | 0.1914 | 0.4377 |
| thought_queries | 199 | 9711.3809 | 48.8009 | 39.8132 | 80.1221 | 111.0476 | 213.2628 |
| thought_results | 199 | 5893.0262 | 29.6132 | 20.6427 | 53.0391 | 67.2668 | 201.1857 |
| thought_schema | 199 | 10639.8109 | 53.4664 | 49.2998 | 77.4007 | 91.2244 | 129.9006 |
