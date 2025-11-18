#handles loaading/cleaning csvs

# src/utils.py
import pandas as pd
from urllib.parse import urlparse

def normalize_url(u: str) -> str:
    u = str(u).strip()
    if not u:
        return ""
    if not u.startswith(("http://", "https://")):
        u = "http://" + u
    return u

def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # assume url column exists; try common names if not
    url_cols = [c for c in df.columns if c.lower() in ("url","link","website")]
    if not url_cols:
        raise ValueError("CSV must contain a column named url/link/website")
    col = url_cols[0]
    df = df.rename(columns={col: "url"})
    df['url'] = df['url'].astype(str).apply(normalize_url)
    df = df.drop_duplicates(subset=['url'])
    df = df[df['url'].str.len() > 6].reset_index(drop=True)
    # if label column present, normalize to 0/1
    if 'label' in df.columns:
        df['label'] = df['label'].astype(int)
    return df

