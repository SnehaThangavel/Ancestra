"""Tests for JWT token creation, encoding, decoding, and validation."""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from jose import jwt
from fastapi import HTTPException

from app.config import settings
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_create_and_decode_access_token() -> None:
    """Test creating a valid access token and decoding its claims."""
    user_id = uuid.uuid4()
    email = "curator@heritage.org"

    token = create_access_token(user_id=user_id, email=email)
    assert token is not None
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_create_and_decode_refresh_token() -> None:
    """Test creating a valid refresh token and verifying its type claim."""
    user_id = uuid.uuid4()

    refresh_token = create_refresh_token(user_id=user_id)
    assert refresh_token is not None

    payload = decode_token(refresh_token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_expired_token_raises_401() -> None:
    """Test that an expired token raises HTTPException with status 401."""
    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": str(uuid.uuid4()),
        "email": "expired@heritage.org",
        "type": "access",
        "exp": int((now - timedelta(hours=1)).timestamp()),
        "iat": int((now - timedelta(hours=2)).timestamp()),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_token(expired_token)

    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_decode_tampered_signature_raises_401() -> None:
    """Test that tampering with secret or token content raises HTTPException 401."""
    user_id = uuid.uuid4()
    # Sign with a different secret key
    fake_token = jwt.encode(
        {"sub": str(user_id), "type": "access", "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())},
        "wrong_secret_key_1234567890",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_token(fake_token)

    assert exc_info.value.status_code == 401
