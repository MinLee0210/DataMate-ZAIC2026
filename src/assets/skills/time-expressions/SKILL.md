---
name: time-expressions
description: How relative Vietnamese time expressions map to date ranges. Use whenever the question mentions a period.
---

# Time expressions

Time expressions are resolved for you, deterministically, against `as_of_date`; the ranges are given
with each question under "Resolved time". Use them as given, inclusive on both ends:
`WHERE d BETWEEN DATE 'start' AND DATE 'end'`. Do not use `current_date` or `now()`.

Rulebook §2, row by row:

1. **Rows after `as_of_date` have not happened.** A file can hold rows dated later than
   `as_of_date`; keep them out of every count, sum and balance with `d <= as_of_date`. Exception:
   an order's cancel/return status is read as written, even when its status date is after
   `as_of_date`; rulebook §1 still decides whether that order counts as revenue.
2. **Ngày X, hôm nay, hôm qua** ask about activity inside that day only.
3. **Từ X đến Y, nhóm X–Y** include both X and Y.
4. **N ngày gần nhất** is the N consecutive days ending today, today included.
5. **Quá N, hơn N, trên N, dưới N** exclude N (`> N`, `< N`). **Từ N trở lên** includes N (`>= N`).
6. **Tuần** starts on Monday. **Tuần này** is Monday of this week to the end of today; **tuần trước,
   tuần rồi** is the whole previous Monday–Sunday week.
7. **Tháng M/Y** is the whole month, day 1 to the last day of the month. **Quý Q** is the three
   calendar months starting at month 3Q−2.
8. **Tháng này, quý này, năm nay** run from the start of the period to **the end of today**, never to
   the end of the period. **Từ đầu năm, từ đầu năm tới nay** is 01/01 of this year to today.
9. **Tháng M, quý Q without a year** use this year if they do not start after today, otherwise last
   year's.
10. **Tháng này so với tháng trước**: the previous month uses the **same number of days**, day 1 to
    the same day number as today, capped at the previous month's last day.
11. **Đến hết ngày X, tính đến hôm nay** ask for a balance (debt, stock, cash): the state at the end
    of X, counting every movement from the beginning of the data up to the end of X. It is not the
    "tháng này" period. When such a question says "hôm nay", the resolved day range means "up to
    today", not a same-day filter.
12. **Tết năm Y, dịp Tết, mùa Tết** is the solar span from **23 tháng Chạp** of lunar year Y−1 to the
    **end of 10 tháng Giêng** of lunar year Y. Without a year, use `as_of_date`'s year. **Trước
    Tết** is the same number of days immediately before 23 tháng Chạp; **N ngày trước Tết** is the N
    days immediately before it. Read these dates from the split's `calendar.csv`, loaded at ingest
    as the `lunar_calendar` table (`date`, `lunar_day`, `lunar_month`, `lunar_year`), never from a
    hard-coded date.
13. **Ca sáng** is 06:00–13:59 and **ca chiều** is 14:00–21:59, by the order's creation time. When a
    question compares ca chiều with ca sáng, the baseline is ca sáng.
14. **No time mentioned**: all the data up to `as_of_date` (`d <= as_of_date`).

Abbreviations seen in questions: hnay = hôm nay, hqua = hôm qua, hkia = hôm kia, trc = trước,
thg = tháng.
