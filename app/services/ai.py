"""Gemini API integration for generating assistant responses."""

from __future__ import annotations

from collections.abc import Sequence

import httpx

from app.config import Settings
from app.models.schemas import ChatMessage


class AIServiceError(RuntimeError):
    """Raised when the external LLM provider cannot complete a request."""


class GeminiAIService:
    """Thin wrapper around the Gemini generateContent REST API."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self._client = client or httpx.AsyncClient(timeout=settings.llm_timeout_seconds)

    async def generate_reply(self, history: Sequence[ChatMessage]) -> str:
        """Generate an assistant reply from the full chat history."""

        if not self.settings.gemini_api_key:
            raise AIServiceError(
                "GEMINI_API_KEY is not configured. Add it to your .env file before calling /chat."
            )

        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": self.settings.system_prompt,
                    }
                ]
            },
            "contents": self._build_contents(history),
            "generationConfig": {
                "temperature": self.settings.temperature,
            },
        }
        headers = {
            "x-goog-api-key": self.settings.gemini_api_key,
            "Content-Type": "application/json",
        }

        try:
            response = await self._client.post(
                self._build_url(),
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip() or str(exc)
            raise AIServiceError(f"Gemini rejected the request: {detail}") from exc
        except httpx.HTTPError as exc:
            raise AIServiceError(f"Gemini request failed: {exc}") from exc

        try:
            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise AIServiceError("Gemini returned an unexpected response payload.") from exc

        reply = self._extract_text_content(parts)
        if not reply:
            raise AIServiceError("Gemini returned an empty assistant response.")
        return reply

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    def _build_contents(self, history: Sequence[ChatMessage]) -> list[dict[str, object]]:
        """Build Gemini conversation contents from stored chat history."""

        return [
            {
                "role": self._map_role(message.role),
                "parts": [{"text": message.content}],
            }
            for message in history
        ]

    def _build_url(self) -> str:
        """Build the Gemini generateContent endpoint for the selected model."""

        base_url = self.settings.gemini_api_base_url.rstrip("/")
        return f"{base_url}/{self.settings.gemini_model}:generateContent"

    @staticmethod
    def _map_role(role: str) -> str:
        """Translate local roles into Gemini API roles."""

        if role == "assistant":
            return "model"
        return "user"

    @staticmethod
    def _extract_text_content(content: object) -> str:
        """Normalize provider responses that may return string or block arrays."""

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text_value = item.get("text", "")
                    if isinstance(text_value, str):
                        text_parts.append(text_value)
            return "\n".join(part.strip() for part in text_parts if part.strip()).strip()

        return ""
