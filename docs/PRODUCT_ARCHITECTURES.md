# Product architecture review (2026-10-28)

Scope: official product documentation, reviewed for patterns useful to an offline, single-question,
penalized-accuracy benchmark. Product claims describe their own systems; no comparative accuracy
claim is transferable to DataMate without a controlled run.

| Product | Architecture described by its documentation | Fit for DataMate |
|---|---|---|
| Snowflake Cortex Analyst | Semantic views define logical entities, facts, dimensions, metrics, relationships, descriptions and synonyms. Verified question/SQL examples guide generation; evaluations check regressions. [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) | Strong case for moving repeated rulebook calculations into generic, tested DuckDB semantics and selecting only relevant metadata. Existing text/status macros are a start. |
| Databricks Genie Agents | Curated knowledge store, selected example SQL, trusted parameterized queries/functions, and benchmarks kept separate from generation context. Its Inspect feature checks filter values, date windows, joins and aggregations with smaller SQL queries. [Concepts](https://learn.microsoft.com/en-us/azure/databricks/genie-agents/concepts) | Keep examples distinct from evaluation questions; add deterministic checks around dates, statuses and joins. Trusted templates may help repeated question shapes after leave-business-out validation. |

## Evaluation

The common architectural strength is **curated meaning before SQL generation**, with execution
and regression evidence after it. DataMate has ingestion, schema cards, examples and traces, but
its semantic layer currently covers only text folding and status predicates. Numeric business
rules are still reconstructed in prompts and generated SQL. That is the largest architectural gap.

The products also offer features outside this task: managed governance, multi-turn conversation,
charts, broad tool orchestration and hosted model selection. The challenge's offline, 15B-model,
six-hour and one-line-answer constraints make those poor immediate investments.

## Implementation order

1. Enforce the four-call reasoning budget, counting failed parses and retries. A bounded loop is
   needed before adding verification steps; implemented in `src/services/qa/malt.py`.
2. Add rulebook-defined, schema-generic semantic macros, with tests across business schemas.
3. Select relevant schema fields, glossary entries and examples instead of sending broad context.
4. Add executable checks for time filters, joins and status exclusions, then calibrate abstention
   on a genuinely untouched business-family split.

No PA improvement is claimed from this review or the call-budget change alone. The target-model
evaluation gate remains necessary.
