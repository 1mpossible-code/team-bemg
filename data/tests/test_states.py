"""
Tests for the states data module.
"""
import pytest
from unittest.mock import patch, MagicMock
from data import states as S

class TestStates:
    """Test class for states module."""

    def test_get_states(self):
        """Test getting all states."""
        with patch('data.db_connect.read') as mock_read:
            mock_read.return_value = [S.TEST_STATE]
            result = S.get_states()
            mock_read.assert_called_once_with(S.STATES_COLLECT)
            assert result == [S.TEST_STATE]

    def test_get_state_dict(self):
        """Test getting states as a dict keyed by code."""
        with patch('data.db_connect.read_dict') as mock_read_dict:
            expected = {'NY': S.TEST_STATE}
            mock_read_dict.return_value = expected
            result = S.get_state_dict()
            mock_read_dict.assert_called_once_with(S.STATES_COLLECT, S.STATE_CODE)
            assert result == expected

    def test_get_state_by_name(self):
        """Test getting a state by its name."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = S.TEST_STATE
            result = S.get_state_by_name('New York')
            mock_read_one.assert_called_once_with(S.STATES_COLLECT, {S.STATE_NAME: 'New York'})
            assert result == S.TEST_STATE

    def test_get_state_by_code(self):
        """Test getting a state by its code."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = S.TEST_STATE
            result = S.get_state_by_code('NY')
            mock_read_one.assert_called_once_with(S.STATES_COLLECT, {S.STATE_CODE: 'NY'})
            assert result == S.TEST_STATE

    def test_get_states_by_country(self):
        """Test getting states by country."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_country('US')
            mock_collection.find.assert_called_once_with({S.COUNTRY_CODE: 'US'})
            assert result == [S.TEST_STATE]

    def test_get_states_by_population_range_min_only(self):
        """Test filtering by min population only builds $gte query."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_population_range(min_pop=100)
            mock_collection.find.assert_called_once_with({S.POPULATION: {'$gte': 100}})
            assert result == [S.TEST_STATE]

    def test_get_states_by_population_range_max_only(self):
        """Test filtering by max population only builds $lte query."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_population_range(max_pop=1000)
            mock_collection.find.assert_called_once_with({S.POPULATION: {'$lte': 1000}})
            assert result == [S.TEST_STATE]

    def test_get_states_by_country_empty(self):
        """Test getting states by country returns empty list when none found."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = []
            result = S.get_states_by_country('XX')
            mock_collection.find.assert_called_once_with({S.COUNTRY_CODE: 'XX'})
            assert result == []

    def test_get_states_by_population_range(self):
        """Test getting states by population range."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_population_range(min_pop=1000000, max_pop=50000000)
            mock_collection.find.assert_called_once_with({
                S.POPULATION: {'$gte': 1000000, '$lte': 50000000}
            })
            assert result == [S.TEST_STATE]

    def test_get_states_by_population_range_no_filters(self):
        """Test getting states by population range with no filters."""
        with patch('data.db_connect.client') as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_population_range()
            mock_collection.find.assert_called_once_with({})
            assert result == [S.TEST_STATE]

    def test_add_state_success(self):
        """Test adding a state successfully."""
        with patch('data.states.get_state_by_code') as mock_get, \
             patch('data.db_connect.create') as mock_create:
            mock_get.return_value = None
            ack = MagicMock(); ack.acknowledged = True
            mock_create.return_value = ack
            assert S.add_state(S.TEST_STATE) is True
            mock_create.assert_called_once()

    def test_add_state_missing_field(self):
        """Test adding a state with missing required field."""
        with pytest.raises(ValueError, match="Missing required field"):
            S.add_state({S.STATE_NAME: 'Foo'})

    def test_add_state_exists(self):
        """Test adding a state that already exists."""
        with patch('data.states.get_state_by_code') as mock_get:
            mock_get.return_value = S.TEST_STATE
            with pytest.raises(ValueError, match="already exists"):
                S.add_state(S.TEST_STATE)

    def test_update_state_success(self):
        """Test updating a state successfully."""
        with patch('data.states.get_state_by_code') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = S.TEST_STATE
            res = MagicMock(); res.modified_count = 1
            mock_update.return_value = res
            assert S.update_state('NY', {S.POPULATION: 1}) is True

    def test_update_state_not_found(self):
        """Test updating a state that does not exist."""
        with patch('data.states.get_state_by_code') as mock_get:
            mock_get.return_value = None
            assert S.update_state('XX', {}) is False

    def test_update_state_strips_code_from_update(self):
        """Test update removes STATE_CODE before calling update."""
        with patch('data.states.get_state_by_code') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = S.TEST_STATE
            res = MagicMock(); res.modified_count = 1
            mock_update.return_value = res
            payload = {S.STATE_CODE: 'ZZ', S.POPULATION: 123}
            assert S.update_state('NY', payload) is True
            mock_update.assert_called_once_with(S.STATES_COLLECT, {S.STATE_CODE: 'NY'}, {S.POPULATION: 123})

    def test_delete_state_success(self):
        """Test deleting a state successfully."""
        with patch('data.db_connect.delete') as mock_delete:
            mock_delete.return_value = 1
            assert S.delete_state('NY') is True

    def test_delete_state_not_found(self):
        """Test deleting a state that does not exist."""
        with patch('data.db_connect.delete') as mock_delete:
            mock_delete.return_value = 0
            assert S.delete_state('XX') is False

    def test_state_exists(self):
        """Test checking if a state exists."""
        with patch('data.states.get_state_by_code') as mock_get:
            mock_get.return_value = S.TEST_STATE
            assert S.state_exists('NY') is True