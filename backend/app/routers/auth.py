"""FastAPI router for Google OAuth 2.0 authentication and JWT lifecycle management."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.auth.oauth import oauth
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.dependencies import get_current_user
from app.schemas.auth import (
    TokenRefreshRequest,
    TokenResponse,
    UserResponse,
    LogoutResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Google OAuth"])


@router.get("/login", summary="Initiate Google OAuth 2.0 Login")
async def login(request: Request):
    """Redirect user to Google's OAuth 2.0 consent screen."""
    # Ensure redirect URI matches backend callback
    redirect_uri = f"{str(request.base_url).rstrip('/')}/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri, prompt="select_account")


@router.get("/callback", name="auth_callback", summary="Google OAuth 2.0 Callback Handshake")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """Exchange authorization code for user info, find/create user, issue JWTs, and redirect to frontend."""
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth token authorization failed: {str(exc)}",
        ) from exc

    user_info = token.get("userinfo")
    if not user_info:
        try:
            user_info = await oauth.google.userinfo(token=token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch Google user profile: {str(exc)}",
            ) from exc

    google_sub = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    hd = user_info.get("hd")

    if not email or not google_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google user profile missing required email or subject identifier.",
        )

    # Optional Google Workspace domain restriction
    if settings.GOOGLE_ALLOWED_DOMAIN:
        email_domain = email.split("@")[-1] if "@" in email else ""
        if hd != settings.GOOGLE_ALLOWED_DOMAIN and email_domain != settings.GOOGLE_ALLOWED_DOMAIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to {settings.GOOGLE_ALLOWED_DOMAIN} accounts.",
            )

    # Find or create User in PostgreSQL
    user = (
        db.query(User)
        .filter((User.google_sub_id == google_sub) | (User.email == email))
        .first()
    )

    now_utc = datetime.now(timezone.utc)

    if not user:
        user = User(
            id=uuid.uuid4(),
            email=email,
            name=name,
            google_sub_id=google_sub,
            picture_url=picture,
            is_active=True,
            created_at=now_utc,
            last_login_at=now_utc,
        )
        db.add(user)
    else:
        user.google_sub_id = google_sub
        if name:
            user.name = name
        if picture:
            user.picture_url = picture
        user.last_login_at = now_utc

    db.commit()
    db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated.",
        )

    # Issue access and refresh JWTs
    access_token = create_access_token(user_id=user.id, email=user.email)
    refresh_token = create_refresh_token(user_id=user.id)

    # Top-level browser redirect to frontend callback handler with tokens
    frontend_target = (
        f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    )
    return RedirectResponse(url=frontend_target)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Expired JWT Access Token",
)
async def refresh_access_token(
    payload: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    """Validate a genuine refresh token and issue a new access token (with token rotation)."""
    decoded = decode_token(payload.refresh_token)

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: refresh token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = decoded.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = create_access_token(user_id=user.id, email=user.email)
    new_refresh_token = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current Authenticated User Profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile and authentication status for current Bearer token holder."""
    return current_user


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Client-side Logout Acknowledgment",
)
async def logout():
    """Acknowledge logout action.

    Note: JWTs are stateless. Server-side revocation would require a distributed token
    blocklist (e.g., Redis). For this version, token disposal is managed on the client side.
    """
    return LogoutResponse(
        status="success",
        message="Successfully logged out. Please discard stored JWT tokens.",
    )
