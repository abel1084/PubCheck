"""
Session-based authentication for PubCheck.

Provides a simple shared-password authentication with session cookies.
Password is configured via PUBCHECK_PASSWORD environment variable.
"""
import os
import secrets
from typing import Optional

from fastapi import Cookie, HTTPException, status


# Session token storage (in-memory for simplicity)
# In production, use Redis or database
_valid_sessions: set[str] = set()


def create_session() -> str:
    """Create a new session token."""
    token = secrets.token_urlsafe(32)
    _valid_sessions.add(token)
    return token


def invalidate_session(token: str) -> None:
    """Invalidate a session token."""
    _valid_sessions.discard(token)


def verify_session(pubcheck_session: Optional[str] = Cookie(None)) -> bool:
    """
    Verify session cookie is valid.

    Args:
        pubcheck_session: Session token from cookie

    Returns:
        True if session is valid

    Raises:
        HTTPException: 401 if session is invalid
    """
    if not pubcheck_session or pubcheck_session not in _valid_sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return True


def check_password(password: str) -> bool:
    """
    Check if password matches the configured password.

    Args:
        password: Password to check

    Returns:
        True if password matches
    """
    correct_password = os.environ.get("PUBCHECK_PASSWORD", "pubcheck")
    return secrets.compare_digest(
        password.encode("utf-8"),
        correct_password.encode("utf-8"),
    )
