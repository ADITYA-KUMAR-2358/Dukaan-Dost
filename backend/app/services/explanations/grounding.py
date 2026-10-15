from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class ExplanationPayload(BaseModel):
    summary: str = Field(min_length=8, max_length=700)
    assumptions: list[str] = Field(max_length=6)
    verify: list[str] = Field(min_length=1, max_length=6)
    cited_stock: float | None = None
    cited_reorder_point: float | None = None
    cited_suggested_qty: float | None = None
    cited_avg_daily: float | None = None


def _fmt(value: float | None) -> str:
    if value is None:
        return "unknown"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def template_explanation(facts: dict[str, Any], language: str) -> dict[str, Any]:
    name = facts["product_name"]
    avg = _fmt(facts.get("avg_daily"))
    stock = _fmt(facts.get("stock"))
    lead = facts.get("lead_time_days")
    suggested = facts.get("suggested_qty")
    suggested_text = _fmt(suggested)
    reorder = _fmt(facts.get("reorder_point"))
    slow = facts.get("slow_status")
    policy = facts.get("policy")
    if language == "hinglish":
        if slow == "stockout_confounds_demand":
            summary = (
                f"{name} ki recent sales kam dikh sakti hain, lekin kai din stockout bhi the. "
                "Ise slow-moving maanne se pehle availability check karein."
            )
        elif suggested is None:
            summary = (
                f"{name} ka recent average demand {avg} unit per day hai. "
                "Stock number missing hai, isliye order quantity nahi banayi gayi."
            )
        elif policy == "lead_time_unknown":
            summary = (
                f"{name} ka average demand {avg} unit per day hai aur stock {stock} hai. "
                "Lead time missing hai, isliye reorder point nahi nikala gaya."
            )
        else:
            summary = (
                f"{name} ka average demand {avg} unit per day hai. "
                f"Lead time {lead} din, stock {stock}, reorder point {reorder}. "
                f"Suggested order {suggested_text} unit hai, pack size aur minimum order ke hisaab se."
            )
        assumptions = [
            "Yeh numbers forecast aur inventory formula se aaye hain, model ne inhe change nahi kiya.",
            "Safety stock tabhi statistical hai jab demand variation available ho.",
        ]
        verify = [
            "Supplier ka actual lead time confirm karein.",
            "Shelf stock aur incoming order ko dobara gin lein.",
        ]
    else:
        if slow == "stockout_confounds_demand":
            summary = (
                f"Recent sales for {name} look weak, and several of those days were stockouts. "
                "Check availability before treating it as slow-moving."
            )
        elif suggested is None:
            summary = (
                f"Recent average demand for {name} is {avg} units a day. "
                "Current stock is missing, so no order quantity was calculated."
            )
        elif policy == "lead_time_unknown":
            summary = (
                f"Average demand for {name} is {avg} units a day and stock is {stock}. "
                "Lead time is missing, so no reorder point was calculated."
            )
        else:
            summary = (
                f"Average demand for {name} is {avg} units a day. "
                f"Lead time is {lead} days, stock is {stock}, and the reorder point is {reorder}. "
                f"The suggested order is {suggested_text} units after pack size and minimum order."
            )
        assumptions = [
            "These figures come from the forecast and the inventory formula.",
            "Statistical safety stock is used only when demand variation is available.",
        ]
        verify = [
            "Confirm the supplier lead time.",
            "Recount shelf stock and any incoming order.",
        ]
    return {
        "language": language,
        "source": "template",
        "summary": summary,
        "assumptions": assumptions,
        "verify": verify,
    }


def _allowed_numbers(facts: dict[str, Any]) -> set[str]:
    allowed: set[str] = set()
    for value in facts.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        number = float(value)
        allowed.add(str(int(number)) if number.is_integer() else f"{number:.2f}")
        allowed.add(f"{number:.1f}".rstrip("0").rstrip("."))
        allowed.add(f"{number:.2f}".rstrip("0").rstrip("."))
    return allowed


def _close(left: float | None, right: float | None) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return abs(float(left) - float(right)) < 0.05


def validate_model_payload(raw: str, facts: dict[str, Any]) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return None
    try:
        payload = ExplanationPayload.model_validate(json.loads(match.group(0)))
    except (json.JSONDecodeError, ValidationError):
        return None
    if not _close(payload.cited_stock, facts.get("stock")):
        return None
    if not _close(payload.cited_reorder_point, facts.get("reorder_point")):
        return None
    if not _close(payload.cited_suggested_qty, facts.get("suggested_qty")):
        return None
    if not _close(payload.cited_avg_daily, facts.get("avg_daily")):
        return None
    allowed = _allowed_numbers(facts)
    for number in re.findall(r"\d+(?:\.\d+)?", payload.summary):
        if number not in allowed:
            return None
    return {
        "language": facts.get("language", "english"),
        "source": "gemma",
        "summary": payload.summary,
        "assumptions": payload.assumptions,
        "verify": payload.verify,
    }


def recommendation_facts(product, calc: dict, model_id: str | None, fallback_reason: str | None) -> dict:
    return {
        "product_name": product.name,
        "stock": product.current_stock,
        "incoming": product.incoming_qty,
        "lead_time_days": product.lead_time_days,
        "reorder_point": calc["reorder_point"],
        "safety_stock": calc["safety_stock"],
        "suggested_qty": calc["suggested_qty"],
        "avg_daily": calc["avg_daily"],
        "policy": calc["policy"],
        "slow_status": calc["slow_status"],
        "model_id": model_id,
        "fallback_reason": fallback_reason,
        "unit_cost_known": product.unit_cost is not None,
    }
