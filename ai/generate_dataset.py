import numpy as np
import pandas as pd

np.random.seed(42)

# Number of normal environmental readings
normal_samples = 1000

temperature = np.random.normal(28, 4, normal_samples)
humidity = np.random.normal(60, 10, normal_samples)
smoke = np.random.normal(0.10, 0.03, normal_samples)
co2 = np.random.normal(420, 40, normal_samples)
air_quality = np.random.normal(50, 10, normal_samples)
soil_moisture = np.random.normal(55, 12, normal_samples)

data = pd.DataFrame({
    "temperature": temperature,
    "humidity": humidity,
    "smoke": smoke,
    "co2": co2,
    "air_quality": air_quality,
    "soil_moisture": soil_moisture
})

# Keep values within realistic ranges
data["temperature"] = data["temperature"].clip(10, 50)
data["humidity"] = data["humidity"].clip(10, 100)
data["smoke"] = data["smoke"].clip(0, 1)
data["co2"] = data["co2"].clip(300, 2000)
data["air_quality"] = data["air_quality"].clip(0, 500)
data["soil_moisture"] = data["soil_moisture"].clip(0, 100)

# Save dataset
data.to_csv("../data/environmental_data.csv", index=False)

print("Dataset created successfully!")
print(f"Number of samples: {len(data)}")
print(data.head())
