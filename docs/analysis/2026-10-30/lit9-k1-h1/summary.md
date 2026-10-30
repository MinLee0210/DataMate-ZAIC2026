# Eval: lit9-k1-h1

Command: `python -m scripts.eval --split train --subset /workspace/dev_h1.txt --topic lit9-k1-h1 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h1.txt`, `pipeline=malt`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8012/v1`

**PA 0.35** on 100 questions: 62 correct, 27 wrong, 11 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 11 |
| correct | 62 |
| wrong_type | 3 |
| wrong_value | 24 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.5 | 1 | 0 | 1 |
| date | 3 | 1.0 | 3 | 0 | 0 |
| list | 5 | -0.2 | 2 | 3 | 0 |
| number | 64 | 0.4219 | 41 | 14 | 9 |
| percent | 17 | 0.0 | 8 | 8 | 1 |
| string | 5 | 0.2 | 3 | 2 | 0 |
| unanswerable | 4 | 1.0 | 4 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.35 | 62 | 27 | 11 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.89 |
| selective_accuracy | 0.6966 |
| oracle_at_k | None |
| top_accuracy | 0.6739 |
| agreement_auroc | 0.6435 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.6667 |
| unanswerable_recall | 1.0 |
| errors | 4 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.32 |
| 0.05 | 0.35 |
| 0.1 | 0.35 |
| 0.15 | 0.35 |
| 0.2 | 0.35 |
| 0.25 | 0.35 |
| 0.3 | 0.35 |
| 0.35 | 0.35 |
| 0.4 | 0.35 |
| 0.45 | 0.35 |
| 0.5 | 0.35 |
| 0.55 | 0.35 |
| 0.6 | 0.35 |
| 0.65 | 0.35 |
| 0.7 | 0.35 |
| 0.75 | 0.35 |
| 0.8 | 0.35 |
| 0.85 | 0.35 |
| 0.9 | 0.34 |
| 0.95 | 0.34 |
| 1.0 | 0.02 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 385 questions fit in 6 h
- LLM time share of wall time: 0.9906
- LLM calls: 324 (0 failed); questions over the 4-step limit: 0
- tokens: 4570533 prompt, 409376 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5602.715 | 56.0271 | 47.956 | 81.492 | 100.334 | 207.746 |
| llm seconds | 100 | 5549.7984 | 55.498 | 47.4693 | 81.1994 | 98.8343 | 206.1996 |
| ingest seconds | 100 | 7.4546 | 0.0745 | 0.0187 | 0.2209 | 0.3945 | 0.7252 |
| llm calls | 100 | 324.0 | 3.24 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 315.0 | 3.15 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4570533.0 | 45705.33 | 42966.0 | 60768.0 | 63425.0 | 81214.0 |
| completion tokens | 100 | 409376.0 | 4093.76 | 3497.0 | 5815.0 | 7172.0 | 14590.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 324 | 158.8122 | 0.4902 | 0.3501 | 0.7944 | 1.3202 | 3.6193 |
| latency (s) | 324 | 5549.7984 | 17.129 | 14.1727 | 23.8458 | 30.2892 | 148.0014 |
| decode tokens/s | 324 | 24762.0279 | 76.426 | 74.7915 | 81.6079 | 91.2278 | 134.7742 |
| prompt tokens | 324 | 4570533.0 | 14106.5833 | 13761.0 | 17212.0 | 19718.0 | 21506.0 |
| completion tokens | 324 | 409376.0 | 1263.5062 | 1044.0 | 1685.0 | 2106.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 96 | 26.7644 | 0.2788 | 0.2461 | 0.5831 | 0.6977 | 1.0955 |
| progress | 96 | 6.1754 | 0.0643 | 0.0558 | 0.0995 | 0.1361 | 0.2737 |
| schema | 96 | 6.1793 | 0.0644 | 0.0291 | 0.1854 | 0.2295 | 0.3535 |
| thought_queries | 96 | 1496.5668 | 15.5892 | 13.0975 | 25.1968 | 31.0422 | 65.5013 |
| thought_results | 96 | 2014.6042 | 20.9855 | 15.9628 | 33.7682 | 49.3625 | 148.0084 |
| thought_schema | 96 | 1758.0592 | 18.3131 | 15.7469 | 25.9119 | 27.9347 | 169.7893 |
