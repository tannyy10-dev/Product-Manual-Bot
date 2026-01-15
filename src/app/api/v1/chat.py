"""Chat API endpoints with streaming support."""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies import get_rag_service
from app.schemas.chat import ChatRequest
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> EventSourceResponse:
    """
    Stream chat responses using Server-Sent Events (SSE).

    Returns a streaming response where each event contains a chunk of text.
    The final event contains source citations.
    """
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    async def event_generator():
        try:
            sources = []
            chunk_count = 0
            async for text_chunk, chunk_sources in rag_service.generate_stream(
                messages, request.query
            ):
                if text_chunk:
                    # Send text chunk
                    chunk_count += 1
                    yield {
                        "event": "message",
                        "data": json.dumps({"type": "chunk", "content": text_chunk}),
                        "id": str(chunk_count),
                    }
                if chunk_sources:
                    sources = chunk_sources

            # Send final event with sources
            if sources:
                yield {
                    "event": "sources",
                    "data": json.dumps({"type": "sources", "sources": sources}),
                    "id": "sources",
                }
            yield {
                "event": "done",
                "data": json.dumps({"type": "done"}),
                "id": "done",
            }
        except Exception as e:
            # Send error event
            import traceback
            error_details = traceback.format_exc()
            yield {
                "event": "error",
                "data": json.dumps({"type": "error", "message": str(e), "details": error_details}),
                "id": "error",
            }
            yield {
                "event": "done",
                "data": json.dumps({"type": "done"}),
                "id": "done",
            }

    return EventSourceResponse(event_generator())


@router.post("/chat")
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Non-streaming chat endpoint.

    Returns complete response with sources in a single response.
    """
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    response, sources = await rag_service.generate(messages, request.query)

    return {"response": response, "sources": sources}
