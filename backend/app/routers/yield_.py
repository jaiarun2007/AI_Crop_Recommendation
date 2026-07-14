from fastapi import APIRouter

from app.schemas import YieldPredictionInput, YieldPredictionResponse
from app.services.yield_predictor import get_predictor

router = APIRouter(prefix="/api/yield", tags=["yield-prediction"])


@router.post("/predict", response_model=YieldPredictionResponse)
def predict_yield(payload: YieldPredictionInput):
    predictor = get_predictor()
    result = predictor.predict(payload.model_dump())
    return result


@router.get("/known-values")
def known_values():
    predictor = get_predictor()
    return {
        "areas": sorted(predictor.known_areas),
        "crops": sorted(predictor.known_crops),
    }
