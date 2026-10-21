import pandas as pd
import matplotlib.pyplot as plt

# Load the environmental dataset
data = pd.read_csv("../data/environmental_data.csv")

print("Dataset shape:")
print(data.shape)

print("\nColumn names:")
print(data.columns.tolist())

print("\nFirst 5 rows:")
print(data.head())

print("\nStatistical summary:")
print(data.describe())

print("\nMissing values:")
print(data.isnull().sum())

# Plot histograms for all environmental parameters
data.hist(figsize=(12, 8))

plt.suptitle("Environmental Data Distribution", fontsize=16)
plt.tight_layout()
plt.show()