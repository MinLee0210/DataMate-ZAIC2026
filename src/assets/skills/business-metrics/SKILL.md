---
name: business-metrics
description: SQL recipes for the rulebook's business terms (valid orders, revenue, order counts, units, averages, shares, growth, customers, debt). Use for any question about money, quantities, orders or customers.
---

# Business metrics

The rulebook (end of this prompt) defines each term; follow it, and the shop-type section when
there is one. These are the ways to compute them on the tables you get.

## Valid orders
- Statuses are written many ways. Look at the distinct values first, then classify them by folded
  text: `replace(strip_accents(lower(status)), 'đ', 'd')` (`strip_accents` keeps `đ`).
  Cancelled: `huy` (`hủy`, `Huỷ đơn`, `Đã hủy`, `cancelled`).
  Returned: `tra` / `hoan` / `doi tra` / `return` (`Trả hàng`, `hàng trả về`, `Đổi trả`,
  `Đã hoàn hàng`). Everything else (done, `xong`, `Thành công`, delivering) is valid.
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

## Averages, shares, growth
- Money averages round to whole VND, half up: `round(x, 0)` on a DECIMAL, not a DOUBLE
  (`round(CAST(x AS DECIMAL(18,4)), 0)`).
- Other averages and percents: 2 decimals. Percent in points: `100.0 * part / total`.
- A group's share divides by the revenue of the **whole shop** in the same period (walk-in orders
  included in the denominator).
- Growth: `100.0 * (current - previous) / previous`, negative when it fell. A difference in
  amounts: `current - compared`, same unit.
- Cancel rate: cancelled orders / **all** orders placed in the period (every status).

## Customers
- With customer codes: one code = one customer; orders without a code (walk-in) are not a
  customer. Without codes: the customer is the name on the order, names differing only in
  spelling (case, accents, spaces) are the same customer; "Khách lẻ" is not a customer.

## Debt
- Debt of an order at day X: order total (after order discount, with shipping) minus payments up
  to the end of day X. Cancelled orders excluded; returned orders still count. COD and
  marketplace orders are not debt.
- Debt age: days from the **order date** to today (an order placed today is 0 days).
