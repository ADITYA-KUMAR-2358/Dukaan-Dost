from __future__ import annotations

import math

import numpy as np

from app.services.forecasting.baselines import baseline_forecast, seasonal_naive
from app.services.forecasting.features import (
    demand_std,
    finite_count,
    future_matrix,
    positive_count,
    round_qty,
    supervised_rows,
    zero_ratio,
)
from app.services.forecasting.metrics import metric_block


def _scale(history: np.ndarray) -> float | None:
    if len(history) < 21:
        return None
    actual = []
    predicted = []
    for index in range(14, len(history)):
        if not math.isfinite(float(history[index])):
            continue
        pred = seasonal_naive(history[:index], 1)[0]
        actual.append(float(history[index]))
        predicted.append(pred)
    if len(actual) < 7:
        return None
    scale = float(np.mean(np.abs(np.asarray(actual) - np.asarray(predicted))))
    return scale if scale > 0 else None


def backtest(demand: np.ndarray, days, stockout: np.ndarray, predict_fn, baseline_id: str) -> dict | None:
    horizon = 7
    if len(demand) < 28:
        return None
    origin = len(demand) - horizon
    train_x, train_y = supervised_rows(demand, days, stockout, horizon=7, origin_exclusive=origin)
    future_x, target_days = future_matrix(demand[:origin], days[:origin], stockout[:origin], horizon)
    if future_x is None or len(target_days) != horizon:
        return None
    # The held-out dates must line up with the real calendar after the origin.
    expected = days[origin:]
    if target_days != expected:
        return None
    actual_mask = ~stockout[origin:]
    actual = demand[origin:]
    try:
        primary = np.asarray(predict_fn(train_x, train_y, future_x), dtype=np.float64)
    except Exception:
        return None
    if len(primary) != horizon:
        return None
    base = np.asarray(baseline_forecast(demand[:origin], horizon, baseline_id), dtype=np.float64)
    usable_actual = actual[actual_mask]
    if len(usable_actual) == 0:
        return {"primary": None, "baseline": None, "note": "held_out_days_were_stockouts"}
    scale = _scale(demand[:origin])
    return {
        "method": "fixed_origin_7_day",
        "primary": metric_block(usable_actual, primary[actual_mask], scale),
        "baseline": metric_block(usable_actual, base[actual_mask], scale),
        "baseline_id": baseline_id,
    }


def forecast_series(
    demand: np.ndarray,
    days,
    stockout: np.ndarray,
    horizon: int,
    prefer_tabpfn: bool,
    tabpfn_enabled: bool,
    tabpfn_version: str,
    adapter,
) -> dict:
    observed = finite_count(demand)
    if observed < 7 or not days:
        return {
            "status": "insufficient_data",
            "model_id": None,
            "baseline_id": None,
            "fallback_reason": "fewer_than_7_observed_days",
            "predictions": [],
            "evaluation": None,
            "limitations": ["This product does not have a week of demand yet."],
            "history": [],
        }
    ratio = zero_ratio(demand)
    intermittent = ratio >= 0.45 and positive_count(demand) >= 2
    if intermittent:
        baseline_id = "croston"
    elif observed >= 14:
        baseline_id = "seasonal_naive_7"
    else:
        baseline_id = "moving_average_7"

    usable = demand.astype(float).copy()
    usable[stockout] = np.nan
    train_x, train_y = supervised_rows(demand, days, stockout, horizon=min(horizon, 14))
    future_x, target_days = future_matrix(demand, days, stockout, horizon)
    baseline_values = baseline_forecast(usable, horizon, baseline_id)

    model_id = baseline_id
    fallback_reason = None
    predictions = baseline_values
    limitations = [
        "Forecasts are daily demand estimates, not a promise of sales.",
        "Stockout days are left out of the averages so an empty shelf is not treated as low demand.",
    ]

    can_try_tabpfn = (
        prefer_tabpfn
        and tabpfn_enabled
        and adapter is not None
        and future_x is not None
        and len(train_y) >= 20
        and observed >= 21
    )
    if prefer_tabpfn and tabpfn_enabled and not can_try_tabpfn:
        fallback_reason = "tabpfn_requirements_not_met"
    if can_try_tabpfn:
        try:
            raw = adapter(train_x, train_y, future_x, tabpfn_version)
            predictions = [round_qty(value) for value in raw]
            model_id = f"tabpfn-{tabpfn_version}"
            fallback_reason = None
        except Exception as exc:
            fallback_reason = f"tabpfn_failed:{type(exc).__name__}"
            model_id = baseline_id
            predictions = baseline_values
            limitations.append("TabPFN did not return a forecast. The baseline above was used instead.")

    if model_id == baseline_id and future_x is not None:
        limitations.append("The number you see is a baseline forecast, not a TabPFN forecast.")
    if intermittent and model_id != baseline_id:
        limitations.append("Demand is intermittent. Compare the result with the Croston baseline.")
    if observed < 21:
        limitations.append("History is shorter than three weeks, so the forecast is rough.")

    evaluation = None
    if future_x is not None and len(demand) >= 28:
        def predict_fn(train_xx, train_yy, test_xx):
            if model_id.startswith("tabpfn") and adapter is not None:
                return adapter(train_xx, train_yy, test_xx, tabpfn_version)
            return baseline_forecast(usable[: len(demand) - 7], 7, baseline_id)

        # Evaluation uses the same model family. Baseline path does not call TabPFN.
        if model_id.startswith("tabpfn"):
            evaluation = backtest(demand, days, stockout, predict_fn, baseline_id)
        else:
            origin = len(demand) - 7
            actual = demand[origin:]
            mask = ~stockout[origin:]
            primary = np.asarray(baseline_forecast(usable[:origin], 7, baseline_id))
            base = primary.copy()
            if mask.any():
                scale = _scale(demand[:origin])
                evaluation = {
                    "method": "fixed_origin_7_day",
                    "primary": metric_block(actual[mask], primary[mask], scale),
                    "baseline": metric_block(actual[mask], base[mask], scale),
                    "baseline_id": baseline_id,
                    "note": "primary_model_is_the_baseline",
                }

    points = []
    if future_x is not None:
        for day, pred, base in zip(target_days, predictions, baseline_values, strict=False):
            points.append(
                {
                    "date": day.isoformat(),
                    "predicted_qty": round_qty(pred),
                    "baseline_qty": round_qty(base),
                }
            )
    return {
        "status": "ok" if points else "insufficient_data",
        "model_id": model_id if points else None,
        "baseline_id": baseline_id if points else None,
        "fallback_reason": fallback_reason,
        "predictions": points,
        "evaluation": evaluation,
        "std": demand_std(demand, stockout),
        "limitations": limitations,
        "history": [
            {
                "date": day.isoformat(),
                "quantity": None if bool(flag) or not math.isfinite(float(qty)) else round_qty(float(qty)),
                "stockout": bool(flag),
            }
            for day, qty, flag in zip(days, demand, stockout)
        ],
    }
