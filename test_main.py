"""
test_main.py
-------------
Unit tests for the FastAPI backend. Run with:
    pytest backend/tests

Note: the /generate endpoint loads real transformer models on first call,
so that particular test may take a while the first time it runs (models are
downloaded and cached locally by Hugging Face afterwards).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import init_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    yield


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_verify_endpoint():
    resp = client.get("/api/v1/verify", params={"query": "blockchain in healthcare"})
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert data["query"] == "blockchain in healthcare"


def test_history_endpoint_empty_or_list():
    resp = client.get("/api/v1/history")
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.slow
def test_generate_endpoint():
    """Marked slow: downloads/loads DistilBERT + GPT-2 the first time it runs."""
    payload = {
        "event_description": "AI for Sustainable Cities",
        "interests": ["climate change", "urban planning"],
        "num_starters": 2,
    }
    resp = client.post("/api/v1/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["conversation_starters"]) == 2
    assert "interaction_id" in data


@pytest.mark.slow
def test_feedback_endpoint_requires_valid_interaction():
    resp = client.post("/api/v1/feedback", json={"interaction_id": 999999, "useful": True})
    assert resp.status_code == 404
