from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_documents():
    res = client.get("/api/assistant/documents")
    assert res.status_code == 200
    docs = res.json()["documents"]
    assert "executive_summary" in docs
    assert "finalist_guidelines" in docs
    assert "presentation_blueprint" in docs
    assert "pitch_strategy" in docs


def test_query_retrieves_relevant_section_about_disease_model():
    res = client.post(
        "/api/assistant/query",
        json={"question": "What model architecture is used for plant disease detection?"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "extractive"  # no ANTHROPIC_API_KEY set in test env
    assert len(body["sources"]) > 0
    joined_sources = " ".join(s["text"].lower() for s in body["sources"])
    assert "yolo" in joined_sources


def test_query_retrieves_relevant_section_about_judging_criteria():
    res = client.post(
        "/api/assistant/query", json={"question": "What are the judging criteria for the finale?"}
    )
    body = res.json()
    joined_sources = " ".join(s["text"].lower() for s in body["sources"])
    assert "innovation" in joined_sources
    assert "feasibility" in joined_sources


def test_query_respects_top_k():
    res = client.post(
        "/api/assistant/query", json={"question": "fertilizer recommendation engine", "top_k": 1}
    )
    assert len(res.json()["sources"]) <= 1


def test_query_too_short_is_422():
    res = client.post("/api/assistant/query", json={"question": "hi"})
    assert res.status_code == 422


def test_query_nonsense_returns_no_relevant_content_gracefully():
    res = client.post("/api/assistant/query", json={"question": "xyzzy plugh qwerty asdfgh"})
    assert res.status_code == 200
    body = res.json()
    assert body["sources"] == []
    assert "no relevant content" in body["answer"].lower()
