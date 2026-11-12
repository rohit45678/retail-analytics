#!/usr/bin/env python3
"""Plain-assert test suite (no pytest dependency).

Run:  python tests/run_tests.py

Aggregate expectations are hand-computed from tests/fixture.csv:
  revenue by row: 20 + 30 + 10 + 20 + 30 + 60 = 170
  months: 2025-01 = 60 (2 orders), 2025-02 = 110 (3 orders)
  products: Gadget 90, Widget 60, Mug 20
  RFM as-of 2025-02-16 (max date + 1 day):
    C1 recency 14, frequency 2, monetary 70
    C2 recency  1, frequency 2, monetary 70
    C3 recency  6, frequency 1, monetary 30
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retail import analysis, generate

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixture.csv")


def load_fixture():
    return analysis.load_transactions(FIXTURE)


def test_monthly_totals():
    trends = analysis.monthly_trends(load_fixture())
    by_month = dict(zip(trends["month"], trends["revenue"]))
    assert by_month == {"2025-01": 60.0, "2025-02": 110.0}, by_month
    orders = dict(zip(trends["month"], trends["orders"]))
    assert orders == {"2025-01": 2, "2025-02": 3}, orders


def test_top_products_and_categories():
    df = load_fixture()
    products = analysis.top_products(df)
    assert list(products["product"]) == ["Gadget", "Widget", "Mug"]
    assert list(products["revenue"]) == [90.0, 60.0, 20.0]
    cats = analysis.category_summary(df)
    by_cat = dict(zip(cats["category"], cats["revenue"]))
    assert by_cat == {"Electronics": 150.0, "Home": 20.0}, by_cat


def test_customer_patterns():
    p = analysis.customer_patterns(load_fixture())
    assert p["total_revenue"] == 170.0, p
    assert p["transactions"] == 5 and p["customers"] == 3, p
    assert p["avg_order_value"] == 34.0, p
    assert p["avg_basket_lines"] == 1.2, p
    assert p["avg_basket_units"] == 2.6, p
    assert p["repeat_customers"] == 2 and p["repeat_rate_pct"] == 66.7, p


def test_rfm_values():
    rfm = analysis.rfm_segmentation(load_fixture()).set_index("customer_id")
    assert (rfm.loc["C1", "recency"], rfm.loc["C1", "frequency"], rfm.loc["C1", "monetary"]) == (14, 2, 70.0)
    assert (rfm.loc["C2", "recency"], rfm.loc["C2", "frequency"], rfm.loc["C2", "monetary"]) == (1, 2, 70.0)
    assert (rfm.loc["C3", "recency"], rfm.loc["C3", "frequency"], rfm.loc["C3", "monetary"]) == (6, 1, 30.0)
    assert rfm["segment"].notna().all()
    assert rfm.loc["C2", "r_score"] > rfm.loc["C1", "r_score"]  # bought more recently


def test_generator_is_deterministic_and_sized():
    import tempfile
    rows_a = generate.generate_transactions()
    rows_b = generate.generate_transactions()
    assert rows_a == rows_b, "generator must be deterministic for a fixed seed"
    assert 2000 <= len(rows_a) <= 5000, f"expected ~2-5k line items, got {len(rows_a)}"
    with tempfile.TemporaryDirectory() as tmp:
        path, n = generate.write_transactions(os.path.join(tmp, "tx.csv"))
        assert n == len(rows_a)
        df = analysis.load_transactions(path)
        assert len(df) == n
        assert set(df["category"]) == {"Electronics", "Clothing", "Home", "Grocery"}
        patterns = analysis.customer_patterns(df)
        assert patterns["transactions"] == generate.NUM_TRANSACTIONS, patterns


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\n{len(tests)} tests passed")
