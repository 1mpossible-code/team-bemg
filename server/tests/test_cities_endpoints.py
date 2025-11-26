"""
Tests for cities API endpoints.
"""
import json
from http import HTTPStatus
from unittest.mock import patch, MagicMock

import pytest
from server.app import create_app
import data.cities as cities_data


class TestCitiesEndpoints:
    """Test class for cities API endpoints."""

    @pytest.fixture
    def client(self):
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def sample_city(self):
        """Sample city data for testing."""
        return cities_data.TEST_CITY.copy()

    def test_get_all_cities_success(self, client):
        """GET /cities should return 200 and a list of cities."""
        with patch('data.cities.get_cities') as mock_get:
            mock_get.return_value = [cities_data.TEST_CITY]

            resp = client.get('/cities')

            assert resp.status_code == HTTPStatus.OK
            data = json.loads(resp.data)
            assert isinstance(data, list)
            assert data[0]['city_name'] == cities_data.TEST_CITY['city_name']
            mock_get.assert_called_once()

    def test_get_cities_with_pagination(self, client):
        """GET /cities supports limit/offset query params."""
        another_city = {**cities_data.TEST_CITY, 'city_name': 'Another'}
        with patch('data.cities.get_cities') as mock_get:
            mock_get.return_value = [cities_data.TEST_CITY, another_city]

            resp = client.get('/cities?limit=1&offset=1')

            assert resp.status_code == HTTPStatus.OK
            data = resp.get_json()
            assert len(data) == 1
            assert data[0]['city_name'] == 'Another'

    def test_get_cities_invalid_limit(self, client):
        resp = client.get('/cities?limit=-10')
        assert resp.status_code == HTTPStatus.BAD_REQUEST

    def test_create_city_success(self, client):
        """POST /cities should create a city when parent state matches country."""
        sample_city = {
            'city_name': 'Gotham',
            'state_code': 'NY',
            'country_code': 'US',
            'population': 1000000,
            'area_km2': 300.0,
            'coordinates': {'lat': 40.7, 'lon': -73.9},
        }

        # Mock the result of a successful add
        mock_add_result = MagicMock()
        mock_add_result.acknowledged = True

        with patch('data.states.get_state_by_code') as mock_get_state, \
                patch('data.cities.add_city') as mock_add:
            mock_get_state.return_value = {'country_code': 'US'}
            mock_add.return_value = mock_add_result

            resp = client.post(
                '/cities',
                data=json.dumps(sample_city),
                content_type='application/json'
            )

            assert resp.status_code == HTTPStatus.CREATED
            payload = resp.get_json()
            assert payload['city_name'] == sample_city['city_name']
            mock_add.assert_called_once()

    def test_create_city_parent_mismatch(self, client):
        """POST /cities should return 400 if state belongs to a different country."""
        sample_city = {
            'city_name': 'Metropolis',
            'state_code': 'NY',
            'country_code': 'CA',  # mismatch with mocked state
            'coordinates': {'lat': 40.7, 'lon': -73.9},
        }

        with patch('data.states.get_state_by_code') as mock_get_state:
            mock_get_state.return_value = {'country_code': 'US'}

            resp = client.post(
                '/cities',
                data=json.dumps(sample_city),
                content_type='application/json'
            )

            assert resp.status_code == HTTPStatus.BAD_REQUEST

    def test_get_city_by_name_and_state_success(self, client):
        """GET /cities/<state_code>/<city_name> should return 200."""

        # Use the TEST_CITY from the data layer
        city = cities_data.TEST_CITY
        state_code = city['state_code']
        city_name = city['city_name']

        with patch('data.cities.get_city_by_name_and_state') as mock_get:
            mock_get.return_value = city

            resp = client.get(f'/cities/{state_code}/{city_name}')

            assert resp.status_code == HTTPStatus.OK
            data = json.loads(resp.data)
            assert data['city_name'] == city_name
            assert 'created_at' in data and 'updated_at' in data
            mock_get.assert_called_once_with(city_name, state_code)

    def test_get_city_by_name_and_state_not_found(self, client):
        """GET /cities/<state_code>/<city_name> should return 404."""
        with patch('data.cities.get_city_by_name_and_state') as mock_get:
            mock_get.return_value = None

            resp = client.get('/cities/XX/FakeCity')

            assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_get_cities_filter_by_name(self, client, sample_city):
        """Test GET /cities?name=New"""
        with patch('data.cities.get_cities_by_name') as mock_get:
            mock_get.return_value = [sample_city]

            # Search for "New" (should match "New York")
            response = client.get('/cities?name=New')

            assert response.status_code == HTTPStatus.OK
            mock_get.assert_called_with('New')

    def test_get_cities_filter_by_state(self, client, sample_city):
        """Test GET /cities?state_code=NY"""
        with patch('data.cities.get_cities_by_state') as mock_get:
            mock_get.return_value = [sample_city]
            response = client.get('/cities?state_code=NY')
            assert response.status_code == HTTPStatus.OK
            mock_get.assert_called_with('NY')

    def test_get_cities_filter_by_population(self, client, sample_city):
        """Test GET /cities?min_population=1000"""
        with patch('data.cities.get_cities_by_population_range') as mock_get:
            mock_get.return_value = [sample_city]
            response = client.get('/cities?min_population=1000')
            assert response.status_code == HTTPStatus.OK
            mock_get.assert_called_with(1000, None)

    def test_get_cities_filter_by_country_normalizes_uppercase(self, client, sample_city):
        """GET /cities?country_code=us should uppercase to 'US' in data call."""
        with patch('data.cities.get_cities_by_country') as mock_get:
            mock_get.return_value = [sample_city]
            resp = client.get('/cities?country_code=us')
            assert resp.status_code == HTTPStatus.OK
            mock_get.assert_called_once_with('US')

    def test_get_cities_filter_by_country_db_error(self, client):
        """GET /cities?country_code=US returns 500 on DB error."""
        with patch('data.cities.get_cities_by_country', side_effect=Exception('boom')):
            resp = client.get('/cities?country_code=US')
            assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_get_cities_by_country_endpoint_success(self, client, sample_city):
        """GET /cities/country/US returns 200 and calls data function."""
        with patch('data.cities.get_cities_by_country') as mock_get:
            mock_get.return_value = [sample_city]
            resp = client.get('/cities/country/US')
            assert resp.status_code == HTTPStatus.OK
            payload = resp.get_json()
            assert isinstance(payload, list)
            if payload:
                assert 'created_at' in payload[0] and 'updated_at' in payload[0]
            mock_get.assert_called_once_with('US')

    def test_get_cities_by_country_endpoint_db_error(self, client):
        """GET /cities/country/US returns 500 on DB error."""
        with patch('data.cities.get_cities_by_country', side_effect=Exception('db error')):
            resp = client.get('/cities/country/US')
            assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_get_cities_by_state_endpoint_success(self, client, sample_city):
        """GET /cities/state/NY returns 200 and calls data function."""
        with patch('data.cities.get_cities_by_state') as mock_get:
            mock_get.return_value = [sample_city]
            resp = client.get('/cities/state/NY')
            assert resp.status_code == HTTPStatus.OK
            mock_get.assert_called_once_with('NY')

    def test_get_cities_by_state_endpoint_db_error(self, client):
        """GET /cities/state/NY returns 500 on DB error."""
        with patch('data.cities.get_cities_by_state', side_effect=Exception('db error')):
            resp = client.get('/cities/state/NY')
            assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    def test_update_city_success(self, client):
        """PUT /cities/<state_code>/<city_name> should return 200."""
        city = cities_data.TEST_CITY
        state_code = city['state_code']
        city_name = city['city_name']

        update_data = {'population': 5000}
        updated_city_doc = {**city, **update_data}

        with patch('data.cities.update_city') as mock_update, \
                patch('data.cities.get_city_by_name_and_state') as mock_get:

            mock_update.return_value = True
            mock_get.return_value = updated_city_doc

            resp = client.put(
                f'/cities/{state_code}/{city_name}',
                data=json.dumps(update_data),
                content_type='application/json'
            )

            assert resp.status_code == HTTPStatus.OK
            data = json.loads(resp.data)
            assert data['population'] == 5000
            assert 'updated_at' in data
            mock_update.assert_called_once_with(
                city_name, state_code, update_data
            )

    def test_delete_city_success(self, client):
        """DELETE /cities/<state_code>/<city_name> should return 204."""
        city = cities_data.TEST_CITY
        state_code = city['state_code']
        city_name = city['city_name']

        with patch('data.cities.delete_city') as mock_delete:
            mock_delete.return_value = True

            resp = client.delete(f'/cities/{state_code}/{city_name}')

            assert resp.status_code == HTTPStatus.NO_CONTENT
            mock_delete.assert_called_once_with(city_name, state_code)

    def test_delete_city_not_found(self, client):
        """DELETE /cities/<state_code>/<city_name> should return 404."""
        with patch('data.cities.delete_city') as mock_delete:
            mock_delete.return_value = False

            resp = client.delete('/cities/XX/FakeCity')

            assert resp.status_code == HTTPStatus.NOT_FOUND
