"""Tests for Google OAuth 2.0 and Authentication API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.config import settings
from app.auth.jwt_handler import create_access_token, create_refresh_token


def test_auth_login_redirect(client: TestClient) -> None:
    """Test /auth/login initiates redirect to Google consent screen."""
    with patch("app.auth.oauth.oauth.google.authorize_redirect", new_callable=AsyncMock) as mock_redirect:
        from fastapi.responses import RedirectResponse
        mock_redirect.return_value = RedirectResponse(url="https://accounts.google.com/o/oauth2/auth?mock=1")

        response = client.get("/auth/login", follow_redirects=False)
        assert response.status_code == 307
        assert "accounts.google.com" in response.headers["location"]


def test_auth_callback_creates_new_user(client: TestClient, db_session: Session) -> None:
    """Test /auth/callback creates a new user on first login and redirects to frontend with tokens."""
    mock_token = {
        "access_token": "mock_google_token",
        "userinfo": {
            "sub": "google_uid_999",
            "email": "archaeologist@heritage.org",
            "name": "Dr. Indiana Stone",
            "picture": "https://example.com/avatar.jpg",
        },
    }

    with patch("app.auth.oauth.oauth.google.authorize_access_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_token

        response = client.get("/auth/callback?code=mock_code", follow_redirects=False)
        assert response.status_code == 307
        target_url = response.headers["location"]
        assert settings.FRONTEND_URL in target_url
        assert "access_token=" in target_url
        assert "refresh_token=" in target_url

        # Verify User created in DB
        user = db_session.query(User).filter_by(google_sub_id="google_uid_999").first()
        assert user is not None
        assert user.email == "archaeologist@heritage.org"
        assert user.name == "Dr. Indiana Stone"
        assert user.picture_url == "https://example.com/avatar.jpg"
        assert user.is_active is True
        assert user.last_login_at is not None


def test_auth_callback_updates_existing_user(client: TestClient, db_session: Session) -> None:
    """Test /auth/callback updates an existing user profile and last_login_at."""
    existing_user = User(
        id=uuid.uuid4(),
        email="curator_senior@heritage.org",
        name="Old Name",
        google_sub_id="google_uid_existing",
        is_active=True,
    )
    db_session.add(existing_user)
    db_session.commit()

    mock_token = {
        "access_token": "mock_google_token_2",
        "userinfo": {
            "sub": "google_uid_existing",
            "email": "curator_senior@heritage.org",
            "name": "Updated Name",
            "picture": "https://example.com/new_pic.jpg",
        },
    }

    with patch("app.auth.oauth.oauth.google.authorize_access_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = mock_token

        response = client.get("/auth/callback?code=mock_code_2", follow_redirects=False)
        assert response.status_code == 307

        db_session.refresh(existing_user)
        assert existing_user.name == "Updated Name"
        assert existing_user.picture_url == "https://example.com/new_pic.jpg"


def test_auth_callback_domain_restriction_rejected(client: TestClient, db_session: Session) -> None:
    """Test that unauthorized domains are rejected with 403 when GOOGLE_ALLOWED_DOMAIN is configured."""
    mock_token = {
        "access_token": "mock_token",
        "userinfo": {
            "sub": "google_uid_random",
            "email": "user@gmail.com",
            "hd": "gmail.com",
        },
    }

    with patch("app.auth.oauth.oauth.google.authorize_access_token", new_callable=AsyncMock) as mock_auth, \
         patch.object(settings, "GOOGLE_ALLOWED_DOMAIN", "heritage.org"):
        mock_auth.return_value = mock_token

        response = client.get("/auth/callback?code=mock_code_3", follow_redirects=False)
        assert response.status_code == 403
        assert "restricted" in response.json()["detail"]


def test_auth_refresh_token_success(client: TestClient, db_session: Session) -> None:
    """Test /auth/refresh exchanges a valid refresh token for a new access token."""
    user = User(
        id=uuid.uuid4(),
        email="refresh_user@heritage.org",
        google_sub_id="sub_refresh_123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    refresh_token = create_refresh_token(user_id=user.id)

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_auth_refresh_with_access_token_fails(client: TestClient, db_session: Session) -> None:
    """Test /auth/refresh rejects an access token passed as a refresh token."""
    user = User(
        id=uuid.uuid4(),
        email="wrong_token@heritage.org",
        google_sub_id="sub_wrong_123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    access_token = create_access_token(user_id=user.id, email=user.email)

    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401
    assert "refresh token required" in response.json()["detail"].lower()


def test_auth_me_protected_route(client: TestClient, db_session: Session) -> None:
    """Test /auth/me returns current user info when valid Bearer token provided."""
    user = User(
        id=uuid.uuid4(),
        email="me_user@heritage.org",
        name="Conservation Specialist",
        google_sub_id="sub_me_123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(user_id=user.id, email=user.email)

    # 1. Without Authorization header -> 401
    res_no_auth = client.get("/auth/me", headers={"Authorization": ""})
    assert res_no_auth.status_code in (401, 403)

    # 2. With valid Authorization header -> 200
    res_auth = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    profile = res_auth.json()
    assert profile["email"] == "me_user@heritage.org"
    assert profile["name"] == "Conservation Specialist"


def test_auth_logout(client: TestClient) -> None:
    """Test /auth/logout endpoint returns success."""
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
