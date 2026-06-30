#!/usr/bin/env python3
"""
Genere le dataset e-commerce pour le projet Big Data.
1 000 000 lignes par defaut avec profils clients realistes.

Usage:
  python scripts/generate_dataset.py
  python scripts/generate_dataset.py --rows 1000000 --output big_dataset.csv
"""
import argparse
import csv
import random
from datetime import datetime, timedelta

# ── Catalogue produits (nom, categorie, prix_base) ────────────────────────────
PRODUCTS = [
    # Electronics
    ("Phone",         "Electronics",  800),
    ("Laptop",        "Electronics", 1200),
    ("Tablet",        "Electronics",  500),
    ("Headphones",    "Electronics",  150),
    ("Smartwatch",    "Electronics",  350),
    ("Camera",        "Electronics",  900),
    ("TV",            "Electronics", 1500),
    ("Speaker",       "Electronics",  200),
    # Clothing
    ("Tshirt",        "Clothing",      25),
    ("Jeans",         "Clothing",      60),
    ("Shoes",         "Clothing",      90),
    ("Jacket",        "Clothing",     120),
    ("Dress",         "Clothing",      80),
    ("Shorts",        "Clothing",      35),
    # Education
    ("Book",          "Education",     20),
    ("Course",        "Education",    150),
    ("Notebook",      "Education",     10),
    ("Pen Set",       "Education",      5),
    # Food
    ("Coffee",        "Food",          15),
    ("Tea",           "Food",          12),
    ("Protein Bar",   "Food",           3),
    ("Vitamins",      "Food",          30),
    # Sport
    ("Running Shoes", "Sport",        110),
    ("Yoga Mat",      "Sport",         45),
    ("Dumbbells",     "Sport",         80),
    ("Bicycle",       "Sport",        600),
]

# Poids de popularite par produit (certains se vendent plus)
PRODUCT_WEIGHTS = [
    12, 10, 7, 8, 5, 4, 3, 6,   # Electronics
    9,  7, 8, 5, 4, 5,           # Clothing
    6,  5, 4, 3,                  # Education
    5,  4, 3, 3,                  # Food
    4,  3, 3, 2,                  # Sport
]

# ── Segments clients ──────────────────────────────────────────────────────────
CLIENT_SEGMENTS = {
    "standard":  {"count": 80000,  "qty_max": 3,  "freq": 10},   # 80k clients standard
    "premium":   {"count": 15000,  "qty_max": 7,  "freq": 25},   # 15k clients premium
    "business":  {"count":  5000,  "qty_max": 20, "freq": 60},   # 5k clients business
}

HEADER = [
    "transaction_id", "date", "product", "category",
    "price", "quantity", "client_id",
    "client_segment", "discount_pct", "total_amount",
    "city", "country"
]

# Villes / pays
LOCATIONS = [
    ("Paris",       "France"),
    ("Lyon",        "France"),
    ("Marseille",   "France"),
    ("Tunis",       "Tunisia"),
    ("Sfax",        "Tunisia"),
    ("Sousse",      "Tunisia"),
    ("Casablanca",  "Morocco"),
    ("Rabat",       "Morocco"),
    ("Alger",       "Algeria"),
    ("Montreal",    "Canada"),
    ("Bruxelles",   "Belgium"),
    ("Geneve",      "Switzerland"),
]
LOCATION_WEIGHTS = [15, 8, 7, 12, 6, 5, 8, 4, 5, 4, 3, 3]


def build_client_pool():
    """Genere un pool de clients avec segment et ville assignes."""
    pool = []
    cid = 1000
    for segment, cfg in CLIENT_SEGMENTS.items():
        for _ in range(cfg["count"]):
            city, country = random.choices(LOCATIONS, weights=LOCATION_WEIGHTS, k=1)[0]
            pool.append({
                "client_id": cid,
                "segment": segment,
                "qty_max": cfg["qty_max"],
                "city": city,
                "country": country,
            })
            cid += 1
    return pool


def random_date(year: int) -> str:
    start = datetime(year, 1, 1)
    end   = datetime(year, 12, 31, 23, 59, 59)
    delta = end - start
    return (start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def price_with_variation(base: float) -> float:
    """Prix +/- 5% pour simuler des variations."""
    return round(base * random.uniform(0.95, 1.05), 2)


def generate_rows(count: int, client_pool: list):
    """Genere `count` transactions."""
    for i in range(1, count + 1):
        client = random.choice(client_pool)
        segment = client["segment"]

        # Produit selon popularite
        product, category, base_price = random.choices(PRODUCTS, weights=PRODUCT_WEIGHTS, k=1)[0]
        price = price_with_variation(base_price)

        # Quantite selon segment
        quantity = random.randint(1, client["qty_max"])

        # Remise selon segment
        if segment == "business":
            discount = random.choice([0, 5, 10, 15, 20])
        elif segment == "premium":
            discount = random.choice([0, 0, 5, 10])
        else:
            discount = random.choice([0, 0, 0, 5])

        total = round(price * quantity * (1 - discount / 100), 2)

        # Date sur 2 ans (2025-2026)
        year = random.choice([2025, 2026])

        yield {
            "transaction_id": i,
            "date":           random_date(year),
            "product":        product,
            "category":       category,
            "price":          price,
            "quantity":       quantity,
            "client_id":      client["client_id"],
            "client_segment": segment,
            "discount_pct":   discount,
            "total_amount":   total,
            "city":           client["city"],
            "country":        client["country"],
        }


def main():
    parser = argparse.ArgumentParser(description="Generer dataset e-commerce Big Data")
    parser.add_argument("--rows",   type=int, default=1_000_000, help="Nb de transactions (defaut: 1 000 000)")
    parser.add_argument("--output", default="ecommerce_dataset_bigdata.csv", help="Fichier CSV de sortie")
    args = parser.parse_args()

    print(f"Generation de {args.rows:,} transactions...")
    print("Construction du pool clients (100 000 clients)...")
    client_pool = build_client_pool()
    print(f"  {len(client_pool):,} clients generes "
          f"(standard={80000}, premium={15000}, business={5000})")

    print(f"Ecriture vers {args.output} ...")
    written = 0
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()

        BATCH = 50_000
        for row in generate_rows(args.rows, client_pool):
            writer.writerow(row)
            written += 1
            if written % BATCH == 0:
                pct = written / args.rows * 100
                print(f"  {written:>10,} / {args.rows:,}  ({pct:.0f}%)")

    print(f"\nDataset cree : {args.output}")
    print(f"Lignes        : {written:,}")
    print(f"Colonnes      : {', '.join(HEADER)}")
    print(f"\nSegments clients:")
    print(f"  standard  : 80 000 clients  (quantite max 3,  remise 0-5%)")
    print(f"  premium   : 15 000 clients  (quantite max 7,  remise 0-10%)")
    print(f"  business  :  5 000 clients  (quantite max 20, remise 0-20%)")
    print(f"\nProduits : {len(PRODUCTS)} produits dans 5 categories")
    print(f"Pays     : France, Tunisie, Maroc, Algerie, Canada, Belgique, Suisse")


if __name__ == "__main__":
    main()
