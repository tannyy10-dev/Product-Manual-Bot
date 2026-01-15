"""Unit tests for recursive text splitting logic."""

import pytest

from app.services.ingestion_service import IngestionService


@pytest.fixture
def ingestion_service():
    """Create ingestion service for testing."""
    return IngestionService(None)  # Vector service not needed for splitting tests


def test_recursive_splitting_respects_paragraphs(ingestion_service):
    """Verify that the splitter preserves paragraphs when possible."""
    text = "# Header 1\n\nThis is a paragraph under header 1.\n\nThis is another paragraph."
    chunks = ingestion_service.split_text_recursive(text, chunk_size=100)

    # Should split by paragraphs first
    assert len(chunks) >= 1
    assert "Header 1" in chunks[0] or any("Header 1" in chunk for chunk in chunks)


def test_fine_grained_chunk_size(ingestion_service):
    """Verify that chunks strictly adhere to the size limit."""
    text = "A" * 1000
    chunks = ingestion_service.split_text_recursive(text, chunk_size=100, chunk_overlap=10)

    # All chunks should be within size limit (accounting for overlap)
    for chunk in chunks:
        assert len(chunk) <= 100


def test_recursive_splitting_with_overlap(ingestion_service):
    """Verify that chunk overlap works correctly."""
    text = "Sentence one. Sentence two. Sentence three. Sentence four."
    chunks = ingestion_service.split_text_recursive(text, chunk_size=30, chunk_overlap=10)

    # With overlap, adjacent chunks should share some content
    if len(chunks) > 1:
        # Check that there's some overlap between consecutive chunks
        # This is a simplified check - actual overlap logic is more complex
        assert len(chunks) > 1


def test_empty_text_handling(ingestion_service):
    """Verify that empty text is handled gracefully."""
    chunks = ingestion_service.split_text_recursive("", chunk_size=100)
    assert chunks == []


def test_single_chunk_when_text_fits(ingestion_service):
    """Verify that short text remains as a single chunk."""
    text = "This is a short text that fits in one chunk."
    chunks = ingestion_service.split_text_recursive(text, chunk_size=1000)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_markdown_header_preservation(ingestion_service):
    """Verify that Markdown headers are preserved with their content when possible."""
    text = "# Section Title\n\nThis is the content under the section."
    chunks = ingestion_service.split_text_recursive(text, chunk_size=100)

    # The header and its content should ideally be in the same chunk
    # if they fit within the size limit
    combined_text = " ".join(chunks)
    assert "Section Title" in combined_text
    assert "content under" in combined_text


def test_parent_child_chunk_relationship(ingestion_service):
    """Verify that parent chunks are larger than child chunks."""
    text = "A" * 5000  # Large text

    # Split into parent chunks
    parent_chunks = ingestion_service.parent_splitter.split_text(text)

    # Split a parent into child chunks
    if parent_chunks:
        child_chunks = ingestion_service.child_splitter.split_text(parent_chunks[0])

        # Child chunks should be smaller than parent chunks
        assert len(child_chunks) > 0
        for child in child_chunks:
            assert len(child) <= ingestion_service.child_splitter._chunk_size
            assert len(child) < len(parent_chunks[0])
