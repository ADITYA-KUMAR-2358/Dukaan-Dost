from __future__ import annotations

import csv
import io
import json
import threading
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.errors import AppError
from app.db.session import get_session
from app.db.store import Store
from app.models.entities import (
    AppSetting,
    ForecastPoint,
    ForecastRun,
    ImportBatch,
    InventoryMovement,
    Product,
    Recommendation,
    SaleLine,
    Shop,
    WorkspaceState,
)
from app.services.explanations.service import explain_facts, gemma_configured
from app.services.forecasting.jobs import execute_run
from app.services.forecasting.tabpfn_adapter import probe as probe_tabpfn
from app.services.ingestion.importer import commit_import
from app.services.ingestion.parser import parse_csv
from app.services.sample_catalog import COLUMNS, write_csv

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductIn(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    category: str = "General"
    unit: str = "piece"
    selling_price: float | None = None
    unit_cost: float | None = None
    current_stock: float | None = None
    min_stock: float | None = None
    lead_time_days: int | None = Field(default=None, ge=0, le=365)
    pack_size: int | None = Field(default=None, ge=1)
    moq: int | None = Field(default=None, ge=1)
    supplier_name: str | None = None


class ProductPatch(BaseModel):
    name: str | None = None
    category: str | None = None
    unit: str | None = None
    selling_price: float | None = None
    unit_cost: float | None = None
    current_stock: float | None = None
    min_stock: float | None = None
    lead_time_days: int | None = Field(default=None, ge=0, le=365)
    pack_size: int | None = Field(default=None, ge=1)
    moq: int | None = Field(default=None, ge=1)
    supplier_name: str | None = None
    archived: bool | None = None


class MovementIn(BaseModel):
    product_id: str
    movement_type: str
    quantity: float
    note: str | None = None


class ForecastIn(BaseModel):
    shop_id: str | None = None
    horizon_days: int = Field(default=14, ge=7, le=30)


class ShopNameIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SettingsPatch(BaseModel):
    shop_id: str | None = None
    active_shop_id: str | None = None
    language: str | None = None
    service_level: float | None = None
    coverage_days: int | None = Field(default=None, ge=7, le=60)
    horizon_days: int | None = Field(default=None, ge=7, le=30)
    prefer_tabpfn: bool | None = None
    ollama_model: str | None = None


class RecommendationPatch(BaseModel):
    user_qty: float | None = Field(default=None, ge=0)
    user_note: str | None = None


def _state(session: Store) -> WorkspaceState:
    state = session.get(WorkspaceState, 1)
    if state is None:
        state = WorkspaceState(id=1, active_shop_id=None)
        session.add(state)
        session.commit()
    return state


def _shop_or_404(session: Store, shop_id: str) -> Shop:
    shop = session.get(Shop, shop_id)
    if shop is None:
        raise AppError("shop_not_found", "That shop was not found.", 404)
    return shop


def _active_shop(session: Store, shop_id: str | None) -> Shop:
    if shop_id:
        return _shop_or_404(session, shop_id)
    state = _state(session)
    if not state.active_shop_id:
        raise AppError("no_shop", "Open the sample shop or create your shop first.", 409)
    return _shop_or_404(session, state.active_shop_id)


def _settings_for(session: Store, shop: Shop) -> AppSetting:
    row = session.get(AppSetting, shop.id)
    if row is None:
        row = AppSetting(
            shop_id=shop.id,
            language="hinglish",
            service_level=0.95,
            coverage_days=14,
            horizon_days=14,
            prefer_tabpfn=True,
            ollama_model=get_settings().llm_model,
        )
        session.add(row)
        session.commit()
    return row


def _product_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "shop_id": product.shop_id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "unit": product.unit,
        "selling_price": product.selling_price,
        "unit_cost": product.unit_cost,
        "current_stock": product.current_stock,
        "incoming_qty": product.incoming_qty,
        "min_stock": product.min_stock,
        "lead_time_days": product.lead_time_days,
        "pack_size": product.pack_size,
        "moq": product.moq,
        "supplier_name": product.supplier_name,
        "archived": product.archived,
    }


def _latest_run(session: Store, shop_id: str) -> ForecastRun | None:
    return session.find_one(
        ForecastRun,
        {"shop_id": shop_id, "status": "completed"},
        sort=[("completed_at", -1)],
    )


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/api/status")
def status(session: Store = Depends(get_session)) -> dict:
    state = _state(session)
    settings = get_settings()
    tabpfn = probe_tabpfn()
    gemma = gemma_configured(settings)
    shop = session.get(Shop, state.active_shop_id) if state.active_shop_id else None
    return {
        "status": "ok",
        "active_shop_id": state.active_shop_id,
        "shop": None if shop is None else {"id": shop.id, "name": shop.name, "is_demo": shop.is_demo},
        "database": settings.database_label,
        "tabpfn": {
            "enabled": settings.tabpfn_enabled,
            "requested_version": settings.tabpfn_model_version,
            "installed": tabpfn["installed"],
            "package_version": tabpfn["version"],
            "compatible": tabpfn["compatible"],
            "weights_loaded": False,
            "detail": tabpfn["detail"],
        },
        "gemma": {
            "ready": gemma,
            "configured_model": settings.llm_model,
            "base_url": settings.llm_base_url,
        },
        "explanation_mode": "gemma" if gemma else "template",
    }


@router.get("/api/workspaces")
def list_workspaces(session: Store = Depends(get_session)) -> dict:
    state = _state(session)
    shops = session.find(Shop, sort=[("created_at", 1)])
    return {
        "active_shop_id": state.active_shop_id,
        "shops": [
            {"id": shop.id, "name": shop.name, "kind": shop.kind, "is_demo": shop.is_demo}
            for shop in shops
        ],
    }


def _seed_sample(session: Store) -> Shop:
    path = write_csv_path()
    raw = path.read_bytes()
    parsed = parse_csv(raw)
    shop = Shop(name="Sharma Kirana (sample)", kind="sample", is_demo=True, created_at=_now())
    session.add(shop)
    session.flush()
    _settings_for(session, shop)
    commit_import(session, shop.id, "kirana_billing.csv", parsed)
    state = _state(session)
    state.active_shop_id = shop.id
    session.commit()
    return shop


def write_csv_path():
    from pathlib import Path

    target = Path(get_settings().sample_csv)
    write_csv(target)
    return target


@router.post("/api/workspaces/sample")
def open_sample(reset: bool = False, session: Store = Depends(get_session)) -> dict:
    shop = session.find_one(Shop, {"kind": "sample"})
    if shop and reset:
        _delete_shop(session, shop.id)
        session.commit()
        shop = None
    if shop is None:
        shop = _seed_sample(session)
    else:
        state = _state(session)
        state.active_shop_id = shop.id
        session.commit()
    return {"shop": {"id": shop.id, "name": shop.name, "kind": shop.kind, "is_demo": True}}


@router.post("/api/workspaces/local")
def open_local(session: Store = Depends(get_session)) -> dict:
    shop = session.find_one(Shop, {"kind": "local"})
    if shop is None:
        shop = Shop(name="My shop", kind="local", is_demo=False, created_at=_now())
        session.add(shop)
        session.flush()
        _settings_for(session, shop)
    state = _state(session)
    state.active_shop_id = shop.id
    session.commit()
    return {"shop": {"id": shop.id, "name": shop.name, "kind": shop.kind, "is_demo": False}}


@router.patch("/api/workspaces/name")
def rename_active_shop(payload: ShopNameIn, session: Store = Depends(get_session)) -> dict:
    shop = _active_shop(session, None)
    if shop.is_demo:
        raise AppError("demo_locked", "The sample shop keeps its name.", 409)
    cleaned = " ".join(payload.name.split())
    if not cleaned:
        raise AppError("bad_shop_name", "Enter a shop name.", 422)
    shop.name = cleaned
    session.commit()
    return {"shop": {"id": shop.id, "name": shop.name, "is_demo": False}}


def _delete_shop(session: Store, shop_id: str) -> None:
    run_ids = session.ids(ForecastRun, {"shop_id": shop_id})
    if run_ids:
        session.delete_many(ForecastPoint, {"run_id": {"$in": run_ids}})
        session.delete_many(Recommendation, {"shop_id": shop_id})
        session.delete_many(ForecastRun, {"shop_id": shop_id})
    session.delete_many(InventoryMovement, {"shop_id": shop_id})
    session.delete_many(SaleLine, {"shop_id": shop_id})
    session.delete_many(ImportBatch, {"shop_id": shop_id})
    session.delete_many(Product, {"shop_id": shop_id})
    session.delete_many(AppSetting, {"shop_id": shop_id})
    state = session.get(WorkspaceState, 1)
    if state and state.active_shop_id == shop_id:
        state.active_shop_id = None
    shop = session.get(Shop, shop_id)
    if shop:
        session.delete(shop)


@router.get("/api/dashboard")
def dashboard(shop_id: str | None = None, session: Store = Depends(get_session)) -> dict:
    shop = _active_shop(session, shop_id)
    products = session.find(Product, {"shop_id": shop.id, "archived": False})
    valued = []
    missing_cost = 0
    for product in products:
        if product.current_stock is None or product.unit_cost is None:
            if product.current_stock is not None and product.unit_cost is None:
                missing_cost += 1
            continue
        valued.append(product.current_stock * product.unit_cost)
    run = _latest_run(session, shop.id)
    recs = []
    if run:
        recs = session.find(Recommendation, {"run_id": run.id})
    reorder = 0
    stockout = 0
    slow = 0
    for rec in recs:
        flags = json.loads(rec.flags_json)
        codes = {flag["code"] for flag in flags}
        if "reorder" in codes:
            reorder += 1
        if "stockout_risk" in codes:
            stockout += 1
        if rec.slow_status in {"declining", "no_recent_sales"}:
            slow += 1
    last_import = session.find_one(ImportBatch, {"shop_id": shop.id}, sort=[("created_at", -1)])
    recent_end = session.maximum(SaleLine, "sale_date", {"shop_id": shop.id})
    trend = None
    if recent_end is not None:
        from datetime import timedelta

        start_recent = recent_end - timedelta(days=6)
        start_prior = recent_end - timedelta(days=13)
        end_prior = recent_end - timedelta(days=7)

        def total(start, end):
            rows = session.find(
                SaleLine,
                {
                    "shop_id": shop.id,
                    "sale_date": {"$gte": start, "$lte": end},
                    "stockout": False,
                },
            )
            return sum(max(0.0, row.quantity - row.returned_quantity) for row in rows)

        trend = {"recent_7_days": total(start_recent, recent_end), "prior_7_days": total(start_prior, end_prior)}
    return {
        "shop": {"id": shop.id, "name": shop.name, "is_demo": shop.is_demo},
        "active_products": len(products),
        "inventory_value": None if not valued else round(sum(valued), 2),
        "inventory_value_products": len(valued),
        "products_missing_cost": missing_cost,
        "reorder_count": reorder,
        "stockout_risk_count": stockout,
        "slow_moving_count": slow,
        "demand_trend": trend,
        "last_import": None
        if last_import is None
        else {
            "id": last_import.id,
            "filename": last_import.filename,
            "accepted_rows": last_import.accepted_rows,
            "rejected_rows": last_import.rejected_rows,
            "created_at": last_import.created_at.isoformat(),
        },
        "last_forecast": None
        if run is None
        else {"id": run.id, "status": run.status, "completed_at": run.completed_at.isoformat() if run.completed_at else None},
        "has_forecast": run is not None,
    }


@router.get("/api/imports/template")
def template() -> Response:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerow(
        {
            "date": "2026-10-01",
            "invoice_number": "INV-1001",
            "product_name": "Example Tea 250g",
            "sku": "TEA-250",
            "category": "Grocery",
            "quantity": 2,
            "selling_price": 120,
            "unit_cost": 98,
            "current_stock": 10,
            "in_stock": "yes",
            "supplier": "Local Distributor",
            "lead_time_days": 3,
            "pack_size": 10,
            "moq": 10,
            "min_stock": 4,
        }
    )
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dukaandost-template.csv"},
    )


@router.post("/api/imports/preview")
async def preview_import(
    file: UploadFile = File(...),
    mapping: str | None = Form(default=None),
) -> dict:
    raw = await _read_upload(file)
    override = json.loads(mapping) if mapping else None
    try:
        parsed = parse_csv(raw, override)
    except ValueError as exc:
        raise AppError("invalid_file", str(exc), 422) from exc
    return {
        "filename": file.filename,
        "encoding": parsed.encoding,
        "delimiter": parsed.delimiter,
        "columns": parsed.columns,
        "mapping": parsed.mapping,
        "assumptions": parsed.assumptions,
        "accepted_rows": len(parsed.rows),
        "rejected_rows": len(parsed.issues),
        "duplicate_rows": parsed.duplicate_in_file,
        "preview": [row.data for row in parsed.rows[:8]],
        "issues": [issue.__dict__ for issue in parsed.issues[:50]],
    }


@router.post("/api/imports")
async def create_import(
    file: UploadFile = File(...),
    shop_id: str | None = Form(default=None),
    mapping: str | None = Form(default=None),
    session: Store = Depends(get_session),
) -> dict:
    shop = _active_shop(session, shop_id)
    if shop.is_demo:
        raise AppError(
            "demo_locked",
            "The sample shop is read-only. Create your own shop before importing billing records.",
            409,
        )
    raw = await _read_upload(file)
    override = json.loads(mapping) if mapping else None
    try:
        parsed = parse_csv(raw, override)
    except ValueError as exc:
        raise AppError("invalid_file", str(exc), 422) from exc
    batch = commit_import(session, shop.id, file.filename or "upload.csv", parsed)
    return {
        "id": batch.id,
        "accepted_rows": batch.accepted_rows,
        "rejected_rows": batch.rejected_rows,
        "duplicate_rows": batch.duplicate_rows,
        "assumptions": json.loads(batch.assumptions_json),
        "issues": json.loads(batch.issues_json),
    }


@router.get("/api/imports")
def list_imports(shop_id: str | None = None, session: Store = Depends(get_session)) -> dict:
    shop = _active_shop(session, shop_id)
    rows = session.find(ImportBatch, {"shop_id": shop.id}, sort=[("created_at", -1)])
    return {
        "imports": [
            {
                "id": row.id,
                "filename": row.filename,
                "accepted_rows": row.accepted_rows,
                "rejected_rows": row.rejected_rows,
                "duplicate_rows": row.duplicate_rows,
                "created_at": row.created_at.isoformat(),
                "assumptions": json.loads(row.assumptions_json),
            }
            for row in rows
        ]
    }


async def _read_upload(file: UploadFile) -> bytes:
    raw = await file.read()
    if len(raw) > get_settings().max_upload_bytes:
        raise AppError("file_too_large", "The file is larger than the 5 MB upload limit.", 413)
    return raw


@router.get("/api/products")
def list_products(
    shop_id: str | None = None,
    q: str | None = None,
    category: str | None = None,
    status: str | None = None,
    session: Store = Depends(get_session),
) -> dict:
    shop = _active_shop(session, shop_id)
    rows = session.find(Product, {"shop_id": shop.id}, sort=[("name", 1)])
    if q:
        needle = q.lower()
        rows = [row for row in rows if needle in row.name.lower() or needle in row.sku.lower()]
    if category:
        rows = [row for row in rows if row.category == category]
    if status == "archived":
        rows = [row for row in rows if row.archived]
    elif status == "low":
        rows = [
            row
            for row in rows
            if not row.archived
            and row.current_stock is not None
            and row.min_stock is not None
            and row.current_stock <= row.min_stock
        ]
    else:
        if status != "all":
            rows = [row for row in rows if not row.archived]
    categories = sorted({row.category for row in session.find(Product, {"shop_id": shop.id})})
    return {"products": [_product_dict(row) for row in rows], "categories": categories}


@router.post("/api/products")
def create_product(payload: ProductIn, shop_id: str | None = None, session: Store = Depends(get_session)) -> dict:
    shop = _active_shop(session, shop_id)
    if shop.is_demo:
        raise AppError("demo_locked", "Add products in your own shop. The sample shop stays unchanged.", 409)
    exists = session.find_one(Product, {"shop_id": shop.id, "sku": payload.sku})
    if exists:
        raise AppError("duplicate_sku", "That SKU already exists in this shop.", 409)
    product = Product(
        shop_id=shop.id,
        archived=False,
        incoming_qty=0,
        created_at=_now(),
        updated_at=_now(),
        **payload.model_dump(),
    )
    session.add(product)
    session.commit()
    return _product_dict(product)


@router.get("/api/products/{product_id}")
def get_product(product_id: str, session: Store = Depends(get_session)) -> dict:
    product = session.get(Product, product_id)
    if product is None:
        raise AppError("product_not_found", "That product was not found.", 404)
    lines = session.find(SaleLine, {"product_id": product.id}, sort=[("sale_date", -1)])
    return {
        **_product_dict(product),
        "recent_sales": [
            {
                "date": line.sale_date.isoformat(),
                "quantity": line.quantity,
                "returned_quantity": line.returned_quantity,
                "stockout": line.stockout,
                "invoice_number": line.invoice_number,
            }
            for line in lines[:30]
        ],
    }


@router.patch("/api/products/{product_id}")
def patch_product(product_id: str, payload: ProductPatch, session: Store = Depends(get_session)) -> dict:
    product = session.get(Product, product_id)
    if product is None:
        raise AppError("product_not_found", "That product was not found.", 404)
    shop = _shop_or_404(session, product.shop_id)
    if shop.is_demo:
        raise AppError("demo_locked", "The sample shop cannot be edited.", 409)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    product.updated_at = _now()
    session.commit()
    return _product_dict(product)


@router.get("/api/inventory")
def inventory(shop_id: str | None = None, session: Store = Depends(get_session)) -> dict:
    shop = _active_shop(session, shop_id)
    products = session.find(Product, {"shop_id": shop.id, "archived": False}, sort=[("name", 1)])
    return {"products": [_product_dict(row) for row in products]}


@router.post("/api/inventory/movements")
def add_movement(payload: MovementIn, session: Store = Depends(get_session)) -> dict:
    product = session.get(Product, payload.product_id)
    if product is None:
        raise AppError("product_not_found", "That product was not found.", 404)
    shop = _shop_or_404(session, product.shop_id)
    if shop.is_demo:
        raise AppError("demo_locked", "Record stock changes in your own shop.", 409)
    kind = payload.movement_type
    qty = payload.quantity
    if kind not in {"receipt", "adjustment", "incoming"}:
        raise AppError("bad_movement", "Use receipt, adjustment, or incoming.", 422)
    if kind in {"receipt", "incoming"} and qty <= 0:
        raise AppError("bad_quantity", "Receipt and incoming quantities must be greater than zero.", 422)
    if kind == "adjustment" and qty == 0:
        raise AppError("bad_quantity", "An adjustment needs a non-zero quantity.", 422)
    if product.current_stock is None and kind in {"receipt", "adjustment"}:
        product.current_stock = 0
    if kind == "receipt":
        product.current_stock = (product.current_stock or 0) + qty
    elif kind == "adjustment":
        updated = (product.current_stock or 0) + qty
        if updated < 0:
            raise AppError("negative_stock", "That adjustment would make stock negative.", 422)
        product.current_stock = updated
    else:
        updated = (product.incoming_qty or 0) + qty
        if updated < 0:
            raise AppError("negative_incoming", "Incoming stock cannot go below zero.", 422)
        product.incoming_qty = updated
    product.updated_at = _now()
    session.add(
        InventoryMovement(
            shop_id=product.shop_id,
            product_id=product.id,
            movement_type=kind,
            quantity=qty,
            note=payload.note,
            created_at=_now(),
        )
    )
    session.commit()
    return _product_dict(product)


@router.post("/api/forecasts")
def create_forecast(payload: ForecastIn, session: Store = Depends(get_session)) -> dict:
    shop = _active_shop(session, payload.shop_id)
    run = ForecastRun(
        shop_id=shop.id,
        horizon_days=payload.horizon_days,
        status="queued",
        summary_json="{}",
        created_at=_now(),
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    if get_settings().forecast_async:
        threading.Thread(target=execute_run, args=(run.id,), daemon=True).start()
        return {"id": run.id, "status": "queued", "horizon_days": run.horizon_days}
    execute_run(run.id)
    session.refresh(run)
    return {"id": run.id, "status": run.status, "horizon_days": run.horizon_days, "error_code": run.error_code}


@router.get("/api/forecasts")
def list_forecasts(shop_id: str | None = None, session: Store = Depends(get_session)) -> dict:
    shop = _active_shop(session, shop_id)
    runs = session.find(ForecastRun, {"shop_id": shop.id}, sort=[("created_at", -1)])
    return {
        "forecasts": [
            {
                "id": run.id,
                "status": run.status,
                "horizon_days": run.horizon_days,
                "created_at": run.created_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error_code": run.error_code,
            }
            for run in runs
        ]
    }


@router.get("/api/forecasts/{run_id}")
def get_forecast(run_id: str, session: Store = Depends(get_session)) -> dict:
    run = session.get(ForecastRun, run_id)
    if run is None:
        raise AppError("forecast_not_found", "That forecast was not found.", 404)
    summary = json.loads(run.summary_json or "{}")
    points = session.find(ForecastPoint, {"run_id": run.id})
    grouped: dict[str, list] = {}
    for point in points:
        grouped.setdefault(point.product_id, []).append(
            {
                "date": point.forecast_date.isoformat(),
                "predicted_qty": point.predicted_qty,
                "baseline_qty": point.baseline_qty,
                "model_id": point.model_id,
                "baseline_id": point.baseline_id,
            }
        )
    for rows in grouped.values():
        rows.sort(key=lambda item: item["date"])
    return {
        "id": run.id,
        "status": run.status,
        "horizon_days": run.horizon_days,
        "error_code": run.error_code,
        "summary": summary,
        "series": grouped,
    }


@router.get("/api/recommendations")
def list_recommendations(
    shop_id: str | None = None,
    slow: str | None = None,
    session: Store = Depends(get_session),
) -> dict:
    shop = _active_shop(session, shop_id)
    run = _latest_run(session, shop.id)
    if run is None:
        return {"run_id": None, "recommendations": []}
    rows = session.find(Recommendation, {"run_id": run.id})
    products = {product.id: product for product in session.find(Product, {"shop_id": shop.id})}
    language = _settings_for(session, shop).language
    payload = []
    for row in rows:
        if slow and row.slow_status != slow:
            continue
        product = products.get(row.product_id)
        facts = json.loads(row.facts_json)
        from app.services.explanations.grounding import template_explanation

        explanation = template_explanation(facts, language)
        payload.append(
            {
                "id": row.id,
                "product_id": row.product_id,
                "product_name": product.name if product else facts.get("product_name"),
                "sku": product.sku if product else None,
                "reorder_point": row.reorder_point,
                "safety_stock": row.safety_stock,
                "lead_time_demand": row.lead_time_demand,
                "suggested_qty": row.user_qty if row.user_qty is not None else row.suggested_qty,
                "calculated_qty": row.suggested_qty,
                "user_qty": row.user_qty,
                "user_note": row.user_note,
                "policy": row.policy,
                "slow_status": row.slow_status,
                "flags": json.loads(row.flags_json),
                "model_id": facts.get("model_id"),
                "fallback_reason": facts.get("fallback_reason"),
                "explanation": explanation,
            }
        )
    return {"run_id": run.id, "recommendations": payload}


@router.patch("/api/recommendations/{recommendation_id}")
def patch_recommendation(
    recommendation_id: str,
    payload: RecommendationPatch,
    session: Store = Depends(get_session),
) -> dict:
    row = session.get(Recommendation, recommendation_id)
    if row is None:
        raise AppError("recommendation_not_found", "That recommendation was not found.", 404)
    shop = _shop_or_404(session, row.shop_id)
    if shop.is_demo:
        raise AppError("demo_locked", "Edit recommendations in your own shop.", 409)
    if payload.user_qty is not None:
        row.user_qty = payload.user_qty
    if payload.user_note is not None:
        row.user_note = payload.user_note
    session.commit()
    return {"id": row.id, "user_qty": row.user_qty, "user_note": row.user_note}


@router.post("/api/recommendations/{recommendation_id}/explain")
def explain_recommendation(recommendation_id: str, request: Request, session: Store = Depends(get_session)) -> dict:
    row = session.get(Recommendation, recommendation_id)
    if row is None:
        raise AppError("recommendation_not_found", "That recommendation was not found.", 404)
    shop = _shop_or_404(session, row.shop_id)
    language = _settings_for(session, shop).language
    facts = json.loads(row.facts_json)
    visitor = request.client.host if request.client else "local"
    return explain_facts(facts, language, visitor)


@router.get("/api/settings")
def get_settings_route(session: Store = Depends(get_session)) -> dict:
    state = _state(session)
    if not state.active_shop_id:
        return {"active_shop_id": None, "settings": None}
    shop = _shop_or_404(session, state.active_shop_id)
    row = _settings_for(session, shop)
    return {"active_shop_id": shop.id, "is_demo": shop.is_demo, "settings": _settings_dict(row)}


@router.patch("/api/settings")
def patch_settings(payload: SettingsPatch, session: Store = Depends(get_session)) -> dict:
    if payload.active_shop_id:
        _shop_or_404(session, payload.active_shop_id)
        state = _state(session)
        state.active_shop_id = payload.active_shop_id
        session.commit()
    shop = _active_shop(session, payload.shop_id)
    row = _settings_for(session, shop)
    if payload.language is not None:
        if payload.language not in {"english", "hinglish"}:
            raise AppError("bad_language", "Choose english or hinglish.", 422)
        row.language = payload.language
    if payload.service_level is not None:
        if payload.service_level not in {0.9, 0.95, 0.99}:
            raise AppError("bad_service_level", "Service level must be 0.9, 0.95, or 0.99.", 422)
        row.service_level = payload.service_level
    if payload.coverage_days is not None:
        row.coverage_days = payload.coverage_days
    if payload.horizon_days is not None:
        row.horizon_days = payload.horizon_days
    if payload.prefer_tabpfn is not None:
        row.prefer_tabpfn = payload.prefer_tabpfn
    if payload.ollama_model is not None:
        row.ollama_model = payload.ollama_model[:120]
    session.commit()
    return {"active_shop_id": shop.id, "settings": _settings_dict(row)}


def _settings_dict(row: AppSetting) -> dict:
    return {
        "language": row.language,
        "service_level": row.service_level,
        "coverage_days": row.coverage_days,
        "horizon_days": row.horizon_days,
        "prefer_tabpfn": row.prefer_tabpfn,
        "ollama_model": row.ollama_model,
    }


@router.get("/api/reports/export")
def export_report(
    kind: str = Query(...),
    shop_id: str | None = None,
    session: Store = Depends(get_session),
) -> Response:
    shop = _active_shop(session, shop_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    if kind == "inventory":
        writer.writerow(["sku", "name", "category", "stock", "incoming", "unit_cost", "min_stock", "supplier", "archived"])
        for product in session.find(Product, {"shop_id": shop.id}):
            writer.writerow(
                [
                    product.sku,
                    product.name,
                    product.category,
                    "" if product.current_stock is None else product.current_stock,
                    product.incoming_qty,
                    "" if product.unit_cost is None else product.unit_cost,
                    "" if product.min_stock is None else product.min_stock,
                    product.supplier_name or "",
                    product.archived,
                ]
            )
    elif kind == "forecast":
        run = _latest_run(session, shop.id)
        writer.writerow(["sku", "name", "date", "predicted_qty", "baseline_qty", "model_id", "baseline_id"])
        if run:
            points = session.find(ForecastPoint, {"run_id": run.id})
            products = {item.id: item for item in session.find(Product, {"shop_id": shop.id})}
            for point in points:
                product = products.get(point.product_id)
                writer.writerow(
                    [
                        product.sku if product else "",
                        product.name if product else "",
                        point.forecast_date.isoformat(),
                        point.predicted_qty,
                        point.baseline_qty,
                        point.model_id,
                        point.baseline_id,
                    ]
                )
    elif kind == "recommendations":
        run = _latest_run(session, shop.id)
        writer.writerow(
            ["sku", "name", "reorder_point", "suggested_qty", "edited_qty", "policy", "slow_status", "model_id", "flags"]
        )
        if run:
            rows = session.find(Recommendation, {"run_id": run.id})
            products = {item.id: item for item in session.find(Product, {"shop_id": shop.id})}
            for row in rows:
                product = products.get(row.product_id)
                facts = json.loads(row.facts_json)
                writer.writerow(
                    [
                        product.sku if product else "",
                        product.name if product else "",
                        row.reorder_point if row.reorder_point is not None else "",
                        row.suggested_qty if row.suggested_qty is not None else "",
                        row.user_qty if row.user_qty is not None else "",
                        row.policy,
                        row.slow_status,
                        facts.get("model_id") or "",
                        "; ".join(flag["code"] for flag in json.loads(row.flags_json)),
                    ]
                )
    elif kind == "quality":
        writer.writerow(["filename", "accepted_rows", "rejected_rows", "duplicate_rows", "issue_row", "issue_code", "issue_message"])
        batches = session.find(ImportBatch, {"shop_id": shop.id})
        for batch in batches:
            issues = json.loads(batch.issues_json or "[]")
            if not issues:
                writer.writerow([batch.filename, batch.accepted_rows, batch.rejected_rows, batch.duplicate_rows, "", "", ""])
            for issue in issues:
                writer.writerow(
                    [
                        batch.filename,
                        batch.accepted_rows,
                        batch.rejected_rows,
                        batch.duplicate_rows,
                        issue.get("row_number"),
                        issue.get("code"),
                        issue.get("message"),
                    ]
                )
    elif kind == "imports":
        writer.writerow(["filename", "accepted_rows", "rejected_rows", "duplicate_rows", "created_at"])
        for batch in session.find(ImportBatch, {"shop_id": shop.id}):
            writer.writerow(
                [batch.filename, batch.accepted_rows, batch.rejected_rows, batch.duplicate_rows, batch.created_at.isoformat()]
            )
    elif kind == "evaluation":
        run = _latest_run(session, shop.id)
        writer.writerow(["sku", "model_id", "baseline_id", "mae", "rmse", "wape", "mase", "baseline_mae", "note"])
        if run:
            summary = json.loads(run.summary_json or "{}").get("products", [])
            for item in summary:
                evaluation = item.get("evaluation") or {}
                primary = evaluation.get("primary") or {}
                baseline = evaluation.get("baseline") or {}
                writer.writerow(
                    [
                        item.get("sku"),
                        item.get("model_id") or "",
                        item.get("baseline_id") or "",
                        primary.get("mae", ""),
                        primary.get("rmse", ""),
                        primary.get("wape", ""),
                        primary.get("mase", ""),
                        baseline.get("mae", ""),
                        evaluation.get("note", ""),
                    ]
                )
    else:
        raise AppError("bad_report", "Unknown report kind.", 422)
    filename = f"dukaandost-{shop.kind}-{kind}.csv"
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
