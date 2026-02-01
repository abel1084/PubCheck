"""
Google Gemini client wrapper with native PDF support and streaming.
Uses Gemini 2.5 Flash with thinking mode for AI-powered document review.
"""
import os
from typing import AsyncGenerator, Optional

from google import genai
from google.genai import types


class AIClientError(Exception):
    """Base exception for AI client errors."""
    pass


class AIConfigurationError(AIClientError):
    """Raised when API key is missing or invalid."""
    pass


class AIClient:
    """
    Wrapper for Google Gemini API with native PDF and streaming support.

    Uses Gemini 2.5 Flash with thinking mode for enhanced reasoning.
    Supports async streaming for real-time response delivery.
    """

    DEFAULT_MODEL = "gemini-2.5-flash"
    DEFAULT_MAX_TOKENS = 16384  # Gemini supports larger outputs

    def __init__(self):
        """Initialize the AI client. API key validated on first use."""
        self._client: Optional[genai.Client] = None
        self._model_name = os.getenv("AI_MODEL", self.DEFAULT_MODEL)

    def _ensure_client(self) -> genai.Client:
        """Lazy initialization of Gemini client."""
        if self._client is None:
            api_key = os.getenv("GOOGLE_API_KEY")

            if not api_key:
                raise AIConfigurationError(
                    "GOOGLE_API_KEY not set.\n"
                    "Get your API key from: https://aistudio.google.com/apikey"
                )

            self._client = genai.Client(api_key=api_key)

        return self._client

    async def review_document_stream(
        self,
        pdf_bytes: bytes,
        user_prompt: str,
        system_prompt: str,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream document review using Gemini's native PDF support.

        Args:
            pdf_bytes: Raw PDF file bytes
            user_prompt: User message with extraction JSON and document type
            system_prompt: System prompt with rules context
            max_tokens: Max response tokens (default: 16384)

        Yields:
            Text chunks as they're generated

        Raises:
            AIClientError: On API errors
            AIConfigurationError: If API key is missing
        """
        client = self._ensure_client()

        try:
            # Build content with PDF document inline
            contents = [
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                types.Part.from_text(text=user_prompt),
            ]

            # Configure generation with thinking enabled
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens or self.DEFAULT_MAX_TOKENS,
                temperature=1.0,  # Required for thinking mode
                thinking_config=types.ThinkingConfig(
                    thinking_budget=8192,
                ),
            )

            # Stream response - await the coroutine to get async iterator
            stream = await client.aio.models.generate_content_stream(
                model=self._model_name,
                contents=contents,
                config=config,
            )
            async for chunk in stream:
                # Extract text from response parts, skip thinking parts
                if chunk.candidates:
                    for candidate in chunk.candidates:
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    # Skip thinking content (has thought=True attribute)
                                    if not getattr(part, 'thought', False):
                                        yield part.text

        except Exception as e:
            error_str = str(e).lower()

            if "invalid" in error_str and "key" in error_str:
                raise AIConfigurationError(f"Invalid API key: {e}") from e

            if "rate" in error_str or "quota" in error_str or "429" in error_str:
                raise AIClientError(f"Rate limit exceeded: {e}") from e

            if "too large" in error_str or "size" in error_str:
                raise AIClientError(f"Document too large: {e}") from e

            raise AIClientError(f"API error: {e}") from e


# Singleton instance
_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get or create AI client singleton."""
    global _client
    if _client is None:
        _client = AIClient()
    return _client
