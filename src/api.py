import os
import json
import csv
from datetime import datetime
from functools import lru_cache
from urllib.parse import urlparse

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import whois  # make sure python-whois is installed

from src.feature_extraction import extract_url_features

# ----------------------------
# Paths & global objects
# ----------------------------

# src/api.py → project root = one level up
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")

TRANCODB_PATH = os.path.join(DATA_DIR, "tranco_top1m.csv")
MODEL_INFO_PATH = os.path.join(MODEL_DIR, "model_info.json")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # extension + local pages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
scaler = None
label_encoder = None
model_info = None

# ----------------------------
# Hybrid decision constants
# ----------------------------

PHISHING_PROB_THRESHOLD = 0.99      # require 99%+ to call phishing
SUSPICIOUS_PROB_THRESHOLD = 0.90    # “suspicious” if >= 0.90
MAX_TOP_RANK = 100_000              # Tranco rank threshold for high reputation
YOUNG_DOMAIN_DAYS = 45              # domains younger than this are “young”

# Hosting providers that often host *both* legit and phishing sites
HIGH_REPUTATION_HOSTS = {
    "pages.dev",
    "github.io",
    "firebaseapp.com",
    "web.app",
    "vercel.app",
    "s3.amazonaws.com",
    "cloudfront.net",
}

PHISHING_KEYWORDS = [
    "account", "review", "verify", "secure", "security",
    "center", "login", "signin", "update", "billing",
    "support", "auth", "credential", "password"
]


# ----------------------------
# Request model
# ----------------------------

class URLRequest(BaseModel):
    url: str


# ----------------------------
# Helper functions
# ----------------------------

def get_registered_domain(hostname: str) -> str:
    """
    Convert full host → registered domain, e.g.:
    'www.facebook.com' -> 'facebook.com'
    Simple rule: last two labels; good enough for this project.
    """
    if not hostname:
        return ""
    parts = hostname.lower().split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return hostname.lower()


def get_subdomain(hostname: str, reg_domain: str) -> str:
    """
    Extract subdomain part from a hostname given the registered domain.
    'account-review-center.pages.dev' + 'pages.dev' -> 'account-review-center'
    """
    if not hostname or not reg_domain:
        return ""
    hostname = hostname.lower()
    reg_domain = reg_domain.lower()

    if hostname == reg_domain:
        return ""

    if hostname.endswith("." + reg_domain):
        sub = hostname[: -len(reg_domain) - 1]  # remove ".<reg_domain>"
        return sub
    elif hostname.endswith(reg_domain):
        # Just in case there's no dot but endswith
        sub = hostname[: -len(reg_domain)]
        if sub.endswith("."):
            sub = sub[:-1]
        return sub

    # Fallback: join all but last two labels
    parts = hostname.split(".")
    if len(parts) > 2:
        return ".".join(parts[:-2])
    return ""


def looks_like_phishy_subdomain(subdomain: str) -> bool:
    """
    Heuristic: subdomain contains phishing-related words / patterns.
    Example: 'account-review-center', 'secure-login', 'verify-billing'
    """
    if not subdomain:
        return False
    s = subdomain.lower()

    # keyword-based
    if any(k in s for k in PHISHING_KEYWORDS):
        return True

    # Lots of hyphens + some sensitive word
    if s.count("-") >= 2 and any(k in s for k in ["login", "account", "secure", "verify"]):
        return True

    # Very long subdomain that contains 'account' or 'login' etc.
    if len(s) > 30 and any(k in s for k in PHISHING_KEYWORDS):
        return True

    return False


@lru_cache(maxsize=1)
def load_top_domains():
    """
    Load Tranco (or similar) top domains into {domain: rank}.
    If the file is missing/unreadable, returns {}.
    """
    top = {}
    print("🔍 [Tranco] Trying to load from:", TRANCODB_PATH)
    if not os.path.exists(TRANCODB_PATH):
        print("⚠️ [Tranco] File does NOT exist at that path.")
        return top

    try:
        with open(TRANCODB_PATH, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                # Accept either "rank,domain" or just "domain"
                if row[0].isdigit() and len(row) >= 2:
                    rank = int(row[0])
                    domain = row[1].strip().lower()
                else:
                    rank = 1_000_000
                    domain = row[0].strip().lower()

                # Normalize trailing dot if present: 'facebook.com.' -> 'facebook.com'
                if domain.endswith("."):
                    domain = domain[:-1]

                if domain and domain not in top:
                    top[domain] = rank

        print(f"✅ [Tranco] Loaded {len(top)} domains.")
        for d in ["facebook.com", "google.com", "github.com", "pages.dev"]:
            print(f"   [Tranco] {d} rank =", top.get(d))
    except Exception as e:
        print("❌ [Tranco] Error loading file:", e)
        top = {}
    return top


def get_domain_reputation(domain: str):
    """
    Return (rank, is_high_reputation).
    is_high_reputation is True if domain is in Tranco and rank <= MAX_TOP_RANK.
    """
    if not domain:
        return None, False
    top = load_top_domains()
    rank = top.get(domain)
    is_high_rep = rank is not None and rank <= MAX_TOP_RANK
    return rank, is_high_rep


@lru_cache(maxsize=10_000)
def get_domain_age_days(domain: str):
    """
    Approximate domain age in days using WHOIS.
    Returns None if WHOIS fails or creation_date is missing/unusable.
    """
    if not domain:
        return None
    try:
        w = whois.whois(domain)
    except Exception:
        return None

    created = getattr(w, "creation_date", None)
    if created is None:
        return None

    if isinstance(created, list) and created:
        created = created[0]

    if not isinstance(created, datetime):
        return None

    try:
        delta = datetime.utcnow() - created
        return delta.days
    except Exception:
        return None


def load_model():
    """
    Load the ML model, scaler (if any), and model_info from MODEL_DIR.
    """
    global model, scaler, label_encoder, model_info

    if not os.path.exists(MODEL_INFO_PATH):
        raise RuntimeError(f"model_info.json not found at {MODEL_INFO_PATH}")

    with open(MODEL_INFO_PATH, "r", encoding="utf-8") as f:
        model_info = json.load(f)

    model_path = model_info.get("model_path", "randomforest_model.joblib")
    model_path = os.path.join(MODEL_DIR, model_path)

    if not os.path.exists(model_path):
        raise RuntimeError(f"Model file not found at {model_path}")

    model = joblib.load(model_path)

    # Optional scaler
    scaler = None
    if model_info.get("uses_scaling"):
        scaler_path = model_info.get("scaler_path", "scaler.joblib")
        scaler_path = os.path.join(MODEL_DIR, scaler_path)
        if os.path.exists(scaler_path):
            scaler = joblib.load(scaler_path)

    # Optional label encoder (not really needed for binary case)
    encoder_path = model_info.get("encoder_path")
    if encoder_path:
        encoder_path = os.path.join(MODEL_DIR, encoder_path)
        if os.path.exists(encoder_path):
            label_encoder = joblib.load(encoder_path)
        else:
            label_encoder = None
    else:
        label_encoder = None


def ensure_model_loaded():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded on server.")


# ----------------------------
# Startup
# ----------------------------

@app.on_event("startup")
async def startup_event():
    try:
        load_model()
        print("✅ Model loaded successfully from", MODEL_DIR)
    except Exception as e:
        print("❌ Failed to load model:", e)


# ----------------------------
# Core prediction logic
# ----------------------------

def predict_internal(url: str) -> dict:
    """
    Core prediction logic: extract features, apply ML model,
    combine with reputation & domain age to make a final decision.
    """
    ensure_model_loaded()

    # Validate URL and extract hostname
    try:
        parsed = urlparse(url)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL format.")

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are supported.")

    hostname = (parsed.hostname or "").lower()
    reg_domain = get_registered_domain(hostname)
    subdomain = get_subdomain(hostname, reg_domain)

    # 1) Extract features from the URL
    try:
        features = extract_url_features(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature extraction failed: {e}")

    feature_cols = model_info.get("feature_columns")
    if not feature_cols:
        raise HTTPException(status_code=500, detail="Model feature_columns not defined in model_info.json")

    # Build a DataFrame with proper feature names
    row = {col: features.get(col, 0) for col in feature_cols}
    X = pd.DataFrame([row])

    # 2) Apply scaler if present
    if scaler is not None:
        try:
            X = scaler.transform(X)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Scaler transform failed: {e}")

    # 3) Get ML probability (class 1 = phishing)
    try:
        proba = model.predict_proba(X)[0][1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {e}")

    probability = float(proba)

    # 4) Get domain reputation and age
    tranco_rank, is_high_rep = get_domain_reputation(reg_domain)
    domain_age_days = get_domain_age_days(reg_domain)

    # 5) Hybrid decision logic (no hard-coded good sites)

    # High-rep + old (or unknown age) domain → strongly bias to safe
    high_rep_safe = is_high_rep and (
        domain_age_days is None or domain_age_days >= YOUNG_DOMAIN_DAYS
    )

    # Young, low-rep domain + moderately high prob
    young_and_suspicious = (
        domain_age_days is not None
        and domain_age_days <= YOUNG_DOMAIN_DAYS
        and not is_high_rep
        and probability >= SUSPICIOUS_PROB_THRESHOLD
    )

    ml_thinks_phishing = probability >= PHISHING_PROB_THRESHOLD

    # Base decision from ML + reputation/age
    if high_rep_safe:
        is_phishing = False
        reason = "high_reputation_or_old_domain"
    elif ml_thinks_phishing and not is_high_rep:
        is_phishing = True
        reason = "ml_high_conf_on_non_high_rep_domain"
    elif young_and_suspicious:
        is_phishing = True
        reason = "young_low_rep_and_suspicious"
    else:
        is_phishing = False
        reason = "below_threshold_or_not_suspicious_enough"

    # 6) Extra rule: suspicious subdomain on trusted hosting (e.g. pages.dev)
    suspicious_on_trusted = (
        reg_domain in HIGH_REPUTATION_HOSTS and looks_like_phishy_subdomain(subdomain)
    )

    if suspicious_on_trusted and not is_phishing:
        is_phishing = True
        reason = "suspicious_subdomain_on_trusted_host"

    # Confidence bucket (for UI display)
    if probability >= PHISHING_PROB_THRESHOLD:
        confidence = "high"
    elif probability >= 0.6:
        confidence = "medium"
    else:
        confidence = "low"

    # If we triggered the heuristic rule, make at least medium confidence
    if suspicious_on_trusted and confidence == "low":
        confidence = "medium"

    return {
        "url": url,
        "is_phishing": bool(is_phishing),
        "probability": probability,
        "confidence": confidence,
        "domain": reg_domain,
        "tranco_rank": tranco_rank,
        "domain_age_days": domain_age_days,
        "decision_reason": reason,
    }


# ----------------------------
# API routes
# ----------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "Phishing detection API running"}


@app.post("/check_url")
def predict(request: URLRequest):
    """
    Main endpoint for the Chrome extension:
    accepts: { "url": "<current tab URL>" }
    """
    return predict_internal(request.url)
