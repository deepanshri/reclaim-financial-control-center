from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import settings
from app.core.security import SESSION_COOKIE, parse_bearer
from app.db import operational as store

PUBLIC_PATHS = {
    "/",
    "/api/health",
    "/api/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class CurrentUser:
    def __init__(self, merchant_id: str, merchant_name: str, token: str):
        self.merchant_id = merchant_id
        self.merchant_name = merchant_name
        self.token = token


def extract_token(request: Request, authorization: Optional[str]) -> Optional[str]:
    bearer = parse_bearer(authorization)
    if bearer:
        return bearer
    cookie = request.cookies.get(SESSION_COOKIE)
    return cookie or None


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> CurrentUser:
    token = extract_token(request, authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in required to view financial records.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session = store.get_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if session["merchant_id"] != settings.demo_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this merchant workspace.",
        )
    return CurrentUser(session["merchant_id"], session["merchant_name"], token)
