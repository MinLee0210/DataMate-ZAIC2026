---
name: answer-types
description: Pick the answer type and shape the SQL result so it can be scored exactly. Use for every question.
---

# Answer types

Pick exactly one type; the query result must have the shape below.

| Type | Result shape | Notes |
|---|---|---|
| number | 1 row, 1 column | counts, sums, averages. Rounding to 2 dp is done for you. |
| percent | 1 row, 1 column | in percentage points: 12.5 means 12.5%. Multiply ratios by 100. Keep the sign (growth can be negative). |
| string | 1 row, 1 column | a name or a code. Return the name unless the question asks for the code. |
| date | 1 row, 1 column | a DATE, or `strftime(d, '%Y-%m')` when the question asks for a month. |
| boolean | 1 row, 1 column | `true` / `false` (yes/no, có/không questions). |
| list | 1 column, N rows | ordered: top-N, "những sản phẩm nào". Order by the ranking rule. |
| table | N columns, N rows | several values per item, e.g. product and revenue. Order by the ranking rule. |
| unanswerable | no SQL | the data has no column, concept or period for the question. |

- "bao nhiêu" (how many / how much) → number. "bao nhiêu phần trăm", "tỉ lệ", "tăng/giảm bao nhiêu %" → percent.
- "khi nào", "ngày nào", "tháng nào" → date. "có ... không" → boolean.
- "top 3", "những ... nào" → list. Asking for an item and its value → table.
- A single best/worst item ("sản phẩm nào bán chạy nhất") → string.
