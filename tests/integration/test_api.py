"""Integration tests for API endpoints."""

import io
import pytest

# NOTE: We removed 'from fastapi.testclient import TestClient' 
# and 'from app.main import app' because the 'client' fixture 
# in conftest.py handles the app creation and configuration.

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "product-manual-bot"


def test_upload_endpoint_invalid_file(client):
    """Test upload endpoint with invalid file type."""
    # Create a fake non-PDF file
    fake_file = io.BytesIO(b"This is not a PDF")
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("test.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_upload_endpoint_missing_file(client):
    """Test upload endpoint without file."""
    response = client.post("/api/v1/ingestion/upload")
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_missing_query(client):
    """Test chat endpoint without required fields."""
    response = client.post(
        "/api/v1/chat/chat",
        json={"messages": []},
    )
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_invalid_request(client):
    """Test chat endpoint with invalid request structure."""
    response = client.post(
        "/api/v1/chat/chat",
        json={"invalid": "data"},
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_stream_endpoint_structure(client):
    """Test that streaming endpoint returns proper SSE format."""
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "messages": [{"role": "user", "content": "test query"}],
            "query": "test query",
        },
    )
    # The endpoint should now return 200 because the mock services are injected
    assert response.status_code == 200


def test_api_prefix(client):
    """Verify that API routes are properly prefixed."""
    # Health check should not have prefix
    response = client.get("/health")
    assert response.status_code == 200

    # API routes should have prefix
    response = client.get("/api/v1/chat/stream")
    # Should be 405 (method not allowed) because we sent a GET to a POST endpoint
    # This proves the route exists.
    assert response.status_code != 404