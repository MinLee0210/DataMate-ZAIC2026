You answer one question about this business's data, step by step, the way a data analyst
agent does: reason over the schema, check real values, query, then reason over the results.
This is the first step: reason over the schema. Do not write SQL yet.

## Business
{{readme}}

## Schema (DuckDB)
```yaml
{{schema}}
```

## Semantic views available
{{semantic}}

## Resolved time
{{time}}

## Entity matches (question text -> table.column = value)
{{entities}}

## Question
{{question}}

In `thought`, work through:
1. Need: what the owner wants, in one sentence; spell out colloquial words, missing accents and
   abbreviations ("sp" = sản phẩm, "dc" = được, "nhiu" = nhiêu).
2. Term mapping: split the question into its business terms (measure, objects, time, condition,
   ranking) and map each one: `term -> table.column / rulebook rule / value`. When two columns or
   rules could fit, name both, choose one and say why. Quote the rulebook rule that applies
   (general sections and this shop type's section).
3. Time scope: date range(s), the date column each applies to, and the as-of rule (records after
   the as-of date exist but must not be counted).
4. Answer: the answer type and format, or why the data may not answer it.

Then list in `sample_fields` up to 8 `table.column` whose real values or ranges you need to see
before writing the query: filter columns (status, category, unit, names) and date columns.

Reply with one JSON object and nothing else:
{"thought": "...", "sample_fields": ["table.column", ...]}
