# charts/plot_top_variance.py
import pandas as pd
import matplotlib.pyplot as plt
import os
os.makedirs("charts", exist_ok=True)

df = pd.read_csv("data/processed/url_feature.csv")
numeric = df.select_dtypes(include=['number']).drop(columns=['label'], errors='ignore')
variances = numeric.var().sort_values(ascending=False).head(8)

plt.figure(figsize=(7,4))
variances.sort_values().plot(kind='barh')  # horizontal bar for readability
plt.title("Top features by variance")
plt.xlabel("Variance")
plt.tight_layout()
plt.savefig("charts/top_variance.png", dpi=150)
print("Saved charts/top_variance.png")
