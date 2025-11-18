# src/train.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
from src.features import FEATURE_ORDER
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline


def main():
    df = pd.read_csv("data/processed/features.csv")
    if 'label' not in df.columns:
        raise ValueError("features.csv must contain 'label' column")
    X = df[FEATURE_ORDER]
    y = df['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    # clf = RandomForestClassifier(n_estimators=200, random_state=42)
    # clf.fit(X_train, y_train)
    # clf = XGBClassifier(
    # max_depth=6,
    # learning_rate=0.1,
    # n_estimators=300,
    # subsample=0.9,
    # colsample_bytree=0.9,
    # eval_metric='logloss')

    # clf.fit(X_train, y_train)
    clf = make_pipeline(
    StandardScaler(),
    LogisticRegression(
        penalty='l2',
        C=1.0,
        class_weight='balanced',
        solver='liblinear',  # robust for small datasets
        random_state=42,
        max_iter=500)
        )

    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, pred))
    print(classification_report(y_test, pred))
    joblib.dump(clf, "model/phish_model.joblib")
    print("Saved model to model/phish_model.joblib")

if __name__ == "__main__":
    main()

