"""Document-related Pydantic schemas."""

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response schema for document upload."""

    message: str = Field(..., description="Status message")
    filename: str = Field(..., description="Uploaded filename")
    job_id: str | None = Field(None, description="Background job ID if applicable")


class ProcessingStatus(BaseModel):
    """Status of document processing."""

    filename: str
    status: str = Field(..., description="Processing status: 'processing', 'completed', 'failed'")
    parent_chunks: int | None = None
    child_chunks: int | None = None
    error: str | None = None
