import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.vector_service import VectorService

@pytest.fixture
def mock_db_pool():
    """Create a mock asyncpg pool with a connection context manager."""
    pool = MagicMock()
    connection = MagicMock()
    
    # Mock the async context manager: async with pool.acquire() as conn:
    pool.acquire.return_value.__aenter__.return_value = connection
    pool.acquire.return_value.__aexit__.return_value = None
    
    return pool, connection

@pytest.mark.asyncio
async def test_retrieve_parent_chunks_success(mock_db_pool):
    """Test the retrieval logic specifically."""
    mock_pool, mock_conn = mock_db_pool
    
    service = VectorService()
    service.pool = mock_pool
    
    # 1. Mock Embeddings
    # We must mock this because retrieve_parent_chunks calls aembed_query
    mock_embeddings = MagicMock()
    mock_embeddings.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
    service.embeddings = mock_embeddings
    
    # 2. Mock DB Results (what conn.fetch returns)
    # The SQL query returns specific columns, so we mock a Row-like dict
    mock_rows = [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "document_name": "manual.pdf",
            "content": "This is the parent content.",
            "page_number": 5,
            "section_title": "Maintenance",
            "metadata": '{"author": "Admin"}', # DB returns JSON string
            "similarity": 0.89
        }
    ]
    mock_conn.fetch = AsyncMock(return_value=mock_rows)

    # 3. Call the method
    results = await service.retrieve_parent_chunks("how to maintain", top_k=2)

    # 4. Assertions
    assert len(results) == 1
    assert results[0]["document_name"] == "manual.pdf"
    assert results[0]["similarity"] == 0.89
    # Verify JSON string was parsed back to dict
    assert results[0]["metadata"] == {"author": "Admin"}
    
    # Verify correct flow
    mock_embeddings.aembed_query.assert_called_once_with("how to maintain")
    mock_conn.fetch.assert_called_once()

@pytest.mark.asyncio
async def test_retrieve_uninitialized_error():
    """Test error when embeddings are not initialized."""
    service = VectorService()
    # We do NOT set service.embeddings
    
    with pytest.raises(RuntimeError, match="Embeddings not initialized"):
        await service.retrieve_parent_chunks("query")

@pytest.mark.asyncio
async def test_initialization():
    """Test the initialize method creates pool and loads embeddings."""
    service = VectorService()
    
    # Mock external dependencies
    with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool, \
         patch("app.services.vector_service.HuggingFaceEmbeddings") as mock_hf, \
         patch.object(service, '_ensure_schema', new_callable=AsyncMock) as mock_schema:
        
        await service.initialize()
        
        mock_create_pool.assert_called_once()
        mock_hf.assert_called_once()
        mock_schema.assert_called_once()
        assert service.pool is not None
        assert service.embeddings is not None