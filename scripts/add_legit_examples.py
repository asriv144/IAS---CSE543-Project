# scripts/add_legit_examples.py
"""
Compute features for extra legitimate URLs (with paths) and append to data/processed/features.csv.
Run from project root with venv active:
    python scripts/add_legit_examples.py
"""

from src.features import extract_features, FEATURE_ORDER
import pandas as pd
import os

OUT_CSV = "data/processed/features.csv"

# List of legitimate example URLs (with paths) to add (50 items)
LEGIT_URLS = [
  "https://www.google.com/search?q=test",
  "https://www.google.com/maps",
  "https://www.google.com/preferences",
  "https://www.amazon.com/gp/cart/view.html",
  "https://www.amazon.com/dp/B08N5WRWNW",
  "https://www.netflix.com/browse",
  "https://www.netflix.com/watch/80057281",
  "https://github.com/login",
  "https://github.com/trending",
  "https://github.com/explore",
  "https://stackoverflow.com/questions/ask",
  "https://stackoverflow.com/questions/11828270/how-to-exit-vim",
  "https://en.wikipedia.org/wiki/Main_Page",
  "https://en.wikipedia.org/wiki/Python_(programming_language)",
  "https://www.reddit.com/r/learnprogramming/",
  "https://www.reddit.com/r/python/",
  "https://www.linkedin.com/in/someone/",
  "https://www.microsoft.com/en-us/microsoft-365",
  "https://www.apple.com/shop/buy-iphone",
  "https://accounts.google.com/ServiceLogin",
  "https://mail.google.com/mail/u/0/#inbox",
  "https://drive.google.com/drive/my-drive",
  "https://calendar.google.com/calendar/u/0/r",
  "https://www.facebook.com/settings",
  "https://www.twitter.com/explore",
  "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
  "https://www.python.org/downloads/release/python-3104/",
  "https://pypi.org/project/requests/",
  "https://www.nytimes.com/section/technology",
  "https://www.bbc.com/news",
  "https://www.imdb.com/title/tt0111161/",
  "https://openai.com/blog/chatgpt",
  "https://stripe.com/docs",
  "https://www.cloudflare.com/learning/ddos/what-is-a-ddos-attack/",
  "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html",
  "https://docs.docker.com/get-started/",
  "https://www.djangoproject.com/start/",
  "https://flask.palletsprojects.com/en/2.0.x/quickstart/",
  "https://www.medium.com/topic/technology",
  "https://www.tutorialspoint.com/data_science/index.htm",
  "https://www.cnn.com/2025/01/01/world/example-story",
  "https://www.gov.uk/check-driving-licence",
  "https://stackoverflow.com/users/22656/jon-skeet",
  "https://support.google.com/accounts/answer/27441",
  "https://help.twitter.com/en/using-twitter",
  "https://www.netflix.com/title/81038963",
  "https://news.ycombinator.com/item?id=1234567",
  "https://www.medium.com/@username/some-article-123456"
]

def main():
    if not os.path.exists(OUT_CSV):
        print("ERROR: expected file not found:", OUT_CSV)
        return

    df = pd.read_csv(OUT_CSV)
    rows = []
    for u in LEGIT_URLS:
        feats = extract_features(u)
        row = {k: feats[k] for k in FEATURE_ORDER}
        row['url'] = u
        row['label'] = 0
        rows.append(row)

    add_df = pd.DataFrame(rows)
    # ensure same columns order as existing features.csv
    cols = list(df.columns)
    # if url/label not last, adapt:
    if 'url' in cols and 'label' in cols:
        base_cols = [c for c in cols if c not in ('url','label')]
        cols = base_cols + ['url','label']
    else:
        cols = add_df.columns.tolist()

    add_df = add_df[cols]
    combined = pd.concat([df, add_df], ignore_index=True)
    combined.to_csv(OUT_CSV, index=False)
    print(f"Appended {len(add_df)} legit examples to {OUT_CSV}. New total rows: {len(combined)}")

if __name__ == "__main__":
    main()
