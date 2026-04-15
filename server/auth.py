"""Lightweight auth helpers for future RBAC/JWT integration."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

ROLE_ADMIN = "admin"
ROLE_USER = "user"
ALLOWED_ROLES = {ROLE_ADMIN, ROLE_USER}


def _jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-jwt-secret")


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def create_access_token(
    user_id: str,
    role: str,
    expires_hours: int = 24,
) -> str:
    """Create a JWT access token with basic role claims."""
    if role not in ALLOWED_ROLES:
        raise ValueError(f"Unsupported role: {role}")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=max(expires_hours, 1)),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    return jwt.decode(token, _jwt_secret(), algorithms=[_jwt_algorithm()])


def extract_bearer_token(auth_header: str | None) -> str | None:
    """Extract bearer token from an Authorization header string."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    return token or None


def authenticate_request(
    auth_header: str | None,
    required_role: str | None = None,
) -> dict[str, Any]:
    """Validate a bearer token header and optionally enforce a role."""
    token = extract_bearer_token(auth_header)
    if token is None:
        raise PermissionError("Missing or invalid bearer token")

    payload = decode_access_token(token)
    if required_role and payload.get("role") != required_role:
        raise PermissionError(f"Role '{required_role}' is required")

    return payload
