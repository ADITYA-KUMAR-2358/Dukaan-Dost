from __future__ import annotations

import math

Z_SCORES = {0.9: 1.2816, 0.95: 1.6449, 0.99: 2.3263}


def _round_pack(quantity: float, pack_size: int | None, moq: int | None) -> float:
    if quantity <= 0:
        return 0.0
    size = pack_size if pack_size and pack_size > 1 else 1
    rounded = math.ceil(quantity / size) * size
    if moq and rounded < moq:
        rounded = math.ceil(moq / size) * size
    return float(rounded)


def slow_status(
    recent_qty: float,
    prior_qty: float,
    stockout_days: int,
    observed_days: int,
    stock: float | None,
) -> str:
    if observed_days < 14:
        return "insufficient_history"
    if stockout_days >= 7:
        return "stockout_confounds_demand"
    if recent_qty == 0 and stock is not None and stock <= 0:
        return "out_of_stock"
    if recent_qty == 0:
        return "no_recent_sales"
    if prior_qty > 0 and recent_qty < 0.3 * prior_qty:
        return "declining"
    return "normal"


def build_recommendation(
    *,
    forecast: list[float],
    history_std: float | None,
    observed_days: int,
    stock: float | None,
    incoming: float,
    lead_time_days: int | None,
    pack_size: int | None,
    moq: int | None,
    service_level: float,
    coverage_days: int,
    recent_qty: float,
    prior_qty: float,
    stockout_days: int,
) -> dict:
    coverage = coverage_days if coverage_days > 0 else 14
    if len(forecast) >= coverage:
        coverage_demand = float(sum(forecast[:coverage]))
        avg_daily = coverage_demand / coverage
    elif forecast:
        avg_daily = float(sum(forecast) / len(forecast))
        coverage_demand = avg_daily * coverage
    else:
        avg_daily = 0.0
        coverage_demand = 0.0

    flags: list[dict[str, str]] = []
    limitations: list[str] = []
    if lead_time_days is None:
        lead_time_demand = None
        safety = None
        reorder_point = None
        policy = "lead_time_unknown"
        limitations.append("Supplier lead time is missing, so no reorder point was calculated.")
    else:
        lead_time_demand = avg_daily * lead_time_days
        if history_std is not None and observed_days >= 14:
            z = Z_SCORES.get(service_level, Z_SCORES[0.95])
            safety = z * history_std * math.sqrt(lead_time_days)
            policy = "lead_time_demand_plus_z_sigma"
        else:
            safety = 0.5 * lead_time_demand
            policy = "simpler_half_lead_time_demand"
            limitations.append(
                "Safety stock uses half of lead-time demand because demand variability is not reliable yet."
            )
        reorder_point = lead_time_demand + safety

    movement = slow_status(recent_qty, prior_qty, stockout_days, observed_days, stock)
    if stock is None:
        suggested = None
        limitations.append("Current stock is unknown, so no order quantity was calculated.")
        flags.append({"code": "stock_unknown", "reason": "Set current stock before trusting an order quantity."})
    else:
        cushion = safety or 0.0
        need = coverage_demand + cushion - stock - incoming
        suggested = _round_pack(max(0.0, need), pack_size, moq if need > 0 else None)
        if reorder_point is not None and stock <= reorder_point:
            flags.append(
                {
                    "code": "reorder",
                    "reason": "Usable stock is at or below the reorder point.",
                }
            )
        if lead_time_demand is not None and stock < lead_time_demand:
            flags.append(
                {
                    "code": "stockout_risk",
                    "reason": "Usable stock is below expected demand during the supplier lead time.",
                }
            )
        cover = coverage_demand + cushion
        if cover > 0 and stock > 2 * cover and movement in {"declining", "no_recent_sales"}:
            flags.append(
                {
                    "code": "overstock",
                    "reason": "Stock covers more than twice the planning need while recent demand is weak.",
                }
            )
    if movement == "declining":
        flags.append({"code": "slow_moving", "reason": "Recent demand is well below the previous two weeks."})
    elif movement == "no_recent_sales":
        flags.append({"code": "slow_moving", "reason": "There were no sales in the last 14 days, and stock is on hand."})
    elif movement == "stockout_confounds_demand":
        flags.append(
            {
                "code": "check_availability",
                "reason": "Several recent days were stockouts, so low sales are not treated as low demand.",
            }
        )
    elif movement == "insufficient_history":
        flags.append({"code": "thin_history", "reason": "There is not enough history to judge movement."})

    return {
        "reorder_point": None if reorder_point is None else round(reorder_point, 2),
        "safety_stock": None if safety is None else round(safety, 2),
        "lead_time_demand": None if lead_time_demand is None else round(lead_time_demand, 2),
        "suggested_qty": None if suggested is None else round(suggested, 2),
        "policy": policy,
        "slow_status": movement,
        "flags": flags,
        "limitations": limitations,
        "coverage_demand": round(coverage_demand, 2),
        "avg_daily": round(avg_daily, 2),
    }
