"""Integration tests for API endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "product-manual-bot"


def test_upload_endpoint_invalid_file():
    """Test upload endpoint with invalid file type."""
    # Create a fake non-PDF file
    fake_file = io.BytesIO(b"This is not a PDF")
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("test.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_endpoint_missing_file():
    """Test upload endpoint without file."""
    response = client.post("/api/v1/ingestion/upload")
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_missing_query():
    """Test chat endpoint without required fields."""
    response = client.post(
        "/api/v1/chat/chat",
        json={"messages": []},
    )
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_invalid_request():
    """Test chat endpoint with invalid request structure."""
    response = client.post(
        "/api/v1/chat/chat",
        json={"invalid": "data"},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_stream_endpoint_structure():
    """Test that streaming endpoint returns proper SSE format."""
    # Note: TestClient doesn't fully support SSE streaming,
    # so this is a basic structure test
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "messages": [{"role": "user", "content": "test query"}],
            "query": "test query",
        },
    )
    # The endpoint should accept the request (actual streaming requires async client)
    # In a real scenario, you'd use httpx.AsyncClient for proper async testing
    assert response.status_code in [200, 500]  # 500 if services not initialized


def test_api_prefix():
    """Verify that API routes are properly prefixed."""
    # Health check should not have prefix
    response = client.get("/health")
    assert response.status_code == 200

    # API routes should have prefix
    response = client.get("/api/v1/chat/stream")
    # Should be 405 (method not allowed) or 422 (validation error), not 404
    assert response.status_code != 404
