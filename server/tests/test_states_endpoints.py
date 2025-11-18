"""
Tests for states API endpoints.
"""
import json
from http import HTTPStatus
from unittest.mock import patch

import pytest
from server.app import create_app
import data.states as states_data


class TestStatesEndpoints:
    """Test class for states API endpoints."""

    @pytest.fixture
    def client(self):
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def sample_state(self):
        return {
            'state_name': 'New York',
            'state_code': 'NY',
            'country_code': 'US',
            'capital': 'Albany',
            'population': 20000000,
            'area_km2': 141297.0,
        }

    def test_get_all_states_success(self, client):
        with patch('data.states.get_states') as mock_get:
            mock_get.return_value = [states_data.TEST_STATE]

            resp = client.get('/states')

            assert resp.status_code == HTTPStatus.OK
            data = json.loads(resp.data)
            assert isinstance(data, list)
            assert data[0]['state_code'] == states_data.TEST_STATE['state_code']
            mock_get.assert_called_once()

    def test_get_states_by_country_success(self, client):
        """GET /states/country/<code> returns filtered list."""
        with patch('data.states.get_states_by_country') as mock_get:
            mock_get.return_value = [states_data.TEST_STATE]

            resp = client.get('/states/country/US')

            assert resp.status_code == HTTPStatus.OK
            data = resp.get_json()
            assert isinstance(data, list)
            assert data[0]['country_code'] == 'US'
            mock_get.assert_called_once_with('US')

    def test_get_states_by_country_db_error(self, client):
        """GET /states/country/<code> handles DB errors with 500."""
        with patch('data.states.get_states_by_country') as mock_get:
            mock_get.side_effect = Exception('DB fail')

            resp = client.get('/states/country/US')

            assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            data = resp.get_json()
            # message may vary; ensure we echoed error context
            assert 'error' in data.get('message', '').lower() or 'db fail' in str(data)

    def test_create_state_success(self, client, sample_state):
        with patch('data.countries.get_country_by_code') as mock_get_country, \
             patch('data.states.add_state') as mock_add:
            mock_get_country.return_value = {'country_code': 'US'}
            mock_add.return_value = True

            resp = client.post('/states', data=json.dumps(sample_state),
                               content_type='application/json')

            assert resp.status_code == HTTPStatus.CREATED
            payload = resp.get_json()
            assert payload['state_code'] == sample_state['state_code']
            mock_add.assert_called_once()

    def test_create_state_missing_country(self, client, sample_state):
        sample = {k: v for k, v in sample_state.items() if k != 'country_code'}

        resp = client.post('/states', data=json.dumps(sample),
                           content_type='application/json')

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    def test_get_state_by_code_success(self, client):
        with patch('data.states.get_state_by_code') as mock_get:
            mock_get.return_value = states_data.TEST_STATE

            resp = client.get('/states/NY')

            assert resp.status_code == HTTPStatus.OK
            data = resp.get_json()
            assert data['state_code'] == 'NY'
            mock_get.assert_called_once_with('NY')

    def test_get_state_by_code_not_found(self, client):
        with patch('data.states.get_state_by_code') as mock_get:
            mock_get.return_value = None

            resp = client.get('/states/ZZ')

            assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_update_state_success(self, client):
        update_data = {'population': 21000000}
        updated = {**states_data.TEST_STATE, **update_data}

        with patch('data.countries.get_country_by_code') as mock_country, \
             patch('data.states.update_state') as mock_update, \
             patch('data.states.get_state_by_code') as mock_get:
            mock_country.return_value = {'country_code': 'US'}
            mock_update.return_value = True
            mock_get.return_value = updated

            resp = client.put('/states/NY', data=json.dumps(update_data),
                              content_type='application/json')

            assert resp.status_code == HTTPStatus.OK
            data = resp.get_json()
            assert data['population'] == 21000000
            mock_update.assert_called_once_with('NY', update_data)

    def test_update_state_not_found(self, client):
        with patch('data.states.update_state') as mock_update:
            mock_update.return_value = False

            resp = client.put('/states/ZZ', data=json.dumps({'capital': 'X'}),
                              content_type='application/json')

            assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_delete_state_success(self, client):
        with patch('data.states.delete_state') as mock_delete:
            mock_delete.return_value = True

            resp = client.delete('/states/NY')

            assert resp.status_code == HTTPStatus.NO_CONTENT
            mock_delete.assert_called_once_with('NY')

    def test_delete_state_not_found(self, client):
        with patch('data.states.delete_state') as mock_delete:
            mock_delete.return_value = False

            resp = client.delete('/states/ZZ')

            assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_delete_state_with_dependent_cities(self, client):
        with patch('data.states.delete_state') as mock_delete:
            mock_delete.side_effect = ValueError('Cannot delete: 2 city/cities depend on this state')

            resp = client.delete('/states/NY')

            assert resp.status_code == HTTPStatus.CONFLICT
            data = resp.get_json()
            assert 'depend' in data['message'].lower()

    def test_get_state_by_name_success(self, client):
        """Test successful retrieval of state by name."""
        with patch('data.states.get_state_by_name') as mock_get:
            mock_get.return_value = states_data.TEST_STATE

            resp = client.get('/states/name/New York')

            assert resp.status_code == HTTPStatus.OK
            data = resp.get_json()
            assert data['state_name'] == states_data.TEST_STATE['state_name']
            assert data['state_code'] == states_data.TEST_STATE['state_code']
            mock_get.assert_called_once_with('New York')

    def test_get_state_by_name_not_found(self, client):
        """Test 404 when state name doesn't exist."""
        with patch('data.states.get_state_by_name') as mock_get:
            mock_get.return_value = None

            resp = client.get('/states/name/NonExistentState')

            assert resp.status_code == HTTPStatus.NOT_FOUND
            data = resp.get_json()
            assert 'not found' in data['message'].lower()
            mock_get.assert_called_once_with('NonExistentState')

    def test_get_state_by_name_database_error(self, client):
        """Test 500 when database error occurs."""
        with patch('data.states.get_state_by_name') as mock_get:
            mock_get.side_effect = Exception('Database connection failed')

            resp = client.get('/states/name/New York')

            assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            data = resp.get_json()
            assert 'error' in data or 'Database' in data.get('message', '')

    def test_get_cities_in_state_success(self, client):
        """GET /states/{state_code}/cities returns cities in a state."""
        with patch('data.cities.get_cities_by_state') as mock_get:
            mock_get.return_value = [{'city_name': 'Albany', 'state_code': 'NY', 'country_code': 'US'}]

            resp = client.get('/states/NY/cities')

            assert resp.status_code == HTTPStatus.OK
            data = resp.get_json()
            assert isinstance(data, list)
            assert data[0]['state_code'] == 'NY'
            mock_get.assert_called_once_with('NY')

    def test_get_cities_in_state_db_error(self, client):
        """GET /states/{state_code}/cities returns 500 on DB error."""
        with patch('data.cities.get_cities_by_state') as mock_get:
            mock_get.side_effect = Exception('DB fail')

            resp = client.get('/states/NY/cities')

            assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
            data = resp.get_json()
            assert 'error' in data.get('message', '').lower() or 'db fail' in str(data)
