import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

# Load dataset
data = pd.read_csv("../data/environmental_data.csv")

# Features used by the AI model
features = [
    "temperature",
    "humidity",
    "smoke",
    "co2",
    "air_quality",
    "soil_moisture"
]

X = data[features]

# Create Isolation Forest model
model = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)

# Train the model
model.fit(X)

# Save the trained model
joblib.dump(model, "../models/environmental_anomaly_model.pkl")

print("Model trained successfully!")
print("Features used:")
for feature in features:
    print(f"- {feature}")

print("\nModel saved to:")
print("../models/environmental_anomaly_model.pkl")