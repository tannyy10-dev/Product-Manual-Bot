"""Startup and shutdown event handlers for FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.services.vector_service import VectorService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    vector_service = VectorService()
    await vector_service.initialize()
    app.state.vector_service = vector_service

    yield

    # Shutdown
    await vector_service.close()
