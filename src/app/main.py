"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.events import lifespan
from app.api.v1 import chat, ingestion

def create_app() -> FastAPI:
    """
    App Factory: Creates and configures the FastAPI application.
    """
    application = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        lifespan=lifespan,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(chat.router, prefix=f"{settings.api_prefix}/chat", tags=["chat"])
    application.include_router(
        ingestion.router,
        prefix=f"{settings.api_prefix}/ingestion",
        tags=["ingestion"],
    )

    # --- MOVED INSIDE THE FACTORY ---
    @application.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "service": "product-manual-bot"}
    
    return application

# Create the global app instance for production
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=True,
    )