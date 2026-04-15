from jwt import InvalidTokenError

from server.auth import (
    ROLE_ADMIN,
    ROLE_USER,
    authenticate_request,
    create_access_token,
    decode_access_token,
    extract_bearer_token,
)


def test_create_and_decode_access_token_round_trip():
    token = create_access_token("alice", ROLE_ADMIN, expires_hours=1)

    payload = decode_access_token(token)

    assert payload["sub"] == "alice"
    assert payload["role"] == ROLE_ADMIN


def test_create_access_token_rejects_unknown_role():
    try:
        create_access_token("alice", "superadmin")
        assert False, "Expected ValueError for unsupported role"
    except ValueError as exc:
        assert "Unsupported role" in str(exc)


def test_decode_access_token_rejects_invalid_token():
    try:
        decode_access_token("not-a-token")
        assert False, "Expected InvalidTokenError"
    except InvalidTokenError:
        assert True


def test_extract_bearer_token_valid_header():
    token = extract_bearer_token("Bearer abc.def.ghi")
    assert token == "abc.def.ghi"


def test_extract_bearer_token_invalid_header():
    assert extract_bearer_token(None) is None
    assert extract_bearer_token("") is None
    assert extract_bearer_token("Basic xyz") is None
    assert extract_bearer_token("Bearer   ") is None


def test_user_role_token_supported():
    token = create_access_token("bob", ROLE_USER, expires_hours=1)
    payload = decode_access_token(token)
    assert payload["role"] == ROLE_USER


def test_authenticate_request_accepts_valid_bearer_token():
    token = create_access_token("alice", ROLE_ADMIN, expires_hours=1)

    payload = authenticate_request(f"Bearer {token}")

    assert payload["sub"] == "alice"
    assert payload["role"] == ROLE_ADMIN


def test_authenticate_request_rejects_missing_bearer_token():
    try:
        authenticate_request(None)
        assert False, "Expected PermissionError"
    except PermissionError as exc:
        assert "Missing or invalid bearer token" in str(exc)


def test_authenticate_request_enforces_required_role():
    token = create_access_token("bob", ROLE_USER, expires_hours=1)

    try:
        authenticate_request(f"Bearer {token}", required_role=ROLE_ADMIN)
        assert False, "Expected PermissionError"
    except PermissionError as exc:
        assert "Role 'admin' is required" in str(exc)


def test_authenticate_request_rejects_invalid_bearer_token():
    try:
        authenticate_request("Bearer not-a-token")
        assert False, "Expected PermissionError"
    except PermissionError as exc:
        assert "Invalid or expired bearer token" in str(exc)
