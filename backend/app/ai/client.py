"""
Google Gemini client wrapper with retry logic for AI-powered analysis.
Uses Gemini 2.0 Flash for vision capabilities.
"""
import base64
import json
import os
import time
from typing import Any, Dict, Optional

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
    Wrapper for Google Gemini API with retry logic.

    Uses Gemini 2.0 Flash for fast, cost-effective vision analysis.
    Includes exponential backoff retry on transient errors.
    """

    DEFAULT_MODEL = "gemini-2.0-flash"
    DEFAULT_TIMEOUT = 60.0  # seconds
    MAX_RETRIES = 5
    RETRY_DELAYS = [2.0, 5.0, 10.0, 20.0, 30.0]  # longer backoff for rate limits

    def __init__(self):
        """
        Initialize the AI client.

        Does NOT validate API key at init time to allow graceful handling.
        API key is validated on first use.
        """
        self._client: Optional[genai.Client] = None
        self._model = os.getenv("AI_MODEL", self.DEFAULT_MODEL)

    def _ensure_client(self) -> genai.Client:
        """
        Lazy initialization of Gemini client.

        Requires GOOGLE_API_KEY from Google AI Studio.

        Raises:
            AIConfigurationError: If API key is not set
        """
        if self._client is None:
            api_key = os.getenv("GOOGLE_API_KEY")

            if not api_key:
                raise AIConfigurationError(
                    "GOOGLE_API_KEY not set.\n"
                    "Get your API key from: https://aistudio.google.com/apikey"
                )

            self._client = genai.Client(api_key=api_key)
        return self._client

    def analyze_page(
        self,
        image_data: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a page image using Gemini Vision.

        Sends the image with the prompt to Gemini and returns parsed JSON response.

        Args:
            image_data: Base64-encoded PNG image data
            prompt: Analysis prompt (user message)
            system_prompt: Optional system prompt for role/context

        Returns:
            Parsed JSON from response text

        Raises:
            AIClientError: On API errors after retries exhausted
            AIConfigurationError: If API key is missing
        """
        client = self._ensure_client()

        # Decode base64 to bytes for Gemini
        image_bytes = base64.b64decode(image_data)

        # Build content parts
        contents = []

        # Add image (JPEG for smaller size)
        contents.append(
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        )

        # Add text prompt
        contents.append(types.Part.from_text(text=prompt))

        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                # Build config
                config = types.GenerateContentConfig(
                    temperature=0,  # Deterministic for verification
                    max_output_tokens=4096,
                )

                if system_prompt:
                    config.system_instruction = system_prompt

                response = client.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config=config,
                )

                # Extract text from response
                text_content = response.text.strip()

                # Parse JSON from response
                # Handle potential markdown code blocks
                if text_content.startswith("```json"):
                    text_content = text_content[7:]
                if text_content.startswith("```"):
                    text_content = text_content[3:]
                if text_content.endswith("```"):
                    text_content = text_content[:-3]
                text_content = text_content.strip()

                return json.loads(text_content)

            except Exception as e:
                error_str = str(e).lower()

                # Check for retryable errors
                if "rate" in error_str or "quota" in error_str or "503" in error_str or "500" in error_str:
                    last_error = e
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAYS[attempt])
                        continue
                    raise AIClientError(
                        f"API error after {self.MAX_RETRIES} retries: {e}"
                    ) from e

                # Non-retryable errors
                if "invalid" in error_str and "key" in error_str:
                    raise AIConfigurationError(f"Invalid API key: {e}") from e

                raise AIClientError(f"API error: {e}") from e

        # Should not reach here, but just in case
        raise AIClientError(
            f"Failed after {self.MAX_RETRIES} retries: {last_error}"
        )


# Singleton instance
_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """
    Get or create AI client singleton.

    Returns:
        AIClient instance (shared across the application)
    """
    global _client
    if _client is None:
        _client = AIClient()
    return _client
