"""
Tests for cities API endpoints.
"""
import json
from http import HTTPStatus
from unittest.mock import patch

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

    def test_get_all_cities_success(self, client):
        """GET /cities should return 200 and a list of cities."""
        with patch('data.cities.get_cities') as mock_get:
            mock_get.return_value = [cities_data.TEST_CITY]

            resp = client.get('/cities')

            assert resp.status_code == HTTPStatus.OK
            data = json.loads(resp.data)
            assert isinstance(data, list)
            assert data[0]['name'] == cities_data.TEST_CITY['name']
            mock_get.assert_called_once()

    def test_create_city_success(self, client):
        """POST /cities should create a city when parent state matches country."""
        sample_city = {
            'name': 'Gotham',
            'state_code': 'NY',
            'country_code': 'US',
            'population': 1000000,
            'area_km2': 300.0,
            'coordinates': {'lat': 40.7, 'lon': -73.9},
        }

        with patch('data.states.get_state_by_code') as mock_get_state, \
             patch('data.cities.add_city') as mock_add:
            mock_get_state.return_value = {'country_code': 'US'}
            mock_add.return_value = True

            resp = client.post(
                '/cities',
                data=json.dumps(sample_city),
                content_type='application/json'
            )

            assert resp.status_code == HTTPStatus.CREATED
            payload = resp.get_json()
            assert payload['name'] == sample_city['name']
            mock_add.assert_called_once()

    def test_create_city_parent_mismatch(self, client):
        """POST /cities should return 400 if state belongs to a different country."""
        sample_city = {
            'name': 'Metropolis',
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
