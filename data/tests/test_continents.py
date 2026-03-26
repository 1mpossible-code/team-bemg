"""
Tests for the continents data module.
"""
import pytest
from unittest.mock import patch, MagicMock
from data import continents


class TestContinents:
    """Test class for continents module."""

    def test_get_continents(self):
        """Test getting all continents."""
        with patch('data.db_connect.read') as mock_read:
            mock_read.return_value = [continents.TEST_CONTINENT]
            result = continents.get_continents()
            mock_read.assert_called_once_with(continents.CONTINENTS_COLLECT)
            assert result == [continents.TEST_CONTINENT]

    def test_get_continent_by_name_found(self):
        """Test getting a continent by name when it exists."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = continents.TEST_CONTINENT
            result = continents.get_continent_by_name('North America')
            mock_read_one.assert_called_once_with(
                continents.CONTINENTS_COLLECT,
                {continents.CONTINENT_NAME: 'North America'}
            )
            assert result == continents.TEST_CONTINENT

    def test_get_continent_by_name_not_found(self):
        """Test getting a continent by name when it does not exist."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = None
            result = continents.get_continent_by_name('Atlantis')
            assert result is None

    def test_add_continent_success(self):
        """Test successfully adding a new continent."""
        with patch('data.continents.get_continent_by_name') as mock_get, \
             patch('data.db_connect.create') as mock_create:
            mock_get.return_value = None
            mock_result = MagicMock()
            mock_result.acknowledged = True
            mock_create.return_value = mock_result

            data = {continents.CONTINENT_NAME: 'North America'}
            result = continents.add_continent(data)

            assert result is True
            mock_create.assert_called_once()
            doc = mock_create.call_args[0][1]
            assert 'created_at' in doc and 'updated_at' in doc
            import datetime as _dt
            assert isinstance(doc['created_at'], _dt.datetime)
            assert isinstance(doc['updated_at'], _dt.datetime)

    def test_add_continent_missing_required_field(self):
        """Test adding a continent without continent_name raises ValueError."""
        with pytest.raises(ValueError, match="Missing required field"):
            continents.add_continent({})

    def test_add_continent_invalid_name(self):
        """Test adding a continent with an invalid name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid continent"):
            continents.add_continent({continents.CONTINENT_NAME: 'Atlantis'})

    def test_add_continent_already_exists(self):
        """Test adding a continent that already exists raises ValueError."""
        with patch('data.continents.get_continent_by_name') as mock_get:
            mock_get.return_value = continents.TEST_CONTINENT
            with pytest.raises(ValueError, match="already exists"):
                continents.add_continent({continents.CONTINENT_NAME: 'North America'})

    def test_add_continent_strips_timestamps(self):
        """Test that client-supplied timestamps are overwritten."""
        with patch('data.continents.get_continent_by_name') as mock_get, \
             patch('data.db_connect.create') as mock_create:
            mock_get.return_value = None
            ack = MagicMock()
            ack.acknowledged = True
            mock_create.return_value = ack

            data = {
                continents.CONTINENT_NAME: 'Asia',
                'created_at': '1999-01-01',
                'updated_at': '1999-01-01',
            }
            continents.add_continent(data)

            doc = mock_create.call_args[0][1]
            assert doc['created_at'] != '1999-01-01'
            assert doc['updated_at'] != '1999-01-01'

    def test_update_continent_success(self):
        """Test successfully updating a continent."""
        with patch('data.continents.get_continent_by_name') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = continents.TEST_CONTINENT
            mock_result = MagicMock()
            mock_result.modified_count = 1
            mock_update.return_value = mock_result

            result = continents.update_continent('North America', {})
            assert result is True
            mock_update.assert_called_once()

    def test_update_continent_not_found(self):
        """Test updating a continent that does not exist returns False."""
        with patch('data.continents.get_continent_by_name') as mock_get:
            mock_get.return_value = None
            result = continents.update_continent('Atlantis', {})
            assert result is False

    def test_update_continent_name_not_changed(self):
        """Test that update_continent keeps the original name regardless of input."""
        with patch('data.continents.get_continent_by_name') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = continents.TEST_CONTINENT
            mock_result = MagicMock()
            mock_result.modified_count = 1
            mock_update.return_value = mock_result

            continents.update_continent('North America', {continents.CONTINENT_NAME: 'Asia'})

            doc = mock_update.call_args[0][2]
            assert doc[continents.CONTINENT_NAME] == 'North America'

    def test_delete_continent_success(self):
        """Test successfully deleting a continent with no dependent countries."""
        with patch('data.countries.get_countries_by_continent') as mock_countries, \
             patch('data.db_connect.delete') as mock_delete:
            mock_countries.return_value = []
            mock_delete.return_value = 1

            result = continents.delete_continent('Antarctica')
            assert result is True
            mock_delete.assert_called_once_with(
                continents.CONTINENTS_COLLECT,
                {continents.CONTINENT_NAME: 'Antarctica'}
            )

    def test_delete_continent_not_found(self):
        """Test deleting a continent that does not exist returns False."""
        with patch('data.countries.get_countries_by_continent') as mock_countries, \
             patch('data.db_connect.delete') as mock_delete:
            mock_countries.return_value = []
            mock_delete.return_value = 0

            result = continents.delete_continent('Antarctica')
            assert result is False

    def test_delete_continent_with_countries(self):
        """Test that deleting a continent with countries raises ValueError."""
        with patch('data.countries.get_countries_by_continent') as mock_countries:
            mock_countries.return_value = [{'country_name': 'Canada'}, {'country_name': 'USA'}]

            with pytest.raises(ValueError, match="Cannot delete"):
                continents.delete_continent('North America')
