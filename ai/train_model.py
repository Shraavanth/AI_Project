"""
Train the Isolation Forest anomaly detector and save it with Joblib.

The model only learns what NORMAL readings look like. Anything far away from
that region is reported as an ANOMALY. Deciding *which* kind of anomaly it is
(fire, pollution, heat) is done separately by ai/event_classifier.py.

Run from anywhere:
    python ai/train_model.py
"""

import os

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest

try:
    from ai.generate_dataset import DATASET_PATH, FEATURES, save_dataset
except ImportError:  # running as a plain script from inside ai/
    from generate_dataset import DATASET_PATH, FEATURES, save_dataset

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "environmental_anomaly_model.pkl")

# 1% of the (synthetic, noisy) training data is treated as outliers.
# The first version used 5%, which flagged about 1 in 20 perfectly normal
# readings - far too many false alarms for 20 agents reading every second.
CONTAMINATION = 0.01
N_ESTIMATORS = 200


def train_and_save(dataset_path: str = DATASET_PATH, model_path: str = MODEL_PATH) -> dict:
    if not os.path.exists(dataset_path):
        save_dataset(dataset_path)

    data = pd.read_csv(dataset_path)
    X = data[FEATURES].to_numpy(dtype=float)

    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination=CONTAMINATION,
        random_state=42,
    )
    model.fit(X)

    bundle = {
        "model": model,
        "features": FEATURES,
        "contamination": CONTAMINATION,
        "n_estimators": N_ESTIMATORS,
        "training_samples": int(len(X)),
        "sklearn_version": sklearn.__version__,
    }
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(bundle, model_path)
    return bundle


if __name__ == "__main__":
    info = train_and_save()
    print("Model trained successfully!")
    print(f"Training samples: {info['training_samples']}")
    print(f"Estimators: {info['n_estimators']}, contamination: {info['contamination']}")
    print("Features:", ", ".join(info["features"]))
    print(f"Saved to: {MODEL_PATH}")
