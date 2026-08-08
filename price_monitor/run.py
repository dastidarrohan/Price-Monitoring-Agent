"""CLI entrypoint: python run.py products.json

Runs the price-monitoring agent over a list of products and prints a
summary of successes/failures. Meant to be run manually or on a schedule
(cron, GitHub Actions, Colab scheduled cell).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from price_monitor.agent import Product, run_monitor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def load_products(path: str) -> list[Product]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [Product(name=item["name"], url=item["url"]) for item in raw]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run competitor price monitoring.")
    parser.add_argument(
        "products_file",
        nargs="?",
        default="products.json",
        help="Path to a JSON file with [{\"name\": ..., \"url\": ...}, ...]",
    )
    args = parser.parse_args()

    products = load_products(args.products_file)
    if not products:
        print("No products to check.")
        sys.exit(1)

    results = run_monitor(products)

    print("\n=== Summary ===")
    ok = sum(1 for v in results.values() if v == "ok")
    for name, status in results.items():
        marker = "✓" if status == "ok" else "✗"
        print(f"{marker} {name}: {status}")
    print(f"\n{ok}/{len(results)} products checked successfully.")


if __name__ == "__main__":
    main()
