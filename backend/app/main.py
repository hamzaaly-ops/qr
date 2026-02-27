from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import QRScanResponse, URLScanRequest, URLScanResponse
from app.services.analyzer import URLAnalyzer
from app.services.qr_service import decode_qr_image

app = FastAPI(
    title="QR Phishing Detector API",
    version="1.0.0",
    description=(
        "Detect malicious URLs from QR scans using domain intelligence, SSL checks, "
        "keyword heuristics, and ML-based phishing probability."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = URLAnalyzer()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze-url", response_model=URLScanResponse)
def analyze_url(payload: URLScanRequest) -> URLScanResponse:
    return analyzer.analyze(payload.url, extracted_from_qr=False)


@app.post("/analyze-qr", response_model=QRScanResponse)
async def analyze_qr(file: UploadFile = File(...)) -> QRScanResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    try:
        qr_text = decode_qr_image(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = analyzer.analyze(qr_text, extracted_from_qr=True)
    payload = result.model_dump()
    payload["qr_text"] = qr_text
    return QRScanResponse(**payload)
