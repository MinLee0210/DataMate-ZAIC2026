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

Result names you can use: {{names}}

Only call the question unanswerable when the data truly lacks it: the period lies entirely outside
the data, or the shop does not record that kind of information. It is not unanswerable when the
measure can be computed from other columns (quantity × price − line discount), when a value is
spelled differently, when a date column needs parsing, or when a period inside the data has no
rows (then the answer is 0, or the filter is wrong). Fix the query instead.

Then choose one action and reply with one JSON object and nothing else:
{{actions}}
