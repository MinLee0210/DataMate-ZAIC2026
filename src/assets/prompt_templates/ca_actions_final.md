- Final answer from one result, which must already be the answer (one row and one column for
  number, percent, string, date and boolean; one column for list; the table for table):
  `{"thought": "...", "action": "final", "answer_type": "number|percent|string|date|boolean|list|table", "data_result": "<result name>"}`.
  `data_result` is the result's **name** as listed above (for example `total_revenue`), not its
  value and not a number.
- The data cannot answer the question (the period lies entirely outside the data, or the shop
  does not record this): `{"thought": "...", "action": "final", "answer_type": "unanswerable", "reason": "..."}`
- Not confident in any answer: `{"thought": "...", "action": "abstain", "reason": "..."}`
