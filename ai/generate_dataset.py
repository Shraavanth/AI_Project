"""
Generate a synthetic dataset of NORMAL environmental readings.

Physical sensors are not available for this project, so the Isolation Forest
is trained on synthetic data that imitates realistic background conditions.
Some sensors are deliberately correlated (for example humidity falls when
temperature rises) so the "normal" region is not just six independent bells.

Run from anywhere:
    python ai/generate_dataset.py
"""

import os

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATASET_PATH = os.path.join(DATA_DIR, "environmental_data.csv")

FEATURES = [
    "temperature",
    "humidity",
    "smoke",
    "co2",
    "air_quality",
    "soil_moisture",
]


def generate_normal_dataset(samples: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    temperature = rng.normal(28.0, 3.5, samples)
    # Warmer air is usually drier
    humidity = 60.0 - 1.2 * (temperature - 28.0) + rng.normal(0, 7.0, samples)
    smoke = rng.normal(0.10, 0.03, samples)
    co2 = rng.normal(420.0, 35.0, samples)
    # Air quality index worsens a little with background smoke
    air_quality = 50.0 + 80.0 * (smoke - 0.10) + rng.normal(0, 8.0, samples)
    # Wetter air -> slightly wetter soil
    soil_moisture = 55.0 + 0.4 * (humidity - 60.0) + rng.normal(0, 9.0, samples)

    data = pd.DataFrame({
        "temperature": temperature,
        "humidity": humidity,
        "smoke": smoke,
        "co2": co2,
        "air_quality": air_quality,
        "soil_moisture": soil_moisture,
    })

    # Keep values in physically realistic ranges
    data["temperature"] = data["temperature"].clip(10, 50)
    data["humidity"] = data["humidity"].clip(10, 100)
    data["smoke"] = data["smoke"].clip(0, 1)
    data["co2"] = data["co2"].clip(300, 2000)
    data["air_quality"] = data["air_quality"].clip(0, 500)
    data["soil_moisture"] = data["soil_moisture"].clip(0, 100)
    return data.round(3)


def save_dataset(path: str = DATASET_PATH, samples: int = 3000) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = generate_normal_dataset(samples=samples)
    data.to_csv(path, index=False)
    return path


if __name__ == "__main__":
    out = save_dataset()
    df = pd.read_csv(out)
    print("Dataset created successfully!")
    print(f"Saved to: {out}")
    print(f"Number of samples: {len(df)}")
    print(df.describe().round(2))
