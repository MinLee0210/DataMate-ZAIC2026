# Suggestions: later improvements

Date: 2026-10-26. This is a backlog of ideas, not a set of decisions. Nothing here counts as an
improvement until a `make eval SUBSET=dev200` run shows it (CLAUDE.md, workflow rules). When an item
is adopted, record the decision in docs/NOTES.md and its result in docs/EXPERIMENTS.md.

Inputs: docs/PROJECT.md, docs/RESEARCH.md, the
[research report](reports/2026-10-26/data-agent-research/report.md), the
[design review](notes/2026-10-26/system-design/review.md), the code in `src/`, the train split, and
online research on Google's Conversational Analytics API (CA-API) and similar products (sources at
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

## 1. Google Conversational Analytics API in 2026, and how DataMate maps to it

### 1.1 What CA-API is now

- **GA for BigQuery and Looker** (2026-06-23): v1 REST endpoints and regional resources. For
  BigQuery, the agent now asks a clarifying question when field names are ambiguous, returned as a
  `TextMessage`.
- **Two shapes.**
  1. *Data agent + Chat*: a `DataAgent` holds `published_context`, and `Chat` runs a reasoning loop
     over tools (SQL, charts; Python analysis was removed for BigQuery on 2026-02-11). The stream
     carries `SystemMessage` parts: text (including `textType = THOUGHT` reasoning steps), schema,
     data, chart, error, plus `Citation`s that link answer parts to context such as glossary terms
     and example queries. Conversations are stateful or stateless (`inline_context`).
  2. *QueryData* (v1beta, Preview, for AlloyDB / Cloud SQL / Spanner): a single NL→SQL call with
     no conversation, which is close to DataMate's job. Pipeline: **value resolution → intent
     matching and disambiguation → query synthesis → execution**. The response holds
     `generated_query`, `intent_explanation`, `query_result`, `natural_language_answer`,
     `disambiguation_question[]`, `pipeline_debug_info` and `token_usage`. Each output is switched
     on by a `GenerationOptions` flag.
- **Context, structured first.** The docs recommend filling structured fields first and using
  `system_instruction` (YAML) only for what those fields cannot express.
  - Tables and fields: `description`, `synonyms`, `tags`.
  - `example_queries[]`: `naturalLanguageQuestion`, `sqlQuery`, typed `parameters` (`{state}` in
    the question, `@state` in the SQL). A matched example comes back as a `MatchedQuery`.
  - `user_functions.bqRoutines[]`: UDFs the agent may call.
  - System-instruction YAML: `tables.fields.aggregations`, `relationships`
    (`join_type`, `left_table`, `right_table`, `relationship_columns`), `glossaries`
    (`term`, `description`, `synonyms`) and `additional_descriptions`.
  - `Context.SchemaRelationship` has `left_schema_paths`, `right_schema_paths`, `sources` and a
    `confidence_score`, so the system suggests relationships and scores them.
  - Looker has golden queries (2026-02).
- **Context sets** (QueryData) have three parts:
  - `templates`: `nl_query`, `sql`, `intent`, an auto-generated `manifest`, and `parameterized`
    (`parameterized_intent` with `$1` slots plus `parameterized_sql`).
  - `facets`: reusable predicates `sql_snippet` + `intent`, also parameterized.
  - `value_searches`: a SQL `query` over `$value` that returns the matched value, its location, a
    `concept_type`, a normalized distance in [0, 1] and a context value. The docs show exact,
    trigram and embedding variants.

  Context files are written with a Gemini CLI "context engineering agent".
- **Lifecycle.** `stagingContext` → `publishedContext`, with `lastPublishedContext` kept for
  rollback.
- **Security.** Parameterized secure views bound what generated SQL can see.
- **Multi-agent.** A2A protocol: an orchestrator delegates to specialised data agents.

### 1.2 Side-by-side

| CA-API concept | DataMate today | Gap / suggestion |
|---|---|---|
| `DataAgent` + `published_context` | Ingest cache per business: DuckDB + schema card + entity dict | Store the context as **one CA-shaped `context.yaml` per business** (S2) |
| Field `description` / `synonyms` / `tags` | `header` (original), top values, range, null ratio | Add auto-authored `synonyms` (accent-folded header, abbreviation expansion, glossary hits) and `tags` (`money`, `qty_base_unit`, `status`, `date_order`) (S3) |
| `relationships` with `confidence_score`, `sources` | None (open item 6 in the review) | Infer join keys from names and value overlap, with a confidence score; render only edges above a threshold (S4) |
| `glossaries` | `business-metrics` skill (still TODO) | Write the rulebook as glossary entries `term / description / synonyms` *plus* the semantic object that implements each one (S5) |
| `user_functions` / UDFs | `assets/semantic/` views and macros (empty) | Fill it. Make the views **parameterized by `as_of_date`**, the analogue of parameterized secure views (S6) |
| Context-set `facets` | None | Rulebook predicates (valid order, returned order, overdue) as named macros the model composes, not re-derives (S6) |
| `value_searches` (exact / trigram / embedding, distance, `concept_type`) | rapidfuzz + phonetic map → canonical name + code | Return `concept_type`, column location and normalized distance. Use the distance as a confidence feature, and let the model see several candidate columns (S7) |
| `example_queries` / templates with `parameterized_intent` / `MatchedQuery` | Teacher pipeline exists; not retrieved at inference | **Masked-intent retrieval**: replace resolved time and entities with slots, then retrieve by BM25 on the masked question (S8). Exact template hit → deterministic fill, a "trusted" answer (S9) |
| Intent matching + `disambiguation_question` | No clarification (correct for batch) | Map "ambiguous" to **abstain**, not to a question: count readings, and abstain when several valid readings give different answers (S11) |
| `THOUGHT` messages, `pipeline_debug_info`, citations | `$WORK_DIR/trace.jsonl` | Give the trace a stable, QueryData-shaped schema with `context_used` (which skills, views, examples, entity links), so errors can be attributed by component (S15) |
| `stagingContext` / `publishedContext` | Git | Hash the rendered context into the trace and the eval summary, so every PA number names the context version it ran with (S15) |
| Evaluations (Snowflake / Genie benchmarks) | `scripts/eval.py` on dev200 | Add a leave-business-out evaluation of retrieved examples (S8), as Snowflake does |
| A2A orchestrator → specialist agents | Single SQL agent | Do not adopt: more LLM steps and more variance (§4) |

### 1.3 Making DataMate "CA-API-relevant" without breaking the rules

The useful link is *format compatibility*, not runtime use. CA-API is a hosted Gemini service, so it
can never run at inference (rules 1–3).

- **S2. CA-shaped context.** Emit per business a `context.yaml` with the same shape as CA-API's
  `Context`: `tables[].schema{description, synonyms, tags, fields[]}`, `relationships[]`,
  `glossaries[]`, `example_queries[]` and `additional_descriptions[]`. `render_schema_card` becomes a
  pruned view of it. Benefits:
  1. One documented schema in place of an ad hoc YAML.
  2. Prompt sections line up with a structure that Gemini-family tooling and the CA docs already
     teach (structured first, instructions last).
  3. The same file feeds the dev-only comparison below.
- **S2b. A dev-only CA-API baseline (optional, train only).** In `scripts/devfree/`, load *train*
  businesses into BigQuery, push the `context.yaml` as `inline_context`, ask the train questions
  through stateless chat, and score with `scripts/eval.py`. This shows how far a frontier agent
  with the *same* authored context gets. That separates "our context is incomplete" (both systems
  fail) from "our 14B model or pipeline is weak" (only DataMate fails). Never run it on
  public_test or private_test (rule 3). Nothing in `src/` imports the client (rule 2). It costs a
  GCP project and BigQuery queries, so it is low priority.
- **S2c. Context-engineering agent → teacher.** Google writes context sets with a Gemini CLI
  agent. Our counterpart is the deepagents teacher in `scripts/datagen/`. Let it also propose
  `synonyms`, `glossaries` and `facets` for train businesses, then turn what generalizes into
  split-wide skills by hand. Only split-wide knowledge reaches `src/assets/` (rule 4).

## 2. Other products and what to borrow

| Product | Mechanism | What to borrow |
|---|---|---|
| **Snowflake Cortex Analyst** | Semantic views (YAML) + Verified Query Repository. A matched verified query is reused and reported in the response `confidence` field. *Optimization* reads verified SQL and suggests new semantic definitions (such as an `is_active` filter). *Evaluations* hold out the verified queries under test from a copy of the semantic view and flag regressions | (a) Mine the teacher's verified SQL for recurring predicates and promote them to semantic macros (S6). (b) Leave-business-out evaluation of retrieval (S8). (c) A regression list of dev questions that used to pass (S16) |
| **Databricks AI/BI Genie** | Trusted assets (parameterized example queries and UC SQL functions). A response is marked *Trusted* when an asset is used verbatim. Benchmarks are kept separate from instructions. Advice: keep the space small and curated, and declare PK/FK | (a) Trusted path: an exact template or macro hit → higher prior confidence (S9). (b) Keep dev200 strictly as a benchmark, never as few-shot data. (c) Prune the schema to the linked tables and columns (S10) |
| **Microsoft Fabric data agent** | Retrieves the ~top-4 example queries per question. Each example is **validated against the schema** before use. A run-steps view shows which examples were applied | Validate each retrieved example against the current business (do its tables and columns exist?) before putting it in the prompt. Log which examples were used (S8, S15) |
| **Wren AI** (open source, Apache-2.0) | MDL semantic layer: models, relationships, calculated fields and metrics, compiled to SQL over DuckDB and others | A single place where metrics are defined. Our `assets/semantic/*.sql` plays this role, but it needs the glossary link (S5) |
| **Vanna** (MIT; repo status unclear in 2026) | Retrieval over (question, SQL) pairs, DDL and docs | Confirms that example retrieval alone works only when examples are fresh and close. Use it as a complement to the semantic layer, not as a replacement |

## 3. Research worth trying

| Item | Evidence | Suggestion |
|---|---|---|
| **Arctic-Text2SQL-R1-14B** (Snowflake) | GRPO with simple execution rewards on Qwen2.5-Coder. Reported as the first open 14B model above 70% on BIRD (greedy, single model) | **S12.** Add it as a target candidate next to Qwen3-14B, Qwen2.5-Coder-14B and OmniSQL-14B. Check the release date (expected 2025-05), the licence and the parameter count on the model card, and add a row to docs/MODELS.md before testing it. Compare all candidates on dev200 with the same pipeline. Vietnamese ability is the unknown |
| XiYanSQL-QwenCoder-14B-2504 | 65.3% on BIRD dev (M-Schema); a multi-generator framework | Its **M-Schema** prompt format (table, column, type, description, examples, PK/FK in one compact block) is an alternative rendering for S2 |
| ReFoRCE / CSC-SQL / N-rep / CHASE-SQL | Already in the report | Spend the 4th LLM step only when agreement is low (S13) |
| **Selective prediction for text-to-SQL** (arXiv:2607.06799, not fully read; check before citing) | Raw self-consistency is over-confident. Cheap black-box signals each reach about 0.61–0.68 AUROC, and an LLM judge 0.72–0.78. Fine-tuned verifiers fall to about 0.66 on unseen schemas | **S14.** Combine cheap signals in a small logistic model and calibrate it by business-grouped CV, which mimics unseen businesses. Expect a gain over agreement alone, but not a large one |
| TrustSQL (penalty-based scoring) | Many abstention methods fail to beat "always abstain" under penalties | Report PA against the always-abstain (0) and always-answer baselines in every eval |
| vLLM batch invariance (`VLLM_BATCH_INVARIANT=1`) | Deterministic outputs regardless of batch composition. Newer docs say compute capability ≥ 8.0 is enough; older docs say ≥ 9.0 | **S17.** Test it on the RTX 5090 (cc 12.0). If it holds, send the k candidates concurrently. That cuts latency, and latency is the PA tie-break |

## 4. Prioritized backlog

Effort: S < 1 day, M 1–3 days, L > 3 days. "Measure" means the dev200 numbers that must move.

| ID | Suggestion | Source | Effort | Measure |
|---|---|---|---|---|
| **S1** | Fix the time skill: later rows exist and must be excluded; state the return-status exception | Rulebook vs skill | S | PA on time-bounded questions; #wrong |
| **S6** | Fill the semantic layer with **`as_of_date`-parameterized table macros** (`valid_orders(as_of)`, `revenue_lines(as_of)`, `returned_orders()`, …) used as facets. The model composes them and does not re-derive rules | CA facets + parameterized secure views; Cortex optimization | M | PA on number/percent (82% of train) |
| **S5** | Glossary = rulebook terms with Vietnamese synonyms → the semantic object that implements each term. Render only the entries the question mentions | CA `glossaries` | S | PA by category; prompt tokens |
| **S8** | Teacher templates with **masked intent**: replace resolved time and entity spans with `{time}` / `{product}` slots. BM25/rapidfuzz on the masked question picks the top-3 examples, each checked against the current schema | CA templates `parameterized_intent`, Fabric top-4 + validation, Cortex VQR | M | Leave-business-out PA with and without examples |
| **S7** | Value search returns `(value, table.column, concept_type, distance)`. Show the top-n candidates when they are close; use the distance as a confidence feature | CA `value_searches` | S | Entity-question PA; errors from wrong entities |
| **S14** | Confidence model: agreement + entity distance + template hit + empty or NULL result + row count + repair count + type plausibility → logistic regression, calibrated by business-grouped CV. `tau` is set on its output | arXiv:2607.06799, TrustSQL | M | PA-vs-tau curve; AUROC; #wrong |
| **S9** | Trusted path: masked question matches a template exactly and every slot is resolved → fill the parameterized SQL, execute, answer with no LLM call or with one confirming candidate | Genie trusted assets, Cortex VQR | M | PA and seconds per question on matched questions |
| **S3** | Auto-authored `synonyms` and `tags` per column (folded header, abbreviation table, unit hints such as `so_luong_le` = base-unit quantity) | CA field context | S | Column-choice errors |
| **S10** | Prune the schema card to tables and columns linked by entities, glossary and synonyms, while keeping join keys | Genie "small, curated" | S | Prompt tokens; PA on wide workbooks |
| **S4** | Inferred relationships with a confidence score (name match + value-containment ratio), rendered as CA `relationships` | CA `SchemaRelationship` | M | PA on multi-table questions |
| **S11** | Ambiguity → abstain: when candidates disagree because the readings differ (period, metric), not because of crashes, abstain instead of taking the majority | CA disambiguation | S | #wrong on low-agreement questions |
| **S13** | 4th step only on low agreement: a pairwise selector over the top-2 result groups, with order swapped (N-rep) | N-rep, CSC-SQL | M | PA in the 0.4–0.7 agreement band |
| **S12** | Target-model bake-off including Arctic-Text2SQL-R1-14B | Arctic paper | M | dev200 PA, latency, Vietnamese errors |
| **S15** | QueryData-shaped trace: `generated_query`, `intent_explanation` (the reason field), `context_used`, `context_hash`, `matched_template`, timings | CA response, citations | S | Error attribution report per component |
| **S16** | Regression list: dev questions that used to pass; eval prints newly failed ids | Cortex/Genie evaluations | S | No new failures without a note |
| **S17** | vLLM batch invariance, then concurrent candidates | vLLM docs | S | Rerun diff ≤ 0.01 PA; seconds per question |
| **S2** | CA-shaped `context.yaml` as the single context artifact | CA `Context` | M | Neutral on PA; simplifies S3–S5, S8 |
| S2b | Dev-only CA-API baseline on train, in `scripts/devfree/` | CA-API | L | Diagnostic only |
| S2c | Teacher proposes synonyms, glossary and facets on train; a human promotes the generic ones | CA context-engineering agent | M | As S3/S5 |

Suggested order: S1 → S6 + S5 → baseline eval → S7, S3, S10 → S8 → S14 → S9, S11 → S12 →
S13, S17 → the rest.

## 4b. Planned feature: charts in the demo app

**S18. Charts, as CA-API does.** The challenge does not score charts and the batch path
(`python -m src`) never makes them. The demo app (`app/`, on top of `POST /ask`) should show a
chart next to the answer, as CA-API returns a `ChartMessage` beside text and data.

Decided so far:
- Scope: the app and `/ask` only. The submission line and the inference time are unchanged.
- Input: the executed result the answer came from (the winning candidate's rows and columns), so
  the chart shows the same numbers as the answer.
- Output: a declarative chart spec (for example Vega-Lite, which CA-API also uses) that the UI
  renders, never an image.
- Chart type from the answer type and the result shape. A first version needs no LLM: list or
  table with one measure → bar, by date or month → line, share of a total → bar with percents,
  single number or string → no chart (show the value). An LLM step that picks or titles the chart
  is optional, app-only, and must stay offline (local model).

Not built yet. Start after `src/` is done (see docs/NOTES.md, "App settings, demo UI later").

## 5. Not recommended, and why

- **Clarifying questions, multi-turn state, A2A multi-agent.** These are CA features that do not
  apply to a scored batch job, and they cost steps and variance. (Charts are planned for the demo
  app, not for the competition: see S18.)
- **Embedding-based value search or example retrieval.** It would use parameter budget that the
  14B model already takes (docs/MODELS.md). The masked-intent approach in S8 gets most of the
  benefit with BM25.
- **An open deep-agent loop at inference.** It conflicts with the 4-step limit and the 0.03 rerun
  rule (H4).
- **Fine-tuned verifier as the main confidence signal.** Reported to degrade on unseen schemas,
  and the private test has unseen businesses.

## Sources

Google Conversational Analytics API
- [Architecture and key concepts](https://docs.cloud.google.com/gemini/docs/conversational-analytics-api/key-concepts)
- [Release notes (GA 2026-06-23, THOUGHT messages, golden Looker queries, database sources)](https://docs.cloud.google.com/gemini/data-agents/conversational-analytics-api/release-notes)
- [Data agent system instructions](https://docs.cloud.google.com/gemini/data-agents/conversational-analytics-api/data-agent-system-instructions)
- [Authored context for BigQuery](https://docs.cloud.google.com/gemini/data-agents/conversational-analytics-api/data-agent-authored-context-bq)
- [Authored context for Looker (golden queries)](https://docs.cloud.google.com/gemini/docs/conversational-analytics-api/data-agent-authored-context-looker)
- [Authored context for databases](https://docs.cloud.google.com/gemini/docs/conversational-analytics-api/data-agent-authored-context-databases)
- [Context sets overview (templates, facets, value searches)](https://docs.cloud.google.com/sql/docs/postgres/context-sets-overview)
- [QueryData overview](https://docs.cloud.google.com/sql/docs/postgres/data-agent-overview)
- [Python client: QueryDataResponse, Context.SchemaRelationship](https://docs.cloud.google.com/python/docs/reference/google-cloud-geminidataanalytics/latest/summary_overview)

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
