import pandas as pd
import joblib

# Load the trained model
model = joblib.load("../models/environmental_anomaly_model.pkl")

# Environmental scenarios to test
scenarios = {
    "Normal": {
        "temperature": 28,
        "humidity": 60,
        "smoke": 0.10,
        "co2": 420,
        "air_quality": 50,
        "soil_moisture": 55
    },

    "Fire-like condition": {
        "temperature": 45,
        "humidity": 15,
        "smoke": 0.90,
        "co2": 950,
        "air_quality": 80,
        "soil_moisture": 20
    },

    "Pollution-like condition": {
        "temperature": 31,
        "humidity": 40,
        "smoke": 0.60,
        "co2": 1200,
        "air_quality": 180,
        "soil_moisture": 50
    }
}

features = [
    "temperature",
    "humidity",
    "smoke",
    "co2",
    "air_quality",
    "soil_moisture"
]

print("=" * 60)
print("ENVIRONMENTAL ANOMALY DETECTION")
print("=" * 60)

for name, values in scenarios.items():

    # Convert scenario to DataFrame
    sample = pd.DataFrame([values])

    # Predict
    prediction = model.predict(sample[features])[0]

    # Calculate anomaly score
    score = model.decision_function(sample[features])[0]

    if prediction == 1:
        result = "NORMAL"
    else:
        result = "ANOMALY"

    print(f"\nScenario: {name}")
    print("-" * 40)

    for feature in features:
        print(f"{feature}: {values[feature]}")

    print(f"Anomaly score: {score:.4f}")
    print(f"AI Decision: {result}")