#!/usr/bin/env python3
"""Retail analytics entry point.

  python main.py            generate data (if needed) -> analyze -> report
  python main.py --force    regenerate the sample dataset first

Outputs:
  out/monthly_trends.csv, out/top_products.csv, out/category_summary.csv,
  out/top_customers.csv, out/rfm_segments.csv
  out/monthly_revenue.png, out/category_revenue.png
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from retail import analysis, generate

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "transactions.csv")
OUT = os.path.join(ROOT, "out")


def save(df, name):
    path = os.path.join(OUT, name)
    df.to_csv(path, index=False)
    print(f"  wrote out/{name} ({len(df)} rows)")
    return path


def main():
    parser = argparse.ArgumentParser(description="Retail transaction analytics")
    parser.add_argument("--force", action="store_true", help="regenerate sample data")
    args = parser.parse_args()

    if args.force or not os.path.exists(DATA):
        path, n = generate.write_transactions(DATA)
        print(f"generated {os.path.relpath(path)}: {n} line items")
    df = analysis.load_transactions(DATA)

    os.makedirs(OUT, exist_ok=True)
    trends = analysis.monthly_trends(df)
    products = analysis.top_products(df)
    categories = analysis.category_summary(df)
    patterns = analysis.customer_patterns(df)
    customers = analysis.top_customers(df)
    rfm = analysis.rfm_segmentation(df)

    print("\n== output tables ==")
    save(trends, "monthly_trends.csv")
    save(products, "top_products.csv")
    save(categories, "category_summary.csv")
    save(customers, "top_customers.csv")
    save(rfm, "rfm_segments.csv")

    # Charts
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(trends["month"], trends["revenue"], marker="o", label="Monthly revenue")
    ax.plot(trends["month"], trends["revenue_3mo_avg"], linestyle="--",
            label="3-month moving average")
    ax.set_title("Monthly revenue and trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue ($)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "monthly_revenue.png"), dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(categories["category"], categories["revenue"])
    ax.set_title("Revenue by category")
    ax.set_ylabel("Revenue ($)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "category_revenue.png"), dpi=120)
    plt.close(fig)
    print("  wrote out/monthly_revenue.png")
    print("  wrote out/category_revenue.png")

    # Console report
    print("\n== summary ==")
    print(f"period:            {trends['month'].iloc[0]} to {trends['month'].iloc[-1]}")
    print(f"total revenue:     ${patterns['total_revenue']:,.2f}")
    print(f"transactions:      {patterns['transactions']}")
    print(f"customers:         {patterns['customers']}")
    print(f"avg order value:   ${patterns['avg_order_value']:,.2f}")
    print(f"avg basket:        {patterns['avg_basket_lines']} lines / "
          f"{patterns['avg_basket_units']} units per transaction")
    print(f"repeat customers:  {patterns['repeat_customers']} "
          f"({patterns['repeat_rate_pct']}% of customers bought more than once)")
    best = trends.loc[trends["revenue"].idxmax()]
    print(f"best month:        {best['month']} (${best['revenue']:,.2f})")
    print("\ntop 3 products by revenue:")
    for _, r in products.head(3).iterrows():
        print(f"  {r['product']:<22} ${r['revenue']:>10,.2f}  ({r['revenue_share_pct']}% of revenue)")
    print("\nRFM segments:")
    for segment, count in rfm["segment"].value_counts().items():
        print(f"  {segment:<22} {count} customers")


if __name__ == "__main__":
    main()
