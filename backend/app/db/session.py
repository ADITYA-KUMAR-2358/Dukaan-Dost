from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.db.store import Store, metadata

_engine = None
logger = logging.getLogger(__name__)


def _sqlite_path(url: str) -> Path | None:
    if not url.startswith("sqlite:///"):
        return None
    raw = url.removeprefix("sqlite:///")
    if raw in {"", ":memory:"}:
        return None
    return Path(raw)


def get_engine():
    global _engine
    if _engine is None:
        url = get_settings().database_url
        sqlite_file = _sqlite_path(url)
        if sqlite_file is not None:
            sqlite_file.parent.mkdir(parents=True, exist_ok=True)
        transaction_pool = ":6543" in url or "pgbouncer=true" in url
        if url.startswith("sqlite"):
            _engine = create_engine(url, connect_args={"check_same_thread": False}, poolclass=NullPool)
        elif transaction_pool:
            _engine = create_engine(
                url,
                poolclass=NullPool,
                pool_pre_ping=True,
                connect_args={"prepare_threshold": None},
            )
        else:
            _engine = create_engine(url, pool_pre_ping=True)
        if url.startswith("sqlite"):

            @event.listens_for(_engine, "connect")
            def _enable_sqlite_foreign_keys(dbapi_connection, _record) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return _engine


def reset_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def _supabase_client():
    from supabase import create_client

    settings = get_settings()
    if not settings.supabase_secret_key.strip():
        logger.warning(
            "SUPABASE_SECRET_KEY is empty, so the API is using the publishable key. "
            "Add the secret key and run backend/app/db/supabase_schema.sql again."
        )
    return create_client(settings.supabase_url, settings.data_api_key)


def ensure_database() -> None:
    settings = get_settings()
    if settings.uses_data_api:
        client = _supabase_client()
        missing = []
        for name in (
            "shops",
            "products",
            "import_batches",
            "sale_lines",
            "inventory_movements",
            "forecast_runs",
            "forecast_points",
            "recommendations",
            "app_settings",
            "workspace_state",
        ):
            try:
                client.table(name).select("*").limit(1).execute()
            except Exception as exc:
                if "PGRST205" in str(exc) or "Could not find the table" in str(exc):
                    missing.append(name)
                else:
                    raise
        if missing:
            raise RuntimeError(
                "Supabase is reachable, but these tables are missing: "
                + ", ".join(missing)
                + ". Run backend/app/db/supabase_schema.sql in the Supabase SQL editor."
            )
        return
    engine = get_engine()
    metadata.create_all(engine)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def open_store() -> Store:
    if get_settings().uses_data_api:
        from app.db.supabase_store import SupabaseStore

        return SupabaseStore(_supabase_client())
    connection = get_engine().connect()
    return Store(connection, connection.begin())


def get_session() -> Generator[Store, None, None]:
    store = open_store()
    try:
        yield store
    finally:
        store.close()
