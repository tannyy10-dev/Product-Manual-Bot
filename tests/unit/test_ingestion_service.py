import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.ingestion_service import IngestionService

@pytest.mark.asyncio
async def test_process_document_success():
    """Test successful document processing."""
    # 1. Setup Mocks
    mock_vector_svc = MagicMock()
    mock_vector_svc.store_parent_chunk = AsyncMock()
    mock_vector_svc.store_child_chunks = AsyncMock()
    
    service = IngestionService(vector_service=mock_vector_svc)
    
    # 2. Mock internal PDF extraction to avoid needing a real PDF file
    with patch.object(service, '_extract_text_from_pdf', return_value="Page 1 content.\n\nPage 2 content."):
        
        # 3. Call method
        result = await service.process_document(b"fake_bytes", "test.pdf")
        
        # 4. Assertions
        assert result["status"] == "success"
        assert result["filename"] == "test.pdf"
        assert result["parent_chunks"] > 0
        # Verify vector service was called
        mock_vector_svc.store_parent_chunk.assert_called()
        mock_vector_svc.store_child_chunks.assert_called()

@pytest.mark.asyncio
async def test_process_document_pdf_error():
    """Test handling of invalid PDF files (Extraction Failure)."""
    mock_vector_svc = MagicMock()
    service = IngestionService(vector_service=mock_vector_svc)
    
    # Simulate a corrupted PDF that causes pdfplumber to fail
    # We patch pdfplumber.open to raise an exception
    with patch("pdfplumber.open", side_effect=Exception("Corrupted file header")):
        
        # The service wraps exceptions in ValueError, so we expect that
        with pytest.raises(ValueError, match="Failed to extract text"):
            await service.process_document(b"bad_bytes", "bad.pdf")

@pytest.mark.asyncio
async def test_process_document_db_error():
    """Test handling of Vector DB failures."""
    mock_vector_svc = MagicMock()
    # Simulate DB connection failure
    mock_vector_svc.store_parent_chunk = AsyncMock(side_effect=RuntimeError("Database connection lost"))
    
    service = IngestionService(vector_service=mock_vector_svc)
    
    # Mock successful PDF extraction so we hit the DB logic
    with patch.object(service, '_extract_text_from_pdf', return_value="Valid text"):
        
        # The exception should propagate up
        with pytest.raises(RuntimeError, match="Database connection lost"):
            await service.process_document(b"bytes", "test.pdf")