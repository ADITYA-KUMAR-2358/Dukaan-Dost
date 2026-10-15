"""CSV parsing for small-shop billing exports.

Dates are read day-first when the text is ambiguous (03/04/2026 is 3 April).
Rows are never dropped silently: each problem is returned with a row number.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

ALIASES: dict[str, tuple[str, ...]] = {
    "date": ("date", "bill date", "invoice date", "sale date", "txn date", "bill_date"),
    "invoice_number": ("invoice", "invoice no", "invoice number", "bill no", "bill number", "voucher"),
    "product_name": ("product", "item", "item name", "product name", "product_name", "particulars", "name"),
    "sku": ("sku", "item code", "product code", "barcode", "code"),
    "quantity": ("qty", "quantity", "qty sold", "units", "qty_sold"),
    "selling_price": ("price", "rate", "selling price", "mrp", "unit price", "selling_price"),
    "unit_cost": ("cost", "unit cost", "purchase price", "cost price", "unit_cost"),
    "purchase_amount": ("amount", "line total", "total", "purchase amount"),
    "discount": ("discount", "disc"),
    "returned_quantity": ("return", "returned qty", "return qty", "returned quantity"),
    "current_stock": ("stock", "current stock", "current_stock", "closing stock", "qty on hand"),
    "category": ("category", "department"),
    "in_stock": ("in stock", "in_stock", "availability", "available"),
    "supplier_name": ("supplier", "supplier name", "supplier_name"),
    "lead_time_days": ("lead time", "lead time days", "lead_time_days"),
    "pack_size": ("pack size", "pack_size"),
    "moq": ("moq", "minimum order", "minimum order qty"),
    "min_stock": ("min stock", "min_stock", "minimum stock", "reorder level"),
}

REQUIRED = ("date", "quantity")
IDENTITY = ("product_name", "sku")


@dataclass
class ParsedRow:
    row_number: int
    data: dict
    fingerprint: str


@dataclass
class RowIssue:
    row_number: int
    code: str
    message: str


@dataclass
class ParseResult:
    encoding: str
    delimiter: str
    columns: list[str]
    mapping: dict[str, str | None]
    rows: list[ParsedRow] = field(default_factory=list)
    issues: list[RowIssue] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    content_hash: str = ""
    duplicate_in_file: int = 0


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def suggest_mapping(columns: list[str]) -> dict[str, str | None]:
    lookup = {_norm(col): col for col in columns}
    mapping: dict[str, str | None] = {}
    used: set[str] = set()
    for field_name, aliases in ALIASES.items():
        found = None
        for alias in aliases:
            if alias in lookup and lookup[alias] not in used:
                found = lookup[alias]
                used.add(found)
                break
        mapping[field_name] = found
    return mapping


def _decode(raw: bytes) -> tuple[str, str, list[str]]:
    assumptions: list[str] = []
    if raw.startswith(b"\x89PNG") or raw.startswith(b"%PDF") or raw.startswith(b"PK"):
        raise ValueError("This file is not a CSV. Photos and PDFs are not read in this version.")
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw.decode(encoding), encoding, assumptions
        except UnicodeDecodeError:
            continue
    assumptions.append("The file was not valid UTF-8 or Windows-1252, so it was read as Latin-1.")
    return raw.decode("latin-1"), "latin-1", assumptions


def _delimiter(text: str) -> str:
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        if sample.count(";") > sample.count(","):
            return ";"
        return ","


def _number(value: str) -> float | None:
    cleaned = value.strip().replace(",", "")
    cleaned = cleaned.replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
    if cleaned == "":
        return None
    return float(cleaned)


def _parse_date(value: str):
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _truthy_stock(value: str) -> bool | None:
    text = value.strip().lower()
    if text in {"", "nan"}:
        return None
    if text in {"1", "y", "yes", "true", "in", "available"}:
        return True
    if text in {"0", "n", "no", "false", "out", "stockout"}:
        return False
    return None


def parse_csv(raw: bytes, mapping_override: dict[str, str | None] | None = None) -> ParseResult:
    if not raw or not raw.strip():
        raise ValueError("The file is empty.")
    digest = hashlib.sha256(raw).hexdigest()
    text, encoding, assumptions = _decode(raw)
    if "\n" not in text and "\r" not in text and "," not in text and ";" not in text:
        raise ValueError("The file has no rows to read.")
    delimiter = _delimiter(text)
    frame = pd.read_csv(io.StringIO(text), sep=delimiter, dtype=str, keep_default_na=False)
    if frame.empty or len(frame.columns) == 0:
        raise ValueError("The file has headers but no data rows.")
    columns = [str(col) for col in frame.columns]
    mapping = suggest_mapping(columns)
    if mapping_override:
        for key, value in mapping_override.items():
            if key in mapping:
                mapping[key] = value or None
    assumptions.append(
        "Ambiguous numeric dates are read day-first, which matches common Indian billing exports."
    )
    if mapping["date"] is None or mapping["quantity"] is None:
        assumptions.append("Date and quantity still need a column mapping before import.")
    if mapping["product_name"] is None and mapping["sku"] is None:
        assumptions.append("Map a product name or SKU column before import.")

    result = ParseResult(
        encoding=encoding,
        delimiter=delimiter,
        columns=columns,
        mapping=mapping,
        assumptions=assumptions,
        content_hash=digest,
    )
    seen: set[str] = set()

    def cell(row: pd.Series, field_name: str) -> str:
        column = mapping.get(field_name)
        if not column or column not in row:
            return ""
        return str(row[column]).strip()

    for index, row in frame.iterrows():
        row_number = int(index) + 2
        issues_before = len(result.issues)
        sale_date = _parse_date(cell(row, "date")) if mapping["date"] else None
        if mapping["date"] is None:
            result.issues.append(RowIssue(row_number, "missing_date_column", "Map a date column."))
        elif sale_date is None:
            result.issues.append(
                RowIssue(row_number, "invalid_date", f"Could not read the date '{cell(row, 'date')}'.")
            )
        name = cell(row, "product_name")
        sku = cell(row, "sku")
        if not name and not sku:
            result.issues.append(
                RowIssue(row_number, "missing_product", "Each row needs a product name or SKU.")
            )
        qty_text = cell(row, "quantity")
        try:
            quantity = _number(qty_text) if qty_text else None
        except ValueError:
            quantity = None
            result.issues.append(RowIssue(row_number, "invalid_quantity", "Quantity is not a number."))
        in_stock = _truthy_stock(cell(row, "in_stock")) if mapping["in_stock"] else None
        stockout = in_stock is False
        if quantity is None and mapping["quantity"]:
            result.issues.append(RowIssue(row_number, "invalid_quantity", "Quantity is missing."))
        elif quantity is not None and quantity < 0:
            result.issues.append(RowIssue(row_number, "negative_quantity", "Quantity cannot be negative."))
        elif quantity == 0 and not stockout:
            result.issues.append(
                RowIssue(
                    row_number,
                    "zero_quantity",
                    "Quantity is zero. Use an in-stock value of no only for a real stockout day.",
                )
            )
        returned = 0.0
        returned_text = cell(row, "returned_quantity")
        if returned_text:
            try:
                returned = _number(returned_text) or 0.0
            except ValueError:
                result.issues.append(RowIssue(row_number, "invalid_return", "Returned quantity is not a number."))
            if returned < 0:
                result.issues.append(RowIssue(row_number, "negative_return", "Returned quantity cannot be negative."))
            if quantity is not None and returned > quantity:
                result.issues.append(
                    RowIssue(row_number, "return_exceeds_sale", "Returned quantity is larger than quantity sold.")
                )

        def optional_number(field_name: str, label: str) -> float | None:
            text_value = cell(row, field_name)
            if not text_value:
                return None
            try:
                return _number(text_value)
            except ValueError:
                result.issues.append(RowIssue(row_number, "invalid_number", f"{label} is not a number."))
                return None

        selling = optional_number("selling_price", "Selling price")
        cost = optional_number("unit_cost", "Unit cost")
        discount = optional_number("discount", "Discount")
        current_stock = optional_number("current_stock", "Current stock")
        lead = optional_number("lead_time_days", "Lead time")
        pack = optional_number("pack_size", "Pack size")
        moq = optional_number("moq", "Minimum order quantity")
        min_stock = optional_number("min_stock", "Minimum stock")
        if len(result.issues) > issues_before or sale_date is None or quantity is None:
            continue
        sku_key = sku or _norm(name).replace(" ", "-")[:80]
        fingerprint = hashlib.sha256(
            f"{sale_date.isoformat()}|{sku_key}|{quantity}|{selling}|{cell(row, 'invoice_number')}".encode()
        ).hexdigest()
        if fingerprint in seen:
            result.duplicate_in_file += 1
            result.issues.append(
                RowIssue(
                    row_number,
                    "duplicate_in_file",
                    "This line matches an earlier row in the same file. It was not imported.",
                )
            )
            continue
        seen.add(fingerprint)
        result.rows.append(
            ParsedRow(
                row_number=row_number,
                fingerprint=fingerprint,
                data={
                    "sale_date": sale_date.isoformat(),
                    "invoice_number": cell(row, "invoice_number") or None,
                    "product_name": name or sku_key,
                    "sku": sku_key,
                    "category": cell(row, "category") or "General",
                    "quantity": quantity,
                    "returned_quantity": returned,
                    "selling_price": selling,
                    "unit_cost": cost,
                    "discount": discount,
                    "current_stock": current_stock,
                    "supplier_name": cell(row, "supplier_name") or None,
                    "lead_time_days": int(lead) if lead is not None else None,
                    "pack_size": int(pack) if pack is not None else None,
                    "moq": int(moq) if moq is not None else None,
                    "min_stock": min_stock,
                    "stockout": stockout,
                },
            )
        )
    return result
