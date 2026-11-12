"""Deterministic sample-data generator.

Creates data/transactions.csv: one row per transaction line item with
  transaction_id, date, customer_id, product, category, quantity, unit_price

The generator is seeded, so the dataset (and therefore every analysis result)
is reproducible. Volume follows a mild upward trend across 2025 with a
December seasonality bump, the way a growing retailer's data would look.
"""

import csv
import os
import random
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "data", "transactions.csv")

PRODUCTS = [
    # (product, category, unit_price, popularity weight)
    ("Wireless Headphones", "Electronics", 79.99, 10),
    ("Bluetooth Speaker", "Electronics", 49.99, 8),
    ("USB-C Cable", "Electronics", 14.99, 12),
    ("T-Shirt", "Clothing", 24.99, 11),
    ("Hoodie", "Clothing", 59.99, 7),
    ("Sneakers", "Clothing", 89.99, 6),
    ("Coffee Mug", "Home", 12.99, 9),
    ("Desk Lamp", "Home", 34.99, 6),
    ("Plant Pot", "Home", 19.99, 5),
    ("Coffee Beans 500g", "Grocery", 16.99, 10),
    ("Olive Oil 750ml", "Grocery", 11.99, 7),
    ("Pasta Pack", "Grocery", 6.99, 9),
]

NUM_CUSTOMERS = 140
NUM_TRANSACTIONS = 1100
SEED = 42

# Relative transaction volume per month: growth trend + December bump.
MONTH_WEIGHTS = [0.80, 0.82, 0.88, 0.90, 0.95, 1.00, 1.02, 1.05, 1.08, 1.12, 1.18, 1.45]


def generate_transactions(seed=SEED):
    """Return a list of transaction line-item dicts (deterministic)."""
    rng = random.Random(seed)
    product_names = [p[0] for p in PRODUCTS]
    weights = [p[3] for p in PRODUCTS]
    catalog = {p[0]: (p[1], p[2]) for p in PRODUCTS}
    customers = [f"CUST-{i:03d}" for i in range(1, NUM_CUSTOMERS + 1)]
    # A minority of customers shop much more often than the rest.
    customer_weights = [10 if i < 25 else (5 if i < 70 else 2) for i in range(NUM_CUSTOMERS)]

    rows = []
    start = date(2025, 1, 1)
    for txn_no in range(1, NUM_TRANSACTIONS + 1):
        month = rng.choices(range(12), weights=MONTH_WEIGHTS)[0]
        day = rng.randint(1, 28)
        txn_date = date(2025, month + 1, day)
        if txn_date < start:
            txn_date = start
        customer = rng.choices(customers, weights=customer_weights)[0]
        num_items = rng.choices([1, 2, 3, 4], weights=[35, 35, 20, 10])[0]
        chosen = rng.choices(product_names, weights=weights, k=num_items)
        for product in dict.fromkeys(chosen):  # one line per distinct product
            category, price = catalog[product]
            rows.append({
                "transaction_id": f"T{txn_no:05d}",
                "date": txn_date.isoformat(),
                "customer_id": customer,
                "product": product,
                "category": category,
                "quantity": rng.choices([1, 2, 3], weights=[70, 22, 8])[0],
                "unit_price": f"{price:.2f}",
            })
    rows.sort(key=lambda r: (r["date"], r["transaction_id"]))
    return rows


def write_transactions(path=DEFAULT_PATH, seed=SEED):
    rows = generate_transactions(seed)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path, len(rows)
