"""
Anthropic client wrapper with retry logic for AI-powered analysis.
Compatible with Pydantic v1 patterns.
"""
import json
import os
import time
from typing import Any, Dict, Optional

import anthropic


class AIClientError(Exception):
    """Base exception for AI client errors."""
    pass


class AIConfigurationError(AIClientError):
    """Raised when API key is missing or invalid."""
    pass


class AIClient:
    """
    Wrapper for Anthropic Claude API with retry logic.

    Uses temperature=0 for deterministic results.
    Includes exponential backoff retry on transient errors.
    30-second timeout per request.
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TIMEOUT = 30.0  # seconds
    MAX_RETRIES = 3
    RETRY_DELAYS = [1.0, 2.0, 4.0]  # exponential backoff

    def __init__(self):
        """
        Initialize the AI client.

        Does NOT validate API key at init time to allow graceful handling.
        API key is validated on first use.
        """
        self._api_key: Optional[str] = None
        self._client: Optional[anthropic.Anthropic] = None
        self._model = os.getenv("AI_MODEL", self.DEFAULT_MODEL)

    def _ensure_client(self) -> anthropic.Anthropic:
        """
        Lazy initialization of Anthropic client.

        Uses CLAUDE_CODE_OAUTH_TOKEN (Claude Code subscription) if available,
        falls back to ANTHROPIC_API_KEY for direct API access.

        Raises:
            AIConfigurationError: If neither token is set
        """
        if self._client is None:
            # Prefer Claude Code OAuth token (uses existing subscription)
            self._api_key = os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
            if not self._api_key:
                # Fall back to direct API key
                self._api_key = os.getenv("ANTHROPIC_API_KEY")

            if not self._api_key:
                raise AIConfigurationError(
                    "No API credentials found. Set either:\n"
                    "  - CLAUDE_CODE_OAUTH_TOKEN (uses your Claude Code subscription)\n"
                    "  - ANTHROPIC_API_KEY (direct API access)"
                )
            self._client = anthropic.Anthropic(
                api_key=self._api_key,
                timeout=self.DEFAULT_TIMEOUT,
            )
        return self._client

    def analyze_page(
        self,
        image_data: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a page image using Claude Vision.

        Sends the image with the prompt to Claude and returns parsed JSON response.

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

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ]

        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                kwargs: Dict[str, Any] = {
                    "model": self._model,
                    "max_tokens": self.DEFAULT_MAX_TOKENS,
                    "temperature": 0,  # Deterministic for verification
                    "messages": messages,
                }

                if system_prompt:
                    kwargs["system"] = system_prompt

                response = client.messages.create(**kwargs)

                # Extract text content from response
                text_content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text_content += block.text

                # Parse JSON from response
                # Handle potential markdown code blocks
                text_content = text_content.strip()
                if text_content.startswith("```json"):
                    text_content = text_content[7:]
                if text_content.startswith("```"):
                    text_content = text_content[3:]
                if text_content.endswith("```"):
                    text_content = text_content[:-3]
                text_content = text_content.strip()

                return json.loads(text_content)

            except anthropic.RateLimitError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAYS[attempt])
                    continue
                raise AIClientError(
                    f"Rate limit exceeded after {self.MAX_RETRIES} retries: {e}"
                ) from e

            except anthropic.APIConnectionError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAYS[attempt])
                    continue
                raise AIClientError(
                    f"API connection error after {self.MAX_RETRIES} retries: {e}"
                ) from e

            except anthropic.APIStatusError as e:
                # 5xx errors are retryable, 4xx are not (except 429 rate limit)
                if e.status_code >= 500:
                    last_error = e
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAYS[attempt])
                        continue
                raise AIClientError(f"API error: {e}") from e

            except json.JSONDecodeError as e:
                # Response wasn't valid JSON - don't retry
                raise AIClientError(
                    f"Failed to parse API response as JSON: {e}"
                ) from e

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
