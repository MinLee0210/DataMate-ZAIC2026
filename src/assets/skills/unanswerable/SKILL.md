---
name: unanswerable
description: When to answer "unanswerable" instead of writing SQL. Use when the question asks for something the data may not contain.
---

# Unanswerable questions

A wrong answer costs a point; "unanswerable" on an unanswerable question earns one. Answer
`unanswerable` (no SQL) when:

- the question needs a concept no table or column holds (e.g. profit with no cost column,
  customer age with no birth date, ratings with no review table);
- the period is entirely outside the data's date range (check the column ranges in the schema),
  or is in the future relative to `as_of_date`;
- the question names an entity (product, customer, branch) with no match in the data;
- the question is not about this business's data at all.

Do not answer `unanswerable` because the query is hard. A question whose result is zero or an
empty set over a period the data covers is answerable (the answer is 0, or false).
