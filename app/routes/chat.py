"""Route handlers for chat and history APIs."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    DeleteHistoryResponse,
    HealthResponse,
    HistoryResponse,
)
from app.services.ai import AIServiceError, GeminiAIService
from app.services.memory import SQLiteMemoryStore

router = APIRouter()


def get_memory_store(request: Request) -> SQLiteMemoryStore:
    """Get the memory store attached during app startup."""

    return request.app.state.memory_store


def get_ai_service(request: Request) -> GeminiAIService:
    """Get the AI service attached during app startup."""

    return request.app.state.ai_service


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """Generate a reply while preserving session-scoped conversation memory."""

    memory_store = get_memory_store(request)
    ai_service = get_ai_service(request)

    existing_history = memory_store.get_history(payload.session_id)
    pending_user_message = ChatMessage(
        role="user",
        content=payload.message,
        created_at=datetime.now(timezone.utc),
    )

    try:
        reply = await ai_service.generate_reply(existing_history + [pending_user_message])
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    memory_store.append_message(
        session_id=payload.session_id,
        role="user",
        content=payload.message,
    )
    memory_store.append_message(
        session_id=payload.session_id,
        role="assistant",
        content=reply,
    )

    updated_history = memory_store.get_history(payload.session_id)
    return ChatResponse(
        session_id=payload.session_id,
        reply=reply,
        history_length=len(updated_history),
    )


@router.get(
    "/history/{session_id}",
    response_model=HistoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_history(session_id: str, request: Request) -> HistoryResponse:
    """Return the ordered conversation history for one session."""

    memory_store = get_memory_store(request)
    messages = memory_store.get_history(session_id.strip())
    return HistoryResponse(session_id=session_id.strip(), messages=messages)


@router.delete(
    "/history/{session_id}",
    response_model=DeleteHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def clear_history(session_id: str, request: Request) -> DeleteHistoryResponse:
    """Delete all messages for one session."""

    normalized_session_id = session_id.strip()
    if not normalized_session_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="session_id must not be empty.",
        )

    memory_store = get_memory_store(request)
    deleted_messages = memory_store.clear_history(normalized_session_id)
    return DeleteHistoryResponse(
        session_id=normalized_session_id,
        cleared=True,
        deleted_messages=deleted_messages,
    )


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check(request: Request) -> HealthResponse:
    """Simple health endpoint for container orchestration and local checks."""

    memory_store = get_memory_store(request)
    settings = request.app.state.settings

    if not memory_store.healthcheck():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        )

    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        provider="gemini",
        database=str(memory_store.database_path),
    )
