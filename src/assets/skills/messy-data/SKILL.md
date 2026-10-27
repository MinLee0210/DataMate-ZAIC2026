---
name: messy-data
description: How the shop's raw files are messy, what ingest already cleaned, and how to check and fix the rest in SQL or pandas. Use when a column, table or result looks wrong before trusting it.
---

# Messy data

Ingest cleans the common cases before you see the tables. Know what it did, and check the rest
yourself: sample the column, then fix it in the query (SQL) or in an analysis step (pandas).

## Already cleaned by ingest
- **Money and numbers** are numeric columns. `50.000đ` = 50000 (VND has no decimals, the dot
  separates thousands), `25k` = 25000, `1,5tr` / `2 triệu` = 1500000 / 2000000, `30 nghìn` = 30000.
- **Split tables are merged.** Sheets split by month (`T01_2025`, `T02_2025`, …) and files split
  in parts (`DonHang_1`, `DonHang_2026`, `Lo_1`, `Lo_2`) with the same columns are one table. The
  column `nguon` holds each row's file and sheet. Query the merged table; do not union by hand.
- **Grouped exports are filled down.** When an order's code, date, status and customer were
  written on its first line only, the next lines got them filled in.
- **Headers** are found below titles; merged cells repeat their value.

## Check before trusting a result
- A money or quantity column that is still `VARCHAR`: ingest could not parse some values.
  Sample them, then convert in SQL, e.g.
  `TRY_CAST(regexp_replace(lower(col), '[^0-9k]', '', 'g') ...)`, or in pandas.
- Values about 1000 times too small or too large: a unit problem (thousands written as `50.0`,
  or a column in nghìn đồng). Compare with `don_gia * so_luong` on the same rows.
- Two tables with the same columns and a similar name that were not merged (different column
  names): `UNION ALL` them, and make sure a row does not appear in both (count distinct order
  codes in each).
- Many rows with NULL in an order code or date column while the line columns are filled: a
  grouped export that was not filled. Fill down in SQL with
  `last_value(col IGNORE NULLS) OVER (ORDER BY rowid)` within the file order, or with pandas `ffill`.
- Line totals vs. order totals: do not add an order-level total once per line. Use one row per
  order (`DISTINCT` on the order code) for order-level columns.
- The same item written differently (accents, case, extra spaces, abbreviations): match on the
  code when there is one; otherwise compare folded text (`lower`, `strip_accents`, `trim`).
- Dates: check `min`/`max` of the date column against the as-of date; rows after it exist and must
  be excluded.
