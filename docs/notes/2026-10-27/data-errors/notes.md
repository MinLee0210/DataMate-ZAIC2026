# Data errors found in error analysis (2026-10-27)

Source: the 54 wrong answers of the CA pipeline on train dev200
(`docs/analysis/2026-10-27/ca/scored.jsonl`). Train only; public_test has no labels and was not
looked at. Several wrong answers were not model errors: the tables the model saw were wrong.
Four ingest errors were found, fixed in code (deterministic) and described in the `messy-data`
skill, so the agent can also recognise and fix a case ingest misses.

## 1. Dot thousands read as decimals (`50.000đ` → 50.0)
- Symptom: money answers about 1000 times too small (`16520.5` instead of `17654500`).
- Cause: `50.000đ` alone is ambiguous (decimal or thousands). The column locale check only
  counted values with two or more dot groups, so `50.000đ`, `99.000đ` stayed decimals.
- Fix: VND has no decimals, so a value with a VND marker (`đ`, `vnd`, `vnđ`, `đồng`) and dot
  groups of three is read as thousands (`clean.parse_number`).
- Seen in: biz_129 `chi_tiet_don.tien_ban` (checked); biz_127 has the same symptom in its wrong
  answers (not checked yet).

## 2. Money shorthand left as text (`25k`, `1,5tr`)
- Symptom: revenue far too low; the column stayed `VARCHAR` and the model cast or skipped it.
- Cause: a column mixing `25k`, `9.999đ` and `18000` did not reach the 95 % parse threshold.
- Fix: `k` / `nghìn` / `ngàn` ×1 000 and `tr` / `triệu` ×1 000 000 are parsed.
- Seen in (columns that are numeric now): biz_105 `sobanhang.gia_le`, `sobanhang.tri_gia`;
  biz_122 `donhang_chitiet.tong_tien`; biz_124 `sotay_chiphi.so_tien`,
  `sotay_nhaphang.gia_nhap`, `sotay_nhaphang.thanh_tien`.

## 3. Tables split by month or part
- Symptom: year-to-date, "30 ngày gần nhất" and multi-month answers far too low; the model
  queried one monthly table, or missed some.
- Cause: one sheet per month (`T01_2025`, …) and files split in parts (`DonHang_ChiTiet_1`,
  `DonHang_ChiTiet_2026`, `DonHang_Lo_1`, `DonHang_Lo_2`) each became a table.
- Fix: tables with the same columns and the same base name (sheet and numeric suffixes removed)
  are merged; the `nguon` column keeps each row's file and sheet (`readers.merge_split_tables`).
  Types are inferred after merging, so a column has one type.
- Seen in 13 of 30 train businesses: biz_102 (20→3 tables), biz_103 (18→3), biz_105 (22→6),
  biz_106 (11→10), biz_112 (18→3), biz_115 (20→5), biz_117 (24→8), biz_118 (24→5),
  biz_119 (29→11), biz_120 (28→11), biz_122 (27→8), biz_128 (26→9), biz_130 (4→3).

## 4. Grouped exports with blank parent cells
- Symptom: monthly totals about half of the truth; filters on date or status dropped the
  continuation lines of each order.
- Cause: the order's code, date, status and customer are written on its first line only.
- Fix: columns blank on exactly the same rows are filled down, but only when that group holds an
  id-like column and a date column (`clean.fill_grouped_rows`), so a legitimately empty field
  (a walk-in customer without a code) stays empty.
- Seen in: biz_103 (date blank on 60 % of rows), biz_121 (47 %), biz_122 (47 %).
- Check: biz_122 valid revenue for May 2025 is now 246,039,400, equal to the gold answer
  (130,353,700 before).

## Other error groups in the same 54 (model side, not fixed here)
- Revenue definition off by 1–4 % (discounts, returns, which total column): about 20 answers.
- Ranking: wrong item in a top-k list or "nhất" (criterion or unit): about 6.
- Quantity in base units vs. unit sold, toppings and sizes: about 5.
- Answer shape: a table where the question asked for a list in a given order: 1.

## Process
- `INGEST_VERSION` is part of the ingest cache key; bump it whenever ingest output changes.
- Re-run `make ingest SPLIT=train` and a dev200 eval after any ingest change.
