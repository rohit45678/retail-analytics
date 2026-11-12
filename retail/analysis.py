"""Analysis of retail transaction line items.

Every function takes a cleaned DataFrame (see load_transactions) with columns:
  transaction_id, date (datetime), customer_id, product, category,
  quantity, unit_price, revenue (= quantity * unit_price), month (Period)
"""

import math

import pandas as pd


def load_transactions(path):
    """Load a transactions CSV, clean it, and add revenue/month columns."""
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.dropna(subset=["transaction_id", "customer_id", "product"])
    df = df[(df["quantity"] > 0) & (df["unit_price"] >= 0)]
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    df["month"] = df["date"].dt.to_period("M")
    return df.sort_values("date").reset_index(drop=True)


def monthly_trends(df):
    """Revenue, orders and units per calendar month, with a 3-month moving
    average of revenue."""
    grouped = df.groupby("month").agg(
        revenue=("revenue", "sum"),
        orders=("transaction_id", "nunique"),
        units=("quantity", "sum"),
        customers=("customer_id", "nunique"),
    ).reset_index()
    grouped["revenue"] = grouped["revenue"].round(2)
    grouped["avg_order_value"] = (grouped["revenue"] / grouped["orders"]).round(2)
    grouped["revenue_3mo_avg"] = grouped["revenue"].rolling(3).mean().round(2)
    grouped["month"] = grouped["month"].astype(str)
    return grouped


def top_products(df, n=10):
    """Top products by revenue, with units sold and revenue share."""
    grouped = df.groupby(["product", "category"]).agg(
        revenue=("revenue", "sum"), units=("quantity", "sum"),
        orders=("transaction_id", "nunique"),
    ).reset_index().sort_values("revenue", ascending=False)
    grouped["revenue"] = grouped["revenue"].round(2)
    grouped["revenue_share_pct"] = (grouped["revenue"] / grouped["revenue"].sum() * 100).round(1)
    return grouped.head(n).reset_index(drop=True)


def category_summary(df):
    """Revenue, units, orders and share per category."""
    grouped = df.groupby("category").agg(
        revenue=("revenue", "sum"), units=("quantity", "sum"),
        orders=("transaction_id", "nunique"),
    ).reset_index().sort_values("revenue", ascending=False)
    grouped["revenue"] = grouped["revenue"].round(2)
    grouped["revenue_share_pct"] = (grouped["revenue"] / grouped["revenue"].sum() * 100).round(1)
    return grouped


def customer_patterns(df):
    """Headline purchasing-pattern metrics, returned as a dict."""
    per_txn = df.groupby("transaction_id").agg(
        lines=("product", "count"), units=("quantity", "sum"), spend=("revenue", "sum"))
    per_customer = df.groupby("customer_id").agg(
        transactions=("transaction_id", "nunique"), spend=("revenue", "sum"))
    repeat_customers = int((per_customer["transactions"] > 1).sum())
    return {
        "total_revenue": round(float(df["revenue"].sum()), 2),
        "transactions": int(df["transaction_id"].nunique()),
        "customers": int(df["customer_id"].nunique()),
        "avg_order_value": round(float(per_txn["spend"].mean()), 2),
        "avg_basket_lines": round(float(per_txn["lines"].mean()), 2),
        "avg_basket_units": round(float(per_txn["units"].mean()), 2),
        "repeat_customers": repeat_customers,
        "repeat_rate_pct": round(repeat_customers / len(per_customer) * 100, 1),
    }


def top_customers(df, n=10):
    grouped = df.groupby("customer_id").agg(
        transactions=("transaction_id", "nunique"), spend=("revenue", "sum"),
        units=("quantity", "sum"),
    ).reset_index().sort_values("spend", ascending=False)
    grouped["spend"] = grouped["spend"].round(2)
    return grouped.head(n).reset_index(drop=True)


def _quintile_score(series, higher_is_better=True):
    """Rank-based 1-5 score; robust for any sample size (no qcut edge cases)."""
    ranks = series.rank(method="average", ascending=higher_is_better)
    pct = ranks / len(series)
    return pct.mul(5).apply(math.ceil).clip(1, 5).astype(int)


def _segment(row):
    if row["r_score"] >= 4 and row["f_score"] >= 4:
        return "Champions"
    if row["f_score"] >= 4:
        return "Loyal Customers"
    if row["r_score"] >= 4 and row["f_score"] >= 2:
        return "Potential Loyalists"
    if row["r_score"] <= 2 and row["f_score"] >= 3:
        return "At Risk"
    if row["r_score"] == 1 and row["f_score"] <= 2:
        return "Lost"
    return "Regular"


def rfm_segmentation(df):
    """RFM table: recency (days), frequency (transactions), monetary (spend),
    1-5 scores and a rule-based segment per customer."""
    as_of = df["date"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("customer_id").agg(
        recency=("date", lambda d: (as_of - d.max()).days),
        frequency=("transaction_id", "nunique"),
        monetary=("revenue", "sum"),
    ).reset_index()
    rfm["monetary"] = rfm["monetary"].round(2)
    rfm["r_score"] = _quintile_score(rfm["recency"], higher_is_better=False)
    rfm["f_score"] = _quintile_score(rfm["frequency"])
    rfm["m_score"] = _quintile_score(rfm["monetary"])
    rfm["segment"] = rfm.apply(_segment, axis=1)
    return rfm.sort_values("monetary", ascending=False).reset_index(drop=True)
