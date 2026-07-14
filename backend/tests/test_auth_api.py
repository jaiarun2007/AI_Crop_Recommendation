from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from fastapi.testclient import TestClient

from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app

# Isolated in-memory SQLite per test run so registrations here never touch the real
# dev database file or leak state across test runs (avoids 409 email-conflict flakiness).
# StaticPool keeps every connection pointed at the same in-memory DB (plain :memory: would
# otherwise give each new connection its own empty database).
engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_users_table():
    yield
    with engine.connect() as conn:
        conn.execute(models.User.__table__.delete())
        conn.commit()


def test_register_creates_user_and_returns_token():
    res = client.post(
        "/api/auth/register",
        json={"email": "farmer@example.com", "password": "correct-horse-battery", "full_name": "Farmer Joe"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "farmer@example.com"
    assert body["user"]["full_name"] == "Farmer Joe"
    assert "access_token" in body and len(body["access_token"]) > 10


def test_register_duplicate_email_is_409():
    client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    res = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password456"})
    assert res.status_code == 409


def test_register_short_password_is_422():
    res = client.post("/api/auth/register", json={"email": "x@example.com", "password": "short"})
    assert res.status_code == 422


def test_login_with_correct_credentials():
    client.post("/api/auth/register", json={"email": "login@example.com", "password": "password123"})
    res = client.post("/api/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_with_wrong_password_is_401():
    client.post("/api/auth/register", json={"email": "login2@example.com", "password": "password123"})
    res = client.post("/api/auth/login", json={"email": "login2@example.com", "password": "wrong-password"})
    assert res.status_code == 401


def test_login_unknown_email_is_401():
    res = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert res.status_code == 401


def test_me_requires_valid_token():
    res = client.get("/api/auth/me")
    assert res.status_code in (401, 403)  # HTTPBearer returns 403 when the header is missing entirely


def test_me_returns_current_user_with_valid_token():
    reg = client.post(
        "/api/auth/register", json={"email": "me@example.com", "password": "password123"}
    )
    token = reg.json()["access_token"]
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@example.com"


def test_me_rejects_garbage_token():
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_password_is_never_returned():
    res = client.post(
        "/api/auth/register", json={"email": "secret@example.com", "password": "password123"}
    )
    assert "password" not in res.json()["user"]
    assert "hashed_password" not in res.json()["user"]
