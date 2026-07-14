from fastapi import APIRouter, HTTPException

from app.schemas import IrrigationRequest, IrrigationResponse
from app.services import irrigation_service, weather_service
from app.services.weather_client import WeatherAPIError

router = APIRouter(prefix="/api/irrigation", tags=["irrigation-engine"])


@router.post(
    "/schedule",
    response_model=IrrigationResponse,
    summary="FAO-56 crop-coefficient irrigation plan against live rainfall forecast",
)
def irrigation_schedule(payload: IrrigationRequest):
    if not payload.location and (payload.lat is None or payload.lon is None):
        raise HTTPException(status_code=400, detail="Provide `location` or both `lat` and `lon`.")

    try:
        forecast = weather_service.get_forecast(
            payload.location, payload.lat, payload.lon, days=payload.days
        )
    except WeatherAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        plan = irrigation_service.build_plan(
            payload.crop, payload.growth_stage, forecast["daily"], payload.field_size_ha
        )
    except KeyError:
        known = ", ".join(irrigation_service.known_crops())
        raise HTTPException(
            status_code=400, detail=f"Unknown crop '{payload.crop}'. Known crops: {known}"
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown growth_stage '{payload.growth_stage}'. "
            f"Must be one of: {', '.join(irrigation_service.GROWTH_STAGES)}",
        )

    plan["location"] = forecast["location"]
    return plan


@router.get("/known-crops", summary="List crops with published Kc values and valid growth stages")
def known_crops():
    return {"crops": irrigation_service.known_crops(), "growth_stages": irrigation_service.GROWTH_STAGES}
