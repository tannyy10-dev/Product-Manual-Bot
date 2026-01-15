"""Configuration module using Pydantic Settings for environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Configuration
    api_title: str = "Product Manual Bot API"
    api_version: str = "v1"
    api_prefix: str = "/api/v1"

    # Groq Configuration
    groq_api_key: str = Field(..., description="Groq API key")
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model to use for generation",
    )
    groq_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation",
    )

    # Neon DB Configuration
    neon_db_url: str = Field(..., description="Neon DB connection string")
    neon_db_pool_size: int = Field(
        default=10,
        ge=1,
        description="Database connection pool size",
    )

    # Embedding Configuration
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model name",
    )
    embedding_dimension: int = Field(
        default=768,
        ge=128,
        description="Embedding vector dimension",
    )

    # Chunking Configuration
    parent_chunk_size: int = Field(
        default=2000,
        ge=100,
        description="Size of parent chunks in characters",
    )
    parent_chunk_overlap: int = Field(
        default=200,
        ge=0,
        description="Overlap between parent chunks in characters",
    )
    child_chunk_size: int = Field(
        default=300,
        ge=50,
        le=500,
        description="Size of child chunks in characters (fine-grained)",
    )
    child_chunk_overlap: int = Field(
        default=50,
        ge=0,
        description="Overlap between child chunks in characters",
    )

    # Retrieval Configuration
    top_k_retrieval: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top chunks to retrieve",
    )

    # Streamlit Configuration
    streamlit_port: int = Field(
        default=8501,
        ge=1024,
        le=65535,
        description="Port for Streamlit frontend",
    )

    # FastAPI Configuration
    fastapi_host: str = Field(
        default="0.0.0.0",
        description="Host for FastAPI server",
    )
    fastapi_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Port for FastAPI server",
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:8501", "http://127.0.0.1:8501"],
        description="Allowed CORS origins",
    )


# Global settings instance
settings = Settings()
