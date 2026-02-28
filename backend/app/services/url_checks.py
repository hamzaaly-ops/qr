import ipaddress
import re
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import whois

from app.services.ml_features import SHORTENER_DOMAINS, SUSPICIOUS_KEYWORDS


_URL_TOKEN_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")
_WRAPPING_PAIRS = (
    ('"', '"'),
    ("'", "'"),
    ("<", ">"),
    ("(", ")"),
    ("[", "]"),
    ("{", "}"),
)
_LEADING_JUNK = "([{<\"'"
_TRAILING_JUNK = ".,;:!?)]}>\"'"


def _strip_wrapping(value: str) -> str:
    cleaned = value.strip()
    while len(cleaned) >= 2:
        unwrapped = False
        for left, right in _WRAPPING_PAIRS:
            if cleaned.startswith(left) and cleaned.endswith(right):
                cleaned = cleaned[len(left) : len(cleaned) - len(right)].strip()
                unwrapped = True
                break
        if not unwrapped:
            break
    return cleaned


def _extract_url_candidate(raw_value: str) -> str:
    value = _strip_wrapping(raw_value)
    if not value:
        return ""

    match = _URL_TOKEN_RE.search(value)
    if match:
        value = match.group(0)

    value = _strip_wrapping(value)
    value = value.lstrip(_LEADING_JUNK).rstrip(_TRAILING_JUNK).strip()
    if value.lower().startswith("url:"):
        value = value[4:].strip()
    return value


def _to_ascii_domain(domain: str | None) -> str | None:
    if not domain:
        return None

    cleaned = domain.strip().strip(".").lower()
    if not cleaned:
        return None

    try:
        return cleaned.encode("idna").decode("ascii")
    except UnicodeError:
        return cleaned


def normalize_url(raw_url: str) -> tuple[str | None, str | None]:
    value = _extract_url_candidate(raw_url.strip())
    if not value:
        return None, "Empty QR content"

    if value.startswith("//"):
        value = f"https:{value}"
    elif "://" not in value:
        value = f"https://{value}"

    parsed = urlparse(value)
    if not parsed.netloc and parsed.path and "://" in parsed.path:
        nested = _extract_url_candidate(parsed.path)
        if nested:
            nested = nested if "://" in nested else f"https://{nested}"
            value = nested
            parsed = urlparse(value)

    if not parsed.netloc and parsed.path and "." in parsed.path:
        value = f"https://{parsed.path.lstrip('/')}"
        parsed = urlparse(value)

    if not parsed.netloc:
        return None, "URL domain is missing"

    cleaned_netloc = parsed.netloc.lstrip(_LEADING_JUNK).rstrip(_TRAILING_JUNK).strip()
    if not cleaned_netloc:
        return None, "URL domain is missing"

    cleaned = parsed._replace(netloc=cleaned_netloc, fragment="")
    normalized = urlunparse(cleaned)
    if not extract_domain(normalized):
        return None, "URL domain is missing"

    return normalized, None


def extract_domain(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.hostname:
        return None
    cleaned = parsed.hostname.strip().strip(".").lower()
    return cleaned or None


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
    ascii_domain = _to_ascii_domain(domain)
    if not ascii_domain:
        return None, "Domain missing"
    try:
        record = whois.whois(ascii_domain)
        created = _coerce_datetime(record.creation_date)
        if not created:
            return None, "Creation date not available from WHOIS"
        age_days = (datetime.now(timezone.utc) - created).days
        if age_days < 0:
            return None, "Invalid WHOIS creation date"
        return age_days, None
    except Exception as exc:  # noqa: BLE001
        text = str(exc).replace("\r", "\n").strip()
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if not first_line:
            first_line = exc.__class__.__name__
        if len(first_line) > 180:
            first_line = f"{first_line[:177]}..."
        return None, first_line


def whois_error_indicates_unregistered(error_text: str | None) -> bool:
    if not error_text:
        return False

    lowered = error_text.lower()
    signals = (
        "no match for",
        "domain not found",
        "not registered",
        "no object found",
        "status: free",
        "no entries found",
        "available for registration",
    )
    return any(token in lowered for token in signals)


def check_ssl_certificate(domain: str | None) -> tuple[bool | None, str | None]:
    ascii_domain = _to_ascii_domain(domain)
    if not ascii_domain:
        return None, "Domain missing"

    context = ssl.create_default_context()
    try:
        with socket.create_connection((ascii_domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=ascii_domain):
                return True, None
    except ssl.SSLError as exc:
        return False, str(exc)
    except socket.gaierror as exc:
        return None, f"DNS lookup failed: {exc}"
    except socket.timeout:
        return None, "SSL connection timed out"
    except OSError as exc:
        return None, str(exc)


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
        return 0
    if age_days < 30:
        return 30
    if age_days < 90:
        return 20
    if age_days < 365:
        return 10
    return 0
