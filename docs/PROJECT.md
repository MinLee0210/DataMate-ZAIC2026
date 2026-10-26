# PROJECT.md — DataMate

## 1. Task
Per question: a business data package (≥1 of .csv/.xlsx/.sqlite + README.md), a colloquial Vietnamese question
(e.g. "sp bán dc nhiều nhất tuần rồi"), an `as_of_date`, plus a split-wide rulebook and solar–lunar calendar.
Output one JSONL line: `{"id", "type", "answer"}`.
Types: number | percent | string | date | boolean | list | table | unanswerable | abstain.

## 2. Metric — Penalized Accuracy
PA = (1/N) Σ s_i, with s_i = +1 correct, 0 abstain or missing, −1 wrong.
- Answering an unanswerable question counts as wrong. No partial credit.
- number: exact (integers, or rounded to 2 dp). percent: exact after 2-dp rounding, sign matters.
- string: NFC, lowercase, non-alphanumeric → space, collapse spaces, diacritics kept; any accepted spelling or the code.
- date: `yyyy-mm-dd`, or `yyyy-mm` for months. list: ordered, matched by position.
- Ranking: the question's criterion, else the rulebook default; descending over valid orders; ties by code ascending.
- Tie-break: total inference time in the organisers' rerun, then earlier submission.
- Consequence: answer only when P(correct) > 0.5. Calibration is a first-class objective.

## 3. Constraints
| Item | Limit |
|---|---|
| Models at inference | ≤ 15B params in total, MoE counts all experts, declared in README |
| Weights | public before 2026-10-01, licence permits use |
| Hardware | 2× RTX 5090 (32 GB each), 512 GB RAM, CUDA ≥ 12.8 |
| Time | whole private test ≤ 6 h, model loading included |
| Network | none, image runs with networking disabled |
| Reproducibility | \|PA_upload − PA_rerun\| ≤ 0.03, logs must explain differences |
| Data | train + self-synthesized + public data; never public/private test |

## 4. Architecture (Conversational-Analytics-style, trimmed)
```
data pkg ─► INGEST (headers, sheets, merged cells, types) ─► DuckDB
         ─► AUTO-AUTHORED CONTEXT
              schema card: tables, columns, types, top-k values, date ranges, row counts
              entity dict: name variants → canonical name + code
              glossary: Vietnamese business terms → columns / views
rulebook ─► SEMANTIC LAYER (written once, split-wide) + skills in assets/skills/
question ─► TIME RESOLVER ─► ENTITY LINKING
         ─► SQL AGENT: plan → SQL (or small Python) over the semantic layer
         ─► EXECUTE ─► repair on error (≤ 2)
         ─► k candidates (fixed seeds) ─► vote on executed results
         ─► DECIDE: answer | abstain (agreement < tau) | unanswerable (missing concept or column)
         ─► FORMAT ─► append to submission.jsonl
```
Dropped from Google CA: clarifying questions, charts, long-form answers, long agent loops.
Kept: authored context as the main lever, plus an execution-grounded answer.

## 5. Phases
- **dev_free:** ingest, context, semantic layer, scorer, agent flow. LLM = hosted copy of the target model.
  Teacher model only in `scripts/datagen/` to synthesize (question, SQL, answer) from train businesses.
- **dev_constraint:** local vLLM; latency budget; tau and k calibration; determinism; Docker.
- The first smoke run on the target GPU happens by the end of week 1, not after dev_free ends.

## 6. Model candidates (verify release date < 2026-10-01 and parameter count)
- Primary: one ~14B dense code/SQL-capable model (e.g. Qwen3-14B, Qwen2.5-Coder-14B, OmniSQL-14B).
- Alternative: an ~8B model plus headroom for a small verifier.
- No embedding model unless the budget allows; use BM25 / rapidfuzz.

## 7. Timeline
| Dates | Milestone |
|---|---|
| 26/10–01/11 | Ingest, schema card, SQL baseline, formatter, first leaderboard submission, GPU smoke run |
| 02/11–08/11 | Semantic layer, entity linking, voting, decision policy, synthetic data, optional LoRA SFT |
| 09/11–14/11 | tau calibration, unanswerable handling, 6-h budget test, Docker and double rerun |
| 16/11 23:59 | Final solution submission (Docker, max 2 uploads, the last one counts) |
| 20/11–23/11 | Run the private test, upload submission.jsonl |

## 8. Definition of done (16/11)
- The Docker image runs offline on a clean machine, writes incrementally and finishes with ≥ 30% time margin.
- Two consecutive runs differ by ≤ 0.01 PA on dev.
- docs/MODELS.md and the README declare every model.

## 9. Risks
Messy Excel parsing; vLLM nondeterminism; type or format mismatches; over-answering (negative PA);
unseen business schemas in the private test.

## 10. Open questions (fill in after reading the Data tab)
- Number of questions and businesses per split? Train size?
- Is `unanswerable` labelled in train, and how often does it occur?
- Required Docker base image and log format?