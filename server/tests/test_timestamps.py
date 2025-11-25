"""
Tests focused on timestamp behavior for API and data layer.
"""
import json
from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import patch

import pytest
from server.app import create_app
import data.countries as countries_data
from data import countries as countries_module


def _parse_iso_maybe_z(s: str) -> datetime:
    """Parse ISO string including trailing Z into a timezone-aware datetime via fromisoformat."""
    if not isinstance(s, str):
        # Already a datetime or other; return as-is for tests
        return s
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    return datetime.fromisoformat(s)


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_country_timestamps_are_iso8601(client):
    """GET /countries/<code> should return created_at/updated_at parseable as ISO datetimes."""
    now = datetime.utcnow()
    mocked_country = dict(countries_data.TEST_COUNTRY)
    mocked_country['created_at'] = now
    mocked_country['updated_at'] = now

    with patch('data.countries.get_country_by_code') as mock_get:
        mock_get.return_value = mocked_country

        resp = client.get('/countries/US')
        assert resp.status_code == HTTPStatus.OK
        data = resp.get_json()
        # Ensure strings parse into datetimes
        parsed_created = _parse_iso_maybe_z(data['created_at'])
        parsed_updated = _parse_iso_maybe_z(data['updated_at'])
        assert isinstance(parsed_created, datetime)
        assert isinstance(parsed_updated, datetime)


def test_update_changes_updated_at(client):
    """PUT /countries/<code> should return an object with a newer updated_at than before."""
    old_dt = datetime(2020, 1, 1, 0, 0, 0)
    new_dt = datetime.utcnow()

    initial_country = dict(countries_data.TEST_COUNTRY)
    initial_country['updated_at'] = old_dt

    updated_country = dict(countries_data.TEST_COUNTRY)
    updated_country['updated_at'] = new_dt

    # get_country_by_code will be called twice across two client requests (GET then PUT)
    with patch('data.countries.get_country_by_code') as mock_get, \
         patch('data.countries.update_country') as mock_update:
        mock_get.side_effect = [initial_country, updated_country]
        mock_update.return_value = True

        # First, confirm initial value via GET
        resp1 = client.get('/countries/US')
        assert resp1.status_code == HTTPStatus.OK
        v1 = _parse_iso_maybe_z(resp1.get_json()['updated_at'])

        # Now perform update
        resp2 = client.put('/countries/US', data=json.dumps({'population': 1}), content_type='application/json')
        assert resp2.status_code == HTTPStatus.OK
        v2 = _parse_iso_maybe_z(resp2.get_json()['updated_at'])

        assert v2 > v1


def test_add_country_overwrites_client_timestamps(monkeypatch):
    """data.countries.add_country should overwrite client-supplied timestamp strings with datetimes.

    This unit-test patches the DB create function to capture the doc passed to the DB layer.
    """
    sample = dict(countries_data.TEST_COUNTRY)
    # Client (malicious or accidental) supplies timestamp strings
    sample['created_at'] = '1999-01-01T00:00:00Z'
    sample['updated_at'] = '1999-01-01T00:00:00Z'

    captured = {}

    def fake_create(collection, doc):
        captured['doc'] = doc
        class R:
            acknowledged = True
        return R()

    # Ensure uniqueness check doesn't fail
    with patch('data.countries.get_country_by_code') as mock_get:
        mock_get.return_value = None
        with patch('data.db_connect.create', side_effect=fake_create):
            ok = countries_module.add_country(sample)
            assert ok is True

    # Validate the captured document has datetime objects for timestamps
    assert 'doc' in captured
    doc = captured['doc']
    assert isinstance(doc.get('created_at'), datetime)
    assert isinstance(doc.get('updated_at'), datetime)
    # And ensure they are not the client-supplied string
    assert doc['created_at'] != '1999-01-01T00:00:00Z'
