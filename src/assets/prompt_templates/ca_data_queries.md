Second step: plan the data queries, now that you have reasoned over the schema and seen sampled
values.

## Schema (DuckDB)
```yaml
{{schema}}
```

## Resolved time
{{time}}

## Entity matches
{{entities}}

## Question
{{question}}

## Your reasoning so far
{{thought}}

## Sampled values
{{samples}}

Write 1 to 3 named data queries. Each is one read-only DuckDB `SELECT` (CTEs are fine) over the
tables above. Make one query return exactly the answer when you can: computed, rounded and
ordered as the answer must be. Use other queries only to check something the answer depends on.
Apply the rulebook: valid records, the right date column and range, the as-of rule, units.

Reply with one JSON object and nothing else:
{"thought": "how the queries answer the question",
 "data_queries": [{"name": "snake_case_name", "question": "what this query answers", "sql": "SELECT ..."}]}
