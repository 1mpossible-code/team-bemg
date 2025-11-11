"""
Tests for countries API endpoints.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from http import HTTPStatus
from server.app import create_app
from data import countries
import data.states as states

class TestCountriesEndpoints:
    """Test class for countries API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def sample_country(self):
        """Sample country data for testing."""
        return {
            'country_name': 'Test Country',
            'country_code': 'TC',
            'continent': 'North America',
            'capital': 'Test Capital',
            'population': 1000000,
            'area_km2': 50000.0
        }

    def test_get_states_in_country(self, client):
        """Test successful retrieval of states in a country."""
        # Arrange
        with patch('data.countries.get_country_by_code') as mock_get_country, \
             patch('data.states.get_states_by_country') as mock_get:
            mock_get_country.return_value = countries.TEST_COUNTRY
            mock_get.return_value = [states.TEST_STATE]

            # Act 
            response = client.get(f'/countries/{countries.TEST_COUNTRY[countries.COUNTRY_CODE]}/states')

            # Assert 
            assert response.status_code == HTTPStatus.OK
            data = json.loads(response.data)
            assert data == [states.TEST_STATE]
            mock_get_country.assert_called_once_with(countries.TEST_COUNTRY[countries.COUNTRY_CODE])
            mock_get.assert_called_once_with(countries.TEST_COUNTRY[countries.COUNTRY_CODE])

    def test_get_all_countries_success(self, client):
        """Test successful retrieval of all countries."""
        with patch('data.countries.get_countries') as mock_get:
            mock_get.return_value = [countries.TEST_COUNTRY]
            
            response = client.get('/countries')
            
            assert response.status_code == HTTPStatus.OK
            data = json.loads(response.data)
            assert isinstance(data, list)
            mock_get.assert_called_once()

    def test_get_all_countries_database_error(self, client):
        """Test database error when retrieving countries."""
        with patch('data.countries.get_countries') as mock_get:
            mock_get.side_effect = Exception("Database connection failed")
            
            response = client.get('/countries')
            
            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_create_country_success(self, client, sample_country):
        """Test successful country creation."""
        with patch('data.countries.add_country') as mock_add:
            mock_add.return_value = True
            
            response = client.post('/countries', 
                                 data=json.dumps(sample_country),
                                 content_type='application/json')
            
            assert response.status_code == HTTPStatus.CREATED
            data = json.loads(response.data)
            assert data['country_name'] == sample_country['country_name']
            mock_add.assert_called_once_with(sample_country)

    def test_create_country_invalid_continent(self, client, sample_country):
        """Test country creation with invalid continent."""
        sample_country['continent'] = 'Invalid Continent'
        
        response = client.post('/countries', 
                             data=json.dumps(sample_country),
                             content_type='application/json')
        
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_create_country_already_exists(self, client, sample_country):
        """Test creating a country that already exists."""
        with patch('data.countries.add_country') as mock_add:
            mock_add.side_effect = ValueError("Country with code TC already exists")
            
            response = client.post('/countries', 
                                 data=json.dumps(sample_country),
                                 content_type='application/json')
            
            assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_country_by_code_success(self, client):
        """Test successful retrieval of country by code."""
        with patch('data.countries.get_country_by_code') as mock_get:
            mock_get.return_value = countries.TEST_COUNTRY
            
            response = client.get('/countries/US')
            
            assert response.status_code == HTTPStatus.OK
            data = json.loads(response.data)
            assert data['country_code'] == 'US'
            mock_get.assert_called_once_with('US')

    def test_get_country_by_code_not_found(self, client):
        """Test retrieval of non-existent country."""
        with patch('data.countries.get_country_by_code') as mock_get:
            mock_get.return_value = None
            
            response = client.get('/countries/XX')
            
            assert response.status_code == HTTPStatus.NOT_FOUND

    def test_update_country_success(self, client):
        """Test successful country update."""
        update_data = {'population': 350000000}
        updated_country = {**countries.TEST_COUNTRY, **update_data}
        
        with patch('data.countries.update_country') as mock_update, \
             patch('data.countries.get_country_by_code') as mock_get:
            mock_update.return_value = True
            mock_get.return_value = updated_country
            
            response = client.put('/countries/US', 
                                data=json.dumps(update_data),
                                content_type='application/json')
            
            assert response.status_code == HTTPStatus.OK
            data = json.loads(response.data)
            assert data['population'] == 350000000
            mock_update.assert_called_once_with('US', update_data)

    def test_update_country_not_found(self, client):
        """Test updating non-existent country."""
        with patch('data.countries.update_country') as mock_update:
            mock_update.return_value = False
            
            response = client.put('/countries/XX', 
                                data=json.dumps({'population': 1000}),
                                content_type='application/json')
            
            assert response.status_code == HTTPStatus.NOT_FOUND

    def test_update_country_invalid_continent(self, client):
        """Test updating country with invalid continent."""
        update_data = {'continent': 'Invalid Continent'}
        
        response = client.put('/countries/US', 
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_delete_country_success(self, client):
        """Test successful country deletion."""
        with patch('data.countries.delete_country') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete('/countries/US')
            
            assert response.status_code == HTTPStatus.NO_CONTENT
            mock_delete.assert_called_once_with('US')

    def test_delete_country_not_found(self, client):
        """Test deleting non-existent country."""
        with patch('data.countries.delete_country') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete('/countries/XX')
            
            assert response.status_code == HTTPStatus.NOT_FOUND

    def test_delete_country_with_dependent_states(self, client):
        """Test DELETE /countries/{code} returns 409 when states exist."""
        with patch('data.countries.delete_country') as mock_delete:
            mock_delete.side_effect = ValueError("Cannot delete: 5 state(s) depend on this country")
            
            response = client.delete('/countries/US')
            
            assert response.status_code == HTTPStatus.CONFLICT
            data = json.loads(response.data)
            assert '5 state' in data['message'].lower()

    def test_get_countries_by_continent_success(self, client):
        """Test successful retrieval of countries by continent."""
        with patch('data.countries.get_countries_by_continent') as mock_get:
            mock_get.return_value = [countries.TEST_COUNTRY]
            
            response = client.get('/countries/continent/North America')
            
            assert response.status_code == HTTPStatus.OK
            data = json.loads(response.data)
            assert isinstance(data, list)
            mock_get.assert_called_once_with('North America')

    def test_get_countries_by_continent_invalid(self, client):
        """Test retrieval with invalid continent."""
        response = client.get('/countries/continent/Invalid Continent')
        
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_case_insensitive_country_code(self, client):
        """Test that country codes are handled case-insensitively."""
        with patch('data.countries.get_country_by_code') as mock_get:
            mock_get.return_value = countries.TEST_COUNTRY
            
            response = client.get('/countries/us')  # lowercase
            
            assert response.status_code == HTTPStatus.OK
            mock_get.assert_called_once_with('US')  # should be converted to uppercase

    def test_create_country_database_error(self, client, sample_country):
        """POST /countries returns 500 when DB insert raises."""
        with patch('data.countries.add_country') as mock_add:
            mock_add.side_effect = Exception('DB write failed')

            response = client.post(
                '/countries',
                data=json.dumps(sample_country),
                content_type='application/json'
            )

            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_create_country_malformed_json(self, client):
        """POST /countries with invalid JSON should yield 400."""
        bad_json = '{"name": "X", "code": "TC",}'  # trailing comma invalid

        response = client.post(
            '/countries',
            data=bad_json,
            content_type='application/json'
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST