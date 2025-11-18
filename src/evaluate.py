# src/evaluate.py
import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from src.features import FEATURE_ORDER

df = pd.read_csv("data/processed/features.csv")
X = df[FEATURE_ORDER]
y = df['label']
model = joblib.load("model/phish_model.joblib")
pred = model.predict(X)
print("Accuracy:", accuracy_score(y, pred))
print(classification_report(y, pred))
cm = confusion_matrix(y, pred)
print("Confusion matrix:\\n", cm)
pd.DataFrame(cm, index=["true_0","true_1"], columns=["pred_0","pred_1"]).to_csv("model/confusion_matrix.csv")
print("Saved model/confusion_matrix.csv")
