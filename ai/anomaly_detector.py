"""
Isolation Forest anomaly detection (step 1 of the AI pipeline).

    sensor readings -> validation -> Isolation Forest -> NORMAL / ANOMALY + score

The decision score comes from IsolationForest.decision_function():
    score > 0  -> looks like the normal training data
    score < 0  -> outlier (ANOMALY); the more negative, the stronger the anomaly

The model is loaded lazily. If the .pkl file is missing, or was saved by a
different scikit-learn version, it is retrained automatically (about a second)
so a fresh clone works without any manual step.
"""

import math
import os
import threading

import joblib
import numpy as np
import sklearn

try:
    from ai.train_model import MODEL_PATH, train_and_save
    from ai.generate_dataset import FEATURES
except ImportError:
    from train_model import MODEL_PATH, train_and_save
    from generate_dataset import FEATURES

# Physical limits used for input validation
VALID_RANGES = {
    "temperature": (-30.0, 90.0),
    "humidity": (0.0, 100.0),
    "smoke": (0.0, 1.0),
    "co2": (250.0, 5000.0),
    "air_quality": (0.0, 500.0),
    "soil_moisture": (0.0, 100.0),
}

_model = None
_model_info = {}
_lock = threading.Lock()


def _load_bundle():
    bundle = joblib.load(MODEL_PATH)
    if not isinstance(bundle, dict) or "model" not in bundle:
        raise ValueError("old model format")
    if bundle.get("sklearn_version") != sklearn.__version__:
        raise ValueError("model saved by a different scikit-learn version")
    return bundle


def get_model():
    global _model, _model_info
    if _model is not None:
        return _model
    with _lock:
        if _model is None:
            try:
                bundle = _load_bundle()
            except Exception:
                bundle = train_and_save()
            _model = bundle["model"]
            _model_info = {k: v for k, v in bundle.items() if k != "model"}
    return _model


def model_info() -> dict:
    get_model()
    return dict(_model_info)


def validate_readings(readings: dict) -> dict:
    """Return a cleaned copy of the readings or raise ValueError."""
    clean = {}
    for name in FEATURES:
        if name not in readings or readings[name] is None:
            raise ValueError(f"Missing sensor value: {name}")
        try:
            value = float(readings[name])
        except (TypeError, ValueError):
            raise ValueError(f"Sensor value for {name} is not a number")
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"Sensor value for {name} is not finite")
        low, high = VALID_RANGES[name]
        if value < low or value > high:
            raise ValueError(f"{name}={value} is outside the valid range {low}..{high}")
        clean[name] = value
    return clean


def predict_batch(readings_list: list) -> list:
    """Run the detector on many readings at once (one call per simulation tick)."""
    if not readings_list:
        return []
    model = get_model()
    X = np.array([[r[f] for f in FEATURES] for r in readings_list], dtype=float)
    predictions = model.predict(X)
    scores = model.decision_function(X)
    return [
        {
            "status": "NORMAL" if p == 1 else "ANOMALY",
            "score": round(float(s), 4),
        }
        for p, s in zip(predictions, scores)
    ]


def predict_environment(temperature, humidity, smoke, co2, air_quality, soil_moisture) -> dict:
    readings = validate_readings({
        "temperature": temperature,
        "humidity": humidity,
        "smoke": smoke,
        "co2": co2,
        "air_quality": air_quality,
        "soil_moisture": soil_moisture,
    })
    return predict_batch([readings])[0]
