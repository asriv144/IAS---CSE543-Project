# fetch_tranco.py
from tranco import Tranco
import pandas as pd
import os

os.makedirs("data/raw", exist_ok=True)
t = Tranco(cache=True, cache_dir=".tranco")
# get the latest list
latest = t.list()            # default is latest
domains = latest.top(500)   # change 1000 -> any N you want

# domains is a list like ['google.com','youtube.com',...]
df = pd.DataFrame({"url": ["https://" + d for d in domains]})
df.to_csv("data/raw/legit_local.csv", index=False)
print("Saved", len(df), "legit sites to data/raw/legit_local.csv")
