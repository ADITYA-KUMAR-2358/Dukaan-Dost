import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    monkeypatch.setenv("SUPABASE_DB_URL", "sqlite:///" + database.as_posix())
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "")
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_URL", "")
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "")
    monkeypatch.setenv("FORECAST_ASYNC", "0")
    monkeypatch.setenv("TABPFN_ENABLED", "0")
    monkeypatch.setenv("TABPFN_API_KEY", "")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("LLM_API_KEY", "")
    from app.config import get_settings
    from app.db.session import reset_engine

    get_settings.cache_clear()
    reset_engine()
    from app.main import create_app

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client
    get_settings.cache_clear()
    reset_engine()
