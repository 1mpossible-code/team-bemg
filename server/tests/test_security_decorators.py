from flask import Flask

from security.decorators import require_protocol
from server.auth import ROLE_ADMIN, ROLE_USER, create_access_token


def _create_test_app():
    app = Flask(__name__)

    @app.get("/protected")
    @require_protocol("countries", "update")
    def protected():
        return {"ok": True}, 200

    return app


def test_security_decorator_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SECURITY_ENFORCEMENT", raising=False)
    app = _create_test_app()

    with app.test_client() as client:
        response = client.get("/protected")

    assert response.status_code == 200


def test_security_decorator_blocks_when_enforcement_enabled(monkeypatch):
    monkeypatch.setenv("SECURITY_ENFORCEMENT", "true")
    app = _create_test_app()

    from security.manager import load_legacy_records
    load_legacy_records({
        "countries": {
            "update": {
                "user_list": ["alice"],
                "checks": {
                    "login": True,
                    "allowed_roles": [ROLE_ADMIN],
                },
            },
        },
    })

    with app.test_client() as client:
        response = client.get("/protected")

    assert response.status_code == 403


def test_security_decorator_allows_authorized_request(monkeypatch):
    monkeypatch.setenv("SECURITY_ENFORCEMENT", "true")
    app = _create_test_app()

    from security.manager import load_legacy_records
    load_legacy_records({
        "countries": {
            "update": {
                "user_list": ["alice"],
                "checks": {
                    "login": True,
                    "allowed_roles": [ROLE_ADMIN],
                },
            },
        },
    })
    token = create_access_token("alice", ROLE_ADMIN, expires_hours=1)

    with app.test_client() as client:
        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_security_decorator_audit_only_does_not_block(monkeypatch):
    monkeypatch.setenv("SECURITY_ENFORCEMENT", "true")
    monkeypatch.setenv("SECURITY_AUDIT_ONLY", "true")
    app = _create_test_app()

    from security.manager import load_legacy_records
    load_legacy_records({
        "countries": {
            "update": {
                "user_list": ["alice"],
                "checks": {
                    "login": True,
                    "allowed_roles": [ROLE_ADMIN],
                },
            },
        },
    })
    token = create_access_token("alice", ROLE_USER, expires_hours=1)

    with app.test_client() as client:
        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
