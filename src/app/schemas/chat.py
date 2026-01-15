"""Chat-related Pydantic schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    messages: list[ChatMessage] = Field(
        ...,
        description="Chat history as list of messages",
        min_length=1,
    )
    query: str = Field(
        ...,
        description="Current user query",
        min_length=1,
        max_length=1000,
    )


class ChatResponse(BaseModel):
    """Response schema for non-streaming chat."""

    response: str = Field(..., description="Assistant response")
    sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Source documents used for generation",
    )


class SourceCitation(BaseModel):
    """Source citation information."""

    document_name: str
    page_number: int | None = None
    section_title: str | None = None
    similarity: float = Field(..., ge=0.0, le=1.0)
