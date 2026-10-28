- Final answer from one result, which must already be the answer (one row and one column for
  number, percent, string, date and boolean; one column for list; the table for table):
  `{"thought": "...", "action": "final", "answer_type": "number|percent|string|date|boolean|list|table", "data_result": "<result name>"}`.
  `data_result` is the result's **name** as listed above (for example `total_revenue`), not its
  value and not a number.
- The data cannot answer the question (the period lies entirely outside the data, or the shop
  does not record this): `{"thought": "...", "action": "final", "answer_type": "unanswerable", "reason": "..."}`
- Analyse the retrieved results with pandas. The snippet sees `results` (a dict of the
  DataFrames above, by name), `pd`, and `query(sql)` (returns a DataFrame); no imports; it must
  assign the answer to `result`. You will see its output before the final answer:
  `{"thought": "...", "action": "analysis", "question": "...", "data_result_names": ["..."], "code": "result = ..."}`
- Run another data query (for example to fix an error or a wrong filter). You will see its
  result before the final answer:
  `{"thought": "...", "action": "data_query", "name": "snake_case_name", "question": "...", "sql": "SELECT ..."}`
- Not confident in any answer: `{"thought": "...", "action": "abstain", "reason": "..."}`
