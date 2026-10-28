# Eval: abstain-wrong-rerun

Command: `python -m scripts.eval --split train --subset /tmp/datamate/abstain_wrong_ids.txt --topic abstain-wrong-rerun --workers 8`

Model: `deepseek-flash`

**PA 0.2949** on 78 questions: 38 correct, 15 wrong, 25 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 25 |
| correct | 38 |
| wrong_value | 15 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 1 | 1.0 | 1 | 0 | 0 |
| date | 4 | 0.75 | 3 | 0 | 1 |
| list | 4 | 0.0 | 1 | 1 | 2 |
| number | 47 | 0.3191 | 22 | 7 | 18 |
| percent | 19 | 0.2105 | 10 | 6 | 3 |
| string | 3 | 0.0 | 1 | 1 | 1 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 78 | 0.2949 | 38 | 15 | 25 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.6795 |
| selective_accuracy | 0.717 |
| oracle_at_k | None |
| top_accuracy | 0.717 |
| agreement_auroc | 0.5 |
| repair_rate | 0.0 |
| unanswerable_precision | None |
| unanswerable_recall | None |
| errors | 14 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.2949 |
| 0.05 | 0.2949 |
| 0.1 | 0.2949 |
| 0.15 | 0.2949 |
| 0.2 | 0.2949 |
| 0.25 | 0.2949 |
| 0.3 | 0.2949 |
| 0.35 | 0.2949 |
| 0.4 | 0.2949 |
| 0.45 | 0.2949 |
| 0.5 | 0.2949 |
| 0.55 | 0.2949 |
| 0.6 | 0.2949 |
| 0.65 | 0.2949 |
| 0.7 | 0.2949 |
| 0.75 | 0.2949 |
| 0.8 | 0.2949 |
| 0.85 | 0.2949 |
| 0.9 | 0.2949 |
| 0.95 | 0.2949 |
| 1.0 | 0.2949 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 78; at the mean pace, 607 questions fit in 6 h
- LLM time share of wall time: 0.9966
- LLM calls: 273 (0 failed); questions over the 4-step limit: 0
- tokens: 4128310 prompt, 494136 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 78 | 2775.019 | 35.5772 | 28.057 | 67.992 | 85.882 | 131.879 |
| llm seconds | 78 | 2765.5894 | 35.4563 | 27.9439 | 67.9356 | 85.7652 | 131.7902 |
| ingest seconds | 78 | 1.3283 | 0.017 | 0.0163 | 0.0338 | 0.0407 | 0.0838 |
| llm calls | 78 | 273.0 | 3.5 | 3.0 | 4.0 | 4.0 | 4.0 |
| llm steps | 78 | 245.0 | 3.141 | 3.0 | 4.0 | 4.0 | 4.0 |
| prompt tokens | 78 | 4128310.0 | 52927.0513 | 52394.0 | 67887.0 | 68898.0 | 78281.0 |
| completion tokens | 78 | 494136.0 | 6335.0769 | 5073.0 | 12411.0 | 15884.0 | 23353.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 273 | 225.3685 | 0.8255 | 0.824 | 1.007 | 1.0598 | 1.3373 |
| latency (s) | 273 | 2765.5894 | 10.1304 | 7.2624 | 19.4441 | 30.1282 | 65.0437 |
| decode tokens/s | 273 | 53653.1655 | 196.5317 | 195.6726 | 221.5196 | 229.5162 | 280.8009 |
| prompt tokens | 273 | 4128310.0 | 15122.0147 | 14750.0 | 17489.0 | 18964.0 | 20220.0 |
| completion tokens | 273 | 494136.0 | 1810.022 | 1256.0 | 3400.0 | 5068.0 | 16384.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 64 | 1.439 | 0.0225 | 0.0202 | 0.0359 | 0.0464 | 0.0738 |
| progress | 64 | 2.1165 | 0.0331 | 0.0348 | 0.0466 | 0.0489 | 0.0749 |
| schema | 64 | 1.5549 | 0.0243 | 0.0175 | 0.0487 | 0.0566 | 0.109 |
| thought_queries | 64 | 818.2373 | 12.785 | 7.4964 | 34.984 | 53.5722 | 65.0442 |
| thought_results | 64 | 942.8258 | 14.7317 | 10.9162 | 30.9734 | 49.6808 | 68.4198 |
| thought_schema | 64 | 561.2335 | 8.7693 | 7.6697 | 12.6963 | 19.4267 | 25.1814 |
