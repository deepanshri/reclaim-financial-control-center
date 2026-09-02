from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, extract_token, get_current_user
from app.core.config import settings
from app.core.security import cookie_kwargs, new_session_token, session_expiry
from app.db import operational as store

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    merchant_id: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    token: str
    merchant_id: str
    merchant_name: str
    expires_at: str
    dataset_type: str = "synthetic_demo"


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response) -> LoginResponse:
    merchant_id = payload.merchant_id.strip()
    if merchant_id != settings.demo_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Merchant ID or password is incorrect.",
        )
    user = store.authenticate(merchant_id, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Merchant ID or password is incorrect.",
        )
    token = new_session_token()
    expires = session_expiry()
    store.create_session(user["merchant_id"], token, expires)
    response.set_cookie(value=token, **cookie_kwargs())
    return LoginResponse(
        token=token,
        merchant_id=user["merchant_id"],
        merchant_name=user["merchant_name"],
        expires_at=expires.isoformat(),
        dataset_type="synthetic_demo",
    )


@router.post("/logout")
def logout(request: Request, response: Response) -> dict:
    token = extract_token(request, request.headers.get("authorization"))
    merchant_id = ""
    if token:
        session = store.get_session(token)
        if session:
            merchant_id = session["merchant_id"]
        store.delete_session(token)
    cookie = cookie_kwargs()
    response.delete_cookie(
        cookie["key"],
        path=cookie.get("path", "/"),
        secure=cookie.get("secure", False),
        httponly=True,
        samesite=cookie.get("samesite", "lax"),
    )
    return {"status": "signed_out", "merchant_id": merchant_id}


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return {
        "merchant_id": user.merchant_id,
        "merchant_name": user.merchant_name,
        "dataset_type": "synthetic_demo",
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
