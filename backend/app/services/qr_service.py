import cv2
import numpy as np


def decode_qr_image(image_bytes: bytes) -> str:
    raw = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Uploaded file is not a valid image.")

    detector = cv2.QRCodeDetector()
    decoded, points, _ = detector.detectAndDecode(image)
    if points is not None and decoded:
        return decoded.strip()

    multi_ok, decoded_multi, _, _ = detector.detectAndDecodeMulti(image)
    if multi_ok and decoded_multi:
        for value in decoded_multi:
            cleaned = (value or "").strip()
            if cleaned:
                return cleaned

    raise ValueError("No QR code found in the image.")
