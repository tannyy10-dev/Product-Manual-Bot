"""Vector service for Neon DB interactions with ParentDocumentRetriever pattern."""

import json
import uuid
from typing import Any

import asyncpg
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings


class VectorService:
    """Service for managing vector embeddings and parent-child chunk retrieval."""

    def __init__(self):
        """Initialize the vector service."""
        self.pool: asyncpg.Pool | None = None
        self.embeddings: Embeddings | None = None

    async def initialize(self) -> None:
        """Initialize database connection pool and embedding model."""
        # Create connection pool
        self.pool = await asyncpg.create_pool(
            settings.neon_db_url,
            min_size=1,
            max_size=settings.neon_db_pool_size,
        )

        # Initialize embedding model
        # Using HuggingFace embeddings as a default (can be swapped for OpenAI/Cohere)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-mpnet-base-v2",
            model_kwargs={"device": "cpu"},
        )

        # Ensure database schema exists
        await self._ensure_schema()

    async def _ensure_schema(self) -> None:
        """Create database tables and indexes if they don't exist."""
        async with self.pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create parent_chunks table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS parent_chunks (
                    id UUID PRIMARY KEY,
                    document_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    page_number INTEGER,
                    section_title TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

            # Create child_chunks table with vector column
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS child_chunks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    parent_id UUID NOT NULL REFERENCES parent_chunks(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    embedding vector({settings.embedding_dimension}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )

            # Create vector similarity index
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS child_chunks_embedding_idx
                ON child_chunks
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
                """
            )

            # Create index on parent_id for faster lookups
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS child_chunks_parent_id_idx
                ON child_chunks(parent_id)
                """
            )

    async def store_parent_chunk(
        self,
        parent_id: uuid.UUID,
        document_name: str,
        content: str,
        page_number: int | None = None,
        section_title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a parent chunk in the database."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO parent_chunks (id, document_name, content, page_number, section_title, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata
                """,
                parent_id,
                document_name,
                content,
                page_number,
                section_title,
                json.dumps(metadata) if metadata else None,
            )

    async def store_child_chunks(
        self,
        parent_id: uuid.UUID,
        child_chunks: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store child chunks with embeddings."""
        if not self.embeddings:
            raise RuntimeError("Embeddings not initialized")

        # Generate embeddings for all child chunks
        embeddings_list = await self.embeddings.aembed_documents(child_chunks)

        async with self.pool.acquire() as conn:
            # Insert all child chunks in a transaction
            async with conn.transaction():
                for content, embedding in zip(child_chunks, embeddings_list):
                    # Convert embedding to PostgreSQL vector format
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

                    await conn.execute(
                        """
                        INSERT INTO child_chunks (parent_id, content, embedding, metadata)
                        VALUES ($1, $2, $3::vector, $4)
                        """,
                        parent_id,
                        content,
                        embedding_str,
                        json.dumps(metadata) if metadata else None,
                    )

    async def retrieve_parent_chunks(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve parent chunks using ParentDocumentRetriever pattern.

        Args:
            query: User query string
            top_k: Number of chunks to retrieve (defaults to config value)

        Returns:
            List of parent chunks with metadata
        """
        if not self.embeddings:
            raise RuntimeError("Embeddings not initialized")

        top_k = top_k or settings.top_k_retrieval

        # Generate query embedding
        query_embedding = await self.embeddings.aembed_query(query)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        async with self.pool.acquire() as conn:
            # Find most similar child chunks, then retrieve their parent chunks
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (p.id)
                    p.id,
                    p.document_name,
                    p.content,
                    p.page_number,
                    p.section_title,
                    p.metadata,
                    1 - (c.embedding <=> $1::vector) as similarity
                FROM child_chunks c
                JOIN parent_chunks p ON c.parent_id = p.id
                ORDER BY p.id, c.embedding <=> $1::vector
                LIMIT $2
                """,
                embedding_str,
                top_k,
            )

            results = []
            for row in rows:
                results.append(
                    {
                        "id": str(row["id"]),
                        "document_name": row["document_name"],
                        "content": row["content"],
                        "page_number": row["page_number"],
                        "section_title": row["section_title"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        "similarity": float(row["similarity"]),
                    }
                )

            return results

    async def delete_document(self, document_name: str) -> None:
        """Delete all chunks associated with a document."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM parent_chunks WHERE document_name = $1",
                document_name,
            )

    async def close(self) -> None:
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
