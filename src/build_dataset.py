# build_dataset.py
import pandas as pd
import requests
import os

PHISH_URL = "https://raw.githubusercontent.com/openphish/public_feed/refs/heads/main/feed.txt"
LEGIT_LOCAL = "data/raw/legit_local.csv"   # create this file (one url per row, header 'url')

def fetch_openphish():
    print("Fetching OpenPhish feed...")
    r = requests.get(PHISH_URL, timeout=10)
    r.raise_for_status()
    lines = [l.strip() for l in r.text.splitlines() if l.strip()]
    return pd.DataFrame({"url": lines})

def load_legit_local():
    if not os.path.exists(LEGIT_LOCAL):
        raise FileNotFoundError(f"{LEGIT_LOCAL} not found. Create it with one column 'url'.")
    df = pd.read_csv(LEGIT_LOCAL)
    if "url" not in df.columns:
        # try if single column without header
        df = pd.read_csv(LEGIT_LOCAL, header=None, names=["url"])
    # Normalize domains -> ensure schema
    df["url"] = df["url"].astype(str).apply(lambda u: u if u.startswith(("http://","https://")) else "https://"+u)
    return df

def build_and_save(phish_df, legit_df, out_path="data/raw/real_urls.csv", sample_neg=None):
    phish_df = phish_df.drop_duplicates(subset=["url"]).reset_index(drop=True)
    legit_df = legit_df.drop_duplicates(subset=["url"]).reset_index(drop=True)

    phish_df = phish_df.assign(label=1)
    legit_df = legit_df.assign(label=0)

    # Optionally sample legit to balance (pass sample_neg=int)
    if sample_neg is not None:
        legit_df = legit_df.sample(n=sample_neg, random_state=42) \
                         .reset_index(drop=True)

    combined = pd.concat([phish_df, legit_df], axis=0).sample(frac=1, random_state=42).reset_index(drop=True)
    combined.to_csv(out_path, index=False)
    print(f"Saved {len(combined)} rows to {out_path}")
    return combined

if __name__ == "__main__":
    phish = fetch_openphish()
    legit = load_legit_local()
    # If you want to balance 1:1 use sample_neg=len(phish)
    df = build_and_save(phish, legit, out_path="data/raw/real_urls.csv", sample_neg=None)
    print(df.head())



