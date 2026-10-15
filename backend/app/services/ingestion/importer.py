from __future__ import annotations

import json
from datetime import datetime, timezone

from app.core.errors import AppError
from app.db.store import Store
from app.models.entities import ImportBatch, Product, SaleLine
from app.services.ingestion.parser import ParseResult


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slug(name: str) -> str:
    return name.strip().lower().replace(" ", "-")[:80] or "item"


def commit_import(session: Store, shop_id: str, filename: str, parsed: ParseResult) -> ImportBatch:
    existing = session.find_one(
        ImportBatch,
        {"shop_id": shop_id, "content_hash": parsed.content_hash},
    )
    if existing:
        raise AppError(
            "duplicate_import",
            "This file was already imported into the shop. Import it again only if you really have a new export.",
            409,
        )
    if parsed.mapping.get("date") is None or parsed.mapping.get("quantity") is None:
        raise AppError("mapping_incomplete", "Map the date and quantity columns before importing.", 422)
    if parsed.mapping.get("product_name") is None and parsed.mapping.get("sku") is None:
        raise AppError("mapping_incomplete", "Map a product name or SKU column before importing.", 422)
    if not parsed.rows:
        raise AppError(
            "nothing_to_import",
            "No rows were valid. Fix the listed problems and try again.",
            422,
            [issue.__dict__ for issue in parsed.issues],
        )

    batch = ImportBatch(
        shop_id=shop_id,
        filename=filename[:255] or "upload.csv",
        content_hash=parsed.content_hash,
        encoding=parsed.encoding,
        delimiter=parsed.delimiter,
        total_rows=len(parsed.rows) + len(parsed.issues),
        accepted_rows=0,
        rejected_rows=len(parsed.issues),
        duplicate_rows=parsed.duplicate_in_file,
        assumptions_json=json.dumps(parsed.assumptions),
        issues_json=json.dumps([issue.__dict__ for issue in parsed.issues]),
        created_at=_now(),
    )
    session.add(batch)
    session.flush()
    accepted = 0
    duplicates = parsed.duplicate_in_file
    known_fingerprints = {line.fingerprint for line in session.find(SaleLine, {"shop_id": shop_id})}
    products_by_sku = {product.sku: product for product in session.find(Product, {"shop_id": shop_id})}
    try:
        for item in parsed.rows:
            data = item.data
            if item.fingerprint in known_fingerprints:
                duplicates += 1
                continue
            product = products_by_sku.get(data["sku"])
            if product is None:
                product = Product(
                    shop_id=shop_id,
                    sku=data["sku"] or _slug(data["product_name"]),
                    name=data["product_name"],
                    category=data["category"],
                    selling_price=data["selling_price"],
                    unit_cost=data["unit_cost"],
                    current_stock=data["current_stock"],
                    incoming_qty=0,
                    min_stock=data["min_stock"],
                    lead_time_days=data["lead_time_days"],
                    pack_size=data["pack_size"],
                    moq=data["moq"],
                    supplier_name=data["supplier_name"],
                    archived=False,
                    created_at=_now(),
                    updated_at=_now(),
                )
                session.add(product)
                products_by_sku[product.sku] = product
            else:
                product.name = data["product_name"] or product.name
                product.category = data["category"] or product.category
                if data["selling_price"] is not None:
                    product.selling_price = data["selling_price"]
                if data["unit_cost"] is not None:
                    product.unit_cost = data["unit_cost"]
                if data["current_stock"] is not None:
                    product.current_stock = data["current_stock"]
                if data["min_stock"] is not None:
                    product.min_stock = data["min_stock"]
                if data["lead_time_days"] is not None:
                    product.lead_time_days = data["lead_time_days"]
                if data["pack_size"] is not None:
                    product.pack_size = data["pack_size"]
                if data["moq"] is not None:
                    product.moq = data["moq"]
                if data["supplier_name"]:
                    product.supplier_name = data["supplier_name"]
                product.updated_at = _now()
            session.add(
                SaleLine(
                    shop_id=shop_id,
                    product_id=product.id,
                    import_batch_id=batch.id,
                    invoice_number=data["invoice_number"],
                    sale_date=datetime.fromisoformat(data["sale_date"]).date(),
                    quantity=0 if data["stockout"] else data["quantity"],
                    returned_quantity=data["returned_quantity"],
                    selling_price=data["selling_price"],
                    unit_cost=data["unit_cost"],
                    discount=data["discount"],
                    stockout=bool(data["stockout"]),
                    fingerprint=item.fingerprint,
                )
            )
            known_fingerprints.add(item.fingerprint)
            accepted += 1
        if accepted == 0:
            raise AppError(
                "nothing_to_import",
                "Every valid-looking row was already in the shop. Nothing new was saved.",
                409,
            )
        batch.accepted_rows = accepted
        batch.duplicate_rows = duplicates
        session.commit()
    except AppError:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise AppError(
            "import_failed",
            "The import was rolled back because it could not be saved.",
            500,
        )
    session.refresh(batch)
    return batch
