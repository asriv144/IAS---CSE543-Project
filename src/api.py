from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import joblib
import json
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from feature_extraction import extract_url_features

app = FastAPI(title="Phishing URL Detection API", version="1.0.0")

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
model = None
scaler = None
label_encoder = None
feature_columns = None

class URLRequest(BaseModel):
    url: Optional[str] = None
    urls: Optional[List[str]] = None

class PredictionResponse(BaseModel):
    url: str
    is_phishing: bool
    probability: float
    confidence: str

class PredictionsResponse(BaseModel):
    predictions: List[PredictionResponse]

def load_model():
    global model, scaler, label_encoder, feature_columns
    
    try:
        with open(os.path.join(MODEL_DIR, "model_info.json"), 'r') as f:
            model_info = json.load(f)
        
        model_path = os.path.join(MODEL_DIR, model_info["model_path"])
        model = joblib.load(model_path)
        
        if model_info.get("uses_scaling"):
            scaler_path = os.path.join(MODEL_DIR, model_info["scaler_path"])
            scaler = joblib.load(scaler_path)
        
        encoder_path = os.path.join(MODEL_DIR, model_info["encoder_path"])
        label_encoder = joblib.load(encoder_path)
        
        feature_columns = model_info["feature_columns"]
        print(f"Model loaded: {model_info['model_name']}")
        
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {str(e)}")

@app.on_event("startup")
async def startup_event():
    load_model()

@app.get("/")
async def root():
    return {"message": "Phishing URL Detection API", "status": "ready"}

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": model is not None}

def predict_url(url: str) -> dict:
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        features = extract_url_features(url)
        
        if 'scheme' in features and label_encoder and 'scheme_encoded' in feature_columns:
            try:
                features['scheme_encoded'] = int(label_encoder.transform([features['scheme']])[0])
            except:
                features['scheme_encoded'] = 0
        
        feature_df = pd.DataFrame([features])
        available_cols = [c for c in feature_columns if c in feature_df.columns]
        feature_vector = feature_df[available_cols].fillna(0)
        
        for col in feature_columns:
            if col not in feature_vector.columns:
                feature_vector[col] = 0
        
        feature_vector = feature_vector[feature_columns]
        
        if scaler:
            feature_vector = scaler.transform(feature_vector)
        
        prediction = model.predict(feature_vector)[0]
        probability = float(model.predict_proba(feature_vector)[0][1])
        
        is_phishing = bool(prediction == 1)
        confidence = "high" if probability > 0.8 or probability < 0.2 else "medium"
        
        return {
            "url": url,
            "is_phishing": is_phishing,
            "probability": probability,
            "confidence": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing URL: {str(e)}")

@app.post("/predict")
async def predict(request: URLRequest):
    if request.url:
        return predict_url(request.url)
    elif request.urls:
        results = [predict_url(url) for url in request.urls]
        return PredictionsResponse(predictions=results)
    else:
        raise HTTPException(status_code=400, detail="Either 'url' or 'urls' must be provided")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

