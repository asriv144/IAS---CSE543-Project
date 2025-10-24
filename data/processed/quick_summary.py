# data/processed/quick_summary.py
import pandas as pd
from pathlib import Path

IN = Path("data/processed/url_feature.csv")
OUT = Path("data/processed/quick_summary.txt")


df = pd.read_csv(IN)

# Basic info
rows, cols = df.shape
label_counts = df['label'].value_counts().to_dict() if 'label' in df.columns else {}

# Numeric features: pick top 5 by variance
numeric = df.select_dtypes(include=['number']).drop(columns=['label']) if 'label' in df.columns else df.select_dtypes(include=['number'])
top5_var = numeric.var().sort_values(ascending=False).head(5)

# First 5 rows (shorten long URLs)
examples = df.head(5).copy()
if 'url' in examples.columns:
    examples['url'] = examples['url'].str.slice(0,120)

# Build summary text
lines = []
lines.append(f"Dataset: {IN}")
lines.append(f"Rows × Columns: {rows} × {cols}")
lines.append("Label counts:")
for k,v in label_counts.items():
    lines.append(f"  {k} : {v}")
lines.append("\nTop 5 numeric features by variance:")
for f,v in top5_var.items():
    lines.append(f"  {f}: {v:.2f}")
lines.append("\nFirst 5 example rows:")
lines.append(examples.to_string(index=False))

# Save and print
OUT.write_text("\n".join(lines))
print("\n".join(lines))
print(f"\nSaved summary to {OUT}")
