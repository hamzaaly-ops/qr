# QR Phishing Detector Backend (FastAPI)

This backend analyzes URLs extracted from QR codes and returns a phishing risk score.
It can also fuse a QR-image CV model score (benign vs malicious QR visuals).

- `SAFE` (green)
- `SUSPICIOUS` (yellow)
- `DANGEROUS` (red)

The score uses:

- domain age (WHOIS)
- SSL certificate validation
- suspicious keyword and URL-pattern checks
- ML phishing probability (trained model if present, heuristic fallback otherwise)
- optional CV model malicious probability from QR image

## 1) Setup

```powershell
cd backend
qrenv\Scripts\activate
pip install -r requirements.txt
```

## 2) Run API

```powershell
uvicorn app.main:app --reload
```

Open docs at: `http://127.0.0.1:8000/docs`

## 3) API Endpoints

- `GET /health`
- `POST /analyze-url` with JSON body:

```json
{
  "url": "https://example.com/login"
}
```

- `POST /analyze-qr` with `multipart/form-data` file upload (`image/*`)
- `POST /analyze-live-frame` with `multipart/form-data`:
  - `file`: image frame
  - `decoded_url` (optional): URL already decoded in frontend (recommended for live stream)

Example:

```powershell
curl -X POST "http://127.0.0.1:8000/analyze-live-frame" `
  -F "file=@frame.jpg" `
  -F "decoded_url=https://example.com/login"
```

## 4) Train URL ML Model (Optional but Recommended)

Input CSV format:

```csv
url,label
https://google.com,0
http://secure-verify-account-login.xyz,1
```

Train:

```powershell
python scripts/train_model.py --input data/phishing_urls.csv --output models/phishing_model.joblib
```

When `models/phishing_model.joblib` exists, the API will use it automatically.

## 5) Plug In Your CV Model

You have two options:

1) Python adapter (recommended for any framework)
- Copy `models/cv_adapter_template.py` to `models/cv_adapter.py`
- Implement:
  - `predict_malicious_probability(image_bgr: np.ndarray) -> float`

2) ONNX model
- Export your CV model to `models/qr_cv_model.onnx`
- Install runtime:

```powershell
pip install onnxruntime
```

The backend auto-load order is:
- `models/cv_adapter.py` first
- then `models/qr_cv_model.onnx`
- otherwise CV model is skipped

## 6) Live Streaming Flow (Frontend + Backend)

Recommended flow for your current setup:

1. Frontend (`html5-qrcode`) decodes URL at 10 FPS
2. Debounce 500 ms and trigger only when URL changes
3. Send one request to `/analyze-live-frame` with:
   - current frame image
   - `decoded_url` from frontend
4. Backend returns combined URL + CV risk score

## 7) Example Response Fields

- `risk_score`: 0-100
- `risk_level`: `SAFE | SUSPICIOUS | DANGEROUS`
- `verdict_color`: `green | yellow | red`
- `domain_age_days`
- `ssl_valid`
- `suspicious_keywords`
- `url_flags`
- `ml_phishing_probability`
- `cv_malicious_probability`
- `cv_prediction` (`BENIGN | MALICIOUS`)
- `cv_model_source` (`python_adapter | onnx`)
- `reasons`
