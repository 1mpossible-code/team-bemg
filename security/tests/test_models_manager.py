from security.manager import get_protocol, is_permitted, load_legacy_records
from security.models import ActionChecks, SecProtocol
from server.auth import ROLE_ADMIN, ROLE_USER, create_access_token


def test_action_checks_enforces_login_users_and_roles():
    checks = ActionChecks(login=True, valid_users=["alice"], allowed_roles=[ROLE_ADMIN])

    assert checks.is_permitted("alice", {"role": ROLE_ADMIN})
    assert not checks.is_permitted("", {"role": ROLE_ADMIN})
    assert not checks.is_permitted("bob", {"role": ROLE_ADMIN})
    assert not checks.is_permitted("alice", {"role": ROLE_USER})


def test_protocol_round_trip_from_legacy_records():
    records = {
        "countries": {
            "update": {
                "user_list": ["alice"],
                "checks": {
                    "login": True,
                    "allowed_roles": [ROLE_ADMIN],
                },
            },
        },
    }

    load_legacy_records(records)
    protocol = get_protocol("countries")

    assert protocol is not None
    assert protocol.name == "countries"
    assert protocol.update.login is True
    assert protocol.update.valid_users == ["alice"]
    assert protocol.update.allowed_roles == [ROLE_ADMIN]


def test_manager_is_permitted_uses_jwt_payload_when_no_user_id_is_passed():
    records = {
        "countries": {
            "update": {
                "user_list": ["alice"],
                "checks": {
                    "login": True,
                    "allowed_roles": [ROLE_ADMIN],
                },
            },
        },
    }
    load_legacy_records(records)
    token = create_access_token("alice", ROLE_ADMIN, expires_hours=1)

    assert is_permitted("countries", "update", auth_header=f"Bearer {token}")
    assert not is_permitted("countries", "update")


def test_unknown_protocol_is_open_by_default():
    load_legacy_records({})
    assert is_permitted("missing", "read")


def test_duplicate_protocol_add_is_rejected():
    protocol = SecProtocol("people")
    load_legacy_records({})
    from security.manager import add_protocol

    add_protocol(protocol)
    try:
        add_protocol(protocol)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Duplicate protocol" in str(exc)
