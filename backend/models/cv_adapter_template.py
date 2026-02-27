"""
Copy this file to `models/cv_adapter.py` and replace the function body
with your trained CV model inference code.

Required function signature:
    predict_malicious_probability(image_bgr: np.ndarray) -> float
Return value:
    0.0 (benign) to 1.0 (malicious)
"""

from __future__ import annotations

import cv2
import numpy as np


def predict_malicious_probability(image_bgr: np.ndarray) -> float:
    # Example placeholder baseline:
    # If QR cannot be detected, return uncertain risk.
    detector = cv2.QRCodeDetector()
    text, points, _ = detector.detectAndDecode(image_bgr)
    if points is None or not text:
        return 0.5

    # Replace this logic with your model's inference.
    return 0.2
