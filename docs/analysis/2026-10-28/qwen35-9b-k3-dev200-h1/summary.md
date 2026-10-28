# Eval: qwen35-9b-k3-dev200-h1

Command: `python -m scripts.eval --split train --subset /tmp/dm-exp/e1_dev200_h1.txt --topic qwen35-9b-k3-dev200-h1 --workers 16`

Model: `Qwen/Qwen3.5-9B`

Config: `split=train`, `subset=/tmp/dm-exp/e1_dev200_h1.txt`, `pipeline=ca`, `thinking=True`, `analyze_extra_body={"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}`, `analyze_max_tokens=10240`, `k=3`, `tau=0.67`, `workers=16`, `llm_base_url=http://127.0.0.1:8013/v1`

**PA 0.5354** on 99 questions: 73 correct, 20 wrong, 6 abstain.

### By verdict

| verdict | n |
|---|---|
| abstain | 6 |
| correct | 73 |
| wrong_type | 2 |
| wrong_value | 18 |

### By answer type

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| boolean | 2 | 0.0 | 1 | 1 | 0 |
| date | 5 | 1.0 | 5 | 0 | 0 |
| list | 2 | 0.0 | 1 | 1 | 0 |
| number | 65 | 0.5385 | 47 | 12 | 6 |
| percent | 21 | 0.5238 | 16 | 5 | 0 |
| string | 1 | -1.0 | 0 | 1 | 0 |
| unanswerable | 3 | 1.0 | 3 | 0 | 0 |

### By question category

| group | n | PA | correct | wrong | abstain |
|---|---|---|---|---|---|
| unknown | 99 | 0.5354 | 73 | 20 | 6 |

### Diagnostics (not scored)

| metric | value |
|---|---|
| coverage | 0.9394 |
| selective_accuracy | 0.7849 |
| oracle_at_k | None |
| top_accuracy | 0.7849 |
| agreement_auroc | 0.7579 |
| repair_rate | 0.0 |
| unanswerable_precision | 0.75 |
| unanswerable_recall | 1.0 |
| errors | 6 |

### PA vs tau (vote agreement threshold)

| tau | PA |
|---|---|
| 0.0 | 0.5354 |
| 0.05 | 0.5354 |
| 0.1 | 0.5354 |
| 0.15 | 0.5354 |
| 0.2 | 0.5354 |
| 0.25 | 0.5354 |
| 0.3 | 0.5354 |
| 0.35 | 0.596 |
| 0.4 | 0.596 |
| 0.45 | 0.596 |
| 0.5 | 0.596 |
| 0.55 | 0.596 |
| 0.6 | 0.596 |
| 0.65 | 0.596 |
| 0.7 | 0.5253 |
| 0.75 | 0.5253 |
| 0.8 | 0.5253 |
| 0.85 | 0.5253 |
| 0.9 | 0.5253 |
| 0.95 | 0.5253 |
| 1.0 | 0.5253 |

### Efficiency (not scored; inference time is the official tie-break)

- questions: 99; at the mean pace, 150 questions fit in 6 h
- LLM time share of wall time: 0.9961
- LLM calls: 939 (0 failed); questions over the 4-step limit: 93
- tokens: 12011586 prompt, 1171392 completion

#### Per question

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| seconds | 99 | 14178.725 | 143.2194 | 124.893 | 213.679 | 292.43 | 369.846 |
| llm seconds | 99 | 14123.521 | 142.6618 | 124.4872 | 213.3705 | 291.297 | 369.2274 |
| ingest seconds | 99 | 7.3611 | 0.0744 | 0.0182 | 0.336 | 0.3985 | 0.7834 |
| llm calls | 99 | 939.0 | 9.4848 | 9.0 | 11.0 | 11.0 | 14.0 |
| llm steps | 99 | 882.0 | 8.9091 | 9.0 | 10.0 | 11.0 | 11.0 |
| prompt tokens | 99 | 12011586.0 | 121329.1515 | 118125.0 | 167769.0 | 177959.0 | 189357.0 |
| completion tokens | 99 | 1171392.0 | 11832.2424 | 10387.0 | 17387.0 | 23864.0 | 31122.0 |

#### Per LLM call

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| time to first token (s) | 932 | 9960.1977 | 10.6869 | 9.3147 | 17.1615 | 21.2471 | 72.7138 |
| latency (s) | 939 | 14123.521 | 15.041 | 12.6711 | 21.5591 | 26.8086 | 125.8464 |
| decode tokens/s | 932 | 339558.7087 | 364.3334 | 323.6284 | 557.8605 | 643.9931 | 1443.9784 |
| prompt tokens | 939 | 12011586.0 | 12791.8914 | 12289.0 | 16555.0 | 16861.0 | 18269.0 |
| completion tokens | 939 | 1171392.0 | 1247.4888 | 1059.0 | 1805.0 | 2251.0 | 10240.0 |

#### Per graph node (seconds)

| metric | n | total | mean | p50 | p90 | p95 | max |
|---|---|---|---|---|---|---|---|
| data | 93 | 5.1043 | 0.0549 | 0.0455 | 0.0908 | 0.1063 | 0.1533 |
| progress | 93 | 20.0857 | 0.216 | 0.2055 | 0.3115 | 0.3359 | 0.389 |
| schema | 93 | 11.9266 | 0.1282 | 0.0215 | 0.4931 | 0.7079 | 0.811 |
| thought_queries | 93 | 4006.8391 | 43.0843 | 37.6773 | 58.3756 | 71.3597 | 223.1054 |
| thought_results | 93 | 4953.8416 | 53.2671 | 43.7263 | 86.8139 | 121.1356 | 200.3163 |
| thought_schema | 93 | 4390.3919 | 47.2085 | 43.6083 | 66.7324 | 74.6296 | 100.7072 |
