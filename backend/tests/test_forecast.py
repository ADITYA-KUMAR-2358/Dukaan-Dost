from datetime import date, timedelta

import numpy as np
import pytest

from app.services.explanations.grounding import template_explanation, validate_model_payload
from app.services.forecasting.baselines import moving_average, seasonal_naive
from app.services.forecasting.engine import forecast_series
from app.services.forecasting.features import feature_vector, fill_calendar
from app.services.inventory.recommendations import build_recommendation, slow_status


def _series(n=40):
    start = date(2026, 8, 1)
    days = [start + timedelta(days=offset) for offset in range(n)]
    demand = np.array([5 + (day.weekday() >= 5) for day in days], dtype=float)
    stockout = np.zeros(n, dtype=bool)
    return days, demand, stockout


def test_features_do_not_use_the_target_day():
    days, demand, _stockout = _series()
    original = feature_vector(demand[:20], days[20], 1)
    demand[20] = 999
    demand[25] = 999
    changed = feature_vector(demand[:20], days[20], 1)
    assert original is not None
    assert np.allclose(original, changed)


def test_stockout_days_are_not_zero_demand():
    day = date(2026, 9, 1)
    days, demand, stockout = fill_calendar(
        [(day, 0, True), (day + timedelta(days=1), 4, False)]
    )
    assert stockout[0]
    assert np.isnan(demand[0])
    assert demand[1] == 4


def test_fallback_is_not_called_tabpfn():
    days, demand, stockout = _series()

    def explode(*_args, **_kwargs):
        raise RuntimeError("weights missing")

    result = forecast_series(
        demand,
        days,
        stockout,
        horizon=7,
        prefer_tabpfn=True,
        tabpfn_enabled=True,
        tabpfn_version="v2",
        adapter=explode,
    )
    assert result["status"] == "ok"
    assert not str(result["model_id"]).startswith("tabpfn")
    assert result["fallback_reason"].startswith("tabpfn_failed")


def test_fake_tabpfn_keeps_its_name():
    days, demand, stockout = _series(50)

    def fake(_x, _y, test_x, version):
        return np.ones(len(test_x))

    result = forecast_series(
        demand,
        days,
        stockout,
        horizon=7,
        prefer_tabpfn=True,
        tabpfn_enabled=True,
        tabpfn_version=version if (version := "v2") else "v2",
        adapter=fake,
    )
    assert result["model_id"] == "tabpfn-v2"
    assert result["predictions"][0]["predicted_qty"] == 1


def test_baselines_cover_the_horizon():
    history = np.arange(21, dtype=float)
    assert len(seasonal_naive(history, 7)) == 7
    assert len(moving_average(history, 7)) == 7


def test_recommendation_does_not_invent_missing_stock():
    calc = build_recommendation(
        forecast=[2, 2, 2, 2, 2, 2, 2],
        history_std=1.0,
        observed_days=30,
        stock=None,
        incoming=0,
        lead_time_days=3,
        pack_size=10,
        moq=10,
        service_level=0.95,
        coverage_days=7,
        recent_qty=10,
        prior_qty=10,
        stockout_days=0,
    )
    assert calc["suggested_qty"] is None
    assert calc["reorder_point"] is not None
    assert any(flag["code"] == "stock_unknown" for flag in calc["flags"])


def test_reorder_uses_pack_size():
    calc = build_recommendation(
        forecast=[5] * 14,
        history_std=None,
        observed_days=10,
        stock=4,
        incoming=0,
        lead_time_days=2,
        pack_size=10,
        moq=10,
        service_level=0.95,
        coverage_days=7,
        recent_qty=20,
        prior_qty=20,
        stockout_days=0,
    )
    assert calc["policy"] == "simpler_half_lead_time_demand"
    assert calc["suggested_qty"] % 10 == 0
    assert calc["suggested_qty"] > 0


def test_slow_status_respects_stockouts():
    assert slow_status(0, 10, 8, 30, 5) == "stockout_confounds_demand"
    assert slow_status(1, 10, 0, 30, 5) == "declining"


def test_explanation_rejects_invented_numbers():
    facts = {
        "product_name": "Amul Butter 100g",
        "stock": 24,
        "reorder_point": 18,
        "suggested_qty": 10,
        "avg_daily": 6,
        "lead_time_days": 3,
        "policy": "lead_time_demand_plus_z_sigma",
        "slow_status": "normal",
    }
    bad = (
        '{"summary":"Order 99 units.","assumptions":["x"],"verify":["y"],'
        '"cited_stock":24,"cited_reorder_point":18,"cited_suggested_qty":10,"cited_avg_daily":6}'
    )
    assert validate_model_payload(bad, facts) is None
    good = (
        '{"summary":"Stock is 24 and the suggested order is 10.",'
        '"assumptions":["Formula output"],"verify":["Recount stock"],'
        '"cited_stock":24,"cited_reorder_point":18,"cited_suggested_qty":10,"cited_avg_daily":6}'
    )
    assert validate_model_payload(good, facts)["source"] == "gemma"
    text = template_explanation(facts, "hinglish")
    assert text["source"] == "template"
    assert "Amul Butter 100g" in text["summary"]


def test_tabpfn_adapter_rejects_bad_shapes(monkeypatch):
    from app.services.forecasting import tabpfn_adapter

    monkeypatch.setattr(
        tabpfn_adapter,
        "probe",
        lambda: {"installed": True, "compatible": True, "version": "9.1.0", "detail": "ok"},
    )
    with pytest.raises(ValueError):
        tabpfn_adapter.predict(np.zeros((4, 3)), np.zeros(4), np.zeros((2, 2)))
