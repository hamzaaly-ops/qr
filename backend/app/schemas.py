from pydantic import BaseModel, Field


class URLScanRequest(BaseModel):
    url: str = Field(..., min_length=3, examples=["https://example.com/login"])


class URLScanResponse(BaseModel):
    input_url: str
    normalized_url: str | None
    domain: str | None
    is_url: bool
    extracted_from_qr: bool = False

    domain_age_days: int | None
    ssl_valid: bool | None
    ssl_error: str | None = None

    suspicious_keywords: list[str] = Field(default_factory=list)
    url_flags: list[str] = Field(default_factory=list)

    ml_phishing_probability: float = Field(ge=0.0, le=1.0)
    cv_malicious_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    cv_prediction: str | None = None
    cv_model_source: str | None = None
    cv_model_error: str | None = None

    risk_score: int = Field(ge=0, le=100)
    risk_level: str
    verdict_color: str
    reasons: list[str] = Field(default_factory=list)


class QRScanResponse(URLScanResponse):
    qr_text: str
