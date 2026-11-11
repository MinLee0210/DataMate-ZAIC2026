Second step: plan the data queries, now that you have reasoned over the schema and seen sampled
values.

## Schema (DuckDB)
```yaml
{{schema}}
```

## Semantic views (already apply rulebook §1 and §3)
{{semantic}}
Prefer a `v_*` view when it answers the question: it already excludes cancelled and returned
orders, uses the order date and treats a customer as a code. Do not re-derive those rules.

## Resolved time
{{time}}

## Entity matches
{{entities}}

## Approach
{{approach}}

## Question
{{question}}

## Your reasoning so far
{{thought}}

## Sampled values
{{samples}}

## Solved examples from other shops
Verified queries for similar questions on other businesses. Their tables and columns are not this
shop's: reuse the approach (filters, rulebook rule, grouping, rounding), never the names.
{{examples}}

## Answer shape (rulebook §9)
{{shape}}
The shape describes the answer if the data can answer the question; it does not make an
unanswerable question answerable.

Write 1 to 3 named data queries. Each is one read-only DuckDB `SELECT` (CTEs are fine) over the
tables above. Make one query return exactly the answer when you can: computed, rounded and
ordered as the answer must be. Use other queries only to check something the answer depends on.
Apply the rulebook: valid records, the right date column and range, the as-of rule, units.

Reply with one JSON object and nothing else:
{"thought": "how the queries answer the question",
 "data_queries": [{"name": "snake_case_name", "question": "what this query answers", "sql": "SELECT ..."}]}
