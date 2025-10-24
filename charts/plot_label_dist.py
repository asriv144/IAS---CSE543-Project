# charts/plot_label_dist.py
import pandas as pd
import matplotlib.pyplot as plt
import os
os.makedirs("charts", exist_ok=True)

df = pd.read_csv("data/processed/url_feature.csv")
counts = df['label'].value_counts().sort_index()  # 0 then 1

labels = ['Legitimate (0)', 'Phishing (1)']
values = [counts.get(0,0), counts.get(1,0)]

plt.figure(figsize=(6,4))
plt.bar(labels, values)
plt.title("Label distribution (dataset)")
plt.ylabel("Number of URLs")
plt.tight_layout()
plt.savefig("charts/label_dist.png", dpi=150)
print("Saved charts/label_dist.png")
