#for checking 0 and 1
# inspect_dataset.py
import pandas as pd
df = pd.read_csv("data/raw/real_urls.csv")
print("Total rows:", len(df))
print("Label counts:")
print(df['label'].value_counts())
print("\nA few phishing examples (label=1):")
print(df[df['label']==1].head(5).to_string(index=False))
print("\nA few legitimate examples (label=0):")
print(df[df['label']==0].head(10).to_string(index=False))