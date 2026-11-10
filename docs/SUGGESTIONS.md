# Suggestions: later improvements

Date: 2026-10-26. This is a backlog of ideas, not a set of decisions. Nothing here counts as an
improvement until a `make eval SUBSET=dev200` run shows it (CLAUDE.md, workflow rules). When an item
is adopted, record the decision in docs/NOTES.md and its result in docs/EXPERIMENTS.md.

Inputs: docs/PROJECT.md, docs/RESEARCH.md, the
[research report](reports/2026-10-26/data-agent-research/report.md), the
[design review](notes/2026-10-26/system-design/review.md), the code in `src/`, the train split, and
online research on similar hosted products (sources at
the end). Product claims come from vendor documentation. Paper claims come from abstracts and search
excerpts, not from full reads.

## 0. Facts from the train split that shape these suggestions

| Fact | Value | Consequence |
|---|---|---|
| Questions | 3,000 over 30 businesses | Enough for business-grouped cross-validation of `tau` and any confidence model |
| Answer types | number 1884 (63%), percent 578 (19%), list 193, date 145, string 88, **unanswerable 70 (2.3%)**, boolean 23, table 19 | Number and percent make up 82% of answers. Gains in aggregation and time filtering matter most. Unanswerable is rare, so a bias toward predicting `unanswerable` costs PA |
| Aliases | 167 answers have 1–5 aliases | The scorer and the vote keys must accept any alias (string answers) |
| Rulebook | Records after `as_of_date` count as not happened. Exception: the cancelled and returned status on an order is read as written, even when the return slip is dated after today | See S1 |

**S1 (bug, do first).** `src/assets/skills/time-expressions/SKILL.md` says "rows after `as_of_date`
do not exist in the data". The rulebook says the opposite: the files *can* hold later rows, and the
model has to exclude them. As written, the skill tells the model it can skip the `<= as_of_date`
filter. The exception for return status also has to be stated. Fix the skill, and enforce the bound
in the semantic layer, not only in the prompt (S6).

## 1. Other products and what to borrow

| Product | Mechanism | What to borrow |
|---|---|---|
| **Snowflake Cortex Analyst** | Semantic views (YAML) + Verified Query Repository. A matched verified query is reused and reported in the response `confidence` field. *Optimization* reads verified SQL and suggests new semantic definitions (such as an `is_active` filter). *Evaluations* hold out the verified queries under test from a copy of the semantic view and flag regressions | (a) Mine the teacher's verified SQL for recurring predicates and promote them to semantic macros (S6). (b) Leave-business-out evaluation of retrieval (S8). (c) A regression list of dev questions that used to pass (S16) |
| **Databricks AI/BI Genie** | Trusted assets (parameterized example queries and UC SQL functions). A response is marked *Trusted* when an asset is used verbatim. Benchmarks are kept separate from instructions. Advice: keep the space small and curated, and declare PK/FK | (a) Trusted path: an exact template or macro hit → higher prior confidence (S9). (b) Keep dev200 strictly as a benchmark, never as few-shot data. (c) Prune the schema to the linked tables and columns (S10) |
| **Microsoft Fabric data agent** | Retrieves the ~top-4 example queries per question. Each example is **validated against the schema** before use. A run-steps view shows which examples were applied | Validate each retrieved example against the current business (do its tables and columns exist?) before putting it in the prompt. Log which examples were used (S8, S15) |
| **Wren AI** (open source, Apache-2.0) | MDL semantic layer: models, relationships, calculated fields and metrics, compiled to SQL over DuckDB and others | A single place where metrics are defined. Our `assets/semantic/*.sql` plays this role, but it needs the glossary link (S5) |
| **Vanna** (MIT; repo status unclear in 2026) | Retrieval over (question, SQL) pairs, DDL and docs | Confirms that example retrieval alone works only when examples are fresh and close. Use it as a complement to the semantic layer, not as a replacement |

## 2. Research worth trying

| Item | Evidence | Suggestion |
|---|---|---|
| **Arctic-Text2SQL-R1-14B** (Snowflake) | GRPO with simple execution rewards on Qwen2.5-Coder. Reported as the first open 14B model above 70% on BIRD (greedy, single model) | **S12.** Add it as a target candidate next to Qwen3-14B, Qwen2.5-Coder-14B and OmniSQL-14B. Check the release date (expected 2025-05), the licence and the parameter count on the model card, and add a row to docs/MODELS.md before testing it. Compare all candidates on dev200 with the same pipeline. Vietnamese ability is the unknown |
| XiYanSQL-QwenCoder-14B-2504 | 65.3% on BIRD dev (M-Schema); a multi-generator framework | Its **M-Schema** prompt format (table, column, type, description, examples, PK/FK in one compact block) is an alternative rendering for S2 |
| ReFoRCE / CSC-SQL / N-rep / CHASE-SQL | Already in the report | Spend the 4th LLM step only when agreement is low (S13) |
| **Selective prediction for text-to-SQL** (arXiv:2607.06799, not fully read; check before citing) | Raw self-consistency is over-confident. Cheap black-box signals each reach about 0.61–0.68 AUROC, and an LLM judge 0.72–0.78. Fine-tuned verifiers fall to about 0.66 on unseen schemas | **S14.** Combine cheap signals in a small logistic model and calibrate it by business-grouped CV, which mimics unseen businesses. Expect a gain over agreement alone, but not a large one |
| TrustSQL (penalty-based scoring) | Many abstention methods fail to beat "always abstain" under penalties | Report PA against the always-abstain (0) and always-answer baselines in every eval |
| vLLM batch invariance (`VLLM_BATCH_INVARIANT=1`) | Deterministic outputs regardless of batch composition. Newer docs say compute capability ≥ 8.0 is enough; older docs say ≥ 9.0 | **S17.** Test it on the RTX 5090 (cc 12.0). If it holds, send the k candidates concurrently. That cuts latency, and latency is the PA tie-break |

## 3. Prioritized backlog

Effort: S < 1 day, M 1–3 days, L > 3 days. "Measure" means the dev200 numbers that must move.

| ID | Suggestion | Source | Effort | Measure |
|---|---|---|---|---|
| **S1** | Fix the time skill: later rows exist and must be excluded; state the return-status exception | Rulebook vs skill | S | PA on time-bounded questions; #wrong |
| **S6** | Fill the semantic layer with **`as_of_date`-parameterized table macros** (`valid_orders(as_of)`, `revenue_lines(as_of)`, `returned_orders()`, …) used as facets. The model composes them and does not re-derive rules | Cortex optimization | M | PA on number/percent (82% of train) |
| **S5** | Glossary = rulebook terms with Vietnamese synonyms → the semantic object that implements each term. Render only the entries the question mentions | Rulebook terms | S | PA by category; prompt tokens |
| **S8** | Teacher templates with **masked intent**: replace resolved time and entity spans with `{time}` / `{product}` slots. BM25/rapidfuzz on the masked question picks the top-3 examples, each checked against the current schema | Fabric top-4 + validation, Cortex VQR | M | Leave-business-out PA with and without examples |
| **S7** | Value search returns `(value, table.column, concept_type, distance)`. Show the top-n candidates when they are close; use the distance as a confidence feature | Value search | S | Entity-question PA; errors from wrong entities |
| **S14** | Confidence model: agreement + entity distance + template hit + empty or NULL result + row count + repair count + type plausibility → logistic regression, calibrated by business-grouped CV. `tau` is set on its output | arXiv:2607.06799, TrustSQL | M | PA-vs-tau curve; AUROC; #wrong |
| **S9** | Trusted path: masked question matches a template exactly and every slot is resolved → fill the parameterized SQL, execute, answer with no LLM call or with one confirming candidate | Genie trusted assets, Cortex VQR | M | PA and seconds per question on matched questions |
| **S3** | Auto-authored `synonyms` and `tags` per column (folded header, abbreviation table, unit hints such as `so_luong_le` = base-unit quantity) | Column metadata | S | Column-choice errors |
| **S10** | Prune the schema card to tables and columns linked by entities, glossary and synonyms, while keeping join keys | Genie "small, curated" | S | Prompt tokens; PA on wide workbooks |
| **S4** | Inferred relationships with a confidence score (name match + value-containment ratio), rendered as `relationships` | Join inference | M | PA on multi-table questions |
| **S11** | Ambiguity → abstain: when candidates disagree because the readings differ (period, metric), not because of crashes, abstain instead of taking the majority | Ambiguity handling | S | #wrong on low-agreement questions |
| **S13** | 4th step only on low agreement: a pairwise selector over the top-2 result groups, with order swapped (N-rep) | N-rep, CSC-SQL | M | PA in the 0.4–0.7 agreement band |
| **S12** | Target-model bake-off including Arctic-Text2SQL-R1-14B | Arctic paper | M | dev200 PA, latency, Vietnamese errors |
| **S15** | Structured trace: `generated_query`, `intent_explanation` (the reason field), `context_used`, `context_hash`, `matched_template`, timings | Trace schema | S | Error attribution report per component |
| **S16** | Regression list: dev questions that used to pass; eval prints newly failed ids | Cortex/Genie evaluations | S | No new failures without a note |
| **S17** | vLLM batch invariance, then concurrent candidates | vLLM docs | S | Rerun diff ≤ 0.01 PA; seconds per question |

Suggested order: S1 → S6 + S5 → baseline eval → S7, S3, S10 → S8 → S14 → S9, S11 → S12 →
S13, S17 → the rest.

## 3a. Additions 2026-10-27 (S19–S28)

From the [second research round](reports/2026-10-27/deep-research/report.md), §7 there has the
full table. In short:
- **S19** question-shape library with a deterministic compiler: 81% of train questions have a
  near-identical shape in another business.
- **S20** model bake-off v2: Qwen3.5-9B, Ministral-3-14B, Gemma-4-12B, Arctic-R1-14B.
- **S21** a small CSC merge reviser if the target is ≤ 10B.
- **S22** SFT / GRPO with the official scorer as reward.
- **S23** deterministic premise checks for unanswerable questions.
- **S24** repair messy cells at ingest instead of annotating them.
- **S25** an abbreviation lexicon mined from train questions.
- **S26** adaptive thinking on low-agreement questions only.
- **S27** grouped-CV tau with confidence intervals.
- **S28** test fewer candidates.

## 3b. Planned feature: charts in the demo app

**S18. Charts.** The challenge does not score charts and the batch path
(`python -m src`) never makes them. The demo app (`app/`, on top of `POST /ask`) should show a
chart next to the answer, as hosted analytics products do.

Decided so far:
- Scope: the app and `/ask` only. The submission line and the inference time are unchanged.
- Input: the executed result the answer came from (the winning candidate's rows and columns), so
  the chart shows the same numbers as the answer.
- Output: a declarative chart spec (for example Vega-Lite) that the UI
  renders, never an image.
- Chart type from the answer type and the result shape. A first version needs no LLM: list or
  table with one measure → bar, by date or month → line, share of a total → bar with percents,
  single number or string → no chart (show the value). An LLM step that picks or titles the chart
  is optional, app-only, and must stay offline (local model).

Not built yet. Start after `src/` is done (see docs/NOTES.md, "App settings, demo UI later").

## 4. Not recommended, and why

- **Clarifying questions, multi-turn state, A2A multi-agent.** These are features of hosted analytics
  products that do not apply to a scored batch job, and they cost steps and variance. (Charts are planned for the demo
  app, not for the competition: see S18.)
- **Embedding-based value search or example retrieval.** It would use parameter budget that the
  14B model already takes (docs/MODELS.md). The masked-intent approach in S8 gets most of the
  benefit with BM25.
- **An open deep-agent loop at inference.** It conflicts with the 4-step limit and the 0.03 rerun
  rule (H4).
- **Fine-tuned verifier as the main confidence signal.** Reported to degrade on unseen schemas,
  and the private test has unseen businesses.

## Sources

Other products
- [Snowflake Cortex Analyst: Verified Query Repository](https://docs.snowflake.com/en/user-guide/views-semantic/verified-query-repository)
- [Snowflake: optimize a semantic view with verified queries](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/analyst-optimization)
- [Snowflake: Cortex Analyst evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst-evaluations)
- [Databricks Genie](https://docs.databricks.com/gcp/en/genie/)
- [Databricks: building confidence with Genie benchmarks](https://www.databricks.com/blog/building-confidence-your-genie-space-benchmarks-and-ask-review)
- [Databricks: production-ready Genie spaces](https://www.databricks.com/blog/how-build-production-ready-genie-spaces-and-build-trust-along-way)
- [Microsoft Fabric data agent: example queries](https://learn.microsoft.com/en-us/fabric/data-science/data-agent-example-queries)
- [Wren AI: semantic layer for text-to-SQL](https://getwren.ai/post/why-the-semantic-layer-is-essential-for-reliable-text-to-sql-and-how-wren-ai-brings-it-to-life)
- [Wren AI vs Vanna comparison (third party)](https://querio.ai/articles/wren-ai-vs-vanna-ai-open-source-text-to-sql-compared)

Research and serving
- [Arctic-Text2SQL-R1 (arXiv:2505.20315)](https://arxiv.org/abs/2505.20315)
- [Snowflake blog: Arctic-Text2SQL-R1 tops BIRD](https://www.snowflake.com/en/blog/engineering/arctic-text2sql-r1-sql-generation-benchmark/)
- [XiYan-SQL (arXiv:2507.04701)](https://arxiv.org/abs/2507.04701)
- [XiYanSQL-QwenCoder-14B-2504](https://huggingface.co/XGenerationLab/XiYanSQL-QwenCoder-14B-2504)
- [What Predicts Correctness in Text-to-SQL? A Selective-Prediction Study (arXiv:2607.06799)](https://arxiv.org/abs/2607.06799)
- [TrustSQL (arXiv:2403.15879)](https://arxiv.org/abs/2403.15879)
- [Confidence Estimation for Error Detection in Text-to-SQL (arXiv:2501.09527)](https://arxiv.org/abs/2501.09527)
- [vLLM batch invariance](https://docs.vllm.ai/en/stable/features/batch_invariance/)
