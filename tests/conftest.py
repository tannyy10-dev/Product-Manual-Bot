"""Pytest configuration and fixtures."""

import pytest

from app.services.ingestion_service import IngestionService
from app.services.vector_service import VectorService


@pytest.fixture
def mock_vector_service():
    """Mock vector service for testing."""
    # This would be replaced with a proper mock in actual tests
    return None


@pytest.fixture
def ingestion_service(mock_vector_service):
    """Create an ingestion service instance for testing."""
    # For unit tests, we can test splitting logic without actual DB
    return IngestionService(mock_vector_service)
