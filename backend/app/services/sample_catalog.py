"""Deterministic fictional billing history for the sample kirana."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

PRODUCTS = [
    {
        "sku": "BUTTER-100",
        "name": "Amul Butter 100g",
        "category": "Dairy",
        "price": 60,
        "cost": 52,
        "stock": 24,
        "min_stock": 12,
        "lead": 3,
        "pack": 10,
        "moq": 10,
        "supplier": "City Dairy Supply",
        "pattern": "steady",
    },
    {
        "sku": "SALT-1",
        "name": "Tata Salt 1kg",
        "category": "Grocery",
        "price": 28,
        "cost": 22,
        "stock": 40,
        "min_stock": 16,
        "lead": 2,
        "pack": 20,
        "moq": 20,
        "supplier": "Metro Wholesale",
        "pattern": "steady_low",
    },
    {
        "sku": "PARLE-800",
        "name": "Parle-G 800g",
        "category": "Grocery",
        "price": 90,
        "cost": 78,
        "stock": 18,
        "min_stock": 10,
        "lead": 4,
        "pack": 12,
        "moq": 12,
        "supplier": "Metro Wholesale",
        "pattern": "weekend",
    },
    {
        "sku": "AGAR-01",
        "name": "Cycle Agarbatti",
        "category": "Pooja",
        "price": 45,
        "cost": 30,
        "stock": 16,
        "min_stock": 8,
        "lead": 5,
        "pack": 10,
        "moq": 10,
        "supplier": "Pooja Traders",
        "pattern": "rising",
    },
    {
        "sku": "RAIN-M",
        "name": "Raincoat Medium",
        "category": "Seasonal",
        "price": 350,
        "cost": 260,
        "stock": 11,
        "min_stock": 2,
        "lead": 7,
        "pack": 1,
        "moq": 1,
        "supplier": "Monsoon Goods",
        "pattern": "falling",
    },
    {
        "sku": "ORS-01",
        "name": "ORS Sachet",
        "category": "Medical",
        "price": 22,
        "cost": 15,
        "stock": 30,
        "min_stock": 12,
        "lead": 2,
        "pack": 10,
        "moq": 10,
        "supplier": "Neighbourhood Pharma",
        "pattern": "intermittent",
    },
    {
        "sku": "BAR-01",
        "name": "Protein Bar",
        "category": "New",
        "price": 80,
        "cost": 55,
        "stock": 10,
        "min_stock": 4,
        "lead": 6,
        "pack": 6,
        "moq": 6,
        "supplier": "City Dairy Supply",
        "pattern": "new",
    },
    {
        "sku": "OIL-01",
        "name": "Ayurvedic Hair Oil",
        "category": "Slow",
        "price": 180,
        "cost": 120,
        "stock": 8,
        "min_stock": 2,
        "lead": 10,
        "pack": 1,
        "moq": 1,
        "supplier": "Neighbourhood Pharma",
        "pattern": "sparse",
    },
    {
        "sku": "MAGGI-70",
        "name": "Maggi 70g",
        "category": "Grocery",
        "price": 14,
        "cost": 11,
        "stock": 48,
        "min_stock": 24,
        "lead": 2,
        "pack": 24,
        "moq": 24,
        "supplier": "Metro Wholesale",
        "pattern": "stockout",
    },
]

START = date(2026, 7, 1)
END = date(2026, 10, 12)
STOCKOUT_START = date(2026, 9, 1)
STOCKOUT_END = date(2026, 9, 10)
SPARSE_DAYS = {date(2026, 7, 3), date(2026, 7, 28), date(2026, 8, 20), date(2026, 9, 18)}
COLUMNS = [
    "date",
    "invoice_number",
    "product_name",
    "sku",
    "category",
    "quantity",
    "selling_price",
    "unit_cost",
    "current_stock",
    "in_stock",
    "supplier",
    "lead_time_days",
    "pack_size",
    "moq",
    "min_stock",
]


def _qty(pattern: str, day: date, index: int, total: int) -> tuple[int, str]:
    weekend = day.weekday() >= 5
    progress = index / max(total - 1, 1)
    if pattern == "steady":
        return (7 if weekend else 5), "yes"
    if pattern == "steady_low":
        return 4, "yes"
    if pattern == "weekend":
        return (9 if weekend else 6), "yes"
    if pattern == "rising":
        return max(1, round(2 + 7 * progress)), "yes"
    if pattern == "falling":
        return max(0, round(6 * (1 - progress))), "yes"
    if pattern == "intermittent":
        return (4, "yes") if day.toordinal() % 6 == 0 else (0, "yes")
    if pattern == "new":
        return (2, "yes") if day >= date(2026, 10, 1) else (0, "yes")
    if pattern == "sparse":
        return (1, "yes") if day in SPARSE_DAYS else (0, "yes")
    if pattern == "stockout":
        if STOCKOUT_START <= day <= STOCKOUT_END:
            return 0, "no"
        return (11 if weekend else 8), "yes"
    return 0, "yes"


def generate_rows() -> list[dict]:
    days = []
    cursor = START
    while cursor <= END:
        days.append(cursor)
        cursor += timedelta(days=1)
    total = len(days)
    rows: list[dict] = []
    last_index = {product["sku"]: None for product in PRODUCTS}
    for index, day in enumerate(days):
        invoice = f"INV-{day.strftime('%Y%m%d')}"
        for product in PRODUCTS:
            quantity, in_stock = _qty(product["pattern"], day, index, total)
            if quantity == 0 and in_stock == "yes":
                continue
            row = {
                "date": day.isoformat(),
                "invoice_number": invoice,
                "product_name": product["name"],
                "sku": product["sku"],
                "category": product["category"],
                "quantity": quantity,
                "selling_price": product["price"],
                "unit_cost": product["cost"],
                "current_stock": "",
                "in_stock": in_stock,
                "supplier": product["supplier"],
                "lead_time_days": product["lead"],
                "pack_size": product["pack"],
                "moq": product["moq"],
                "min_stock": product["min_stock"],
            }
            rows.append(row)
            last_index[product["sku"]] = len(rows) - 1
    for product in PRODUCTS:
        pointer = last_index[product["sku"]]
        if pointer is not None:
            rows[pointer]["current_stock"] = product["stock"]
    return rows


def write_csv(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_rows()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
