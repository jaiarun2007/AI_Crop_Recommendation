"""Thin HTTP client around the free, public Open-Meteo APIs.

No API key is required. Docs: https://open-meteo.com/en/docs
This module makes real network calls — nothing here is mocked or synthetic.
Callers should catch `WeatherAPIError` and surface an honest upstream-failure
message rather than falling back to fabricated weather data.
"""
import httpx

from app import config


class WeatherAPIError(RuntimeError):
    pass


DAILY_VARIABLES = ",".join(
    [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "precipitation_probability_max",
        "relative_humidity_2m_mean",
        "windspeed_10m_max",
        "et0_fao_evapotranspiration",
    ]
)


def geocode(location_name: str) -> dict:
    """Resolve a place name to lat/lon via Open-Meteo's geocoding API."""
    try:
        resp = httpx.get(
            config.OPEN_METEO_GEOCODING_URL,
            params={"name": location_name, "count": 1},
            timeout=config.HTTP_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise WeatherAPIError(f"Geocoding request failed: {exc}") from exc

    data = resp.json()
    results = data.get("results") or []
    if not results:
        raise WeatherAPIError(f"No location found matching '{location_name}'.")

    top = results[0]
    return {
        "name": top["name"],
        "country": top.get("country"),
        "latitude": top["latitude"],
        "longitude": top["longitude"],
    }


def fetch_forecast(latitude: float, longitude: float, days: int = 7) -> dict:
    """Fetch a real daily forecast (up to 16 days) from Open-Meteo."""
    days = max(1, min(days, 16))
    try:
        resp = httpx.get(
            config.OPEN_METEO_FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": DAILY_VARIABLES,
                "timezone": "auto",
                "forecast_days": days,
            },
            timeout=config.HTTP_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise WeatherAPIError(f"Forecast request failed: {exc}") from exc

    return resp.json()
