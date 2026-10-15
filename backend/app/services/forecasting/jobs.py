from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.db.session import open_store
from app.models.entities import (
    AppSetting,
    ForecastPoint,
    ForecastRun,
    Product,
    Recommendation,
    SaleLine,
)
from app.services.forecasting.engine import forecast_series
from app.services.forecasting.features import fill_calendar, finite_count
from app.services.forecasting.tabpfn_adapter import predict as tabpfn_predict
from app.services.inventory.recommendations import build_recommendation

# Tests replace this with a fake that never downloads weights.
ADAPTER = tabpfn_predict


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _window(days, demand, stockout, end, length: int) -> tuple[float, int]:
    start = end - timedelta(days=length - 1)
    total = 0.0
    stockouts = 0
    for day, qty, flag in zip(days, demand, stockout):
        if start <= day <= end:
            if flag:
                stockouts += 1
            elif math.isfinite(float(qty)):
                total += float(qty)
    return total, stockouts


def execute_run(run_id: str) -> None:
    session = open_store()
    try:
        run = session.get(ForecastRun, run_id)
        if run is None:
            return
        run.status = "running"
        session.commit()
        settings_row = session.get(AppSetting, run.shop_id)
        prefer = True if settings_row is None else settings_row.prefer_tabpfn
        service_level = 0.95 if settings_row is None else settings_row.service_level
        coverage_days = 14 if settings_row is None else settings_row.coverage_days
        app_settings = get_settings()
        products = session.find(Product, {"shop_id": run.shop_id, "archived": False})
        summary = []
        for product in products:
            lines = session.find(SaleLine, {"product_id": product.id}, sort=[("sale_date", 1)])
            observations = []
            for line in lines:
                net = 0.0 if line.stockout else max(0.0, line.quantity - line.returned_quantity)
                observations.append((line.sale_date, net, line.stockout))
            days, demand, stockout = fill_calendar(observations)
            result = forecast_series(
                demand,
                days,
                stockout,
                run.horizon_days,
                prefer_tabpfn=prefer,
                tabpfn_enabled=app_settings.tabpfn_enabled,
                tabpfn_version=app_settings.tabpfn_model_version,
                adapter=ADAPTER,
            )
            product_summary = {
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "status": result["status"],
                "model_id": result["model_id"],
                "baseline_id": result["baseline_id"],
                "fallback_reason": result["fallback_reason"],
                "evaluation": result["evaluation"],
                "limitations": result["limitations"],
                "history": result["history"],
            }
            summary.append(product_summary)
            if result["status"] != "ok":
                continue
            for point in result["predictions"]:
                session.add(
                    ForecastPoint(
                        run_id=run.id,
                        product_id=product.id,
                        forecast_date=datetime.fromisoformat(point["date"]).date(),
                        predicted_qty=point["predicted_qty"],
                        baseline_qty=point["baseline_qty"],
                        model_id=result["model_id"],
                        baseline_id=result["baseline_id"],
                    )
                )
            recent, stockout_days = _window(days, demand, stockout, days[-1], 14)
            prior, _prior_stockouts = _window(
                days, demand, stockout, days[-1] - timedelta(days=14), 14
            )
            calc = build_recommendation(
                forecast=[point["predicted_qty"] for point in result["predictions"]],
                history_std=result.get("std"),
                observed_days=finite_count(demand),
                stock=product.current_stock,
                incoming=product.incoming_qty or 0,
                lead_time_days=product.lead_time_days,
                pack_size=product.pack_size,
                moq=product.moq,
                service_level=service_level,
                coverage_days=coverage_days,
                recent_qty=recent,
                prior_qty=prior,
                stockout_days=stockout_days,
            )
            facts = {
                "product_name": product.name,
                "stock": product.current_stock,
                "incoming": product.incoming_qty,
                "lead_time_days": product.lead_time_days,
                "reorder_point": calc["reorder_point"],
                "safety_stock": calc["safety_stock"],
                "suggested_qty": calc["suggested_qty"],
                "avg_daily": calc["avg_daily"],
                "coverage_demand": calc["coverage_demand"],
                "policy": calc["policy"],
                "slow_status": calc["slow_status"],
                "model_id": result["model_id"],
                "fallback_reason": result["fallback_reason"],
                "limitations": calc["limitations"] + result["limitations"],
            }
            session.add(
                Recommendation(
                    shop_id=run.shop_id,
                    product_id=product.id,
                    run_id=run.id,
                    reorder_point=calc["reorder_point"],
                    safety_stock=calc["safety_stock"],
                    lead_time_demand=calc["lead_time_demand"],
                    suggested_qty=calc["suggested_qty"],
                    policy=calc["policy"],
                    slow_status=calc["slow_status"],
                    flags_json=json.dumps(calc["flags"]),
                    facts_json=json.dumps(facts),
                    created_at=_now(),
                )
            )
        run.status = "completed"
        run.completed_at = _now()
        run.summary_json = json.dumps({"products": summary})
        session.commit()
    except Exception as exc:
        session.rollback()
        failed = session.get(ForecastRun, run_id)
        if failed is not None:
            failed.status = "failed"
            failed.error_code = type(exc).__name__
            failed.completed_at = _now()
            session.commit()
    finally:
        session.close()
