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
    whois_error_indicates_unregistered,
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
        whois_unregistered = whois_error_indicates_unregistered(age_error)

        age_penalty = domain_age_penalty(age_days)
        ssl_penalty = 0
        if parsed.scheme.lower() == "https" and ssl_valid is False:
            ssl_penalty = 25
        if parsed.scheme.lower() != "https":
            ssl_penalty = max(ssl_penalty, 12)
        whois_penalty = 18 if whois_unregistered else 0

        ml_points = int(round(ml_probability * 45))
        raw_score = ml_points + age_penalty + ssl_penalty + keyword_penalty + pattern_penalty + whois_penalty
        risk_score = max(0, min(100, raw_score))
        forced_suspicious = False
        forced_non_https_suspicious = False
        if parsed.scheme.lower() != "https" and risk_score < 35:
            risk_score = 35
            forced_non_https_suspicious = True

        has_other_risk_signals = (
            keyword_penalty > 0
            or pattern_penalty > 0
            or whois_unregistered
            or ml_probability >= 0.30
        )
        if parsed.scheme.lower() == "https" and ssl_valid is None and has_other_risk_signals:
            if risk_score < 35:
                risk_score = 35
                forced_suspicious = True

        risk_level, verdict_color = _risk_level(risk_score)

        reasons: list[str] = []
        if age_days is None:
            reasons.append("Domain age could not be determined.")
        elif age_days < 90:
            reasons.append(f"Domain is very new ({age_days} days old).")
        elif age_days < 365:
            reasons.append(f"Domain is less than 1 year old ({age_days} days).")
        if whois_unregistered:
            reasons.append("WHOIS indicates this domain may be unregistered.")

        if parsed.scheme.lower() != "https":
            reasons.append("URL is using non-HTTPS scheme.")
            if forced_non_https_suspicious:
                reasons.append("Marked as suspicious because the URL is not using HTTPS.")
        elif ssl_valid is False:
            reasons.append("SSL certificate validation failed.")
        elif ssl_valid is None and ssl_error:
            reasons.append("SSL certificate check could not be completed.")
            if forced_suspicious:
                reasons.append("Marked as suspicious because HTTPS trust checks are unavailable.")

        if suspicious_keywords:
            reasons.append(f"Suspicious terms found: {', '.join(suspicious_keywords)}.")

        if url_flags:
            reasons.append(f"Risky URL patterns: {', '.join(url_flags)}.")

        if age_error and age_days is None:
            reasons.append(f"WHOIS note: {age_error}")
        if ssl_error and ssl_valid is not True:
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

    def merge_cv_signal(
        self,
        scan: URLScanResponse,
        cv_malicious_probability: float | None,
        cv_prediction: str | None,
        cv_model_source: str | None,
        cv_error: str | None = None,
    ) -> URLScanResponse:
        payload = scan.model_dump()
        reasons = list(payload["reasons"])

        payload["cv_malicious_probability"] = (
            None if cv_malicious_probability is None else round(float(cv_malicious_probability), 4)
        )
        payload["cv_prediction"] = cv_prediction
        payload["cv_model_source"] = cv_model_source
        payload["cv_model_error"] = cv_error

        if cv_malicious_probability is None:
            if cv_error:
                reasons.append(f"CV model note: {cv_error}")
            else:
                reasons.append("CV model is unavailable, so it was not used in the final risk score.")
            payload["reasons"] = reasons
            return URLScanResponse(**payload)

        cv_points = int(round(float(cv_malicious_probability) * 50))
        combined_score = max(0, min(100, int(payload["risk_score"]) + cv_points))
        level, color = _risk_level(combined_score)

        payload["risk_score"] = combined_score
        payload["risk_level"] = level
        payload["verdict_color"] = color

        if cv_malicious_probability >= 0.7:
            reasons.append(
                f"CV model indicates malicious visual pattern ({cv_malicious_probability:.2f})."
            )
        elif cv_malicious_probability <= 0.3:
            reasons.append(
                f"CV model indicates benign visual pattern ({cv_malicious_probability:.2f})."
            )
        else:
            reasons.append(
                f"CV model is uncertain ({cv_malicious_probability:.2f})."
            )
        reasons.append(
            f"CV model probability ({cv_malicious_probability:.2f}) was included in the final risk score."
        )

        payload["reasons"] = reasons
        return URLScanResponse(**payload)
