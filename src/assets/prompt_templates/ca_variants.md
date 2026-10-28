Use the most direct method for this question.
---
Work bottom-up: start from the line-level (detail) table, apply every filter on the lines, then aggregate. Build the set of valid orders first and join to it.
---
Verify independently: fetch the needed rows with a plain query, then compute the answer in a pandas analysis step instead of one SQL aggregate; check units and spellings on the raw rows.
