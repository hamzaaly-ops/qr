from urllib.parse import urlparse

from app.schemas import URLScanResponse
from app.services.ml_service import PhishingModelService
from app.services.url_checks import (
    check_ssl_certificate,
    domain_age_penalty,
    extract_domain,
    find_suspicious_keywords,
    get_domain_age_days,
    inspect_url_patterns,
    normalize_url,
)


def _risk_level(score: int) -> tuple[str, str]:
    if score < 35:
        return "SAFE", "green"
    if score < 70:
        return "SUSPICIOUS", "yellow"
    return "DANGEROUS", "red"


class URLAnalyzer:
    def __init__(self) -> None:
        self.model = PhishingModelService()

    def analyze(self, raw_url: str, extracted_from_qr: bool = False) -> URLScanResponse:
        normalized_url, normalize_error = normalize_url(raw_url)
        if normalize_error or not normalized_url:
            return URLScanResponse(
                input_url=raw_url,
                normalized_url=None,
                domain=None,
                is_url=False,
                extracted_from_qr=extracted_from_qr,
                domain_age_days=None,
                ssl_valid=None,
                ssl_error=normalize_error or "Invalid URL",
                suspicious_keywords=[],
                url_flags=["invalid_url_payload"],
                ml_phishing_probability=1.0,
                risk_score=90,
                risk_level="DANGEROUS",
                verdict_color="red",
                reasons=["QR content is not a valid URL."],
            )

        parsed = urlparse(normalized_url)
        domain = extract_domain(normalized_url)

        age_days, age_error = get_domain_age_days(domain)
        ssl_valid, ssl_error = check_ssl_certificate(domain)
        suspicious_keywords, keyword_penalty = find_suspicious_keywords(normalized_url)
        url_flags, pattern_penalty = inspect_url_patterns(normalized_url, domain)
        ml_probability = self.model.predict_proba(normalized_url)

        age_penalty = domain_age_penalty(age_days)
        ssl_penalty = 0
        if parsed.scheme.lower() == "https" and ssl_valid is False:
            ssl_penalty = 25
        if parsed.scheme.lower() != "https":
            ssl_penalty = max(ssl_penalty, 12)

        ml_points = int(round(ml_probability * 45))
        raw_score = ml_points + age_penalty + ssl_penalty + keyword_penalty + pattern_penalty
        risk_score = max(0, min(100, raw_score))
        risk_level, verdict_color = _risk_level(risk_score)

        reasons: list[str] = []
        if age_days is None:
            reasons.append("Domain age is unavailable.")
        elif age_days < 90:
            reasons.append(f"Domain is very new ({age_days} days old).")
        elif age_days < 365:
            reasons.append(f"Domain is less than 1 year old ({age_days} days).")

        if parsed.scheme.lower() != "https":
            reasons.append("URL is using non-HTTPS scheme.")
        elif ssl_valid is False:
            reasons.append("SSL certificate validation failed.")

        if suspicious_keywords:
            reasons.append(f"Suspicious terms found: {', '.join(suspicious_keywords)}.")

        if url_flags:
            reasons.append(f"Risky URL patterns: {', '.join(url_flags)}.")

        if age_error and age_days is None:
            reasons.append(f"WHOIS note: {age_error}")
        if ssl_error and ssl_valid is False:
            reasons.append(f"SSL note: {ssl_error}")

        if not reasons:
            reasons.append("No major phishing indicators found.")

        return URLScanResponse(
            input_url=raw_url,
            normalized_url=normalized_url,
            domain=domain,
            is_url=True,
            extracted_from_qr=extracted_from_qr,
            domain_age_days=age_days,
            ssl_valid=ssl_valid,
            ssl_error=ssl_error,
            suspicious_keywords=suspicious_keywords,
            url_flags=url_flags,
            ml_phishing_probability=round(ml_probability, 4),
            risk_score=risk_score,
            risk_level=risk_level,
            verdict_color=verdict_color,
            reasons=reasons,
        )
