# Eval: old9-k1-h0

Command: `python -m scripts.eval --split train --subset /workspace/dev_h0.txt --topic old9-k1-h0 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/workspace/dev_h0.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8011/v1`

**PA 0.53** on 100 questions: 71 correct, 18 wrong, 11 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 11 |
| correct | 71 |
| wrong_type | 2 |
| wrong_value | 16 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| date | 7 | 0.5714 | 5 | 1 | 1 |
| list | 3 | 0.6667 | 2 | 0 | 1 |
| number | 66 | 0.4848 | 45 | 13 | 8 |
| percent | 23 | 0.6087 | 18 | 4 | 1 |
| string | 1 | 1.0 | 1 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 100 | 0.53 | 71 | 18 | 11 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.89 |
| selective_accuracy | 0.7978 |
| oracle_at_k | None |
| top_accuracy | 0.7978 |
| agreement_auroc | 0.6514 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.0 |
| unanswerable_recall | None |
| errors | 3 |

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
| 0.35 | 0.53 |
| 0.4 | 0.53 |
| 0.45 | 0.53 |
| 0.5 | 0.53 |
| 0.55 | 0.53 |
| 0.6 | 0.53 |
| 0.65 | 0.53 |
| 0.7 | 0.53 |
| 0.75 | 0.53 |
| 0.8 | 0.53 |
| 0.85 | 0.54 |
| 0.9 | 0.52 |
| 0.95 | 0.38 |
| 1.0 | 0.0 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 100; at the mean pace, 370 questions fit in 6 h
- LLM time share of wall time: 0.9947
- LLM calls: 323 (0 failed); questions over the 4-step limit: 0
- tokens: 4621802 prompt, 427194 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 100 | 5827.668 | 58.2767 | 48.162 | 81.177 | 114.729 | 208.385 |
| llm seconds | 100 | 5796.7595 | 57.9676 | 47.943 | 81.0759 | 114.6238 | 208.1788 |
| ingest seconds | 100 | 8.1322 | 0.0813 | 0.0206 | 0.1377 | 0.5107 | 0.9675 |
| llm calls | 100 | 323.0 | 3.23 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 100 | 317.0 | 3.17 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 100 | 4621802.0 | 46218.02 | 42416.0 | 60855.0 | 67384.0 | 82472.0 |
| completion tokens | 100 | 427194.0 | 4271.94 | 3490.0 | 6440.0 | 8380.0 | 15044.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 323 | 151.5598 | 0.4692 | 0.3554 | 0.6842 | 0.9314 | 4.214 |
| latency (s) | 323 | 5796.7595 | 17.9466 | 14.9906 | 24.9763 | 32.0224 | 146.4662 |
| decode tokens/s | 323 | 24658.5138 | 76.3421 | 75.6964 | 82.6611 | 84.6989 | 134.5139 |
| prompt tokens | 323 | 4621802.0 | 14308.9845 | 13945.0 | 17444.0 | 18152.0 | 20956.0 |
| completion tokens | 323 | 427194.0 | 1322.582 | 1100.0 | 1938.0 | 2534.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| analysis | 1 | 0.0065 | 0.0065 | 0.0065 | 0.0065 | 0.0065 | 0.0065 |
| data | 97 | 1.5971 | 0.0165 | 0.0141 | 0.0275 | 0.0302 | 0.0963 |
| progress | 97 | 7.2584 | 0.0748 | 0.0658 | 0.1103 | 0.1228 | 0.4283 |
| schema | 97 | 7.5942 | 0.0783 | 0.0415 | 0.2552 | 0.2774 | 0.4796 |
| thought_queries | 97 | 1606.6177 | 16.5631 | 13.7582 | 25.3905 | 30.577 | 65.9643 |
| thought_results | 97 | 2076.3285 | 21.4054 | 14.9827 | 40.2031 | 44.7015 | 175.0304 |
| thought_schema | 97 | 2009.1468 | 20.7129 | 17.3685 | 30.6747 | 35.1829 | 144.3376 |
