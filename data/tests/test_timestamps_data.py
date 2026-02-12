"""
Unit tests for timestamp functionality in add_* and update_* functions.  Tests that datetime objects are properly set when creating and updating data.  All tests mock the database to ensure unit testing without DB dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC
from freezegun import freeze_time

import data.cities as cities
import data.states as states
import data.countries as countries


class TestCityTimestamps:
    @freeze_time("2025-01-15 10:30:00")
    @patch('data.cities.dbc.create')
    @patch('data.states.state_exists', return_value=True)
    @patch('data.countries.country_exists', return_value=True)
    @patch('data.cities.get_city_by_name_and_state', return_value=None)
    def test_add_city_sets_timestamps(
            self,
            mock_get_city,
            mock_country_exists,
            mock_state_exists,
            mock_create):
        """Test that add_city sets created_at and updated_at as datetime objects"""
        # Setup mock response
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_create.return_value = mock_result

        # Call add_city
        city_data = {
            cities.CITY_NAME: 'Test City',
            cities.STATE_CODE: 'NY',
            cities.COUNTRY_CODE: 'US',
            cities.POPULATION: 100000
        }
        result = cities.add_city(city_data)

        # Verify result
        assert result is True
        mock_create.assert_called_once()

        # Get the actual data passed to create
        call_args = mock_create.call_args[0]
        actual_data = call_args[1]

        # Assert timestamps are datetime objects
        assert 'created_at' in actual_data
        assert 'updated_at' in actual_data
        assert isinstance(actual_data['created_at'], datetime)
        assert isinstance(actual_data['updated_at'], datetime)

        # Assert timestamps match frozen time
        expected_time = datetime(2025, 1, 15, 10, 30, 0)
        assert actual_data['created_at'] == expected_time
        assert actual_data['updated_at'] == expected_time

    @freeze_time("2025-02-20 14:45:30")
    @patch('data.cities.dbc.update')
    @patch('data.cities.get_city_by_name_and_state')
    def test_update_city_sets_updated_at(
            self,
            mock_get_city,
            mock_update):
        """Test that update_city sets updated_at as a datetime object"""
        # Setup mocks
        mock_get_city.return_value = {'city_name': 'Test City'}
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_update.return_value = mock_result

        # Call update_city
        update_data = {cities.POPULATION: 150000}
        result = cities.update_city('Test City', 'NY', update_data)

        # Verify result
        assert result is True
        mock_update.assert_called_once()

        # Get the actual update data
        call_args = mock_update.call_args[0]
        actual_update = call_args[2]

        # Assert updated_at is a datetime object
        assert 'updated_at' in actual_update
        assert isinstance(actual_update['updated_at'], datetime)

        # Assert timestamp matches frozen time
        expected_time = datetime(2025, 2, 20, 14, 45, 30, tzinfo=UTC)
        assert actual_update['updated_at'] == expected_time

        # Ensure created_at is not in update
        assert 'created_at' not in actual_update

    @patch('data.cities.dbc.create')
    @patch('data.states.state_exists', return_value=True)
    @patch('data.countries.country_exists', return_value=True)
    @patch('data.cities.get_city_by_name_and_state', return_value=None)
    def test_add_city_strips_user_provided_timestamps(
            self,
            mock_get_city,
            mock_country_exists,
            mock_state_exists,
            mock_create):
        """Test that user-provided timestamp values are stripped and replaced"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_create.return_value = mock_result

        # Try to inject timestamps
        user_time = datetime(2020, 1, 1, 0, 0, 0)
        city_data = {
            cities.CITY_NAME: 'Test City',
            cities.STATE_CODE: 'NY',
            cities.COUNTRY_CODE: 'US',
            'created_at': user_time,  # Should be stripped
            'updated_at': user_time   # Should be stripped
        }
        
        cities.add_city(city_data)

        # Get actual data passed to DB
        call_args = mock_create.call_args[0]
        actual_data = call_args[1]

        # Assert server-side timestamps are set (not user values)
        assert actual_data['created_at'] != user_time
        assert actual_data['updated_at'] != user_time
        assert isinstance(actual_data['created_at'], datetime)
        assert isinstance(actual_data['updated_at'], datetime)


class TestStateTimestamps:
    """Test timestamp handling in state add/update operations"""

    @freeze_time("2025-03-10 09:15:00")
    @patch('data.states.dbc.create')
    @patch('data.states.get_state_by_code', return_value=None)
    def test_add_state_sets_timestamps(
            self,
            mock_get_state,
            mock_create):
        """Test that add_state sets created_at and updated_at as datetime objects"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_create.return_value = mock_result

        # Call add_state
        state_data = {
            states.STATE_NAME: 'Test State',
            states.STATE_CODE: 'TS',
            states.COUNTRY_CODE: 'US'
        }
        result = states.add_state(state_data)

        # Verify result
        assert result is True
        mock_create.assert_called_once()

        # Get actual data
        call_args = mock_create.call_args[0]
        actual_data = call_args[1]

        # Assert timestamps are datetime objects
        assert 'created_at' in actual_data
        assert 'updated_at' in actual_data
        assert isinstance(actual_data['created_at'], datetime)
        assert isinstance(actual_data['updated_at'], datetime)

        # Assert timestamps match frozen time
        expected_time = datetime(2025, 3, 10, 9, 15, 0, tzinfo=UTC)
        assert actual_data['created_at'] == expected_time
        assert actual_data['updated_at'] == expected_time

    @freeze_time("2025-04-25 16:20:45")
    @patch('data.states.dbc.update')
    @patch('data.states.get_state_by_code')
    def test_update_state_sets_updated_at(
            self,
            mock_get_state,
            mock_update):
        """Test that update_state sets updated_at as a datetime object"""
        # Setup mocks
        mock_get_state.return_value = {'state_code': 'TS'}
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_update.return_value = mock_result

        # Call update_state
        update_data = {states.POPULATION: 5000000}
        result = states.update_state('TS', update_data)

        # Verify result
        assert result is True
        mock_update.assert_called_once()

        # Get actual update data
        call_args = mock_update.call_args[0]
        actual_update = call_args[2]

        # Assert updated_at is a datetime object
        assert states.UPDATED_AT in actual_update
        assert isinstance(actual_update[states.UPDATED_AT], datetime)

        # Assert timestamp matches frozen time
        expected_time = datetime(2025, 4, 25, 16, 20, 45, tzinfo=UTC)
        assert actual_update[states.UPDATED_AT] == expected_time

        # Ensure created_at is not in update
        assert 'created_at' not in actual_update

    @patch('data.states.dbc.create')
    @patch('data.states.get_state_by_code', return_value=None)
    def test_add_state_strips_user_provided_timestamps(
            self,
            mock_get_state,
            mock_create):
        """Test that user-provided timestamp values are stripped"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_create.return_value = mock_result

        # Try to inject timestamps
        user_time = datetime(2015, 6, 1, 12, 0, 0)
        state_data = {
            states.STATE_NAME: 'Test State',
            states.STATE_CODE: 'TS',
            states.COUNTRY_CODE: 'US',
            'created_at': user_time,
            'updated_at': user_time
        }
        
        states.add_state(state_data)

        # Get actual data
        call_args = mock_create.call_args[0]
        actual_data = call_args[1]

        # Assert server-side timestamps (not user values)
        assert actual_data['created_at'] != user_time
        assert actual_data['updated_at'] != user_time
        assert isinstance(actual_data['created_at'], datetime)


class TestCountryTimestamps:
    """Test timestamp handling in country add/update operations"""

    @freeze_time("2025-05-05 11:00:00")
    @patch('data.countries.dbc.create')
    @patch('data.countries.get_country_by_code', return_value=None)
    def test_add_country_sets_timestamps(
            self,
            mock_get_country,
            mock_create):
        """Test that add_country sets created_at and updated_at as datetime objects"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_create.return_value = mock_result

        # Call add_country
        country_data = {
            countries.COUNTRY_NAME: 'Test Country',
            countries.COUNTRY_CODE: 'TC',
            countries.CONTINENT: 'Europe',
            countries.CAPITAL: 'Test Capital'
        }
        result = countries.add_country(country_data)

        # Verify result
        assert result is True
        mock_create.assert_called_once()

        # Get actual data
        call_args = mock_create.call_args[0]
        actual_data = call_args[1]

        # Assert timestamps are datetime objects
        assert 'created_at' in actual_data
        assert 'updated_at' in actual_data
        assert isinstance(actual_data['created_at'], datetime)
        assert isinstance(actual_data['updated_at'], datetime)

        # Assert timestamps match frozen time
        expected_time = datetime(2025, 5, 5, 11, 0, 0, tzinfo=UTC)
        assert actual_data['created_at'] == expected_time
        assert actual_data['updated_at'] == expected_time

    @freeze_time("2025-06-18 13:30:15")
    @patch('data.countries.dbc.update')
    @patch('data.countries.get_country_by_code')
    def test_update_country_sets_updated_at(
            self,
            mock_get_country,
            mock_update):
        """Test that update_country sets updated_at as a datetime object"""
        # Setup mocks
        mock_get_country.return_value = {'country_code': 'TC'}
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_update.return_value = mock_result

        # Call update_country
        update_data = {countries.POPULATION: 10000000}
        result = countries.update_country('TC', update_data)

        # Verify result
        assert result is True
        mock_update.assert_called_once()

        # Get actual update data
        call_args = mock_update.call_args[0]
        actual_update = call_args[2]

        # Assert updated_at is a datetime object
        assert 'updated_at' in actual_update
        assert isinstance(actual_update['updated_at'], datetime)

        # Assert timestamp matches frozen time
        expected_time = datetime(2025, 6, 18, 13, 30, 15, tzinfo=UTC)
        assert actual_update['updated_at'] == expected_time

        # Ensure created_at is not in update
        assert 'created_at' not in actual_update

    @patch('data.countries.dbc.create')
    @patch('data.countries.get_country_by_code', return_value=None)
    def test_add_country_strips_user_provided_timestamps(
            self,
            mock_get_country,
            mock_create):
        """Test that user-provided timestamp values are stripped"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_create.return_value = mock_result

        # Try to inject timestamps
        user_time = datetime(2010, 3, 15, 8, 30, 0)
        country_data = {
            countries.COUNTRY_NAME: 'Test Country',
            countries.COUNTRY_CODE: 'TC',
            countries.CONTINENT: 'Asia',
            countries.CAPITAL: 'Test Capital',
            'created_at': user_time,
            'updated_at': user_time
        }
        
        countries.add_country(country_data)

        # Get actual data
        call_args = mock_create.call_args[0]
        actual_data = call_args[1]

        # Assert server-side timestamps (not user values)
        assert actual_data['created_at'] != user_time
        assert actual_data['updated_at'] != user_time
        assert isinstance(actual_data['created_at'], datetime)


class TestTimestampConsistency:
    """Test that timestamps are consistent across add/update operations"""

    @freeze_time("2025-07-01 12:00:00")
    @patch('data.cities.dbc.create')
    @patch('data.states.state_exists', return_value=True)
    @patch('data.countries.country_exists', return_value=True)
    @patch('data.cities.get_city_by_name_and_state', return_value=None)
    def test_add_city_created_and_updated_same(
            self,
            mock_get_city,
            mock_country_exists,
            mock_state_exists,
            mock_create):
        """Test that created_at and updated_at are the same on creation"""
        mock_result = MagicMock()
        mock_result.acknowledged = True
        mock_create.return_value = mock_result

        city_data = {
            cities.CITY_NAME: 'Test',
            cities.STATE_CODE: 'NY',
            cities.COUNTRY_CODE: 'US'
        }
        cities.add_city(city_data)

        call_args = mock_create.call_args[0]
        actual_data = call_args[1]

        # Both timestamps should be identical on creation
        assert actual_data['created_at'] == actual_data['updated_at']

    @freeze_time("2025-07-01 12:00:00")
    @patch('data.states.dbc.update')
    @patch('data.states.get_state_by_code')
    def test_update_state_preserves_created_at(
            self,
            mock_get_state,
            mock_update):
        """Test that update operations don't include created_at"""
        mock_get_state.return_value = {'state_code': 'TS'}
        mock_result = MagicMock()
        mock_result.modified_count = 1
        mock_update.return_value = mock_result

        # Try to update with created_at in the data
        update_data = {
            states.POPULATION: 5000000,
            'created_at': datetime(2020, 1, 1)
        }
        states.update_state('TS', update_data)

        call_args = mock_update.call_args[0]
        actual_update = call_args[2]

        # created_at should be stripped from update
        assert 'created_at' not in actual_update
        # But updated_at should be present
        assert states.UPDATED_AT in actual_update
