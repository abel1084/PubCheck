"""
HTTP Basic Authentication middleware for PubCheck.

Provides a simple shared-password authentication using browser-native
HTTP Basic Auth dialog. Password is configured via PUBCHECK_PASSWORD
environment variable.
"""
import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# HTTPBasic with auto_error=True triggers browser's native auth dialog
security = HTTPBasic(auto_error=True)


def verify_password(
    credentials: HTTPBasicCredentials = Depends(security),
) -> bool:
    """
    Verify HTTP Basic Auth credentials.

    Username can be anything - only password is checked.
    Password is compared using constant-time comparison to prevent timing attacks.

    Args:
        credentials: HTTP Basic credentials from request

    Returns:
        True if password is valid

    Raises:
        HTTPException: 401 if password is invalid
    """
    # Get password from environment, default to "pubcheck" for development
    correct_password = os.environ.get("PUBCHECK_PASSWORD", "pubcheck")

    # Use constant-time comparison to prevent timing attacks
    password_correct = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        correct_password.encode("utf-8"),
    )

    if not password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return True
