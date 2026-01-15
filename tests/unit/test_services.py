"""Unit tests for service methods."""

import pytest

from app.core.config import settings


def test_config_loading():
    """Verify that configuration can be loaded."""
    # This test verifies that settings can be instantiated
    # In actual tests, you'd use environment variables or mocks
    assert settings.parent_chunk_size > 0
    assert settings.child_chunk_size > 0
    assert settings.child_chunk_size < settings.parent_chunk_size


def test_chunk_size_constraints():
    """Verify that chunk size constraints are enforced."""
    assert settings.parent_chunk_size >= 100
    assert 50 <= settings.child_chunk_size <= 500
    assert settings.parent_chunk_overlap >= 0
    assert settings.child_chunk_overlap >= 0
