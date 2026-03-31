import os

from server.app import create_app


def test_dev_config_returns_safe_runtime_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PORT", "9090")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("FEATURE_BETA_DASHBOARD", "true")
    monkeypatch.setenv("FEATURE_METRICS_ENABLED", "false")
    monkeypatch.setenv("DB_NAME", "geo")
    monkeypatch.setenv("CLOUD_MONGO", "1")
    monkeypatch.setenv("GIT_SHA", "abc123")
    monkeypatch.setenv("JWT_SECRET", "super-secret")
    monkeypatch.setenv("LOCAL_MONGO_DB_URI", "mongodb://user:pass@localhost:27017/")
    monkeypatch.setenv(
        "ATLAS_MONGO_DB_URI", "mongodb+srv://user:pass@example.mongodb.net/"
    )

    app = create_app()
    with app.test_client() as client:
        response = client.get("/dev/config")

    payload = response.get_json()
    response_text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert payload == {
        "app_name": "Geographic Database API",
        "environment": "production",
        "version": "v1",
        "port": 9090,
        "log_level": "DEBUG",
        "feature_flags": {
            "beta_dashboard": True,
            "metrics_enabled": False,
        },
        "database": {
            "name": "geo",
            "mode": "cloud",
        },
        "cache_enabled": True,
        "build": {
            "commit_sha": "abc123",
        },
    }
    assert "super-secret" not in response_text
    assert "mongodb://user:pass@localhost:27017/" not in response_text
    assert "mongodb+srv://user:pass@example.mongodb.net/" not in response_text
    assert "JWT_SECRET" not in response_text


def test_dev_config_omits_optional_build_metadata_when_absent(monkeypatch):
    for key in [
        "APP_ENV",
        "PORT",
        "LOG_LEVEL",
        "DB_NAME",
        "CLOUD_MONGO",
        "FEATURE_BETA_DASHBOARD",
        "FEATURE_METRICS_ENABLED",
        "GIT_SHA",
        "BUILD_ID",
        "RELEASE_ID",
        "DEPLOY_ID",
    ]:
        monkeypatch.delenv(key, raising=False)

    app = create_app()
    with app.test_client() as client:
        response = client.get("/dev/config")

    payload = response.get_json()

    assert response.status_code == 200
    assert payload["version"] == "v1"
    assert payload["environment"] == "development"
    assert payload["port"] == 8000
    assert payload["feature_flags"] == {}
    assert payload["database"] == {
        "name": "seDB",
        "mode": "local",
    }
    assert "build" not in payload
