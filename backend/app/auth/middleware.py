"""
Signed-cookie authentication for PubCheck.

Uses HMAC signing (stdlib) to create a cookie proving the browser
authenticated successfully. No server-side session state, so
authentication survives worker restarts and serverless cold starts.

Password is configured via PUBCHECK_PASSWORD environment variable.
Signing key is configured via PUBCHECK_SECRET_KEY environment variable.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional

from fastapi import Cookie, HTTPException, status


MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _get_secret() -> bytes:
    """Get the signing secret from env vars."""
    secret = os.environ.get("PUBCHECK_SECRET_KEY", "")
    if not secret:
        secret = os.environ.get("PUBCHECK_PASSWORD", "pubcheck")
    return secret.encode("utf-8")


def _sign(payload: bytes) -> str:
    """Sign payload and return base64-encoded token: payload.signature"""
    sig = hmac.new(_get_secret(), payload, hashlib.sha256).digest()
    b64_payload = base64.urlsafe_b64encode(payload).decode()
    b64_sig = base64.urlsafe_b64encode(sig).decode()
    return f"{b64_payload}.{b64_sig}"


def _verify(token: str) -> Optional[dict]:
    """Verify token signature and expiry. Returns payload dict or None."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_payload, b64_sig = parts
        payload = base64.urlsafe_b64decode(b64_payload)
        expected_sig = hmac.new(_get_secret(), payload, hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(b64_sig)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        data = json.loads(payload)
        issued_at = data.get("iat", 0)
        if time.time() - issued_at > MAX_AGE:
            return None
        return data
    except Exception:
        return None


def create_signed_token() -> str:
    """Create a signed token encoding the authentication timestamp."""
    payload = json.dumps({"auth": True, "iat": int(time.time())}).encode()
    return _sign(payload)


def verify_signed_token(token: str) -> bool:
    """Verify a signed token is valid and not expired."""
    return _verify(token) is not None


def verify_session(pubcheck_session: Optional[str] = Cookie(None)) -> bool:
    """
    Verify session cookie has a valid signature.

    Raises:
        HTTPException: 401 if cookie is missing or signature is invalid
    """
    if not pubcheck_session or not verify_signed_token(pubcheck_session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return True


def check_password(password: str) -> bool:
    """
    Check if password matches the configured password.
    """
    correct_password = os.environ.get("PUBCHECK_PASSWORD", "pubcheck")
    return secrets.compare_digest(
        password.encode("utf-8"),
        correct_password.encode("utf-8"),
    )
