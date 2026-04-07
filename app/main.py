"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.routes.chat import router as chat_router
from app.services.ai import GeminiAIService
from app.services.memory import SQLiteMemoryStore


def create_app(
    settings: Settings | None = None,
    memory_store: SQLiteMemoryStore | None = None,
    ai_service: GeminiAIService | None = None,
) -> FastAPI:
    """Create a configured FastAPI application instance."""

    app_settings = settings or get_settings()
    app_memory_store = memory_store or SQLiteMemoryStore(app_settings.database_path)
    app_ai_service = ai_service or GeminiAIService(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app_memory_store.initialize()
        app.state.settings = app_settings
        app.state.memory_store = app_memory_store
        app.state.ai_service = app_ai_service
        try:
            yield
        finally:
            await app_ai_service.aclose()

    app = FastAPI(
        title=app_settings.app_name,
        debug=app_settings.debug,
        version="1.0.0",
        lifespan=lifespan,
        description=(
            "ChatGPT-style conversational AI backend with session-scoped memory, "
            "FastAPI endpoints, and Docker-ready packaging."
        ),
    )
    app.include_router(chat_router)
    return app


app = create_app()
