# Research

## Question
How far can a ≤15B open model, run offline under a 6-hour budget, answer colloquial Vietnamese
questions over messy small-business tables, when the metric punishes a wrong answer as much as it
rewards a right one (Penalized Accuracy, docs/PROJECT.md §2)?

## Hypotheses
- **H1 — Context over model size.** Most errors come from not knowing the data (headers, types,
  entity spellings, business rules), not from SQL skill. Deterministic ingest plus an auto-authored
  context (schema card, entity dict, rulebook skills, semantic views) gives more PA than a bigger model.
- **H2 — Execution-grounded confidence.** Agreement among k executed candidates is a usable estimate
  of P(correct); abstaining below a calibrated tau raises PA over always answering.
- **H3 — Deterministic pre-processing.** Resolving time expressions and entities in Python, before
  the LLM, removes a class of errors a 14B model makes often (dates, accents, abbreviations).
- **H4 — Bounded graph beats open loop.** At this model size and step budget, a fixed
  LangGraph pipeline (generate → execute → repair → vote) is more accurate and more reproducible
  than an autonomous deep agent.
- **H5 — Synthetic verified queries help.** (question, SQL) pairs written by a teacher on train
  businesses, used as few-shot examples or LoRA data, transfer to unseen businesses.

## Method
Each hypothesis is an ablation on the fixed `dev200` train subset with the target model
(`make eval SUBSET=dev200 TOPIC=<name>`), reporting PA, #correct / #wrong / #abstain, and breakdowns
by answer type and category; `decide/` changes also report the PA-vs-tau curve. Results live under
`docs/analysis/<date>/<topic>/` and are indexed in EXPERIMENTS.md.

Background: [data-agent research report](reports/2026-10-26/data-agent-research/report.md) and
[system design review](notes/2026-10-26/system-design/review.md).
