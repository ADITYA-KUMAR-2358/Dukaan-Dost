from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import uuid4


def new_id() -> str:
    return str(uuid4())


@dataclass
class Shop:
    name: str
    kind: str
    is_demo: bool
    created_at: datetime
    id: str = field(default_factory=new_id)


@dataclass
class Product:
    shop_id: str
    sku: str
    name: str
    created_at: datetime
    updated_at: datetime
    category: str = "General"
    unit: str = "piece"
    selling_price: float | None = None
    unit_cost: float | None = None
    current_stock: float | None = None
    incoming_qty: float = 0
    min_stock: float | None = None
    lead_time_days: int | None = None
    pack_size: int | None = None
    moq: int | None = None
    supplier_name: str | None = None
    archived: bool = False
    id: str = field(default_factory=new_id)


@dataclass
class ImportBatch:
    shop_id: str
    filename: str
    content_hash: str
    encoding: str
    delimiter: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    duplicate_rows: int
    created_at: datetime
    assumptions_json: str = "[]"
    issues_json: str = "[]"
    id: str = field(default_factory=new_id)


@dataclass
class SaleLine:
    shop_id: str
    product_id: str
    sale_date: date
    quantity: float
    fingerprint: str
    import_batch_id: str | None = None
    invoice_number: str | None = None
    returned_quantity: float = 0
    selling_price: float | None = None
    unit_cost: float | None = None
    discount: float | None = None
    stockout: bool = False
    id: str = field(default_factory=new_id)


@dataclass
class InventoryMovement:
    shop_id: str
    product_id: str
    movement_type: str
    quantity: float
    created_at: datetime
    note: str | None = None
    id: str = field(default_factory=new_id)


@dataclass
class ForecastRun:
    shop_id: str
    horizon_days: int
    created_at: datetime
    status: str = "queued"
    summary_json: str = "{}"
    error_code: str | None = None
    completed_at: datetime | None = None
    id: str = field(default_factory=new_id)


@dataclass
class ForecastPoint:
    run_id: str
    product_id: str
    forecast_date: date
    predicted_qty: float
    baseline_qty: float
    model_id: str
    baseline_id: str
    id: str = field(default_factory=new_id)


@dataclass
class Recommendation:
    shop_id: str
    product_id: str
    run_id: str
    policy: str
    slow_status: str
    created_at: datetime
    reorder_point: float | None = None
    safety_stock: float | None = None
    lead_time_demand: float | None = None
    suggested_qty: float | None = None
    flags_json: str = "[]"
    facts_json: str = "{}"
    user_qty: float | None = None
    user_note: str | None = None
    id: str = field(default_factory=new_id)


@dataclass
class AppSetting:
    shop_id: str
    language: str = "hinglish"
    service_level: float = 0.95
    coverage_days: int = 14
    horizon_days: int = 14
    prefer_tabpfn: bool = True
    ollama_model: str = "gemma-4-26b-a4b-it"


@dataclass
class WorkspaceState:
    id: int
    active_shop_id: str | None = None
