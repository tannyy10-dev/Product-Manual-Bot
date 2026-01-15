"""Ingestion service for PDF parsing and recursive text splitting."""

import io
import uuid
from typing import Any

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.vector_service import VectorService


class IngestionService:
    """Service for processing and ingesting documents."""

    def __init__(self, vector_service: VectorService):
        """Initialize the ingestion service."""
        self.vector_service = vector_service

        # Parent chunk splitter (large chunks for context)
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.parent_chunk_size,
            chunk_overlap=settings.parent_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

        # Child chunk splitter (fine-grained for retrieval)
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.child_chunk_size,
            chunk_overlap=settings.child_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    async def process_document(
        self,
        file_content: bytes,
        filename: str,
    ) -> dict[str, Any]:
        """
        Process a PDF document and store it in the vector database.

        Args:
            file_content: Raw PDF file content
            filename: Name of the uploaded file

        Returns:
            Dictionary with processing results
        """
        # Parse PDF
        text_content = self._extract_text_from_pdf(file_content)

        # Split into parent chunks
        parent_chunks = self.parent_splitter.split_text(text_content)

        # Process each parent chunk
        total_child_chunks = 0
        for idx, parent_chunk in enumerate(parent_chunks):
            parent_id = uuid.uuid4()

            # Store parent chunk
            await self.vector_service.store_parent_chunk(
                parent_id=parent_id,
                document_name=filename,
                content=parent_chunk,
                page_number=None,  # Could be enhanced to track page numbers
                section_title=None,  # Could be enhanced to extract section titles
                metadata={"chunk_index": idx, "total_chunks": len(parent_chunks)},
            )

            # Split parent into child chunks
            child_chunks = self.child_splitter.split_text(parent_chunk)

            # Store child chunks with embeddings
            await self.vector_service.store_child_chunks(
                parent_id=parent_id,
                child_chunks=child_chunks,
                metadata={"parent_index": idx},
            )

            total_child_chunks += len(child_chunks)

        return {
            "filename": filename,
            "parent_chunks": len(parent_chunks),
            "child_chunks": total_child_chunks,
            "status": "success",
        }

    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """
        Extract text from PDF file.

        Args:
            file_content: Raw PDF file content

        Returns:
            Extracted text content
        """
        text_parts = []
        file_obj = io.BytesIO(file_content)

        try:
            with pdfplumber.open(file_obj) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}") from e

        return "\n\n".join(text_parts)

    def split_text_recursive(
        self,
        text: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> list[str]:
        """
        Split text using recursive character splitting.

        This method is exposed for testing purposes.

        Args:
            text: Text to split
            chunk_size: Size of chunks (defaults to child chunk size)
            chunk_overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.child_chunk_size,
            chunk_overlap=chunk_overlap or settings.child_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        return splitter.split_text(text)
