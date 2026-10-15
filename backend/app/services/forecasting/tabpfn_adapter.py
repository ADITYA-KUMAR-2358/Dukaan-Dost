"""TabPFN adapter.

When TABPFN_API_KEY is set, predictions go to the Prior Labs TabPFN API through
tabpfn-client. The key is read from the environment and is never written to disk
by this app. When the key is empty, a locally installed tabpfn package can still
be used. If neither is available, the caller keeps the named baseline.
"""

from __future__ import annotations

import importlib.metadata
from typing import Any

import numpy as np

_MODEL: Any = None
_READY: dict[str, Any] | None = None


def probe() -> dict[str, Any]:
    global _READY
    if _READY is not None:
        return _READY
    from app.config import get_settings

    if get_settings().tabpfn_api_key.strip():
        _READY = {
            "installed": True,
            "version": "api",
            "compatible": True,
            "mode": "api",
            "detail": "tabpfn_api",
        }
        return _READY
    try:
        version = importlib.metadata.version("tabpfn")
    except importlib.metadata.PackageNotFoundError:
        _READY = {
            "installed": False,
            "version": None,
            "compatible": False,
            "mode": "unavailable",
            "detail": "tabpfn_api_key_missing",
        }
        return _READY
    major = int(version.split(".")[0]) if version[:1].isdigit() else 0
    compatible = major >= 9
    _READY = {
        "installed": True,
        "version": version,
        "compatible": compatible,
        "mode": "local",
        "detail": "ok" if compatible else "tabpfn_version_unsupported",
    }
    return _READY


def reset_cache() -> None:
    global _MODEL, _READY
    _MODEL = None
    _READY = None


def _model(version_name: str):
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    from app.config import get_settings

    key = get_settings().tabpfn_api_key.strip()
    if key:
        import tabpfn_client
        from tabpfn_client import TabPFNRegressor

        tabpfn_client.set_access_token(key)
        _MODEL = TabPFNRegressor()
        return _MODEL
    from tabpfn import TabPFNRegressor
    from tabpfn.constants import ModelVersion

    if version_name == "v2":
        _MODEL = TabPFNRegressor.create_default_for_version(ModelVersion.V2)
    elif version_name in {"v3.5-fast", "v3.5_fast"}:
        _MODEL = TabPFNRegressor.create_default_for_version(ModelVersion.V3_5_FAST)
    else:
        _MODEL = TabPFNRegressor()
    return _MODEL


def predict(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    version_name: str = "v2",
) -> np.ndarray:
    status = probe()
    if not status["installed"] or not status["compatible"]:
        raise RuntimeError(status["detail"])
    if train_x.ndim != 2 or test_x.ndim != 2:
        raise ValueError("tabpfn_expected_2d")
    if train_x.shape[0] != train_y.shape[0]:
        raise ValueError("tabpfn_shape_mismatch")
    if train_x.shape[1] != test_x.shape[1]:
        raise ValueError("tabpfn_feature_mismatch")
    if not np.isfinite(train_x).all() or not np.isfinite(train_y).all() or not np.isfinite(test_x).all():
        raise ValueError("tabpfn_non_finite")
    model = _model(version_name)
    model.fit(train_x, train_y)
    predicted = np.asarray(model.predict(test_x), dtype=np.float64)
    if predicted.shape[0] != test_x.shape[0]:
        raise RuntimeError("tabpfn_bad_output")
    return np.clip(predicted, 0, None)
