"""Forecast baselines.

These are not TabPFN. Callers must keep the model id set to the function they used.
"""

from __future__ import annotations

import math

import numpy as np


def _finite_series(history: np.ndarray) -> list[float]:
    return [float(value) if math.isfinite(float(value)) else math.nan for value in history]


def seasonal_naive(history: np.ndarray, horizon: int, season: int = 7) -> list[float]:
    series = _finite_series(history)
    preds: list[float] = []
    for step in range(1, horizon + 1):
        index = len(series) - season + (step - 1)
        while index >= len(series):
            index -= season
        guard = 0
        while index >= 0 and not math.isfinite(series[index]) and guard < 8:
            index -= season
            guard += 1
        value = series[index] if index >= 0 and math.isfinite(series[index]) else 0.0
        preds.append(round(max(0.0, value), 2))
    return preds


def moving_average(history: np.ndarray, horizon: int, window: int = 7) -> list[float]:
    finite = [float(value) for value in history if math.isfinite(float(value))]
    tail = finite[-window:] if finite else []
    average = sum(tail) / len(tail) if tail else 0.0
    return [round(max(0.0, average), 2) for _ in range(horizon)]


def croston_rate(history: np.ndarray, alpha: float = 0.2) -> float | None:
    finite = [float(value) for value in history if math.isfinite(float(value))]
    if sum(1 for value in finite if value > 0) < 2:
        return None
    size = None
    interval = None
    gap = 1
    for value in finite:
        if value > 0:
            if size is None:
                size = value
                interval = float(gap)
            else:
                size = size + alpha * (value - size)
                interval = interval + alpha * (gap - interval)
            gap = 1
        else:
            gap += 1
    if not size or not interval:
        return None
    return max(0.0, size / interval)


def croston_forecast(history: np.ndarray, horizon: int) -> list[float] | None:
    rate = croston_rate(history)
    if rate is None:
        return None
    return [round(rate, 2) for _ in range(horizon)]


def choose_baseline(history: np.ndarray) -> tuple[str, list[float] | None]:
    finite = history[np.isfinite(history)]
    if len(finite) < 7:
        return "insufficient", None
    if float(np.mean(finite == 0)) >= 0.45 and int(np.sum(finite > 0)) >= 2:
        forecast = croston_forecast(history, 1)
        if forecast is not None:
            return "croston", forecast
    if len(finite) >= 14:
        return "seasonal_naive_7", seasonal_naive(history, 1)
    return "moving_average_7", moving_average(history, 1)


def baseline_forecast(history: np.ndarray, horizon: int, baseline_id: str) -> list[float]:
    if baseline_id == "croston":
        return croston_forecast(history, horizon) or moving_average(history, horizon)
    if baseline_id == "seasonal_naive_7":
        return seasonal_naive(history, horizon)
    return moving_average(history, horizon)
