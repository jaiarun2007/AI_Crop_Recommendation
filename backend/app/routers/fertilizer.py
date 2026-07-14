from fastapi import APIRouter, HTTPException

from app.schemas import FertilizerRequest, FertilizerResponse
from app.services import fertilizer_service

router = APIRouter(prefix="/api/fertilizer", tags=["fertilizer-engine"])


@router.post(
    "/recommend",
    response_model=FertilizerResponse,
    summary="N-P-K balancing advice + product dosing for a crop's soil test",
)
def recommend_fertilizer(payload: FertilizerRequest):
    try:
        return fertilizer_service.recommend(payload.crop, payload.N, payload.P, payload.K, payload.ph)
    except KeyError:
        known = ", ".join(fertilizer_service.known_crops())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown crop '{payload.crop}'. Known crops: {known}",
        )


@router.get("/known-crops", summary="List crops with reference nutrient targets")
def known_crops():
    return {"crops": fertilizer_service.known_crops()}
