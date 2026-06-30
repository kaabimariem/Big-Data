#!/usr/bin/env python3
"""
Genere le dataset e-commerce pour le projet Big Data.
Usage: python scripts/generate_dataset.py
       python scripts/generate_dataset.py --rows 5000 --output data.csv
"""
import argparse
import csv
import random
from datetime import datetime, timedelta

PRODUCTS = [
    ("Phone", "Electronics", 800),
    ("Laptop", "Electronics", 1200),
    ("Headphones", "Electronics", 150),
    ("Tablet", "Electronics", 500),
    ("Tshirt", "Clothing", 25),
    ("Jeans", "Clothing", 60),
    ("Shoes", "Clothing", 90),
    ("Jacket", "Clothing", 120),
    ("Book", "Education", 20),
    ("Course", "Education", 150),
]

HEADER = ["transaction_id", "date", "product", "category", "price", "quantity", "client_id"]


def random_date(start: datetime, end: datetime) -> str:
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return (start + timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")


def generate_rows(count: int):
    start = datetime(2026, 6, 1)
    end = datetime(2025, 6, 30, 23, 59, 59)
    for i in range(1, count + 1):
        product, category, price = random.choice(PRODUCTS)
        yield {
            "transaction_id": str(i),
            "date": random_date(start, end),
            "product": product,
            "category": category,
            "price": price,
            "quantity": random.randint(1, 5),
            "client_id": str(random.randint(1000, 9999)),
        }


def main():
    parser = argparse.ArgumentParser(description="Generer dataset e-commerce")
    parser.add_argument("--rows", type=int, default=1000, help="Nombre de transactions")
    parser.add_argument(
        "--output",
        default="ecommerce_dataset_bigdata.csv",
        help="Fichier CSV de sortie",
    )
    args = parser.parse_args()

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(generate_rows(args.rows))

    print(f"Dataset cree: {args.output} ({args.rows} lignes)")


if __name__ == "__main__":
    main()
