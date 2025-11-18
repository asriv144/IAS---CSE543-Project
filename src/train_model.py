import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import joblib
import json

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("XGBoost not available, skipping...")

FEATURE_PATH = "data/processed/url_feature.csv"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def load_data():
    df = pd.read_csv(FEATURE_PATH)
    print(f"Loaded {len(df)} samples")
    
    if 'label' not in df.columns:
        raise ValueError("'label' column not found in dataset")
    
    df = df.dropna(subset=['label'])
    df['label'] = df['label'].astype(int)
    
    feature_cols = [c for c in df.columns if c not in ['url', 'label', 'scheme']]
    
    X = df[feature_cols].copy()
    y = df['label'].copy()
    
    if 'scheme' in df.columns:
        le = LabelEncoder()
        X['scheme_encoded'] = le.fit_transform(df['scheme'].fillna(''))
        joblib.dump(le, os.path.join(MODEL_DIR, "label_encoder.joblib"))
        if 'scheme_encoded' not in feature_cols:
            feature_cols.append('scheme_encoded')
    
    X = X.fillna(0)
    return X, y, list(X.columns)

def train_and_evaluate(X_train, X_test, y_train, y_test, model_name, model, scaler=None):
    if scaler:
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
    else:
        X_train_scaled = X_train
        X_test_scaled = X_test
    
    # Cross-validation for better evaluation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='f1')
    
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, 'predict_proba') else y_pred
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0.0,
        'cv_f1_mean': float(cv_scores.mean()),
        'cv_f1_std': float(cv_scores.std())
    }
    
    return model, metrics, scaler

def main():
    X, y, feature_cols = load_data()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    print(f"Features: {len(feature_cols)}")
    
    models_to_test = {
        'RandomForest': RandomForestClassifier(
            n_estimators=200, 
            max_depth=20, 
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42, 
            n_jobs=-1,
            class_weight='balanced'
        ),
        'LogisticRegression': LogisticRegression(
            random_state=42, 
            max_iter=2000,
            class_weight='balanced',
            C=1.0
        ),
        'SVM': SVC(
            probability=True, 
            random_state=42,
            class_weight='balanced',
            C=1.0,
            kernel='rbf'
        )
    }
    
    if HAS_XGBOOST:
        models_to_test['XGBoost'] = XGBClassifier(
            random_state=42, 
            eval_metric='logloss',
            n_estimators=200,
            max_depth=10,
            learning_rate=0.1,
            scale_pos_weight=len(y[y==0])/len(y[y==1]) if len(y[y==1]) > 0 else 1
        )
    
    all_results = {}
    best_model = None
    best_metrics = None
    best_name = None
    best_scaler = None
    
    for name, model in models_to_test.items():
        print(f"\nTraining {name}...")
        use_scaler = name in ['LogisticRegression', 'SVM']
        scaler = StandardScaler() if use_scaler else None
        
        trained_model, metrics, scaler = train_and_evaluate(
            X_train, X_test, y_train, y_test, name, model, scaler
        )
        
        all_results[name] = metrics
        print(f"{name} - Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_score']:.4f}, CV-F1: {metrics['cv_f1_mean']:.4f}±{metrics['cv_f1_std']:.4f}")
        
        # Use CV score for model selection to avoid overfitting
        score = metrics['cv_f1_mean']
        if best_model is None or (best_metrics is not None and score > best_metrics.get('cv_f1_mean', 0)):
            best_model = trained_model
            best_metrics = metrics
            best_name = name
            best_scaler = scaler
    
    print(f"\nBest model: {best_name}")
    print(f"Best metrics: {best_metrics}")
    
    joblib.dump(best_model, os.path.join(MODEL_DIR, f"{best_name.lower()}_model.joblib"))
    if best_scaler:
        joblib.dump(best_scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
    
    model_info = {
        "model_name": best_name,
        "model_path": f"{best_name.lower()}_model.joblib",
        "uses_scaling": best_scaler is not None,
        "scaler_path": "scaler.joblib" if best_scaler else None,
        "encoder_path": "label_encoder.joblib",
        "feature_columns": list(X.columns)
    }
    
    with open(os.path.join(MODEL_DIR, "model_info.json"), 'w') as f:
        json.dump(model_info, f, indent=2)
    
    metrics_output = {
        "best_model": best_name,
        "best_model_metrics": best_metrics,
        "all_models": all_results
    }
    
    with open(os.path.join(MODEL_DIR, "metrics.json"), 'w') as f:
        json.dump(metrics_output, f, indent=2)
    
    print(f"\nModel saved to {MODEL_DIR}/")

if __name__ == "__main__":
    main()

