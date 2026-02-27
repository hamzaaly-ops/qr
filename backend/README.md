# QR Phishing Detector Backend (FastAPI)

This backend analyzes URLs extracted from QR codes and returns a phishing risk score:

- `SAFE` (green)
- `SUSPICIOUS` (yellow)
- `DANGEROUS` (red)

The score uses:

- domain age (WHOIS)
- SSL certificate validation
- suspicious keyword and URL-pattern checks
- ML phishing probability (trained model if present, heuristic fallback otherwise)

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

## 4) Train ML Model (Optional but Recommended)

Input CSV format:

```csv
url,label
https://google.com,0
http://secure-verify-account-login.xyz,1
```

Train:

```powershell
 python -m scripts.train_model --input data/phishing_urls.csv --output models/phishing_model.joblib
 ```

When `models/phishing_model.joblib` exists, the API will use it automatically.

## 5) Example Response Fields

- `risk_score`: 0-100
- `risk_level`: `SAFE | SUSPICIOUS | DANGEROUS`
- `verdict_color`: `green | yellow | red`
- `domain_age_days`
- `ssl_valid`
- `suspicious_keywords`
- `url_flags`
- `ml_phishing_probability`
- `reasons`
