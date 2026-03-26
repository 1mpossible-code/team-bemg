"""
Tests for continents API endpoints.
"""
import json
import pytest
from unittest.mock import patch
from http import HTTPStatus
from server.app import create_app
from data import continents


class TestContinentsEndpoints:
    """Test class for continents API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def sample_continent(self):
        return {'continent_name': 'Asia'}

    # --- GET /continents ---

    def test_get_all_continents_success(self, client):
        """GET /continents returns list of all continents."""
        with patch('data.continents.get_continents') as mock_get:
            mock_get.return_value = [continents.TEST_CONTINENT]
            response = client.get('/continents')
            assert response.status_code == HTTPStatus.OK
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 1
            mock_get.assert_called_once()

    def test_get_all_continents_with_pagination(self, client):
        """GET /continents supports limit and offset query parameters."""
        two_continents = [
            {'continent_name': 'Africa'},
            {'continent_name': 'Asia'},
        ]
        with patch('data.continents.get_continents') as mock_get:
            mock_get.return_value = two_continents
            response = client.get('/continents?limit=1&offset=1')
            assert response.status_code == HTTPStatus.OK
            data = response.get_json()
            assert len(data) == 1
            assert data[0]['continent_name'] == 'Asia'

    def test_get_all_continents_invalid_limit(self, client):
        """GET /continents?limit=-1 returns 400."""
        response = client.get('/continents?limit=-1')
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_get_all_continents_db_error(self, client):
        """GET /continents returns 500 on database error."""
        with patch('data.continents.get_continents') as mock_get:
            mock_get.side_effect = Exception('DB connection failed')
            response = client.get('/continents')
            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    # --- POST /continents ---

    def test_create_continent_success(self, client, sample_continent):
        """POST /continents creates a new continent and returns 201."""
        with patch('data.continents.add_continent') as mock_add:
            mock_add.return_value = True
            response = client.post(
                '/continents',
                data=json.dumps(sample_continent),
                content_type='application/json'
            )
            assert response.status_code == HTTPStatus.CREATED
            data = response.get_json()
            assert data['continent_name'] == 'Asia'
            mock_add.assert_called_once_with(sample_continent)

    def test_create_continent_invalid_name(self, client):
        """POST /continents with invalid continent_name returns 400."""
        response = client.post(
            '/continents',
            data=json.dumps({'continent_name': 'Atlantis'}),
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_create_continent_already_exists(self, client, sample_continent):
        """POST /continents with duplicate name returns 409."""
        with patch('data.continents.add_continent') as mock_add:
            mock_add.side_effect = ValueError("Continent 'Asia' already exists")
            response = client.post(
                '/continents',
                data=json.dumps(sample_continent),
                content_type='application/json'
            )
            assert response.status_code == HTTPStatus.CONFLICT

    def test_create_continent_db_error(self, client, sample_continent):
        """POST /continents returns 500 on unexpected database error."""
        with patch('data.continents.add_continent') as mock_add:
            mock_add.side_effect = Exception('DB write failed')
            response = client.post(
                '/continents',
                data=json.dumps(sample_continent),
                content_type='application/json'
            )
            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    # --- GET /continents/<name> ---

    def test_get_continent_success(self, client):
        """GET /continents/<name> returns the continent."""
        with patch('data.continents.get_continent_by_name') as mock_get:
            mock_get.return_value = continents.TEST_CONTINENT
            response = client.get('/continents/North America')
            assert response.status_code == HTTPStatus.OK
            data = response.get_json()
            assert data['continent_name'] == continents.TEST_CONTINENT['continent_name']

    def test_get_continent_not_found(self, client):
        """GET /continents/<name> returns 404 when not found."""
        with patch('data.continents.get_continent_by_name') as mock_get:
            mock_get.return_value = None
            response = client.get('/continents/Atlantis')
            assert response.status_code == HTTPStatus.NOT_FOUND

    def test_get_continent_db_error(self, client):
        """GET /continents/<name> returns 500 on database error."""
        with patch('data.continents.get_continent_by_name') as mock_get:
            mock_get.side_effect = Exception('DB error')
            response = client.get('/continents/Asia')
            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    # --- PUT /continents/<name> ---

    def test_update_continent_success(self, client):
        """PUT /continents/<name> returns 204 on success."""
        with patch('data.continents.update_continent') as mock_update:
            mock_update.return_value = True
            response = client.put('/continents/Asia')
            assert response.status_code == HTTPStatus.NO_CONTENT

    def test_update_continent_not_found(self, client):
        """PUT /continents/<name> returns 404 when continent does not exist."""
        with patch('data.continents.update_continent') as mock_update:
            mock_update.return_value = False
            response = client.put('/continents/Atlantis')
            assert response.status_code == HTTPStatus.NOT_FOUND

    def test_update_continent_db_error(self, client):
        """PUT /continents/<name> returns 500 on database error."""
        with patch('data.continents.update_continent') as mock_update:
            mock_update.side_effect = Exception('DB error')
            response = client.put('/continents/Asia')
            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    # --- DELETE /continents/<name> ---

    def test_delete_continent_success(self, client):
        """DELETE /continents/<name> returns 204 on success."""
        with patch('data.continents.delete_continent') as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/continents/Antarctica')
            assert response.status_code == HTTPStatus.NO_CONTENT

    def test_delete_continent_not_found(self, client):
        """DELETE /continents/<name> returns 404 when not found."""
        with patch('data.continents.delete_continent') as mock_delete:
            mock_delete.return_value = False
            response = client.delete('/continents/Atlantis')
            assert response.status_code == HTTPStatus.NOT_FOUND

    def test_delete_continent_with_countries(self, client):
        """DELETE /continents/<name> returns 409 when countries reference it."""
        with patch('data.continents.delete_continent') as mock_delete:
            mock_delete.side_effect = ValueError(
                'Cannot delete: 3 country/countries reference this continent'
            )
            response = client.delete('/continents/Africa')
            assert response.status_code == HTTPStatus.CONFLICT
            data = response.get_json()
            assert 'Cannot delete' in data['message']

    def test_delete_continent_db_error(self, client):
        """DELETE /continents/<name> returns 500 on unexpected error."""
        with patch('data.continents.delete_continent') as mock_delete:
            mock_delete.side_effect = Exception('DB error')
            response = client.delete('/continents/Asia')
            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
