from __future__ import annotations

from dataclasses import asdict, fields
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    and_,
    func,
    select,
)

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

metadata = MetaData()

shops = Table(
    "shops",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("kind", String(20), nullable=False),
    Column("is_demo", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
products = Table(
    "products",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("shop_id", String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
    Column("sku", String(80), nullable=False),
    Column("name", String(200), nullable=False),
    Column("category", String(80), nullable=False),
    Column("unit", String(40), nullable=False),
    Column("selling_price", Float),
    Column("unit_cost", Float),
    Column("current_stock", Float),
    Column("incoming_qty", Float, nullable=False),
    Column("min_stock", Float),
    Column("lead_time_days", Integer),
    Column("pack_size", Integer),
    Column("moq", Integer),
    Column("supplier_name", String(200)),
    Column("archived", Boolean, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("shop_id", "sku", name="uq_product_shop_sku"),
)
import_batches = Table(
    "import_batches",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("shop_id", String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
    Column("filename", String(255), nullable=False),
    Column("content_hash", String(64), nullable=False),
    Column("encoding", String(40), nullable=False),
    Column("delimiter", String(8), nullable=False),
    Column("total_rows", Integer, nullable=False),
    Column("accepted_rows", Integer, nullable=False),
    Column("rejected_rows", Integer, nullable=False),
    Column("duplicate_rows", Integer, nullable=False),
    Column("assumptions_json", Text, nullable=False),
    Column("issues_json", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("shop_id", "content_hash", name="uq_import_hash"),
)
sale_lines = Table(
    "sale_lines",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("shop_id", String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
    Column("product_id", String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
    Column("import_batch_id", String(36), ForeignKey("import_batches.id", ondelete="SET NULL")),
    Column("invoice_number", String(80)),
    Column("sale_date", Date, nullable=False),
    Column("quantity", Float, nullable=False),
    Column("returned_quantity", Float, nullable=False),
    Column("selling_price", Float),
    Column("unit_cost", Float),
    Column("discount", Float),
    Column("stockout", Boolean, nullable=False),
    Column("fingerprint", String(64), nullable=False),
    UniqueConstraint("shop_id", "fingerprint", name="uq_sale_fingerprint"),
)
inventory_movements = Table(
    "inventory_movements",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("shop_id", String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
    Column("product_id", String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
    Column("movement_type", String(40), nullable=False),
    Column("quantity", Float, nullable=False),
    Column("note", String(400)),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
forecast_runs = Table(
    "forecast_runs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("shop_id", String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
    Column("horizon_days", Integer, nullable=False),
    Column("status", String(20), nullable=False),
    Column("summary_json", Text, nullable=False),
    Column("error_code", String(200)),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True)),
)
forecast_points = Table(
    "forecast_points",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False),
    Column("product_id", String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
    Column("forecast_date", Date, nullable=False),
    Column("predicted_qty", Float, nullable=False),
    Column("baseline_qty", Float, nullable=False),
    Column("model_id", String(80), nullable=False),
    Column("baseline_id", String(80), nullable=False),
)
recommendations = Table(
    "recommendations",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("shop_id", String(36), ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
    Column("product_id", String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
    Column("run_id", String(36), ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False),
    Column("reorder_point", Float),
    Column("safety_stock", Float),
    Column("lead_time_demand", Float),
    Column("suggested_qty", Float),
    Column("policy", String(80), nullable=False),
    Column("slow_status", String(80), nullable=False),
    Column("flags_json", Text, nullable=False),
    Column("facts_json", Text, nullable=False),
    Column("user_qty", Float),
    Column("user_note", String(400)),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
app_settings = Table(
    "app_settings",
    metadata,
    Column("shop_id", String(36), ForeignKey("shops.id", ondelete="CASCADE"), primary_key=True),
    Column("language", String(20), nullable=False),
    Column("service_level", Float, nullable=False),
    Column("coverage_days", Integer, nullable=False),
    Column("horizon_days", Integer, nullable=False),
    Column("prefer_tabpfn", Boolean, nullable=False),
    Column("ollama_model", String(120), nullable=False),
)
workspace_state = Table(
    "workspace_state",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("active_shop_id", String(36), ForeignKey("shops.id", ondelete="SET NULL")),
)

TABLES = {
    Shop: shops,
    Product: products,
    ImportBatch: import_batches,
    SaleLine: sale_lines,
    InventoryMovement: inventory_movements,
    ForecastRun: forecast_runs,
    ForecastPoint: forecast_points,
    Recommendation: recommendations,
    AppSetting: app_settings,
    WorkspaceState: workspace_state,
}

DATE_FIELDS = {"sale_date", "forecast_date"}
DATETIME_FIELDS = {"created_at", "updated_at", "completed_at"}


def _key(obj: Any) -> Any:
    if isinstance(obj, AppSetting):
        return obj.shop_id
    return obj.id


def _pk_column(model: type):
    if model is AppSetting:
        return "shop_id"
    return "id"


def _coerce(name: str, value: Any) -> Any:
    if value is None:
        return None
    if name in DATE_FIELDS and isinstance(value, str):
        return date.fromisoformat(value[:10])
    if name in DATETIME_FIELDS and isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def _values(obj: Any) -> dict:
    return asdict(obj)


def _model_from_row(model: type, row: dict) -> Any:
    names = {item.name for item in fields(model)}
    payload = {key: _coerce(key, value) for key, value in row.items() if key in names}
    return model(**payload)


class Store:
    """One database transaction. commit writes the unit of work. rollback undoes it."""

    def __init__(self, connection, transaction) -> None:
        self.conn = connection
        self.txn = transaction
        self.identity: dict[tuple[type, Any], Any] = {}
        self.snapshots: dict[tuple[type, Any], dict] = {}
        self.pending: list[Any] = []

    def add(self, obj: Any) -> None:
        self.identity[(type(obj), _key(obj))] = obj
        self.pending.append(obj)

    def get(self, model: type, identifier: Any) -> Any:
        cached = self.identity.get((model, identifier))
        if cached is not None:
            return cached
        table = TABLES[model]
        row = self.conn.execute(
            select(table).where(table.c[_pk_column(model)] == identifier)
        ).mappings().first()
        return self._hydrate(model, None if row is None else dict(row))

    def find(self, model: type, filt: dict | None = None, sort: list | None = None) -> list:
        self._flush_inserts()
        table = TABLES[model]
        stmt = select(table)
        clause = _where(table, filt or {})
        if clause is not None:
            stmt = stmt.where(clause)
        if sort:
            stmt = stmt.order_by(*[_order(table, name, direction) for name, direction in sort])
        rows = self.conn.execute(stmt).mappings().all()
        return [self._hydrate(model, dict(row)) for row in rows]

    def find_one(self, model: type, filt: dict | None = None, sort: list | None = None) -> Any:
        rows = self.find(model, filt, sort)
        return rows[0] if rows else None

    def ids(self, model: type, filt: dict) -> list:
        self._flush_inserts()
        table = TABLES[model]
        column = table.c[_pk_column(model)]
        stmt = select(column)
        clause = _where(table, filt)
        if clause is not None:
            stmt = stmt.where(clause)
        return list(self.conn.execute(stmt).scalars().all())

    def maximum(self, model: type, field_name: str, filt: dict) -> Any:
        self._flush_inserts()
        table = TABLES[model]
        stmt = select(func.max(table.c[field_name]))
        clause = _where(table, filt)
        if clause is not None:
            stmt = stmt.where(clause)
        value = self.conn.execute(stmt).scalar()
        return _coerce(field_name, value)

    def delete(self, obj: Any) -> None:
        self._flush_updates()
        model = type(obj)
        identifier = _key(obj)
        table = TABLES[model]
        self.conn.execute(table.delete().where(table.c[_pk_column(model)] == identifier))
        self.pending = [item for item in self.pending if item is not obj]
        key = (model, identifier)
        self.identity.pop(key, None)
        self.snapshots.pop(key, None)

    def delete_many(self, model: type, filt: dict) -> None:
        self._flush_inserts()
        identifiers = self.ids(model, filt)
        if not identifiers:
            return
        table = TABLES[model]
        column = table.c[_pk_column(model)]
        self.conn.execute(table.delete().where(column.in_(identifiers)))
        for identifier in identifiers:
            key = (model, identifier)
            self.identity.pop(key, None)
            self.snapshots.pop(key, None)

    def flush(self) -> None:
        self._flush_inserts()
        self._flush_updates()

    def commit(self) -> None:
        self.flush()
        self.txn.commit()
        self.txn = self.conn.begin()
        self.snapshots = {key: _values(obj) for key, obj in self.identity.items()}

    def rollback(self) -> None:
        self.pending.clear()
        if self.txn.is_active:
            self.txn.rollback()
        self.txn = self.conn.begin()
        for key in list(self.identity):
            if key not in self.snapshots:
                self.identity.pop(key, None)
        for key, snap in list(self.snapshots.items()):
            model, _identifier = key
            obj = self.identity.get(key)
            if obj is None:
                continue
            restored = _model_from_row(model, snap)
            for item in fields(model):
                setattr(obj, item.name, getattr(restored, item.name))

    def refresh(self, obj: Any) -> None:
        model = type(obj)
        identifier = _key(obj)
        table = TABLES[model]
        row = self.conn.execute(
            select(table).where(table.c[_pk_column(model)] == identifier)
        ).mappings().first()
        if row is None:
            return
        fresh = _model_from_row(model, dict(row))
        for item in fields(model):
            setattr(obj, item.name, getattr(fresh, item.name))
        key = (model, identifier)
        self.identity[key] = obj
        self.snapshots[key] = _values(obj)

    def close(self) -> None:
        if self.txn.is_active:
            self.txn.rollback()
        self.conn.close()

    def _hydrate(self, model: type, row: dict | None) -> Any:
        if row is None:
            return None
        identifier = row[_pk_column(model)]
        key = (model, identifier)
        cached = self.identity.get(key)
        if cached is not None:
            return cached
        obj = _model_from_row(model, row)
        self.identity[key] = obj
        self.snapshots[key] = _values(obj)
        return obj

    def _flush_inserts(self) -> None:
        ready = list(self.pending)
        self.pending.clear()
        for obj in ready:
            table = TABLES[type(obj)]
            self.conn.execute(table.insert().values(**_values(obj)))

    def _flush_updates(self) -> None:
        for key, obj in list(self.identity.items()):
            current = _values(obj)
            if self.snapshots.get(key) == current:
                continue
            model, identifier = key
            table = TABLES[model]
            self.conn.execute(
                table.update().where(table.c[_pk_column(model)] == identifier).values(**current)
            )


def _where(table, filt: dict):
    clauses = []
    for name, value in filt.items():
        column = table.c[name]
        if isinstance(value, dict):
            if "$in" in value:
                clauses.append(column.in_(value["$in"]))
            if "$gte" in value:
                clauses.append(column >= value["$gte"])
            if "$lte" in value:
                clauses.append(column <= value["$lte"])
            continue
        clauses.append(column == value)
    if not clauses:
        return None
    return and_(*clauses)


def _order(table, name: str, direction: int):
    column = table.c[name]
    if direction < 0:
        return column.desc()
    return column.asc()
