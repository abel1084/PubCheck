"""
Authentication API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from .middleware import check_password, create_session, invalidate_session, _valid_sessions


router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class AuthStatus(BaseModel):
    authenticated: bool


@router.post("/login")
async def login(request: LoginRequest, response: Response) -> AuthStatus:
    """
    Login with password and set session cookie.
    """
    if not check_password(request.password):
        return AuthStatus(authenticated=False)

    token = create_session()
    response.set_cookie(
        key="pubcheck_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    return AuthStatus(authenticated=True)


@router.post("/logout")
async def logout(
    response: Response,
    pubcheck_session: Optional[str] = Cookie(None),
) -> AuthStatus:
    """
    Logout and clear session cookie.
    """
    if pubcheck_session:
        invalidate_session(pubcheck_session)

    response.delete_cookie(key="pubcheck_session")
    return AuthStatus(authenticated=False)


@router.get("/check")
async def check_auth(
    pubcheck_session: Optional[str] = Cookie(None),
) -> AuthStatus:
    """
    Check if current session is authenticated.
    """
    authenticated = pubcheck_session is not None and pubcheck_session in _valid_sessions
    return AuthStatus(authenticated=authenticated)
