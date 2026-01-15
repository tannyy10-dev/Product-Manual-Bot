"""Dependency injection for FastAPI endpoints."""

from fastapi import Request

from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService
from app.services.vector_service import VectorService


def get_vector_service(request: Request) -> VectorService:
    """Get vector service from application state."""
    return request.app.state.vector_service


def get_rag_service(request: Request) -> RAGService:
    """Get RAG service with vector service dependency."""
    vector_service = get_vector_service(request)
    return RAGService(vector_service)


def get_ingestion_service(request: Request) -> IngestionService:
    """Get ingestion service with vector service dependency."""
    vector_service = get_vector_service(request)
    return IngestionService(vector_service)
