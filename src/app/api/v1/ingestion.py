"""Document ingestion API endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.api.dependencies import get_ingestion_service
from app.schemas.document import UploadResponse
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.post("/upload", status_code=202, response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> UploadResponse:
    """
    Upload and process a PDF document.

    Returns immediately with 202 Accepted status.
    Processing happens in the background.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    # Validate file size (e.g., 50MB limit)
    file_content = await file.read()
    if len(file_content) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 50MB limit",
        )

    # Add background task for processing
    background_tasks.add_task(
        ingestion_service.process_document,
        file_content,
        file.filename,
    )

    return UploadResponse(
        message="Upload accepted. Document is being processed.",
        filename=file.filename,
    )
