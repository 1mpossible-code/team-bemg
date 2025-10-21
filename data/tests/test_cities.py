"""
Tests for the cities data module.
"""
import pytest
from unittest.mock import patch, MagicMock, DEFAULT
from data import cities


class TestCities:
    """Test class for cities module."""

    # ===== Fixtures for reusable test data and mocks =====
    @pytest.fixture
    def sample_city_with_state(self):
        """Sample city with state code."""
        return {
            cities.CITY_NAME: 'Springfield', cities.STATE_CODE: 'IL',
            cities.COUNTRY_CODE: 'US', cities.POPULATION: 116000,
            cities.AREA_KM2: 160, cities.COORDINATES: {
                cities.LATITUDE: 39.78, cities.LONGITUDE: -89.64
            }
        }

    @pytest.fixture
    def sample_city_no_state(self):
        """Sample city without state code."""
        return {
            cities.CITY_NAME: 'Monaco',
            cities.COUNTRY_CODE: 'MC',
            cities.POPULATION: 38000
        }

    @pytest.fixture
    def mock_acknowledged_result(self):
        """Mock result for successful database create operations."""
        result = MagicMock()
        result.acknowledged = True
        return result

    @pytest.fixture
    def mock_modified_result(self):
        """Mock result for successful database update operations."""
        result = MagicMock()
        result.modified_count = 1
        return result

    @pytest.fixture
    def mock_not_modified_result(self):
        """Mock result for database update with no changes."""
        result = MagicMock()
        result.modified_count = 0
        return result

    # ===== Read operations tests =====

    def test_get_cities(self):
        """Test getting all cities."""
        with patch('data.db_connect.read') as mock_read:
            mock_read.return_value = [cities.TEST_CITY]
            result = cities.get_cities()
            mock_read.assert_called_once_with(cities.CITIES_COLLECT)
            assert result == [cities.TEST_CITY]

    def test_get_cities_by_country(self):
        """Test getting cities by country."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [cities.TEST_CITY]
            result = cities.get_cities_by_country('US')
            mock_collection.find.assert_called_once_with({cities.COUNTRY_CODE: 'US'})
            assert result == [cities.TEST_CITY]

    def test_get_cities_by_state(self):
        """Test getting cities by state."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [cities.TEST_CITY]
            result = cities.get_cities_by_state('IL')
            mock_collection.find.assert_called_once_with({cities.STATE_CODE: 'IL'})
            assert result == [cities.TEST_CITY]

    def test_get_cities_by_country_empty(self):
        """Test getting cities by country returns empty list when none found."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = []
            result = cities.get_cities_by_country('XX')
            mock_collection.find.assert_called_once_with({cities.COUNTRY_CODE: 'XX'})
            assert result == []

    def test_get_cities_by_state_empty(self):
        """Test getting cities by state returns empty list when none found."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = []
            result = cities.get_cities_by_state('XX')
            mock_collection.find.assert_called_once_with({cities.STATE_CODE: 'XX'})
            assert result == []

    def test_get_cities_by_population_range_min_only(self):
        """Test filtering by min population only builds $gte query."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [cities.TEST_CITY]
            result = cities.get_cities_by_population_range(min_pop=100000)
            mock_collection.find.assert_called_once_with({cities.POPULATION: {'$gte': 100000}})
            assert result == [cities.TEST_CITY]

    def test_get_cities_by_population_range_max_only(self):
        """Test filtering by max population only builds $lte query."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [cities.TEST_CITY]
            result = cities.get_cities_by_population_range(max_pop=200000)
            mock_collection.find.assert_called_once_with({cities.POPULATION: {'$lte': 200000}})
            assert result == [cities.TEST_CITY]

    def test_get_cities_by_population_range(self):
        """Test getting cities by population range."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [cities.TEST_CITY]
            result = cities.get_cities_by_population_range(min_pop=50000, max_pop=500000)
            mock_collection.find.assert_called_once_with({
                cities.POPULATION: {'$gte': 50000, '$lte': 500000}
            })
            assert result == [cities.TEST_CITY]

    def test_get_cities_by_population_range_no_filters(self):
        """Test getting cities by population range with no filters."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [cities.TEST_CITY]
            result = cities.get_cities_by_population_range()
            mock_collection.find.assert_called_once_with({})
            assert result == [cities.TEST_CITY]

    def test_get_city_by_name(self):
        """Test getting a city by its name."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = cities.TEST_CITY
            result = cities.get_city_by_name('Springfield')
            mock_read_one.assert_called_once_with(cities.CITIES_COLLECT, {cities.CITY_NAME: 'Springfield'})
            assert result == cities.TEST_CITY

    def test_get_city_by_name_and_country(self):
        """Test getting a city by its name and country code."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = cities.TEST_CITY
            result = cities.get_city_by_name_and_country('Springfield', 'US')
            mock_read_one.assert_called_once_with(
                cities.CITIES_COLLECT, 
                {cities.CITY_NAME: 'Springfield', cities.COUNTRY_CODE: 'US'}
            )
            assert result == cities.TEST_CITY

    def test_get_city_by_name_and_state(self):
        """Test getting a city by its name and state code."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = cities.TEST_CITY
            result = cities.get_city_by_name_and_state('Springfield', 'IL')
            mock_read_one.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Springfield', cities.STATE_CODE: 'IL'}
            )
            assert result == cities.TEST_CITY

    # ===== Create operations tests =====

    def test_add_city_success_with_state(self, sample_city_with_state, mock_acknowledged_result):
        """Test successfully adding a new city with state."""
        with patch('data.cities.get_city_by_name_and_state') as mock_get, \
             patch('data.db_connect.create') as mock_create:
            mock_get.return_value = None
            mock_create.return_value = mock_acknowledged_result
            
            result = cities.add_city(sample_city_with_state)
            assert result is True
            mock_create.assert_called_once_with(cities.CITIES_COLLECT, sample_city_with_state)

    def test_add_city_success_without_state(self, sample_city_no_state, mock_acknowledged_result):
        """Test successfully adding a new city without state."""
        with patch('data.cities.get_city_by_name_and_country') as mock_get, \
             patch('data.db_connect.create') as mock_create:
            mock_get.return_value = None
            mock_create.return_value = mock_acknowledged_result
            
            result = cities.add_city(sample_city_no_state)
            assert result is True
            mock_create.assert_called_once_with(cities.CITIES_COLLECT, sample_city_no_state)

    def test_add_city_missing_required_field(self):
        """Test adding a city with missing required field."""
        incomplete_city = {cities.CITY_NAME: 'Test City'}
        with pytest.raises(ValueError, match="Missing required field"):
            cities.add_city(incomplete_city)

    def test_add_city_missing_city_name(self):
        """Test adding a city without city name raises ValueError."""
        city_no_name = {cities.COUNTRY_CODE: 'US'}
        with pytest.raises(ValueError, match="Missing required field: name"):
            cities.add_city(city_no_name)

    def test_add_city_missing_country_code(self):
        """Test adding a city without country code raises ValueError."""
        city_no_country = {cities.CITY_NAME: 'Somewhere'}
        with pytest.raises(ValueError, match="Missing required field: country_code"):
            cities.add_city(city_no_country)

    def test_add_city_already_exists_in_state(self, sample_city_with_state):
        """Test adding a city that already exists in the same state."""
        with patch('data.cities.get_city_by_name_and_state') as mock_get:
            mock_get.return_value = sample_city_with_state
            with pytest.raises(ValueError, match="already exists in state"):
                cities.add_city(sample_city_with_state)

    def test_add_city_already_exists_in_country(self, sample_city_no_state):
        """Test adding a city that already exists in the same country (no state)."""
        with patch('data.cities.get_city_by_name_and_country') as mock_get:
            mock_get.return_value = sample_city_no_state
            with pytest.raises(ValueError, match="already exists in country"):
                cities.add_city(sample_city_no_state)

    # ===== Update operations tests =====

    def test_update_city_success(self, sample_city_with_state, mock_modified_result):
        """Test successfully updating a city."""
        update_data = {cities.POPULATION: 120000}
        
        with patch('data.cities.get_city_by_name_and_state') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = sample_city_with_state
            mock_update.return_value = mock_modified_result
            
            result = cities.update_city('Springfield', 'IL', update_data)
            assert result is True
            mock_update.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Springfield', cities.STATE_CODE: 'IL'},
                update_data
            )

    def test_update_city_not_found(self):
        """Test updating a city that doesn't exist."""
        with patch('data.cities.get_city_by_name_and_state') as mock_get:
            mock_get.return_value = None  # City doesn't exist
            
            result = cities.update_city('Nowhere', 'XX', {})
            assert result is False

    def test_update_city_strips_name_from_update(self, sample_city_with_state, mock_modified_result):
        """Test update removes CITY_NAME before calling update."""
        with patch('data.cities.get_city_by_name_and_state') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = sample_city_with_state
            mock_update.return_value = mock_modified_result
            payload = {cities.CITY_NAME: 'NewName', cities.POPULATION: 123}
            
            result = cities.update_city('Springfield', 'IL', payload)
            assert result is True
            mock_update.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Springfield', cities.STATE_CODE: 'IL'},
                {cities.POPULATION: 123}
            )

    def test_update_city_strips_state_code_from_update(self, sample_city_with_state, mock_modified_result):
        """Test update removes STATE_CODE before calling update."""
        with patch('data.cities.get_city_by_name_and_state') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = sample_city_with_state
            mock_update.return_value = mock_modified_result
            payload = {cities.STATE_CODE: 'XX', cities.POPULATION: 123}
            
            result = cities.update_city('Springfield', 'IL', payload)
            assert result is True
            mock_update.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Springfield', cities.STATE_CODE: 'IL'},
                {cities.POPULATION: 123}
            )

    def test_update_city_by_name_and_country_success(self, sample_city_no_state, mock_modified_result):
        """Test successfully updating a city by name and country."""
        update_data = {cities.POPULATION: 40000}
        
        with patch('data.cities.get_city_by_name_and_country') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = sample_city_no_state
            mock_update.return_value = mock_modified_result
            
            result = cities.update_city_by_name_and_country('Monaco', 'MC', update_data)
            assert result is True
            mock_update.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Monaco', cities.COUNTRY_CODE: 'MC'},
                update_data
            )

    def test_update_city_by_name_and_country_not_found(self):
        """Test updating a city by name and country that doesn't exist."""
        with patch('data.cities.get_city_by_name_and_country') as mock_get:
            mock_get.return_value = None
            
            result = cities.update_city_by_name_and_country('Nowhere', 'XX', {})
            assert result is False

    def test_update_city_by_name_and_country_strips_name(self, sample_city_no_state, mock_modified_result):
        """Test update by country removes CITY_NAME before calling update."""
        with patch('data.cities.get_city_by_name_and_country') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = sample_city_no_state
            mock_update.return_value = mock_modified_result
            payload = {cities.CITY_NAME: 'NewName', cities.POPULATION: 123}
            
            result = cities.update_city_by_name_and_country('Monaco', 'MC', payload)
            assert result is True
            mock_update.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Monaco', cities.COUNTRY_CODE: 'MC'},
                {cities.POPULATION: 123}
            )

    def test_update_city_by_name_and_country_strips_country_code(self, sample_city_no_state, mock_modified_result):
        """Test update by country removes COUNTRY_CODE before calling update."""
        with patch('data.cities.get_city_by_name_and_country') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = sample_city_no_state
            mock_update.return_value = mock_modified_result
            payload = {cities.COUNTRY_CODE: 'XX', cities.POPULATION: 123}
            
            result = cities.update_city_by_name_and_country('Monaco', 'MC', payload)
            assert result is True
            mock_update.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Monaco', cities.COUNTRY_CODE: 'MC'},
                {cities.POPULATION: 123}
            )

    # ===== Delete operations tests =====

    def test_delete_city_success(self):
        """Test successfully deleting a city."""
        with patch('data.db_connect.delete') as mock_delete:
            mock_delete.return_value = 1
            
            result = cities.delete_city('Springfield', 'IL')
            assert result is True
            mock_delete.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Springfield', cities.STATE_CODE: 'IL'}
            )

    def test_delete_city_not_found(self):
        """Test deleting a city that doesn't exist."""
        with patch('data.db_connect.delete') as mock_delete:
            mock_delete.return_value = 0  # No documents deleted
            
            result = cities.delete_city('Nowhere', 'XX')
            assert result is False

    def test_delete_city_by_name_and_country_success(self):
        """Test successfully deleting a city by name and country."""
        with patch('data.db_connect.delete') as mock_delete:
            mock_delete.return_value = 1  # One document deleted
            
            result = cities.delete_city_by_name_and_country('Monaco', 'MC')
            assert result is True
            mock_delete.assert_called_once_with(
                cities.CITIES_COLLECT,
                {cities.CITY_NAME: 'Monaco', cities.COUNTRY_CODE: 'MC'}
            )

    def test_delete_city_by_name_and_country_not_found(self):
        """Test deleting a city by name and country that doesn't exist."""
        with patch('data.db_connect.delete') as mock_delete:
            mock_delete.return_value = 0
            
            result = cities.delete_city_by_name_and_country('Nowhere', 'XX')
            assert result is False

    # ===== Existence check tests =====

    def test_city_exists_with_state(self):
        """Test checking if a city exists by name and state."""
        with patch('data.cities.get_city_by_name_and_state') as mock_get:
            mock_get.return_value = cities.TEST_CITY
            
            result = cities.city_exists('Springfield', state_code='IL')
            assert result is True

    def test_city_exists_with_state_false(self):
        """Test checking if a city exists by name and state - returns False."""
        with patch('data.cities.get_city_by_name_and_state') as mock_get:
            mock_get.return_value = None
            
            result = cities.city_exists('Nowhere', state_code='XX')
            assert result is False

    def test_city_exists_with_country(self):
        """Test checking if a city exists by name and country."""
        with patch('data.cities.get_city_by_name_and_country') as mock_get:
            mock_get.return_value = cities.TEST_CITY
            
            result = cities.city_exists('Monaco', country_code='MC')
            assert result is True

    def test_city_exists_with_country_false(self):
        """Test checking if a city exists by name and country - returns False."""
        with patch('data.cities.get_city_by_name_and_country') as mock_get:
            mock_get.return_value = None
            
            result = cities.city_exists('Nowhere', country_code='XX')
            assert result is False

    def test_city_exists_by_name_only(self):
        """Test checking if a city exists by name only."""
        with patch('data.cities.get_city_by_name') as mock_get:
            mock_get.return_value = cities.TEST_CITY
            
            result = cities.city_exists('Springfield')
            assert result is True

    def test_city_exists_by_name_only_false(self):
        """Test checking if a city exists by name only - returns False."""
        with patch('data.cities.get_city_by_name') as mock_get:
            mock_get.return_value = None
            
            result = cities.city_exists('Nowhere')
            assert result is False

    # ===== Integration tests (skipped) =====

    @pytest.mark.skip(reason="Integration test - requires MongoDB with geospatial indexes")
    def test_geospatial_query_integration(self):
        """
        Integration test for geospatial queries on city coordinates.
        Would test finding cities within a certain radius using MongoDB's $near operator.
        """
        # This would require:
        # 1. A running MongoDB instance with 2dsphere index on coordinates
        # 2. Real city data with valid lat/long coordinates
        # 3. Testing queries like "find all cities within 50km of these coordinates"
        pass
