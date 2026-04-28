"""Tests for the security protocol enforcement on countries write actions."""
import json
from http import HTTPStatus
from unittest.mock import patch

import pytest

from server.app import create_app
from server.auth import ROLE_ADMIN, ROLE_USER, create_access_token


SAMPLE_COUNTRY = {
    "country_name": "Test Country",
    "country_code": "TC",
    "continent": "North America",
    "capital": "Test Capital",
    "population": 1000000,
    "area_km2": 50000.0,
}


@pytest.fixture
def enforced_client(monkeypatch):
    monkeypatch.setenv("SECURITY_ENFORCEMENT", "true")
    monkeypatch.delenv("SECURITY_AUDIT_ONLY", raising=False)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _bearer(role: str, user_id: str = "alice") -> dict:
    token = create_access_token(user_id, role, expires_hours=1)
    return {"Authorization": f"Bearer {token}"}


def test_post_country_without_token_is_forbidden(enforced_client):
    response = enforced_client.post(
        "/countries",
        data=json.dumps(SAMPLE_COUNTRY),
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_post_country_with_user_role_is_forbidden(enforced_client):
    response = enforced_client.post(
        "/countries",
        data=json.dumps(SAMPLE_COUNTRY),
        content_type="application/json",
        headers=_bearer(ROLE_USER),
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_post_country_with_admin_role_is_allowed(enforced_client):
    with patch("data.countries.add_country") as mock_add:
        mock_add.return_value = True
        response = enforced_client.post(
            "/countries",
            data=json.dumps(SAMPLE_COUNTRY),
            content_type="application/json",
            headers=_bearer(ROLE_ADMIN),
        )
    assert response.status_code == HTTPStatus.CREATED


def test_put_country_without_token_is_forbidden(enforced_client):
    response = enforced_client.put(
        "/countries/US",
        data=json.dumps({"population": 350000000}),
        content_type="application/json",
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_put_country_with_admin_role_is_allowed(enforced_client):
    with patch("data.countries.update_country") as mock_update, \
            patch("data.countries.get_country_by_code") as mock_get:
        mock_update.return_value = True
        mock_get.return_value = SAMPLE_COUNTRY
        response = enforced_client.put(
            "/countries/TC",
            data=json.dumps({"population": 2000000}),
            content_type="application/json",
            headers=_bearer(ROLE_ADMIN),
        )
    assert response.status_code == HTTPStatus.OK


def test_delete_country_without_token_is_forbidden(enforced_client):
    response = enforced_client.delete("/countries/US")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_delete_country_with_admin_role_is_allowed(enforced_client):
    with patch("data.countries.delete_country") as mock_delete:
        mock_delete.return_value = True
        response = enforced_client.delete(
            "/countries/TC",
            headers=_bearer(ROLE_ADMIN),
        )
    assert response.status_code == HTTPStatus.NO_CONTENT


def test_get_countries_remains_open_under_enforcement(enforced_client):
    with patch("data.countries.get_countries_filtered") as mock_get:
        mock_get.return_value = []
        response = enforced_client.get("/countries")
    assert response.status_code == HTTPStatus.OK
