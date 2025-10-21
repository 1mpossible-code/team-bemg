import pytest
from unittest.mock import MagicMock, patch

from server.app import create_app


def test_health():
    app = create_app()
    with app.test_client() as c:
        r = c.get("/healthz")
        assert r.status_code == 200
        assert r.get_json() == {"status": "ok"}


def test_ready_ok():
    """readyz returns 200 when Mongo ping succeeds."""
    # Patch the DB client before creating the app so the closure captures it
    with patch("server.app.db_connect.connect_db") as mock_connect:
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1.0}
        mock_connect.return_value = mock_client

        app = create_app()
        with app.test_client() as c:
            r = c.get("/readyz")
            assert r.status_code == 200
            assert r.get_json() == {"status": "ok"}
            mock_client.admin.command.assert_called_once_with("ping")


def test_ready_db_failure():
    """readyz returns 500 and detail when Mongo ping raises."""
    with patch("server.app.db_connect.connect_db") as mock_connect:
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = Exception("DB down")
        mock_connect.return_value = mock_client

        app = create_app()
        with app.test_client() as c:
            r = c.get("/readyz")
            assert r.status_code == 500
            payload = r.get_json()
            assert payload["status"] == "error"
            assert "DB down" in payload["detail"]


@pytest.mark.skip(reason="Integration test – requires a running MongoDB instance")
def test_ready_integration_against_real_db():
    """Example integration test that would hit a real MongoDB if available."""
    app = create_app()
    with app.test_client() as c:
        r = c.get("/readyz")
        # If a real DB is up and reachable, this should be 200; otherwise 500.
        assert r.status_code in (200, 500)