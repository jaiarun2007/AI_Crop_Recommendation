from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

INDIA_RICE = {
    "Area": "India",
    "Item": "Rice, paddy",
    "Year": 2013,
    "average_rain_fall_mm_per_year": 1083.0,
    "pesticides_tonnes": 46765.0,
    "avg_temp": 24.5,
}


def test_yield_predict_happy_path():
    res = client.post("/api/yield/predict", json=INDIA_RICE)
    assert res.status_code == 200
    body = res.json()
    assert body["predicted_yield_kg_per_ha"] > 0
    assert body["warnings"] == []
    assert body["model_r2"] > 0.9


def test_yield_predict_unknown_area_warns_but_still_predicts():
    payload = {**INDIA_RICE, "Area": "Atlantis"}
    res = client.post("/api/yield/predict", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["predicted_yield_kg_per_ha"] > 0
    assert any("Atlantis" in w for w in body["warnings"])


def test_yield_predict_validation_error():
    payload = {**INDIA_RICE, "avg_temp": 999}
    res = client.post("/api/yield/predict", json=payload)
    assert res.status_code == 422


def test_known_values_endpoint():
    res = client.get("/api/yield/known-values")
    assert res.status_code == 200
    body = res.json()
    assert "India" in body["areas"]
    assert "Rice, paddy" in body["crops"]
