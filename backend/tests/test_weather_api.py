"""Tests the weather module's parsing/alerting logic by mocking Open-Meteo at the
HTTP transport layer (via respx) with a fixture matching Open-Meteo's real, documented
response schema. This validates OUR parsing/alert logic deterministically; it does not
claim the external API itself was exercised — see README for how to do a live check.
"""
import httpx
import respx

from app import config
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

GEOCODE_FIXTURE = {
    "results": [
        {"name": "Coimbatore", "country": "India", "latitude": 11.0168, "longitude": 76.9558}
    ]
}

FORECAST_FIXTURE = {
    "timezone": "Asia/Kolkata",
    "daily": {
        "time": ["2026-07-15", "2026-07-16", "2026-07-17"],
        "temperature_2m_max": [32.0, 41.0, 30.0],
        "temperature_2m_min": [24.0, 28.0, 22.0],
        "precipitation_sum": [2.0, 0.0, 150.0],
        "precipitation_probability_max": [10, 5, 85],
        "relative_humidity_2m_mean": [65, 40, 88],
        "windspeed_10m_max": [12.0, 15.0, 45.0],
        "et0_fao_evapotranspiration": [4.1, 5.8, 3.0],
    },
}


@respx.mock
def test_forecast_by_location_name():
    respx.get(config.OPEN_METEO_GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=GEOCODE_FIXTURE)
    )
    respx.get(config.OPEN_METEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_FIXTURE)
    )

    res = client.get("/api/weather/forecast", params={"location": "Coimbatore"})
    assert res.status_code == 200
    body = res.json()
    assert body["location"]["name"] == "Coimbatore"
    assert len(body["daily"]) == 3
    assert body["daily"][1]["temp_max_c"] == 41.0


@respx.mock
def test_forecast_by_lat_lon_skips_geocoding():
    route = respx.get(config.OPEN_METEO_GEOCODING_URL)
    respx.get(config.OPEN_METEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_FIXTURE)
    )

    res = client.get("/api/weather/forecast", params={"lat": 11.0168, "lon": 76.9558})
    assert res.status_code == 200
    assert not route.called


@respx.mock
def test_alerts_detects_heatwave_and_heavy_rain_and_high_wind():
    respx.get(config.OPEN_METEO_GEOCODING_URL).mock(
        return_value=httpx.Response(200, json=GEOCODE_FIXTURE)
    )
    respx.get(config.OPEN_METEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_FIXTURE)
    )

    res = client.get("/api/weather/alerts", params={"location": "Coimbatore"})
    assert res.status_code == 200
    alerts = res.json()["alerts"]
    types = {a["type"] for a in alerts}
    assert "heatwave" in types
    assert "very_heavy_rain" in types
    assert "high_wind" in types
    assert "dry_spell_risk" not in types  # 152mm total, above the 5mm threshold


@respx.mock
def test_dry_spell_detected_when_rain_is_negligible():
    dry_fixture = {
        "timezone": "Asia/Kolkata",
        "daily": {
            "time": ["2026-07-15", "2026-07-16"],
            "temperature_2m_max": [30.0, 31.0],
            "temperature_2m_min": [20.0, 21.0],
            "precipitation_sum": [0.0, 0.5],
            "precipitation_probability_max": [5, 5],
            "relative_humidity_2m_mean": [30, 28],
            "windspeed_10m_max": [10.0, 10.0],
            "et0_fao_evapotranspiration": [4.0, 4.2],
        },
    }
    respx.get(config.OPEN_METEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=dry_fixture)
    )

    res = client.get("/api/weather/alerts", params={"lat": 11.0, "lon": 77.0})
    types = {a["type"] for a in res.json()["alerts"]}
    assert "dry_spell_risk" in types


@respx.mock
def test_upstream_failure_returns_502_not_fake_data():
    respx.get(config.OPEN_METEO_GEOCODING_URL).mock(
        return_value=httpx.Response(503, text="upstream down")
    )
    res = client.get("/api/weather/forecast", params={"location": "Nowhere"})
    assert res.status_code == 502


def test_missing_location_and_coords_is_400():
    res = client.get("/api/weather/forecast")
    assert res.status_code == 400
