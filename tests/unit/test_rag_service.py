import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from types import SimpleNamespace
from app.services.rag_service import RAGService

@pytest.mark.asyncio
async def test_generate_flow():
    # 1. Setup Vector Service Mock
    mock_vector_svc = MagicMock()
    mock_vector_svc.retrieve_parent_chunks = AsyncMock(return_value=[
        {
            "content": "The batteries last 5 years.",
            "document_name": "manual.pdf",
            "page_number": 10,
            "section_title": "Battery Life",
            "similarity": 0.95
        }
    ])

    # 2. Setup LLM Response
    # Use SimpleNamespace so .content is a real string, not a mock
    mock_llm_response = SimpleNamespace(content="The batteries last 5 years based on the manual.")

    # 3. Setup LLM Mock
    mock_llm = MagicMock()
    
    # CRITICAL FIX: LangChain treats a MagicMock as a callable function, not a Runnable.
    # So it calls mock_llm(...) directly. We must set return_value for the object itself.
    mock_llm.return_value = mock_llm_response
    
    # We also set these for safety, in case implementation changes to use .invoke() directly
    mock_llm.invoke.return_value = mock_llm_response
    mock_llm.ainvoke = AsyncMock(return_value=mock_llm_response)

    # 4. Patch ChatGroq
    with patch("app.services.rag_service.ChatGroq", return_value=mock_llm):
        
        # Initialize Service
        service = RAGService(vector_service=mock_vector_svc)
        # Force inject just to be safe
        service.llm = mock_llm

        # 5. Call the method
        messages = [{"role": "user", "content": "Hello"}]
        query = "How long do batteries last?"
        
        response_text, sources = await service.generate(messages, query)

        # 6. Assertions
        assert "The batteries last 5 years" in response_text
        assert len(sources) == 1
        assert sources[0]["document_name"] == "manual.pdf"
        
        mock_vector_svc.retrieve_parent_chunks.assert_called_once_with(query)