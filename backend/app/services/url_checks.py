import ipaddress
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import whois

from app.services.ml_features import SHORTENER_DOMAINS, SUSPICIOUS_KEYWORDS


def normalize_url(raw_url: str) -> tuple[str | None, str | None]:
    value = raw_url.strip()
    if not value:
        return None, "Empty QR content"

    if "://" not in value:
        value = f"https://{value}"

    parsed = urlparse(value)
    if not parsed.netloc and parsed.path and "." in parsed.path:
        value = f"https://{parsed.path}"
        parsed = urlparse(value)

    if not parsed.netloc:
        return None, "URL domain is missing"

    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned), None


def extract_domain(url: str) -> str | None:
    return urlparse(url).hostname


def _coerce_datetime(raw_value) -> datetime | None:
    if raw_value is None:
        return None

    if isinstance(raw_value, list):
        candidates = [item for item in raw_value if item is not None]
        if not candidates:
            return None
        candidates = [_coerce_datetime(item) for item in candidates]
        valid = [item for item in candidates if item is not None]
        return min(valid) if valid else None

    if isinstance(raw_value, datetime):
        if raw_value.tzinfo is None:
            return raw_value.replace(tzinfo=timezone.utc)
        return raw_value.astimezone(timezone.utc)

    if isinstance(raw_value, str):
        trimmed = raw_value.strip()
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
        ]
        for fmt in formats:
            try:
                parsed = datetime.strptime(trimmed, fmt)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue
    return None


def get_domain_age_days(domain: str | None) -> tuple[int | None, str | None]:
    if not domain:
        return None, "Domain missing"
    try:
        record = whois.whois(domain)
        created = _coerce_datetime(record.creation_date)
        if not created:
            return None, "Creation date not available from WHOIS"
        age_days = (datetime.now(timezone.utc) - created).days
        if age_days < 0:
            return None, "Invalid WHOIS creation date"
        return age_days, None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def check_ssl_certificate(domain: str | None) -> tuple[bool | None, str | None]:
    if not domain:
        return None, "Domain missing"

    context = ssl.create_default_context()
    try:
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain):
                return True, None
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def find_suspicious_keywords(url: str) -> tuple[list[str], int]:
    lowered = url.lower()
    hits = sorted(keyword for keyword in SUSPICIOUS_KEYWORDS if keyword in lowered)
    penalty = min(len(hits) * 6, 30)
    return hits, penalty


def _domain_is_ip(domain: str | None) -> bool:
    if not domain:
        return False
    try:
        ipaddress.ip_address(domain)
        return True
    except ValueError:
        return False


def inspect_url_patterns(url: str, domain: str | None) -> tuple[list[str], int]:
    parsed = urlparse(url)
    flags: list[str] = []
    penalty = 0

    if "@" in url:
        flags.append("contains_at_symbol")
        penalty += 15

    if _domain_is_ip(domain):
        flags.append("ip_address_domain")
        penalty += 20

    if domain and domain.startswith("xn--"):
        flags.append("punycode_domain")
        penalty += 12

    if domain and domain in SHORTENER_DOMAINS:
        flags.append("url_shortener")
        penalty += 18

    if domain and domain.count("-") >= 3:
        flags.append("many_hyphens_in_domain")
        penalty += 8

    if domain:
        labels = domain.split(".")
        if len(labels) > 4:
            flags.append("deep_subdomains")
            penalty += min((len(labels) - 3) * 4, 12)

    if len(url) > 120:
        flags.append("very_long_url")
        penalty += 10

    if parsed.scheme.lower() != "https":
        flags.append("non_https_scheme")
        penalty += 15

    if parsed.query and len(parsed.query) > 80:
        flags.append("long_query_string")
        penalty += 5

    return flags, penalty


def domain_age_penalty(age_days: int | None) -> int:
    if age_days is None:
        return 10
    if age_days < 30:
        return 30
    if age_days < 90:
        return 20
    if age_days < 365:
        return 10
    return 0
