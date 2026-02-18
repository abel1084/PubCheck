"""
Authentication API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from .middleware import check_password, create_signed_token, verify_signed_token


router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class AuthStatus(BaseModel):
    authenticated: bool


@router.post("/login")
async def login(request: LoginRequest, response: Response) -> AuthStatus:
    """
    Login with password and set signed session cookie.
    """
    if not check_password(request.password):
        return AuthStatus(authenticated=False)

    token = create_signed_token()
    response.set_cookie(
        key="pubcheck_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    return AuthStatus(authenticated=True)


@router.post("/logout")
async def logout(response: Response) -> AuthStatus:
    """
    Logout and clear session cookie.
    """
    response.delete_cookie(key="pubcheck_session")
    return AuthStatus(authenticated=False)


@router.get("/check")
async def check_auth(
    pubcheck_session: Optional[str] = Cookie(None),
) -> AuthStatus:
    """
    Check if current session is authenticated.
    """
    authenticated = bool(pubcheck_session and verify_signed_token(pubcheck_session))
    return AuthStatus(authenticated=authenticated)
