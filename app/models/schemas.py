"""Request and response schemas for the chatbot API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Request payload for sending a new user message."""

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Unique identifier used to scope one conversation session.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The latest message from the user.",
    )

    @field_validator("session_id", "message")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        """Normalize whitespace-only input into a validation error."""

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty or whitespace only")
        return cleaned


class ChatMessage(BaseModel):
    """One message in the stored conversation history."""

    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    """Response returned after generating an assistant reply."""

    session_id: str
    reply: str
    history_length: int = Field(
        ...,
        description="Total number of messages now stored in the session.",
    )


class HistoryResponse(BaseModel):
    """Full ordered history for a session."""

    session_id: str
    messages: list[ChatMessage]


class DeleteHistoryResponse(BaseModel):
    """Response returned after clearing session history."""

    session_id: str
    cleared: bool
    deleted_messages: int


class HealthResponse(BaseModel):
    """Service health payload."""

    status: str
    environment: str
    provider: str
    database: str

