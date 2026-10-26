---
name: ranking-rules
description: How to rank items (best-selling, top-N, highest, lowest) and break ties. Use for any question that ranks or picks a maximum or minimum.
---

# Ranking rules

- Rank by the criterion the question names ("doanh thu" = revenue, "số lượng" = quantity,
  "số đơn" = number of orders). If it names none, use the rulebook default criterion
  (see the business metrics skill).
- Rank over valid orders only (see the business metrics skill).
- Sort descending for "nhiều nhất / cao nhất / bán chạy nhất / top", ascending for
  "ít nhất / thấp nhất / bán chậm nhất".
- Break ties by the item code, ascending: `ORDER BY metric DESC, code ASC`.
- Top-N: `LIMIT N` after the full ORDER BY. "Nhất" alone means N = 1 and the answer type is string.
- Return the item's name, unless the question asks for the code.
