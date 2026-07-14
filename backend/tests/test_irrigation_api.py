"""Router-level tests: mocks Open-Meteo at the HTTP transport layer (same pattern as
test_weather_api.py) so the irrigation endpoint's weather->plan composition is verified
without a live network call."""
import httpx
import respx
from fastapi.testclient import TestClient

from app import config
from app.main import app

client = TestClient(app)

FORECAST_FIXTURE = {
    "timezone": "Asia/Kolkata",
    "daily": {
        "time": ["2026-07-15", "2026-07-16"],
        "temperature_2m_max": [32.0, 33.0],
        "temperature_2m_min": [24.0, 25.0],
        "precipitation_sum": [0.0, 10.0],
        "precipitation_probability_max": [5, 40],
        "relative_humidity_2m_mean": [60, 62],
        "windspeed_10m_max": [10.0, 12.0],
        "et0_fao_evapotranspiration": [5.0, 5.5],
    },
}


@respx.mock
def test_irrigation_schedule_end_to_end():
    respx.get(config.OPEN_METEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_FIXTURE)
    )

    res = client.post(
        "/api/irrigation/schedule",
        json={"crop": "rice", "growth_stage": "mid_season", "lat": 11.0, "lon": 77.0, "days": 2},
    )
    assert res.status_code == 200
    body = res.json()
    assert len(body["daily_plan"]) == 2
    assert body["daily_plan"][0]["irrigation_needed_mm"] == 6.0  # 5.0 * 1.20 Kc, no rain
    assert body["daily_plan"][1]["action"] == "skip"  # 5.5*1.2=6.6 demand vs 10mm rain


@respx.mock
def test_irrigation_schedule_unknown_crop():
    respx.get(config.OPEN_METEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=FORECAST_FIXTURE)
    )
    res = client.post(
        "/api/irrigation/schedule",
        json={"crop": "dragonfruit", "growth_stage": "mid_season", "lat": 11.0, "lon": 77.0},
    )
    assert res.status_code == 400


def test_irrigation_schedule_missing_location():
    res = client.post("/api/irrigation/schedule", json={"crop": "rice", "growth_stage": "mid_season"})
    assert res.status_code == 400


def test_known_crops_endpoint():
    res = client.get("/api/irrigation/known-crops")
    assert res.status_code == 200
    body = res.json()
    assert "rice" in body["crops"]
    assert "mid_season" in body["growth_stages"]
