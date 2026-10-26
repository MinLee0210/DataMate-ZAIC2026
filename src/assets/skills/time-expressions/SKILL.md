---
name: time-expressions
description: How relative Vietnamese time expressions map to date ranges. Use whenever the question mentions a period.
---

# Time expressions

Time expressions are resolved for you, deterministically, against `as_of_date`; the ranges are given
with each question under "Resolved time". Use them as given, inclusive on both ends:
`WHERE d BETWEEN DATE 'start' AND DATE 'end'`. Do not use `current_date` or `now()`.

Conventions (from the rulebook, to be confirmed):
- A week runs Monday to Sunday. "tuần rồi / tuần trước / tuần qua" is the previous full week.
- "tháng này", "quý này", "năm nay" run from the start of the period to its end, not just to `as_of_date`;
  rows after `as_of_date` do not exist in the data.
- "N ngày qua / gần đây" is the N days ending on `as_of_date`.
- "tháng M" without a year is the most recent month M not after `as_of_date`.
- If no time is mentioned, use all the data up to `as_of_date`.
- Lunar dates (Tết, rằm, mùng 1) map to solar dates through the split's calendar table if one is
  listed in the schema.

Abbreviations seen in questions: hnay = hôm nay, hqua = hôm qua, trc = trước, thg = tháng.
