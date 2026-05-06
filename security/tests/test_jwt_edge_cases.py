"""Edge-case JWT handling around the security manager's permission check."""

from datetime import datetime, timedelta, timezone

import jwt

from security.manager import is_permitted, load_legacy_records
from server.auth import (
    ROLE_ADMIN,
    _jwt_algorithm,
    _jwt_secret,
    create_access_token,
)


COUNTRIES_PROTOCOL = {
    "countries": {
        "create": {
            "checks": {
                "login": True,
                "allowed_roles": [ROLE_ADMIN],
            },
        },
    },
}


def _expired_admin_token() -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "alice",
        "role": ROLE_ADMIN,
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_algorithm())


def _wrong_secret_admin_token() -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "alice",
        "role": ROLE_ADMIN,
        "iat": now,
        "exp": now + timedelta(hours=1),
    }
    return jwt.encode(
        payload, "definitely-not-the-real-secret", algorithm=_jwt_algorithm()
    )


def test_malformed_bearer_token_is_denied():
    load_legacy_records(COUNTRIES_PROTOCOL)
    assert not is_permitted(
        "countries", "create", auth_header="Bearer not-a-jwt"
    )


def test_empty_bearer_token_is_denied():
    load_legacy_records(COUNTRIES_PROTOCOL)
    assert not is_permitted(
        "countries", "create", auth_header="Bearer "
    )


def test_non_bearer_authorization_scheme_is_denied():
    load_legacy_records(COUNTRIES_PROTOCOL)
    assert not is_permitted(
        "countries", "create", auth_header="Basic dXNlcjpwYXNz"
    )


def test_expired_admin_token_is_denied():
    load_legacy_records(COUNTRIES_PROTOCOL)
    assert not is_permitted(
        "countries",
        "create",
        auth_header=f"Bearer {_expired_admin_token()}",
    )


def test_token_signed_with_wrong_secret_is_denied():
    load_legacy_records(COUNTRIES_PROTOCOL)
    assert not is_permitted(
        "countries",
        "create",
        auth_header=f"Bearer {_wrong_secret_admin_token()}",
    )


def test_valid_admin_token_is_still_permitted():
    load_legacy_records(COUNTRIES_PROTOCOL)
    token = create_access_token("alice", ROLE_ADMIN, expires_hours=1)
    assert is_permitted(
        "countries",
        "create",
        auth_header=f"Bearer {token}",
    )
