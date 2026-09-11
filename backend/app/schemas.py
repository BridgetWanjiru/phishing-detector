from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    url: str = Field(..., min_length=3, examples=["http://paypal-secure-login.tk/verify"])


class PredictResponse(BaseModel):
    url: str
    is_phishing: bool
    risk_score: float  # 0.0 (safe) - 1.0 (high risk)
    risk_level: str    # "low" | "medium" | "high"
    top_signals: list[str]
