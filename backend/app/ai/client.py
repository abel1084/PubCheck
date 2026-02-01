"""
Anthropic Claude client wrapper with native PDF support and streaming.
Uses Claude for AI-powered document review with full PDF understanding.
"""
import base64
import os
from typing import AsyncGenerator, Optional

from anthropic import AsyncAnthropic


class AIClientError(Exception):
    """Base exception for AI client errors."""
    pass


class AIConfigurationError(AIClientError):
    """Raised when API key is missing or invalid."""
    pass


class AIClient:
    """
    Wrapper for Anthropic Claude API with native PDF and streaming support.

    Uses Claude's native PDF document type for full text + visual understanding.
    Supports async streaming for real-time response delivery.
    """

    DEFAULT_MODEL = "claude-sonnet-4-5"
    DEFAULT_MAX_TOKENS = 8192

    def __init__(self):
        """Initialize the AI client. API key validated on first use."""
        self._client: Optional[AsyncAnthropic] = None
        self._model = os.getenv("AI_MODEL", self.DEFAULT_MODEL)

    def _ensure_client(self) -> AsyncAnthropic:
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                raise AIConfigurationError(
                    "ANTHROPIC_API_KEY not set.\n"
                    "Get your API key from: https://console.anthropic.com/settings/keys"
                )

            self._client = AsyncAnthropic(api_key=api_key)
        return self._client

    async def review_document_stream(
        self,
        pdf_bytes: bytes,
        user_prompt: str,
        system_prompt: str,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream document review using Claude's native PDF support.

        Args:
            pdf_bytes: Raw PDF file bytes
            user_prompt: User message with extraction JSON and document type
            system_prompt: System prompt with rules context
            max_tokens: Max response tokens (default: 8192)

        Yields:
            Text chunks as they're generated

        Raises:
            AIClientError: On API errors
            AIConfigurationError: If API key is missing
        """
        client = self._ensure_client()
        pdf_base64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        try:
            async with client.messages.stream(
                model=self._model,
                max_tokens=max_tokens or self.DEFAULT_MAX_TOKENS,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt,
                            }
                        ],
                    }
                ],
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            error_str = str(e).lower()

            if "invalid" in error_str and "key" in error_str:
                raise AIConfigurationError(f"Invalid API key: {e}") from e

            if "rate" in error_str or "quota" in error_str:
                raise AIClientError(f"Rate limit exceeded: {e}") from e

            raise AIClientError(f"API error: {e}") from e


# Singleton instance
_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get or create AI client singleton."""
    global _client
    if _client is None:
        _client = AIClient()
    return _client
