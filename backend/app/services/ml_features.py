import ipaddress
from urllib.parse import urlparse


SUSPICIOUS_KEYWORDS = {
    "login",
    "verify",
    "account",
    "secure",
    "update",
    "payment",
    "bank",
    "wallet",
    "free",
    "gift",
    "bonus",
    "urgent",
    "confirm",
    "password",
    "otp",
    "signin",
    "reset",
    "claim",
    "invoice",
    "kyc",
}

SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "rb.gy",
    "rebrand.ly",
    "ow.ly",
    "is.gd",
    "soo.gd",
    "cutt.ly",
    "shorturl.at",
}

FEATURE_NAMES = [
    "url_length",
    "num_dots",
    "num_hyphens",
    "num_digits",
    "num_special_chars",
    "has_ip",
    "has_at_symbol",
    "is_https",
    "subdomain_count",
    "path_length",
    "query_length",
    "has_punycode",
    "has_shortener",
    "keyword_hits",
]


def _is_ip_address(hostname: str | None) -> bool:
    if not hostname:
        return False
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def extract_url_features(url: str) -> dict[str, float]:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""

    keyword_hits = sum(1 for keyword in SUSPICIOUS_KEYWORDS if keyword in url.lower())
    special_chars = sum(1 for char in url if not char.isalnum())

    subdomain_count = 0
    if hostname:
        labels = hostname.split(".")
        if len(labels) > 2:
            subdomain_count = len(labels) - 2

    features = {
        "url_length": float(len(url)),
        "num_dots": float(url.count(".")),
        "num_hyphens": float(url.count("-")),
        "num_digits": float(sum(char.isdigit() for char in url)),
        "num_special_chars": float(special_chars),
        "has_ip": 1.0 if _is_ip_address(hostname) else 0.0,
        "has_at_symbol": 1.0 if "@" in url else 0.0,
        "is_https": 1.0 if parsed.scheme.lower() == "https" else 0.0,
        "subdomain_count": float(subdomain_count),
        "path_length": float(len(path)),
        "query_length": float(len(query)),
        "has_punycode": 1.0 if hostname.startswith("xn--") else 0.0,
        "has_shortener": 1.0 if hostname in SHORTENER_DOMAINS else 0.0,
        "keyword_hits": float(keyword_hits),
    }
    return features
