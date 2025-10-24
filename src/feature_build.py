#feature_build

import os
import pandas as pd
from feature_extraction import extract_url_features

IN_PATH='data/raw/real_urls.csv'
OUT_DIR='data/processed'
OUT_PATH=os.path.join(OUT_DIR,"url_feature.csv")

os.makedirs(OUT_DIR, exist_ok=True)

infile=IN_PATH
print("Reading URLs from: ", infile)

df=pd.read_csv(infile)
print("Loaded rows: ", len(df))

#parse only the columns we need
if 'url' not in df.columns:
    df=df.rename(columns={df.columns[0]: 'url'})

rows=[]
for i,r in df.iterrows():
    url=r['url']
    try:
        feats=extract_url_features(url)
        feats['label']=int(r['label']) if 'label' in r and not pd.isna(r['label']) else None
        rows.append(feats)
    except Exception as e:
        print("Error extracting for" , url, ":", e)
        continue


out_df=pd.DataFrame(rows) #converting list into df

out_df.to_csv(OUT_PATH,index=False)
print("Saved features to:", OUT_PATH)
print("Feature matrix shape:", out_df.shape)
print("Label distribution:\n", out_df['label'].value_counts())
print("Sample rows:\n", out_df.head(5).to_string(index=False))