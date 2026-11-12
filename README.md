# Retail Analytics — Customer Transactions & Product Sales
Analysis of a large customer-transaction and product-sales dataset: data cleaning, exploration of purchasing behavior, and sales-trend analysis to identify patterns and support data-driven decisions. Challenges included inconsistent source data and selecting the metrics that mattered.
**Tech stack:** Python, Pandas
**Highlights:** transaction data cleaning at scale; purchasing-pattern analysis; sales-trend reporting.

Implemented with Python + Pandas + Matplotlib. The pipeline generates a reproducible sample dataset (seeded, ~2,150 transaction line items across 1,100 transactions and 135 customers in 2025) and runs the full analysis end to end — swap in a real transactions CSV with the same columns and everything works unchanged.

## What it analyzes

- **Sales trends** — monthly revenue, orders, units and average order value, with a 3-month moving average to smooth seasonality.
- **Top products & categories** — revenue, units, order counts and revenue share, so the catalog's revenue drivers are explicit.
- **Purchasing patterns** — repeat-customer rate, average basket size (lines and units per transaction), average order value, top customers by spend.
- **RFM segmentation** — every customer scored 1–5 on Recency, Frequency and Monetary value (rank-based quintiles) and assigned a segment: Champions, Loyal Customers, Potential Loyalists, Regular, At Risk, Lost.

## How to run

```bash
pip install -r requirements.txt
python main.py            # generate data if needed -> analyze -> report
python main.py --force    # regenerate the sample dataset first
```

Outputs land in `out/`: five CSV tables (`monthly_trends`, `top_products`, `category_summary`, `top_customers`, `rfm_segments`) and two charts (`monthly_revenue.png`, `category_revenue.png`).

## Sample output

```
== summary ==
period:            2025-01 to 2025-12
total revenue:     $98,773.60
transactions:      1100
customers:         135
avg order value:   $89.79
avg basket:        1.96 lines / 2.67 units per transaction
repeat customers:  125 (92.6% of customers bought more than once)
best month:        2025-12 ($13,957.82)

top 3 products by revenue:
  Wireless Headphones    $ 23,597.05  (23.9% of revenue)
  Sneakers               $ 14,488.39  (14.7% of revenue)
  Hoodie                 $ 13,437.76  (13.6% of revenue)

RFM segments:
  Champions              34 customers
  Loyal Customers        19 customers
  Potential Loyalists    22 customers
  Regular                26 customers
  At Risk                15 customers
  Lost                   19 customers
```

## Data model

`data/transactions.csv` — one row per transaction line item:

| column | meaning |
|---|---|
| `transaction_id` | basket identifier (a transaction has 1+ line items) |
| `date` | transaction date |
| `customer_id` | customer identifier |
| `product` / `category` | catalog item and its category |
| `quantity` / `unit_price` | line-item quantity and price (revenue = quantity × unit_price) |

## Tests

```bash
python tests/run_tests.py
```

Plain-assert suite (no pytest needed). Aggregate expectations are hand-computed from a tiny fixed fixture (`tests/fixture.csv`): monthly totals, top-product ranking, basket/repeat-rate metrics, exact RFM values, plus generator determinism and size checks.

## Project layout

```
main.py              entry point: generate -> analyze -> report + charts
retail/
  generate.py        seeded sample-data generator (deterministic)
  analysis.py        cleaning, trends, top products, basket metrics, RFM
data/                generated transactions.csv (git-ignored)
out/                 generated result tables and charts (git-ignored)
tests/
  fixture.csv        tiny hand-checked dataset
  run_tests.py       test suite
```
