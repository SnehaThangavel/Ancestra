"""JWT token encoding, decoding, and verification handlers."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Union, Dict, Any
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status

from app.config import settings


def create_access_token(user_id: Union[uuid.UUID, str], email: str) -> str:
    """Generate a signed short-lived JWT access token.

    Args:
        user_id: Unique user identifier (UUID or string).
        email: User email address.

    Returns:
        str: Encoded JWT access token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: Union[uuid.UUID, str]) -> str:
    """Generate a signed longer-lived JWT refresh token.

    Args:
        user_id: Unique user identifier (UUID or string).

    Returns:
        str: Encoded JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token string.

    Args:
        token: Encoded JWT token string.

    Returns:
        Dict[str, Any]: Decoded token payload claims.

    Raises:
        HTTPException(401): If token is expired, invalid, or signature verification fails.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials / invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
