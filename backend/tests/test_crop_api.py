from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

RICE_LIKE = {
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 20.9,
    "humidity": 82.0,
    "ph": 6.5,
    "rainfall": 203.0,
}


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_crop_recommend_happy_path():
    res = client.post("/api/crop/recommend", json=RICE_LIKE)
    assert res.status_code == 200
    body = res.json()
    assert body["top_recommendation"] == "rice"
    assert 0 <= body["confidence"] <= 1
    assert len(body["alternatives"]) == 3


def test_crop_recommend_validation_error():
    bad_payload = {**RICE_LIKE, "ph": 999}
    res = client.post("/api/crop/recommend", json=bad_payload)
    assert res.status_code == 422


def test_crop_recommend_missing_field():
    payload = dict(RICE_LIKE)
    del payload["N"]
    res = client.post("/api/crop/recommend", json=payload)
    assert res.status_code == 422
