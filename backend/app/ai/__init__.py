"""
AI module for document review.
Provides Claude-powered document analysis with native PDF support.
"""
from .client import AIClient, AIClientError, AIConfigurationError, get_ai_client
from .reviewer import review_document, load_rules_context
from .prompts import build_system_prompt, build_user_prompt
from .schemas import ReviewRequest, ReviewMetadata

__all__ = [
    # Client
    "AIClient",
    "AIClientError",
    "AIConfigurationError",
    "get_ai_client",
    # Reviewer
    "review_document",
    "load_rules_context",
    # Prompts
    "build_system_prompt",
    "build_user_prompt",
    # Schemas
    "ReviewRequest",
    "ReviewMetadata",
]
