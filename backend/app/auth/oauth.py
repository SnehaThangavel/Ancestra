"""Authlib OAuth client registry configured for Google OAuth 2.0."""

from authlib.integrations.starlette_client import OAuth
from app.config import settings

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID or "",
    client_secret=settings.GOOGLE_CLIENT_SECRET or "",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
    },
)
