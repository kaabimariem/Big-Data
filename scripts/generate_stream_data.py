#!/usr/bin/env python3
"""
Simulates real-time e-commerce transactions by writing CSV batches
to the Spark streaming input directory.
"""
import csv
import random
import time
import argparse
from datetime import datetime
from pathlib import Path

PRODUCTS = [
    ("Phone", "Electronics", 800),
    ("Laptop", "Electronics", 1200),
    ("Headphones", "Electronics", 150),
    ("Tshirt", "Clothing", 25),
    ("Jeans", "Clothing", 60),
    ("Shoes", "Clothing", 90),
    ("Book", "Education", 20),
]

HEADER = ["transaction_id", "date", "product", "category", "price", "quantity", "client_id"]


def generate_transaction(tx_id):
    product, category, price = random.choice(PRODUCTS)
    return {
        "transaction_id": str(tx_id),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product": product,
        "category": category,
        "price": price,
        "quantity": random.randint(1, 5),
        "client_id": str(random.randint(1000, 9999)),
    }


def write_batch(output_dir: Path, batch_num: int, batch_size: int, start_id: int):
    file_path = output_dir / f"batch_{batch_num:04d}.csv"
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        for i in range(batch_size):
            writer.writerow(generate_transaction(start_id + i))
    print(f"Ecrit: {file_path} ({batch_size} transactions)")


def main():
    parser = argparse.ArgumentParser(description="Generate streaming CSV batches")
    parser.add_argument("--output", default="stream_input", help="Output directory")
    parser.add_argument("--batch-size", type=int, default=20, help="Transactions per batch")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between batches")
    parser.add_argument("--batches", type=int, default=0, help="Max batches (0 = infinite)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    tx_id = 1
    batch_num = 1

    print(f"Generation de flux vers {output_dir}/")
    print(f"Taille batch: {args.batch_size}, intervalle: {args.interval}s")

    try:
        while args.batches == 0 or batch_num <= args.batches:
            write_batch(output_dir, batch_num, args.batch_size, tx_id)
            tx_id += args.batch_size
            batch_num += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nArret.")


if __name__ == "__main__":
    main()
