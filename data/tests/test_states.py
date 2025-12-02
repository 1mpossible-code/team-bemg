"""
Tests for the states data module.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from data import states as S


class TestStates:
    """Test class for states module."""

    # ===== Fixtures =====
    @pytest.fixture
    def sample_state(self):
        """Sample state data."""
        return {
            S.STATE_NAME: "New York",
            S.STATE_CODE: "NY",
            S.COUNTRY_CODE: "US",
            S.CAPITAL: "Albany",
            S.POPULATION: 20201249,
            S.AREA_KM2: 141297,
        }

    @pytest.fixture
    def mock_successful_insert(self):
        """Mock for successful insert."""
        result = MagicMock()
        result.acknowledged = True
        return result

    @pytest.fixture
    def mock_modified_result(self):
        """Mock for successful update."""
        result = MagicMock()
        result.modified_count = 1
        return result

    # ===== Read operations tests =====

    def test_get_states(self):
        """Test getting all states."""
        with patch("data.db_connect.read") as mock_read:
            mock_read.return_value = [S.TEST_STATE]
            result = S.get_states()
            mock_read.assert_called_once_with(S.STATES_COLLECT)
            assert result == [S.TEST_STATE]

    def test_get_state_dict(self):
        """Test getting states as a dict keyed by code."""
        with patch("data.db_connect.read_dict") as mock_read_dict:
            expected = {"NY": S.TEST_STATE}
            mock_read_dict.return_value = expected
            result = S.get_state_dict()
            mock_read_dict.assert_called_once_with(S.STATES_COLLECT, S.STATE_CODE)
            assert result == expected

    def test_get_state_by_name(self):
        """Test getting a state by its name."""
        with patch("data.db_connect.read_one") as mock_read_one:
            mock_read_one.return_value = S.TEST_STATE
            result = S.get_state_by_name("New York")
            mock_read_one.assert_called_once_with(
                S.STATES_COLLECT, {S.STATE_NAME: "New York"}
            )
            assert result == S.TEST_STATE

    def test_get_state_by_code(self):
        """Test getting a state by its code."""
        with patch("data.db_connect.read_one") as mock_read_one:
            mock_read_one.return_value = S.TEST_STATE
            result = S.get_state_by_code("NY")
            mock_read_one.assert_called_once_with(
                S.STATES_COLLECT, {S.STATE_CODE: "NY"}
            )
            assert result == S.TEST_STATE

    def test_get_states_by_country(self):
        """Test getting states by country."""
        with patch("data.db_connect.client") as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_country("US")
            mock_collection.find.assert_called_once_with({S.COUNTRY_CODE: "US"})
            assert result == [S.TEST_STATE]

    def test_get_states_by_population_range_min_only(self):
        """Test filtering by min population only builds $gte query."""
        with patch("data.db_connect.client") as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_population_range(min_pop=100)
            mock_collection.find.assert_called_once_with({S.POPULATION: {"$gte": 100}})
            assert result == [S.TEST_STATE]

    def test_get_states_by_population_range_max_only(self):
        """Test filtering by max population only builds $lte query."""
        with patch("data.db_connect.client") as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_population_range(max_pop=1000)
            mock_collection.find.assert_called_once_with({S.POPULATION: {"$lte": 1000}})
            assert result == [S.TEST_STATE]

    def test_get_states_by_country_empty(self):
        """Test getting states by country returns empty list when none found."""
        with patch("data.db_connect.client") as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = []
            result = S.get_states_by_country("XX")
            mock_collection.find.assert_called_once_with({S.COUNTRY_CODE: "XX"})
            assert result == []

    def test_get_states_by_population_range(self):
        """Test getting states by population range."""
        with patch("data.db_connect.client") as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_population_range(min_pop=1000000, max_pop=50000000)
            mock_collection.find.assert_called_once_with(
                {S.POPULATION: {"$gte": 1000000, "$lte": 50000000}}
            )
            assert result == [S.TEST_STATE]

    def test_get_states_by_population_range_no_filters(self):
        """Test getting states by population range with no filters."""
        with patch("data.db_connect.client") as mock_client:
            mock_collection = mock_client.__getitem__().__getitem__()
            mock_collection.find.return_value = [S.TEST_STATE]
            result = S.get_states_by_population_range()
            mock_collection.find.assert_called_once_with({})
            assert result == [S.TEST_STATE]

    # ===== Create operations tests =====

    def test_add_state_success(self, sample_state, mock_successful_insert):
        """Test adding a state successfully."""
        with patch("data.states.get_state_by_code") as mock_get, patch(
            "data.db_connect.create"
        ) as mock_create:
            mock_get.return_value = None
            mock_create.return_value = mock_successful_insert
            assert S.add_state(sample_state) is True
            mock_create.assert_called_once()

    def test_add_state_missing_field(self):
        """Test adding a state with missing required field."""
        with pytest.raises(ValueError, match="Missing required field"):
            S.add_state({S.STATE_NAME: "Foo"})

    def test_add_state_missing_state_code(self):
        """Test adding a state without state_code raises ValueError."""
        incomplete = {S.STATE_NAME: "Test", S.COUNTRY_CODE: "US"}
        with pytest.raises(ValueError, match="Missing required field: state_code"):
            S.add_state(incomplete)

    def test_add_state_exists(self, sample_state):
        """Test adding a state that already exists."""
        with patch("data.states.get_state_by_code") as mock_get:
            mock_get.return_value = sample_state
            with pytest.raises(ValueError, match="already exists"):
                S.add_state(sample_state)

    def test_add_state_invalid_code_pattern_raises(self, sample_state):
        """Test adding state with invalid code pattern raises DB validation error."""
        invalid_state = {**sample_state, S.STATE_CODE: "TOOLONG"}
        with patch("data.states.get_state_by_code", return_value=None), patch(
            "data.db_connect.create"
        ) as mock_create:
            mock_create.side_effect = Exception(
                "Document failed validation: state_code pattern"
            )
            with pytest.raises(Exception, match="failed validation"):
                S.add_state(invalid_state)

    def test_add_state_negative_population_raises(self, sample_state):
        """Test adding state with negative population raises DB validation error."""
        invalid_state = {**sample_state, S.POPULATION: -1000}
        with patch("data.states.get_state_by_code", return_value=None), patch(
            "data.db_connect.create"
        ) as mock_create:
            mock_create.side_effect = ValueError("Population cannot be negative")
            with pytest.raises(ValueError, match="Population cannot be negative"):
                S.add_state(invalid_state)

    # ===== Update operations tests =====

    def test_update_state_success(self, sample_state, mock_modified_result):
        """Test updating a state successfully."""
        with patch("data.states.get_state_by_code") as mock_get, patch(
            "data.db_connect.update"
        ) as mock_update:
            mock_get.return_value = sample_state
            mock_update.return_value = mock_modified_result
            assert S.update_state("NY", {S.POPULATION: 1}) is True

    def test_update_state_not_found(self):
        """Test updating a state that does not exist."""
        with patch("data.states.get_state_by_code") as mock_get:
            mock_get.return_value = None
            assert S.update_state("XX", {}) is False

    def test_update_state_strips_code_from_update(
        self, sample_state, mock_modified_result
    ):
        """Test update removes STATE_CODE before calling update."""
        with patch("data.states.get_state_by_code") as mock_get, patch(
            "data.db_connect.update"
        ) as mock_update:
            mock_get.return_value = sample_state
            mock_update.return_value = mock_modified_result
            payload = {
                S.STATE_CODE: "ZZ",
                S.POPULATION: 123,
                S.UPDATED_AT: datetime.now(),
            }
            assert S.update_state("NY", payload) is True
            mock_update.assert_called_once_with(
                S.STATES_COLLECT,
                {S.STATE_CODE: "NY"},
                {S.POPULATION: 123, S.UPDATED_AT: payload[S.UPDATED_AT]},
            )

    def test_update_state_country_code_not_found_raises(self, sample_state):
        """Test updating state with non-existent country_code raises DB error."""
        with patch("data.states.get_state_by_code", return_value=sample_state), patch(
            "data.db_connect.update"
        ) as mock_update:
            mock_update.side_effect = Exception("FK violation: country_code not found")
            with pytest.raises(Exception, match="country_code not found"):
                S.update_state("NY", {S.COUNTRY_CODE: "ZZ"})

    def test_update_state_with_patch_object(self, sample_state, mock_modified_result):
        """Test using patch.object for more targeted mocking."""
        with patch.object(S, "get_state_by_code", return_value=sample_state), patch(
            "data.db_connect.update", return_value=mock_modified_result
        ):
            assert S.update_state("NY", {S.CAPITAL: "New Albany"}) is True

    def test_update_state_transient_failure_side_effect(
        self, sample_state, mock_modified_result
    ):
        """Test side_effect with multiple return values."""
        with patch("data.states.get_state_by_code", return_value=sample_state), patch(
            "data.db_connect.update"
        ) as mock_update:
            mock_update.side_effect = [Exception("Transient"), mock_modified_result]
            with pytest.raises(Exception, match="Transient"):
                S.update_state("NY", {S.POPULATION: 999})
            # Retry succeeds
            mock_update.side_effect = [mock_modified_result]
            assert S.update_state("NY", {S.POPULATION: 999}) is True

    # ===== Delete operations tests =====

    def test_delete_state_success(self):
        """Test deleting a state successfully."""
        with patch("data.states.can_delete_state", return_value=(True, "")), patch(
            "data.db_connect.delete"
        ) as mock_delete:
            mock_delete.return_value = 1
            assert S.delete_state("NY") is True

    def test_delete_state_not_found(self):
        """Test deleting a state that does not exist."""
        with patch("data.states.can_delete_state", return_value=(True, "")), patch(
            "data.db_connect.delete"
        ) as mock_delete:
            mock_delete.return_value = 0
            assert S.delete_state("XX") is False

    def test_delete_state_with_dependent_cities(self):
        """Test that deleting a state with cities raises ValueError."""
        reason = "Cannot delete: 2 city/cities depend on this state"
        with patch("data.states.can_delete_state", return_value=(False, reason)) as mock_can_delete:
            with pytest.raises(ValueError, match="Cannot delete: 2 city"):
                S.delete_state("NY")
            mock_can_delete.assert_called_once_with("NY")

    def test_can_delete_state_with_dependencies(self):
        """Test can_delete_state returns False when cities exist."""
        with patch("data.states.get_dependent_cities_count", return_value=5):
            can_delete, reason = S.can_delete_state("NY")
            assert can_delete is False
            assert "5 city" in reason

    def test_can_delete_state_no_dependencies(self):
        """Test can_delete_state returns True when no cities exist."""
        with patch("data.states.get_dependent_cities_count", return_value=0):
            can_delete, reason = S.can_delete_state("XX")
            assert can_delete is True
            assert reason == ""

    # ===== Existence check tests =====

    def test_state_exists(self):
        """Test checking if a state exists."""
        with patch("data.states.get_state_by_code") as mock_get:
            mock_get.return_value = S.TEST_STATE
            assert S.state_exists("NY") is True

    # ===== Input Sanitization tests =====

    def test_add_state_sanitizes_whitespace(self, mock_successful_insert):
        """Test that add_state strips whitespace and normalizes codes."""
        with patch("data.states.get_state_by_code") as mock_get, patch(
            "data.db_connect.create", return_value=mock_successful_insert
        ):
            mock_get.return_value = None

            state_data = {
                S.STATE_NAME: "  New York  ",
                S.STATE_CODE: " ny ",
                S.COUNTRY_CODE: " us ",
                S.CAPITAL: "  Albany  ",
            }
            S.add_state(state_data)

            # Verify sanitization
            assert state_data[S.STATE_NAME] == "New York"
            assert state_data[S.STATE_CODE] == "NY"
            assert state_data[S.COUNTRY_CODE] == "US"
            assert state_data[S.CAPITAL] == "Albany"

    def test_add_state_collapses_spaces(self, mock_successful_insert):
        """Test that add_state collapses multiple spaces."""
        with patch("data.states.get_state_by_code") as mock_get, patch(
            "data.db_connect.create", return_value=mock_successful_insert
        ):
            mock_get.return_value = None

            state_data = {
                S.STATE_NAME: "New  York",
                S.STATE_CODE: "NY",
                S.COUNTRY_CODE: "US",
                S.CAPITAL: "Albany  City",
            }
            S.add_state(state_data)

            assert state_data[S.STATE_NAME] == "New York"
            assert state_data[S.CAPITAL] == "Albany City"

    def test_update_state_sanitizes_whitespace(
        self, sample_state, mock_modified_result
    ):
        """Test that update_state sanitizes input fields."""
        with patch("data.states.get_state_by_code", return_value=sample_state), patch(
            "data.db_connect.update", return_value=mock_modified_result
        ):
            update_data = {
                S.STATE_NAME: "  Updated Name  ",
                S.CAPITAL: "  New Capital  ",
            }
            S.update_state("NY", update_data)

            # Verify sanitization occurred
            assert update_data[S.STATE_NAME] == "Updated Name"
            assert update_data[S.CAPITAL] == "New Capital"

