from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np

MAX_LAG = 14
FEATURE_NAMES = [
    "lag_1",
    "lag_7",
    "lag_14",
    "roll_mean_7",
    "roll_std_7",
    "dow",
    "month",
    "days_since_sale",
    "trend_7",
    "zero_ratio_14",
    "horizon",
]


def _lag(history: np.ndarray, k: int) -> float:
    if len(history) < k:
        return 0.0
    value = history[-k]
    if np.isfinite(value):
        return float(value)
    for step in range(k + 1, len(history) + 1):
        older = history[-step]
        if np.isfinite(older):
            return float(older)
    return 0.0


def feature_vector(history: np.ndarray, target_day: date, horizon: int) -> np.ndarray | None:
    """Build features using only history from before the forecast origin.

    `history` must end on the last day that is already known. `target_day` is
    the calendar day being predicted. Horizon is how many days ahead that is.
    """
    if len(history) < MAX_LAG:
        return None
    finite = history[np.isfinite(history)]
    if len(finite) < 7:
        return None
    window = history[-7:]
    finite_window = window[np.isfinite(window)]
    if len(finite_window) == 0:
        return None
    roll_mean = float(finite_window.mean())
    roll_std = float(finite_window.std()) if len(finite_window) > 1 else 0.0
    previous = history[-14:-7]
    finite_previous = previous[np.isfinite(previous)]
    previous_mean = float(finite_previous.mean()) if len(finite_previous) else roll_mean
    recent = history[-14:]
    finite_recent = recent[np.isfinite(recent)]
    zero_ratio = float(np.mean(finite_recent == 0)) if len(finite_recent) else 0.0
    days_since = len(history)
    for offset, value in enumerate(reversed(history), start=1):
        if np.isfinite(value) and value > 0:
            days_since = offset
            break
    return np.array(
        [
            _lag(history, 1),
            _lag(history, 7),
            _lag(history, 14),
            roll_mean,
            roll_std,
            float(target_day.weekday()),
            float(target_day.month),
            float(days_since),
            roll_mean - previous_mean,
            zero_ratio,
            float(horizon),
        ],
        dtype=np.float64,
    )


def fill_calendar(
    observations: list[tuple[date, float, bool]],
) -> tuple[list[date], np.ndarray, np.ndarray]:
    """Collapse lines into a continuous daily series.

    Stockout days are stored as NaN demand so averages do not treat a stockout
    as evidence that customers bought nothing.
    """
    if not observations:
        return [], np.array([]), np.array([])
    by_day: dict[date, list[tuple[float, bool]]] = {}
    for day, qty, stockout in observations:
        by_day.setdefault(day, []).append((qty, stockout))
    start = min(by_day)
    end = max(by_day)
    days: list[date] = []
    demand: list[float] = []
    stockout: list[bool] = []
    cursor = start
    while cursor <= end:
        rows = by_day.get(cursor, [])
        if rows and all(flag for _, flag in rows):
            days.append(cursor)
            demand.append(np.nan)
            stockout.append(True)
        else:
            total = sum(qty for qty, flag in rows if not flag)
            days.append(cursor)
            demand.append(float(total))
            stockout.append(False)
        cursor += timedelta(days=1)
    return days, np.asarray(demand, dtype=np.float64), np.asarray(stockout, dtype=bool)


def supervised_rows(
    demand: np.ndarray,
    days: list[date],
    stockout: np.ndarray,
    horizon: int,
    origin_exclusive: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Direct multi-horizon rows. Features at origin t never include day t or later."""
    usable = demand.astype(float).copy()
    usable[stockout] = np.nan
    last = len(demand) if origin_exclusive is None else origin_exclusive
    features: list[np.ndarray] = []
    targets: list[float] = []
    for origin in range(MAX_LAG, last):
        for step in range(1, horizon + 1):
            index = origin + step - 1
            if index >= len(demand):
                break
            if origin_exclusive is not None and index >= origin_exclusive:
                break
            if stockout[index]:
                continue
            vector = feature_vector(usable[:origin], days[index], step)
            if vector is None:
                continue
            features.append(vector)
            targets.append(float(demand[index]))
    if not features:
        return np.empty((0, len(FEATURE_NAMES))), np.empty((0,))
    return np.vstack(features), np.asarray(targets, dtype=np.float64)


def future_matrix(demand: np.ndarray, days: list[date], stockout: np.ndarray, horizon: int):
    usable = demand.astype(float).copy()
    usable[stockout] = np.nan
    origin_day = days[-1]
    rows = []
    target_days = []
    for step in range(1, horizon + 1):
        target = origin_day + timedelta(days=step)
        vector = feature_vector(usable, target, step)
        if vector is None:
            return None, []
        rows.append(vector)
        target_days.append(target)
    return np.vstack(rows), target_days


def demand_std(demand: np.ndarray, stockout: np.ndarray) -> float | None:
    usable = demand[np.isfinite(demand) & ~stockout]
    if len(usable) < 14:
        return None
    return float(usable.std())


def finite_count(demand: np.ndarray) -> int:
    return int(np.isfinite(demand).sum())


def zero_ratio(demand: np.ndarray) -> float:
    usable = demand[np.isfinite(demand)]
    if len(usable) == 0:
        return 1.0
    return float(np.mean(usable == 0))


def positive_count(demand: np.ndarray) -> int:
    return int(np.sum(np.isfinite(demand) & (demand > 0)))


def round_qty(value: float) -> float:
    if not math.isfinite(value):
        return 0.0
    return round(max(0.0, float(value)), 2)
