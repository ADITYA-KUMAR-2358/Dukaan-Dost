from __future__ import annotations

import json
import threading
import time
from datetime import date

import httpx

from app.config import Settings, get_settings
from app.services.explanations.grounding import template_explanation, validate_model_payload

_lock = threading.Lock()
_rpm_marks: list[float] = []
_visitor_marks: dict[str, list[float]] = {}
_day: date | None = None
_day_count = 0


def gemma_configured(settings: Settings | None = None) -> bool:
    current = settings or get_settings()
    return bool(current.llm_api_key.strip())


def _claim_quota(visitor: str, settings: Settings) -> str | None:
    global _day, _day_count
    now = time.monotonic()
    today = date.today()
    with _lock:
        if _day != today:
            _day = today
            _day_count = 0
        if settings.llm_max_per_day > 0 and _day_count >= settings.llm_max_per_day:
            return "daily_quota"
        recent = [mark for mark in _rpm_marks if now - mark < 60]
        if settings.llm_max_rpm > 0 and len(recent) >= settings.llm_max_rpm:
            return "rpm_limit"
        visits = [mark for mark in _visitor_marks.get(visitor, []) if now - mark < 600]
        if settings.submit_limit > 0 and len(visits) >= settings.submit_limit:
            return "submit_limit"
        recent.append(now)
        visits.append(now)
        _rpm_marks[:] = recent
        _visitor_marks[visitor] = visits
        _day_count += 1
        return None


def _message_text(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def explain_facts(facts: dict, language: str, visitor: str = "local") -> dict:
    template = template_explanation(facts, "hinglish" if language == "hinglish" else "english")
    settings = get_settings()
    if not gemma_configured(settings):
        template["model_ready"] = False
        return template
    blocked = _claim_quota(visitor, settings)
    if blocked:
        template["model_ready"] = False
        template["fallback_reason"] = blocked
        return template
    prompt = json.dumps(
        {
            "task": "Explain these verified inventory facts. Do not change any number.",
            "language": language,
            "facts": facts,
            "response_schema": {
                "summary": "string",
                "assumptions": ["string"],
                "verify": ["string"],
                "cited_stock": facts.get("stock"),
                "cited_reorder_point": facts.get("reorder_point"),
                "cited_suggested_qty": facts.get("suggested_qty"),
                "cited_avg_daily": facts.get("avg_daily"),
            },
        }
    )[:4000]
    body: dict = {
        "model": settings.llm_model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": "You explain shop inventory facts in JSON only. Never invent quantities. Never run tools or code.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    if settings.llm_thinking_level.strip():
        body["thinking_config"] = {"thinking_level": settings.llm_thinking_level.strip()}
    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.llm_api_key.strip()}"}
    waited = False
    stripped_thinking = False
    try:
        while True:
            response = httpx.post(url, json=body, headers=headers, timeout=settings.llm_timeout)
            if response.status_code == 429 and not waited and settings.llm_max_wait > 0:
                retry_after = response.headers.get("retry-after", "")
                pause = settings.llm_max_wait
                if retry_after.replace(".", "", 1).isdigit():
                    pause = min(pause, float(retry_after))
                time.sleep(pause)
                waited = True
                continue
            if response.status_code == 400 and "thinking_config" in body and not stripped_thinking:
                body.pop("thinking_config")
                stripped_thinking = True
                continue
            response.raise_for_status()
            validated = validate_model_payload(_message_text(response.json()), facts)
            if validated is None:
                template["model_ready"] = True
                template["fallback_reason"] = "model_output_rejected"
                return template
            validated["model_ready"] = True
            return validated
    except Exception:
        template["model_ready"] = False
        template["fallback_reason"] = "model_request_failed"
        return template
