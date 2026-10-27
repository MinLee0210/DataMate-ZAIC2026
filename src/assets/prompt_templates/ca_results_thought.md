Reason over the results of the data queries before giving the final answer. A wrong answer costs
a point and no answer costs nothing: give a final answer only when you believe it is correct.

## Schema (DuckDB)
```yaml
{{schema}}
```

## Resolved time
{{time}}

## Question
{{question}}

## Your reasoning so far
{{thought}}

## Data queries and results
{{data}}

Check the results against the question and the rulebook: the time range and the as-of rule,
valid records, the measure's definition and unit, the objects, ranking direction, tie-break by
code and top-k, rounding and answer type, and plausibility (empty or NULL results, impossible
signs or magnitudes, 0 vs. "no data"). An error from a query is recoverable: fix it or try
another way.

Then choose one action and reply with one JSON object and nothing else:
{{actions}}
