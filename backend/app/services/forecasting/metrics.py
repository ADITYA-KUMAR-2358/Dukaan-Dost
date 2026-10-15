from __future__ import annotations

import numpy as np


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def wape(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    denom = float(np.sum(np.abs(actual)))
    if denom == 0:
        return None
    return float(np.sum(np.abs(actual - predicted)) / denom)


def mase(actual: np.ndarray, predicted: np.ndarray, scale: float | None) -> float | None:
    if scale is None or scale == 0:
        return None
    return float(mae(actual, predicted) / scale)


def metric_block(actual: np.ndarray, predicted: np.ndarray, scale: float | None) -> dict:
    if len(actual) == 0:
        return {"mae": None, "rmse": None, "wape": None, "mase": None, "n": 0}
    return {
        "mae": round(mae(actual, predicted), 4),
        "rmse": round(rmse(actual, predicted), 4),
        "wape": None if wape(actual, predicted) is None else round(wape(actual, predicted), 4),
        "mase": None if mase(actual, predicted, scale) is None else round(mase(actual, predicted, scale), 4),
        "n": int(len(actual)),
    }
