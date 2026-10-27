Before any SQL is written, work out what the shop owner really needs and how the data answers it.
Do not write SQL. Another step writes the query from your analysis, so be exact and short (at most
about 300 words).

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

Answer under these headings, in Vietnamese or English:

1. **Need**: what the owner wants to know, in one sentence. Spell out colloquial words, missing
   accents and abbreviations (e.g. "sp" = sản phẩm, "dc" = được, "nhiu" = nhiêu).
2. **Term mapping**: split the question into its business terms (measure, objects, time, condition,
   ranking). For each term give one line: `term -> table.column / rulebook rule / exact value`.
   When two columns or rules could fit, name both and say which one you choose and why (e.g.
   quantity in base units vs. in the unit sold; order date vs. delivery date; revenue vs. amount
   paid). Quote the rulebook rule by its name or row: general sections and this shop type's section.
3. **Values to check**: the filter values the query relies on (statuses, names, codes, categories).
   Say which ones appear in the schema's top values or the entity matches, and which ones the
   query must look up (e.g. with `ILIKE` or a distinct-values CTE) because they are not shown.
4. **Time scope**: the date range(s), the date column each applies to, and the as-of rule: records
   dated after the as-of date exist in the data but must not be counted, and a period that only
   partly overlaps the data is computed on the overlap.
5. **Plan**: 3 to 6 short steps from rows to answer: filter valid records, join, aggregate, rank,
   tie-break (code ascending unless the rulebook says otherwise), top-k.
6. **Answer**: the answer type (number, percent, string, date, boolean, list, table) and its
   format: rounding, money in whole VND, percent in percentage points, list order, table columns.
7. **Answerable?**: yes, or `unanswerable` with the reason (the period lies entirely outside the
   data, or the shop does not record this). "No data" is not the same as 0.
