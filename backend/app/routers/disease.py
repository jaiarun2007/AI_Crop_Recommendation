from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import DiseaseDetectionResponse
from app.services.disease_detector import analyze

router = APIRouter(prefix="/api/disease", tags=["disease-detection"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


@router.post("/detect", response_model=DiseaseDetectionResponse)
async def detect_disease(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Upload a JPEG, PNG, or WEBP image.")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image too large (max 8MB).")
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file upload.")

    try:
        result = analyze(image_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not process image.")

    return result
