"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import create_app

# --- Mock Services ---
class MockVectorService:
    """Mock vector service for testing."""
    def __init__(self):
        # Mock search to return an empty list
        self.search = AsyncMock(return_value=[])
        # Mock ingest to return True
        self.ingest_text = AsyncMock(return_value=True)

class MockIngestionService:
    """Mock ingestion service for testing."""
    def __init__(self, vector_service):
        self.vector_service = vector_service
        # Mock processing a file
        self.process_file = AsyncMock(return_value={"status": "processed", "chunks": 1})

# --- Fixtures ---

@pytest.fixture
def mock_vector_service():
    """Returns a mock instance of the VectorService."""
    return MockVectorService()

@pytest.fixture
def mock_ingestion_service(mock_vector_service):
    """Returns a mock instance of the IngestionService."""
    return MockIngestionService(mock_vector_service)

@pytest.fixture
def client(mock_vector_service, mock_ingestion_service):
    """
    Creates a TestClient with a fresh app instance and 
    INJECTS the mock services into app.state.
    """
    # 1. Create a fresh app using the factory
    app = create_app()

    # 2. MANUALLY INJECT MOCKS into app.state
    # This overrides whatever the lifespan event would have done
    # and ensures integration tests have access to these services.
    app.state.vector_service = mock_vector_service
    app.state.ingestion_service = mock_ingestion_service

    # 3. Return the client
    # We use a context manager to ensure startup/shutdown events run
    # (though our manual injection above ensures the services exist regardless)
    with TestClient(app) as test_client:
        yield test_client