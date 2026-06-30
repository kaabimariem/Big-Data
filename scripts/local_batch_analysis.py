#!/usr/bin/env python3
"""
Local batch analysis (no Hadoop/Spark required) - for quick validation.
"""
import csv
from collections import defaultdict
from pathlib import Path

DATASET = Path(__file__).resolve().parent.parent / "ecommerce_dataset_bigdata.csv"


def main():
    revenue_by_product = defaultdict(float)
    sales_by_category = defaultdict(int)
    qty_by_product = defaultdict(int)
    total_revenue = 0.0

    with open(DATASET, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            price = float(row["price"])
            qty = int(row["quantity"])
            revenue = price * qty
            total_revenue += revenue
            revenue_by_product[row["product"]] += revenue
            sales_by_category[row["category"]] += qty
            qty_by_product[row["product"]] += qty

    print("=== Chiffre d'affaires global ===")
    print(f"TOTAL: {total_revenue:,.2f} EUR\n")

    print("=== Chiffre d'affaires par produit ===")
    for product, rev in sorted(revenue_by_product.items(), key=lambda x: -x[1]):
        print(f"  {product:15s} {rev:>12,.2f} EUR")

    print("\n=== Ventes par categorie ===")
    for cat, qty in sorted(sales_by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat:15s} {qty:>6d} unites")

    print("\n=== Top produits ===")
    for product, qty in sorted(qty_by_product.items(), key=lambda x: -x[1]):
        print(f"  {product:15s} {qty:>6d} unites")


if __name__ == "__main__":
    main()
