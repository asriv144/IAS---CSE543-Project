# src/show_importance.py
import joblib, pandas as pd
from src.features import FEATURE_ORDER

clf = joblib.load("model/phish_model.joblib")
if hasattr(clf, "feature_importances_"):
    importances = clf.feature_importances_
    df = pd.DataFrame({"feature": FEATURE_ORDER, "importance": importances})
    df = df.sort_values("importance", ascending=False)
    print(df.to_string(index=False))
    df.to_csv("model/feature_importances.csv", index=False)
    print("Saved model/feature_importances.csv")
else:
    print("Model has no feature_importances_ attribute.")
