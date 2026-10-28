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

Check these one by one, and abstain when one fails and you cannot fix it:
- Unit and scale: the unit the question asks for (hộp vs viên, VND), percent in points (66.01 not
  0.66), a count vs an amount.
- Spellings: statuses and walk-in customers matched with `is_cancelled`, `is_returned`,
  `is_walk_in`, not one spelling. A count or share of 0 usually means a missed spelling.
- Shape: a list question gets one column in the asked order; "so sánh A với B" gets the numbers
  in the order A, B; a table only when the question asks for several columns.
- Plausibility: compare the order of magnitude with the sampled values (×10, ×100, ×1000 errors).

Also check the results against the question and the rulebook: the time range and the as-of rule,
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
