from fastapi import APIRouter

from app.schemas import CropRecommendationResponse, SoilClimateInput
from app.services.crop_recommender import get_recommender

router = APIRouter(prefix="/api/crop", tags=["crop-recommendation"])


@router.post("/recommend", response_model=CropRecommendationResponse)
def recommend_crop(payload: SoilClimateInput):
    recommender = get_recommender()
    result = recommender.predict(payload.model_dump())
    return result
