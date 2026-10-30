Use the most direct method for this question.
---
Work bottom-up: start from the line-level (detail) table, apply every filter on the lines, then aggregate. Build the set of valid orders first and join to it.
---
Verify independently: fetch the needed rows with a plain query, then compute the answer in a pandas analysis step instead of one SQL aggregate; check units and spellings on the raw rows.
---
Start from the rulebook: write down the exact rulebook definition of every business term in the question (valid record, revenue, period, ranking, rounding) before you query, then build the query to match those definitions one by one.
---
Compute the answer two independent ways, for example through the order table and through the line table, or with and without a join, and use the one that matches the rulebook; if the two disagree, find out why before you answer.
---
Be defensive about the data: count rows before and after each filter, look at the distinct values of every filtered column, and handle spellings, NULLs and text numbers explicitly; then aggregate.
