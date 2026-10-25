"""
Quick look at the training dataset.

    python ai/analyze_data.py

Prints summary statistics. If matplotlib is installed it also shows histograms
(matplotlib is optional and not needed by the web application).
"""

import os

import pandas as pd

try:
    from ai.generate_dataset import DATASET_PATH, save_dataset
except ImportError:
    from generate_dataset import DATASET_PATH, save_dataset

if not os.path.exists(DATASET_PATH):
    save_dataset()

data = pd.read_csv(DATASET_PATH)

print("Dataset shape:", data.shape)
print("\nColumns:", data.columns.tolist())
print("\nFirst 5 rows:\n", data.head())
print("\nStatistical summary:\n", data.describe().round(2))
print("\nMissing values:\n", data.isnull().sum())
print("\nCorrelation matrix:\n", data.corr().round(2))

try:
    import matplotlib.pyplot as plt

    data.hist(figsize=(12, 8))
    plt.suptitle("Environmental Data Distribution", fontsize=16)
    plt.tight_layout()
    plt.show()
except ImportError:
    print("\n(matplotlib not installed - skipping histograms)")
