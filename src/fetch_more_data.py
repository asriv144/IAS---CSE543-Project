import pandas as pd
import requests
import os
from tranco import Tranco

PHISHTANK_API = "https://openphish.com/feed.txt"  # Free feed
LEGIT_SOURCES = [
    "https://tranco-list.eu/download_daily/Top-100k.csv",  # Top legitimate sites
]

def fetch_phishing_urls():
    """Fetch more phishing URLs from OpenPhish"""
    print("Fetching phishing URLs from OpenPhish...")
    try:
        r = requests.get(PHISHTANK_API, timeout=30)
        r.raise_for_status()
        urls = [line.strip() for line in r.text.splitlines() if line.strip() and line.startswith('http')]
        print(f"Fetched {len(urls)} phishing URLs")
        return pd.DataFrame({"url": urls})
    except Exception as e:
        print(f"Error fetching phishing URLs: {e}")
        return pd.DataFrame()

def fetch_legitimate_urls():
    """Fetch more legitimate URLs from Tranco"""
    print("Fetching legitimate URLs from Tranco...")
    try:
        t = Tranco(cache=True, cache_dir=".tranco")
        latest = t.list()
        domains = latest.top(2000)  # Get top 2000 legitimate sites
        urls = [f"https://{d}" for d in domains]
        print(f"Fetched {len(urls)} legitimate URLs")
        return pd.DataFrame({"url": urls})
    except Exception as e:
        print(f"Error fetching legitimate URLs: {e}")
        return pd.DataFrame()

def merge_with_existing():
    """Merge new data with existing dataset"""
    existing_path = "data/raw/real_urls.csv"
    
    if os.path.exists(existing_path):
        existing = pd.read_csv(existing_path)
        print(f"Existing dataset: {len(existing)} URLs")
    else:
        existing = pd.DataFrame(columns=["url", "label"])
        print("No existing dataset found, creating new one")
    
    # Fetch new data
    phish_df = fetch_phishing_urls()
    legit_df = fetch_legitimate_urls()
    
    if len(phish_df) > 0:
        phish_df['label'] = 1
    if len(legit_df) > 0:
        legit_df['label'] = 0
    
    # Combine
    new_data = pd.concat([phish_df, legit_df], ignore_index=True)
    
    if len(existing) > 0:
        combined = pd.concat([existing, new_data], ignore_index=True)
        combined = combined.drop_duplicates(subset=['url']).reset_index(drop=True)
    else:
        combined = new_data.drop_duplicates(subset=['url']).reset_index(drop=True)
    
    # Save
    os.makedirs("data/raw", exist_ok=True)
    combined.to_csv(existing_path, index=False)
    print(f"\nSaved {len(combined)} total URLs to {existing_path}")
    print(f"  Phishing (1): {len(combined[combined['label']==1])}")
    print(f"  Legitimate (0): {len(combined[combined['label']==0])}")
    
    return combined

if __name__ == "__main__":
    merge_with_existing()

