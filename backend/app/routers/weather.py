from fastapi import APIRouter, HTTPException, Query

from app.schemas import WeatherAlertsResponse, WeatherForecastResponse
from app.services import weather_service
from app.services.weather_client import WeatherAPIError

router = APIRouter(prefix="/api/weather", tags=["weather-intelligence"])


@router.get("/forecast", response_model=WeatherForecastResponse)
def get_forecast(
    location: str | None = Query(None, description="Place name, e.g. 'Coimbatore'"),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    days: int = Query(7, ge=1, le=16),
):
    if not location and (lat is None or lon is None):
        raise HTTPException(status_code=400, detail="Provide `location` or both `lat` and `lon`.")
    try:
        return weather_service.get_forecast(location, lat, lon, days=days)
    except WeatherAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/alerts", response_model=WeatherAlertsResponse)
def get_alerts(
    location: str | None = Query(None, description="Place name, e.g. 'Coimbatore'"),
    lat: float | None = Query(None),
    lon: float | None = Query(None),
    days: int = Query(7, ge=1, le=16),
):
    if not location and (lat is None or lon is None):
        raise HTTPException(status_code=400, detail="Provide `location` or both `lat` and `lon`.")
    try:
        forecast = weather_service.get_forecast(location, lat, lon, days=days)
    except WeatherAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    alerts = weather_service.compute_alerts(forecast["daily"])
    return {"location": forecast["location"], "alerts": alerts}
