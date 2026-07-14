import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def make_image_bytes(rgb_color):
    img = Image.new("RGB", (300, 300), rgb_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_disease_detect_healthy_green_leaf():
    img = make_image_bytes((34, 139, 34))  # forest green
    res = client.post(
        "/api/disease/detect", files={"file": ("leaf.png", img, "image/png")}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert body["severity_percent"] < 10


def test_disease_detect_diseased_brown_leaf():
    img = make_image_bytes((139, 90, 43))  # brownish
    res = client.post(
        "/api/disease/detect", files={"file": ("leaf.png", img, "image/png")}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "diseased"
    assert body["severity_percent"] > 25


def test_disease_detect_rejects_bad_content_type():
    res = client.post(
        "/api/disease/detect",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert res.status_code == 400
