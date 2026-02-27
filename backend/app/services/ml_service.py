import math
from pathlib import Path

import joblib

from app.services.ml_features import FEATURE_NAMES, extract_url_features


class PhishingModelService:
    def __init__(self, model_path: str | Path = "models/phishing_model.joblib"):
        self.model_path = Path(model_path)
        self.model = None
        self._load_model()

    @property
    def using_trained_model(self) -> bool:
        return self.model is not None

    def _load_model(self) -> None:
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)

    def predict_proba(self, url: str) -> float:
        features = extract_url_features(url)

        if self.model is not None:
            ordered = [[features[name] for name in FEATURE_NAMES]]
            try:
                return float(self.model.predict_proba(ordered)[0][1])
            except Exception:  # noqa: BLE001
                # Fall back to deterministic heuristic if model inference fails.
                return self._heuristic_probability(features)

        return self._heuristic_probability(features)

    def _heuristic_probability(self, features: dict[str, float]) -> float:
        score = -3.0
        score += 0.020 * features["url_length"]
        score += 0.280 * features["num_dots"]
        score += 0.180 * features["num_hyphens"]
        score += 0.550 * features["has_at_symbol"]
        score += 1.100 * features["has_ip"]
        score += 0.120 * features["subdomain_count"]
        score += 0.065 * features["keyword_hits"]
        score += 0.500 * features["has_shortener"]
        score += 0.300 * features["has_punycode"]
        score -= 0.200 * features["is_https"]
        return 1.0 / (1.0 + math.exp(-score))
