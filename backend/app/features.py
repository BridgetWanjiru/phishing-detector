"""
URL feature extraction.

IMPORTANT: This module is the single source of truth for turning a raw URL
string into a numeric feature vector. Both the training script
(backend/model/train.py) and the live API (backend/app/main.py) import
FEATURE_NAMES and extract_features from here, so the model always sees
features computed the exact same way it was trained on.

All features are derived from the URL string alone,no network calls,
no fetching the live page. This keeps the classifier fast, safe (it never
visits a potentially malicious link) and fully self-contained.
"""

import math
import re
from urllib.parse import urlparse

SUSPICIOUS_WORDS = [
    "login", "verify", "update", "secure", "account", "banking",
    "confirm", "signin", "webscr", "password", "suspend", "urgent",
    "click", "billing", "invoice", "wallet", "recover",
]

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd",
    "buff.ly", "rebrand.ly", "cutt.ly", "shorte.st",
}

IP_PATTERN = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}$"
)

FEATURE_NAMES = [
    "url_length",
    "hostname_length",
    "path_length",
    "num_dots",
    "num_hyphens",
    "num_underscores",
    "num_slashes",
    "num_digits",
    "num_special_chars",
    "num_at_symbols",
    "num_equal_signs",
    "num_question_marks",
    "num_ampersands",
    "num_subdomains",
    "has_ip_address",
    "has_https",
    "has_port",
    "has_suspicious_word",
    "num_suspicious_words",
    "is_shortener",
    "digit_ratio",
    "letter_ratio",
    "special_char_ratio",
    "shannon_entropy",
    "tld_length",
    "has_double_slash_redirect",
]


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def extract_features(url: str) -> dict:
    """Turn a raw URL string into the fixed feature dict used by the model."""
    url = (url or "").strip()

    parse_target = url if "://" in url else f"http://{url}"
    parsed = urlparse(parse_target)

    hostname = parsed.hostname or ""
    path = parsed.path or ""

    labels = [p for p in hostname.split(".") if p]
    tld = labels[-1] if labels else ""
    num_subdomains = max(len(labels) - 2, 0)

    digits = sum(c.isdigit() for c in url)
    letters = sum(c.isalpha() for c in url)
    specials = sum(not c.isalnum() for c in url)

    lowered = url.lower()
    suspicious_hits = [w for w in SUSPICIOUS_WORDS if w in lowered]

    features = {
        "url_length": len(url),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_underscores": url.count("_"),
        "num_slashes": url.count("/"),
        "num_digits": digits,
        "num_special_chars": specials,
        "num_at_symbols": url.count("@"),
        "num_equal_signs": url.count("="),
        "num_question_marks": url.count("?"),
        "num_ampersands": url.count("&"),
        "num_subdomains": num_subdomains,
        "has_ip_address": int(bool(IP_PATTERN.match(hostname))),
        "has_https": int(parsed.scheme == "https"),
        "has_port": int(parsed.port is not None),
        "has_suspicious_word": int(len(suspicious_hits) > 0),
        "num_suspicious_words": len(suspicious_hits),
        "is_shortener": int(hostname in SHORTENER_DOMAINS),
        "digit_ratio": digits / len(url) if url else 0.0,
        "letter_ratio": letters / len(url) if url else 0.0,
        "special_char_ratio": specials / len(url) if url else 0.0,
        "shannon_entropy": _shannon_entropy(url),
        "tld_length": len(tld),
        "has_double_slash_redirect": int(path.count("//") > 0 or url.rfind("//") > 7),
    }
    return features


def features_to_vector(features: dict) -> list:
    """Ordered vector matching FEATURE_NAMES, for feeding into the model."""
    return [features[name] for name in FEATURE_NAMES]
