# src/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
from src.features import extract_features, FEATURE_ORDER
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)

class UrlReq(BaseModel):
    url: str

app = FastAPI(title="Phish Detector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "model/phish_model.joblib"
model = joblib.load(MODEL_PATH)

@app.post("/predict")
def predict(req: UrlReq):
    try:
        feats = extract_features(req.url)
        X = np.array([feats[k] for k in FEATURE_ORDER]).reshape(1, -1)
        if hasattr(model, "predict_proba"):
            proba = float(model.predict_proba(X)[0][1])
        else:
            proba = float(model.predict(X)[0])
        label = 1 if proba > 0.5 else 0
        logging.info("PREDICT: %s -> proba=%s label=%s", req.url, proba, label)
        return {"label": label, "confidence": proba}
    except Exception as e:
        logging.exception("Predict error")
        raise HTTPException(status_code=400, detail=str(e))

# Debug endpoint kept for deeper inspection
@app.post("/debug_predict")
def debug_predict(req: UrlReq):
    feats = extract_features(req.url)
    X = [feats[k] for k in FEATURE_ORDER]
    logging.info("DEBUG: incoming url -> %s", req.url)
    logging.info("DEBUG: feature_vector -> %s", X)
    if hasattr(model, "predict_proba"):
        proba = float(model.predict_proba([X])[0][1])
    else:
        proba = float(model.predict([X])[0])
    label = 1 if proba > 0.5 else 0
    logging.info("DEBUG: model proba -> %s label -> %s", proba, label)
    return {"label": label, "confidence": proba, "features": feats}
