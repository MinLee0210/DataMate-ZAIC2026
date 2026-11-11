# Phase 0: question families and their current precision

Train questions: 3000. Dev500: 500.

| family | train n | share | dev n | correct | wrong | abstain | precision |
|---|---|---|---|---|---|---|---|
| revenue_plain | 868 | 28.9 % | 145 | 99 | 26 | 20 | 0.79
| other | 478 | 15.9 % | 79 | 55 | 9 | 15 | 0.86
| count_orders | 206 | 6.9 % | 37 | 28 | 8 | 1 | 0.78
| count_qty | 156 | 5.2 % | 39 | 15 | 9 | 15 | 0.62
| difference_amount | 114 | 3.8 % | 17 | 6 | 3 | 8 | 0.67
| count_cancelled | 108 | 3.6 % | 17 | 16 | 1 | 0 | 0.94
| cancel_rate | 100 | 3.3 % | 14 | 12 | 1 | 1 | 0.92
| share_by_group | 97 | 3.2 % | 13 | 7 | 4 | 2 | 0.64
| top_items | 87 | 2.9 % | 14 | 6 | 1 | 7 | 0.86
| growth_percent | 85 | 2.8 % | 11 | 6 | 1 | 4 | 0.86
| unanswerable | 70 | 2.3 % | 9 | 9 | 0 | 0 | 1.00
| count_items | 60 | 2.0 % | 9 | 2 | 5 | 2 | 0.29
| string_other | 56 | 1.9 % | 12 | 10 | 1 | 1 | 0.91
| count_threshold_orders | 47 | 1.6 % | 6 | 3 | 3 | 0 | 0.50
| date_other | 46 | 1.5 % | 9 | 7 | 2 | 0 | 0.78
| avg_order | 43 | 1.4 % | 6 | 3 | 2 | 1 | 0.60
| import_total | 35 | 1.2 % | 7 | 7 | 0 | 0 | 1.00
| count_customers | 31 | 1.0 % | 3 | 1 | 1 | 1 | 0.50
| import_avg_price | 31 | 1.0 % | 4 | 1 | 1 | 2 | 0.50
| list_other | 31 | 1.0 % | 9 | 0 | 1 | 8 | 0.00
| stock_qty | 30 | 1.0 % | 5 | 2 | 1 | 2 | 0.67
| price_on_date | 29 | 1.0 % | 2 | 2 | 0 | 0 | 1.00
| revenue_by_item | 28 | 0.9 % | 4 | 4 | 0 | 0 | 1.00
| revenue_by_customer | 27 | 0.9 % | 5 | 0 | 2 | 3 | 0.00
| debt_paid | 20 | 0.7 % | 2 | 0 | 1 | 1 | 0.00
| revenue_by_channel | 19 | 0.6 % | 6 | 1 | 1 | 4 | 0.50
| debt_total | 19 | 0.6 % | 2 | 1 | 1 | 0 | 0.50
| revenue_by_payment | 18 | 0.6 % | 5 | 1 | 0 | 4 | 1.00
| debt_by_customer | 16 | 0.5 % | 2 | 1 | 1 | 0 | 0.50
| revenue_by_group | 14 | 0.5 % | 2 | 2 | 0 | 0 | 1.00
| list_items | 11 | 0.4 % | 0 | 0 | 0 | 0 | 0.00
| price_change_effect | 7 | 0.2 % | 2 | 0 | 1 | 1 | 0.00
| expiry_list | 6 | 0.2 % | 1 | 0 | 0 | 1 | 0.00
| top_customers | 3 | 0.1 % | 1 | 0 | 0 | 1 | 0.00
| revenue_by_staff | 1 | 0.0 % | 0 | 0 | 0 | 0 | 0.00
| avg_price | 1 | 0.0 % | 0 | 0 | 0 | 0 | 0.00
| list_customers | 1 | 0.0 % | 1 | 0 | 0 | 1 | 0.00
| best_day | 1 | 0.0 % | 0 | 0 | 0 | 0 | 0.00

## Coverage

- 50 % of train is covered by the top families up to `count_orders`.
- 70 % of train is covered by the top families up to `share_by_group`.
- 80 % of train is covered by the top families up to `count_items`.
- 90 % of train is covered by the top families up to `import_avg_price`.
- 95 % of train is covered by the top families up to `revenue_by_customer`.

## Reading

`precision` is the current k=1 pipeline on the 500 dev questions in that family.
A family worth compiling has a large dev n and precision well below 1.0; the ceiling of
compiling it is its dev share, not its precision.
