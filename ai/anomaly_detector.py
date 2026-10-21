import os
import joblib
import pandas as pd


# Get the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build the correct path to the trained model
MODEL_PATH = os.path.join(
    BASE_DIR,
    "..",
    "models",
    "environmental_anomaly_model.pkl"
)

# Load the trained model
model = joblib.load(MODEL_PATH)

FEATURES = [
    "temperature",
    "humidity",
    "smoke",
    "co2",
    "air_quality",
    "soil_moisture"
]


def predict_environment(
    temperature,
    humidity,
    smoke,
    co2,
    air_quality,
    soil_moisture
):
    """
    Analyze environmental conditions and return
    anomaly status and anomaly score.
    """

    data = pd.DataFrame([{
        "temperature": temperature,
        "humidity": humidity,
        "smoke": smoke,
        "co2": co2,
        "air_quality": air_quality,
        "soil_moisture": soil_moisture
    }])

    prediction = model.predict(data[FEATURES])[0]
    score = model.decision_function(data[FEATURES])[0]

    if prediction == 1:
        status = "NORMAL"
    else:
        status = "ANOMALY"

    return {
        "status": status,
        "score": round(float(score), 4)
    }