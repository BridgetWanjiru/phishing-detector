import json
import os

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .features import FEATURE_NAMES, extract_features, features_to_vector
from .schemas import PredictRequest, PredictResponse

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "model")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")

app = FastAPI(
    title="Phishing URL Detector",
    description="Classifies a URL as phishing or legitimate using a trained ML model.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None

SIGNAL_RULES = [
    ("has_https", lambda v: v == 0, "Site does not use HTTPS"),
    ("has_ip_address", lambda v: v == 1, "URL uses a raw IP address instead of a domain name"),
    ("has_suspicious_word", lambda v: v == 1, "Contains wording commonly used in phishing (e.g. 'login', 'verify', 'secure')"),
    ("is_shortener", lambda v: v == 1, "URL uses a link-shortening service, which can hide the real destination"),
    ("num_subdomains", lambda v: v >= 3, "Unusually high number of subdomains"),
    ("has_double_slash_redirect", lambda v: v == 1, "Contains a suspicious redirect pattern ('//') in the path"),
    ("shannon_entropy", lambda v: v > 4.5, "URL has unusually high randomness (common in generated phishing links)"),
    ("num_at_symbols", lambda v: v >= 1, "Contains an '@' symbol, which can be used to obscure the real domain"),
    ("url_length", lambda v: v > 75, "URL is unusually long"),
    ("hostname_length", lambda v: v > 30, "Domain name is unusually long"),
]


@app.on_event("startup")
def load_model():
    global model
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(
            f"Model not found at {MODEL_PATH}. Run `python model/train.py` first."
        )
    model = joblib.load(MODEL_PATH)


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


def _risk_level(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _top_signals(features: dict) -> list[str]:
    signals = []
    for name, condition, message in SIGNAL_RULES:
        if condition(features.get(name, 0)):
            signals.append(message)
    return signals[:5]


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    features = extract_features(req.url)
    vector = np.array([features_to_vector(features)])

    proba = model.predict_proba(vector)[0]
    risk_score = float(proba[1])

    return PredictResponse(
        url=req.url,
        is_phishing=risk_score >= 0.5,
        risk_score=round(risk_score, 4),
        risk_level=_risk_level(risk_score),
        top_signals=_top_signals(features),
    )
