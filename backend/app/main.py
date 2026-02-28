from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import QRScanResponse, URLScanRequest, URLScanResponse
from app.services.analyzer import URLAnalyzer
from app.services.cv_model_service import QRCVModelService
from app.services.qr_service import decode_qr_image

app = FastAPI(
    title="QR Phishing Detector API",
    version="1.0.0",
    description=(
        "Detect malicious URLs from QR scans using domain intelligence, SSL checks, "
        "keyword heuristics, and ML-based phishing probability."
    ),
)
origins = [
    "http://localhost:8080",
    "https://qr.techyaim.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = URLAnalyzer()
cv_model = QRCVModelService()


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

    cv_result = cv_model.predict_from_bytes(image_bytes)

    try:
        qr_text = decode_qr_image(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = analyzer.analyze(qr_text, extracted_from_qr=True)
    result = analyzer.merge_cv_signal(
        scan=result,
        cv_malicious_probability=cv_result.malicious_probability,
        cv_prediction=cv_result.prediction,
        cv_model_source=cv_result.model_source,
        cv_error=cv_result.error,
    )
    payload = result.model_dump()
    payload["qr_text"] = qr_text
    return QRScanResponse(**payload)


@app.post("/analyze-live-frame", response_model=QRScanResponse)
async def analyze_live_frame(
    file: UploadFile = File(...),
    decoded_url: str | None = Form(default=None),
) -> QRScanResponse:
    """
    Stream-friendly endpoint:
    - Frontend can send decoded URL from html5-qrcode (preferred), plus the frame image.
    - If decoded_url is missing, backend attempts QR decode from the image.
    - CV model prediction is combined with URL analysis.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    cv_result = cv_model.predict_from_bytes(image_bytes)

    qr_text = (decoded_url or "").strip()
    if not qr_text:
        try:
            qr_text = decode_qr_image(image_bytes)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"No URL found in live frame. {exc}",
            ) from exc

    result = analyzer.analyze(qr_text, extracted_from_qr=True)
    result = analyzer.merge_cv_signal(
        scan=result,
        cv_malicious_probability=cv_result.malicious_probability,
        cv_prediction=cv_result.prediction,
        cv_model_source=cv_result.model_source,
        cv_error=cv_result.error,
    )
    payload = result.model_dump()
    payload["qr_text"] = qr_text
    return QRScanResponse(**payload)
