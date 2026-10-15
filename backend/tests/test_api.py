def test_health_and_status(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    status = client.get("/api/status")
    assert status.status_code == 200
    body = status.json()
    assert body["database"] == "sqlite"
    assert body["explanation_mode"] == "template"
    assert body["tabpfn"]["weights_loaded"] is False
    assert "nosniff" in health.headers["x-content-type-options"]


def test_sample_shop_forecast_and_export(client):
    opened = client.post("/api/workspaces/sample")
    assert opened.status_code == 200
    assert opened.json()["shop"]["is_demo"] is True
    settings = client.patch("/api/settings", json={"prefer_tabpfn": False, "language": "english"})
    assert settings.status_code == 200
    forecast = client.post("/api/forecasts", json={"horizon_days": 14})
    assert forecast.status_code == 200
    body = forecast.json()
    assert body["status"] == "completed"
    detail = client.get(f"/api/forecasts/{body['id']}")
    assert detail.status_code == 200
    summary = detail.json()["summary"]["products"]
    assert summary
    model_ids = {item["model_id"] for item in summary if item["model_id"]}
    assert model_ids
    assert all(not str(model_id).startswith("tabpfn") for model_id in model_ids)
    dashboard = client.get("/api/dashboard")
    assert dashboard.status_code == 200
    dash = dashboard.json()
    assert dash["active_products"] >= 8
    assert dash["inventory_value"] is not None
    assert dash["has_forecast"] is True
    recommendations = client.get("/api/recommendations")
    assert recommendations.status_code == 200
    rows = recommendations.json()["recommendations"]
    assert rows
    assert rows[0]["explanation"]["source"] == "template"
    exported = client.get("/api/reports/export", params={"kind": "recommendations"})
    assert exported.status_code == 200
    assert "sku" in exported.text.splitlines()[0]
    hinglish = client.patch("/api/settings", json={"language": "hinglish"})
    assert hinglish.status_code == 200
    again = client.get("/api/recommendations")
    assert "hai" in again.json()["recommendations"][0]["explanation"]["summary"].lower() or "hai" in again.json()["recommendations"][0]["explanation"]["summary"]


def test_rename_local_shop_and_keep_sample_name(client):
    local = client.post("/api/workspaces/local")
    assert local.status_code == 200
    renamed = client.patch("/api/workspaces/name", json={"name": "  Gupta Stores  "})
    assert renamed.status_code == 200
    assert renamed.json()["shop"]["name"] == "Gupta Stores"
    status = client.get("/api/status")
    assert status.json()["shop"]["name"] == "Gupta Stores"
    blank = client.patch("/api/workspaces/name", json={"name": "   "})
    assert blank.status_code == 422
    sample = client.post("/api/workspaces/sample")
    assert sample.status_code == 200
    locked = client.patch("/api/workspaces/name", json={"name": "Not the sample"})
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "demo_locked"


def test_invalid_csv_and_duplicate_import(client):
    created = client.post("/api/workspaces/local")
    assert created.status_code == 200
    empty = client.post("/api/imports/preview", files={"file": ("empty.csv", b"", "text/csv")})
    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "invalid_file"
    good = (
        "date,product_name,sku,quantity,invoice_number\n"
        "01/10/2026,Tea,TEA,2,INV-1\n"
        "01/10/2026,Tea,TEA,2,INV-1\n"
        "32/10/2026,Tea,TEA,1,INV-2\n"
        "02/10/2026,Tea,TEA,-3,INV-3\n"
    ).encode()
    preview = client.post("/api/imports/preview", files={"file": ("bills.csv", good, "text/csv")})
    assert preview.status_code == 200
    body = preview.json()
    assert body["accepted_rows"] == 1
    assert body["duplicate_rows"] == 1
    assert any(issue["code"] == "invalid_date" for issue in body["issues"])
    assert any(issue["code"] == "negative_quantity" for issue in body["issues"])
    imported = client.post("/api/imports", files={"file": ("bills.csv", good, "text/csv")})
    assert imported.status_code == 200
    assert imported.json()["accepted_rows"] == 1
    again = client.post("/api/imports", files={"file": ("bills.csv", good, "text/csv")})
    assert again.status_code == 409
    products = client.get("/api/products")
    assert products.json()["products"][0]["name"] == "Tea"
    binary = client.post(
        "/api/imports/preview",
        files={"file": ("pic.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert binary.status_code == 422


def test_archive_and_stock_movement(client):
    client.post("/api/workspaces/local")
    created = client.post(
        "/api/products",
        json={"sku": "RICE-1", "name": "Rice 1kg", "current_stock": 5, "unit_cost": 40, "min_stock": 2},
    )
    assert created.status_code == 200
    product_id = created.json()["id"]
    sale = (
        "date,sku,product_name,quantity,invoice_number\n"
        "2026-10-01,RICE-1,Rice 1kg,1,INV-9\n"
    ).encode()
    imported = client.post("/api/imports", files={"file": ("rice.csv", sale, "text/csv")})
    assert imported.status_code == 200
    moved = client.post(
        "/api/inventory/movements",
        json={"product_id": product_id, "movement_type": "receipt", "quantity": 4, "note": "bag"},
    )
    assert moved.status_code == 200
    assert moved.json()["current_stock"] == 9
    archived = client.patch(f"/api/products/{product_id}", json={"archived": True})
    assert archived.status_code == 200
    detail = client.get(f"/api/products/{product_id}")
    assert detail.json()["recent_sales"]
    listed = client.get("/api/products")
    assert listed.json()["products"] == []
    hidden = client.get("/api/products", params={"status": "archived"})
    assert hidden.json()["products"][0]["archived"] is True


def test_import_rollback(client, monkeypatch):
    client.post("/api/workspaces/local")
    from app.db.store import Store

    original_commit = Store.commit

    def explode(_self):
        raise RuntimeError("disk full")

    monkeypatch.setattr(Store, "commit", explode)
    payload = (
        "date,sku,product_name,quantity,invoice_number\n"
        "2026-10-02,SOAP,Soap,1,INV-8\n"
    ).encode()
    response = client.post("/api/imports", files={"file": ("soap.csv", payload, "text/csv")})
    assert response.status_code == 500
    monkeypatch.setattr(Store, "commit", original_commit)
    products = client.get("/api/products")
    assert products.json()["products"] == []
