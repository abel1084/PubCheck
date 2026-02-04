"""
Google Gemini client wrapper with native PDF support and streaming.
Uses Gemini 2.5 Flash with thinking mode for AI-powered document review.
"""
import io
import logging
import os
from typing import AsyncGenerator, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


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
    INLINE_SIZE_LIMIT = 900 * 1024  # 900KB - stay under 1MB inline limit

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

    def _upload_file(self, pdf_bytes: bytes, filename: str = "document.pdf"):
        """Upload PDF to Gemini Files API for large documents."""
        client = self._ensure_client()

        # Upload using file-like object
        file_obj = io.BytesIO(pdf_bytes)
        file_obj.name = filename

        uploaded_file = client.files.upload(
            file=file_obj,
            config={"mime_type": "application/pdf"}
        )

        return uploaded_file

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
        uploaded_file = None

        try:
            pdf_size = len(pdf_bytes)
            logger.info(f"PDF size: {pdf_size} bytes ({pdf_size/1024:.1f}KB)")

            # Use File API for large PDFs, inline for small ones
            if pdf_size > self.INLINE_SIZE_LIMIT:
                logger.info(f"Using Files API (size {pdf_size} > limit {self.INLINE_SIZE_LIMIT})")
                # Upload large file first
                uploaded_file = self._upload_file(pdf_bytes)
                logger.info(f"File uploaded: {uploaded_file.name}, uri={uploaded_file.uri}")
                pdf_part = types.Part.from_uri(
                    file_uri=uploaded_file.uri,
                    mime_type="application/pdf"
                )
            else:
                logger.info(f"Using inline bytes (size {pdf_size} <= limit {self.INLINE_SIZE_LIMIT})")
                # Use inline bytes for small files
                pdf_part = types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type="application/pdf"
                )

            contents = [
                pdf_part,
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
            logger.error(f"AI API error: {type(e).__name__}: {e}")
            error_str = str(e).lower()

            if "invalid" in error_str and "key" in error_str:
                raise AIConfigurationError(f"Invalid API key: {e}") from e

            if "rate" in error_str or "quota" in error_str or "429" in error_str:
                raise AIClientError(f"Rate limit exceeded: {e}") from e

            if "too large" in error_str or "size" in error_str or "1024kb" in error_str:
                raise AIClientError(f"Document too large for processing: {e}") from e

            raise AIClientError(f"API error: {e}") from e

        finally:
            # Clean up uploaded file if used
            if uploaded_file:
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass  # Ignore cleanup errors


# Singleton instance
_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get or create AI client singleton."""
    global _client
    if _client is None:
        _client = AIClient()
    return _client
