from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_known_crops_lists_reference_crops():
    res = client.get("/api/fertilizer/known-crops")
    assert res.status_code == 200
    crops = res.json()["crops"]
    assert "rice" in crops
    assert len(crops) == 22


def test_recommend_flags_nitrogen_deficit():
    # Rice ideal N=80; giving it 20 should flag a large deficit + a Urea dose.
    res = client.post(
        "/api/fertilizer/recommend", json={"crop": "rice", "N": 20, "P": 40, "K": 40, "ph": 5.5}
    )
    assert res.status_code == 200
    body = res.json()
    n_advice = next(n for n in body["nutrients"] if n["nutrient"] == "N")
    assert n_advice["status"] == "deficient"
    assert n_advice["recommended_product"] == "Urea"
    assert n_advice["recommended_dose_kg_ha"] > 0
    assert body["ph_advice"]["status"] == "adequate"


def test_recommend_flags_surplus_and_adequate():
    # Exactly matching ideal values -> adequate on all fronts.
    res = client.post(
        "/api/fertilizer/recommend", json={"crop": "rice", "N": 80, "P": 40, "K": 40, "ph": 5.5}
    )
    body = res.json()
    for n in body["nutrients"]:
        assert n["status"] == "adequate"


def test_recommend_flags_acidic_ph():
    res = client.post(
        "/api/fertilizer/recommend", json={"crop": "banana", "N": 100, "P": 75, "K": 50, "ph": 4.0}
    )
    body = res.json()
    assert body["ph_advice"]["status"] == "too_acidic"
    assert "lime" in body["ph_advice"]["message"].lower()


def test_recommend_unknown_crop_returns_400_with_known_list():
    res = client.post(
        "/api/fertilizer/recommend", json={"crop": "dragonfruit", "N": 10, "P": 10, "K": 10, "ph": 6}
    )
    assert res.status_code == 400
    assert "rice" in res.json()["detail"]


def test_recommend_validation_error():
    res = client.post(
        "/api/fertilizer/recommend", json={"crop": "rice", "N": 10, "P": 10, "K": 10, "ph": 99}
    )
    assert res.status_code == 422
