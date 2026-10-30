---
name: business-metrics
description: SQL recipes for the rulebook's business terms (valid orders, revenue, order counts, units, averages, shares, growth, customers, debt). Use for any question about money, quantities, orders or customers.
---

# Business metrics

The rulebook (end of this prompt) defines each term; follow it, and the shop-type section when
there is one. These are the ways to compute them on the tables you get.

## Helper macros (in every business database)
- `is_cancelled(status)`, `is_returned(status)`: true for every way the status is written
  (`hủy đơn`, `Đã hủy đơn`, `Huỷ đơn`, `khách hủy`; `hàng trả về`, `Đổi trả`, `Đã hoàn hàng`).
  **Use them instead of comparing to one spelling**: a shop often writes the same status 2-4
  ways, and `= 'Đã hủy'` misses the others (a cancel count of 0 is almost always this mistake).
  Both return false for a blank or NULL status; `NOT is_cancelled(status) AND NOT
  is_returned(status)` therefore keeps ordinary rows with unspecified status.
- `is_walk_in(customer_name)`: `khách lẻ`, `Khách lẻ`, `kl`, `lẻ`, `vãng lai`, empty. Walk-in
  orders are never a customer in counts or rankings.
- `fold(x)`: lowercase, no accents, `đ` → `d`; compare names and labels with it.

## Valid orders
- Valid = `NOT is_cancelled(status) AND NOT is_returned(status)`. Everything else (done, `xong`,
  `Thành công`, delivering) is valid.
- An order with **any** returned line is a returned order: drop the whole order, not the line.
  Build the set of order codes first, then filter lines by `order_code NOT IN (...)`.
- With a status column only on the order table, join lines to orders by the order code.
- When the status sits in a notes column (no status column), read it from there; a note that does
  not mention a status means a completed order.

## Revenue (doanh thu, tiền hàng, bán được bao nhiêu tiền)
- Sum of the **line totals after line discounts** of valid orders, by **order date**.
- Not the order-level total after an order discount or voucher, not VAT, not shipping, not the
  amount paid. If only `quantity * unit price` and a line discount exist, use
  `quantity * unit price - line discount`.
- A table with both order-level and line-level money: never add the order total once per line.
- "Phí phục vụ" (service fee) lines count in revenue, but are not an item for rankings or counts.

## Counts and quantities
- Order count: `count(DISTINCT order_code)` over valid orders.
- Quantity in base units: multiply by the conversion factor (a "quy đổi" table or column; a unit
  with no conversion row has factor 1). Use an existing base-unit column when there is one.
- "Bán được bao nhiêu <đơn vị>": only items whose **base unit** is that unit, converted.

## Units and prices
- A price or cost "per <unit>" (một hộp, một viên, một thùng) is per **that** unit: convert with
  the conversion table. Average purchase price = sum(quantity × price) / sum(quantity), in the
  unit asked, not the sum of prices and not per base unit when the question names a larger unit.
- "Số bill", "số đơn", "số phiếu" are counts of documents, not money.

## Averages, shares, growth
- Money averages round to whole VND, half up: `round(CAST(x AS DECIMAL(18,4)), 0)`, never
  `round(x, 2)` (an average order value is money).
- Other averages and percents: 2 decimals. Percent in points: `100.0 * part / total`.
- A group's share divides by the revenue of the **whole shop** in the same period (walk-in orders
  included in the denominator).
- Growth: `100.0 * (current - previous) / previous`, negative when it fell. A difference in
  amounts: `current - compared`, same unit.
- Cancel rate: cancelled orders / **all** orders placed in the period (every status).
- Percent is in points: 66.01, not 0.6601; a share is a percent, never the amount itself.
- "X tăng hay giảm bao nhiêu % so với Y": X is the current period, Y the base; the answer is
  `100.0 * (X - Y) / Y`. Compute X and Y with the same filters (valid orders, same revenue
  definition), then check the sign against the two amounts before answering.
- Effect of a price change ("tăng giá từ A lên B ngày D … N ngày kể từ đó so với N ngày trước"):
  answerable from order lines. After = days D to D+N-1, before = days D-N to D-1, same item,
  valid orders; the answer is the percent change `100.0 * (after - before) / before` of the
  quantity (or revenue, if asked). Do not answer unanswerable because no price-history table
  exists: the question gives the date.
- Order counts by status ("đơn huỷ", "đơn trả hàng"): use the `is_cancelled` / `is_returned`
  macros on the status column, never an exact string match. A count of 0 over a period with
  orders means the filter missed: look at the distinct status values first.

## Customers
- With customer codes: one code = one customer; orders without a code (walk-in) are not a
  customer. Without codes: the customer is the name on the order, names differing only in
  spelling (case, accents, spaces) are the same customer; "Khách lẻ" is not a customer.

## Debt
- Debt of an order at day X: order total (after order discount, with shipping) minus payments up
  to the end of day X. Cancelled orders excluded; returned orders still count. COD and
  marketplace orders are not debt.
- Debt age: days from the **order date** to today (an order placed today is 0 days).
- Debt collected ("thu nợ", "tiền khách trả nợ", "thu hồi công nợ") in a period: payments whose
  **payment date** falls in the period, on credit orders, excluding the payment made at checkout
  (same day as the order, or a payment row typed as the initial payment). Filter on the payment
  date, not the order date: a debt paid in June for a May order counts in June.
