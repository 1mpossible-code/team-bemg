"""Tests for in-memory cache integration in the data layer.

These tests ensure that get-by-code/name functions consult the cache
and that create/update/delete operations invalidate or refresh entries.
"""
from datetime import datetime
from unittest.mock import patch, MagicMock

import data.countries as countries
import data.states as states
import data.cities as cities
from data.cache import (
    country_by_code_cache,
    state_by_code_cache,
    city_by_name_state_cache,
)


def setup_function(function):
    # Clear caches before each test to avoid cross-test interference
    country_by_code_cache.clear()
    state_by_code_cache.clear()
    city_by_name_state_cache.clear()


def test_get_country_by_code_uses_cache():
    """Second call to get_country_by_code should hit cache, not DB."""
    sample = countries.TEST_COUNTRY.copy()

    with patch("data.db_connect.read_one", return_value=sample) as mock_read_one:
        # First call should hit DB
        c1 = countries.get_country_by_code(sample[countries.COUNTRY_CODE])
        assert c1 == sample
        assert mock_read_one.call_count == 1

        # Second call should be served from cache (no new DB calls)
        c2 = countries.get_country_by_code(sample[countries.COUNTRY_CODE])
        assert c2 == sample
        assert mock_read_one.call_count == 1


def test_update_country_invalidates_cache():
    """Updating a country should invalidate its cache entry."""
    code = countries.TEST_COUNTRY[countries.COUNTRY_CODE]
    # Prime cache
    country_by_code_cache.set(code, {"country_code": code, "population": 1})

    with patch("data.countries.get_country_by_code", return_value=True), \
         patch("data.db_connect.update") as mock_update:
        mock_update.return_value = MagicMock(modified_count=1)
        ok = countries.update_country(code, {"population": 2})

    assert ok is True
    # Cache should be cleared
    assert country_by_code_cache.get(code) is None


def test_get_state_by_code_uses_cache():
    sample = states.TEST_STATE.copy()

    with patch("data.db_connect.read_one", return_value=sample) as mock_read_one:
        s1 = states.get_state_by_code(sample[states.STATE_CODE])
        assert s1 == sample
        assert mock_read_one.call_count == 1

        s2 = states.get_state_by_code(sample[states.STATE_CODE])
        assert s2 == sample
        assert mock_read_one.call_count == 1


def test_delete_state_invalidates_cache():
    code = states.TEST_STATE[states.STATE_CODE]
    state_by_code_cache.set(code, states.TEST_STATE.copy())

    with patch("data.states.can_delete_state", return_value=(True, "")), \
         patch("data.db_connect.delete", return_value=1):
        ok = states.delete_state(code)

    assert ok is True
    assert state_by_code_cache.get(code) is None


def test_get_city_by_name_and_state_uses_cache():
    sample = cities.TEST_CITY.copy()
    name = sample[cities.CITY_NAME]
    state_code = sample[cities.STATE_CODE]

    with patch("data.db_connect.read_one", return_value=sample) as mock_read_one:
        c1 = cities.get_city_by_name_and_state(name, state_code)
        assert c1 == sample
        assert mock_read_one.call_count == 1

        c2 = cities.get_city_by_name_and_state(name, state_code)
        assert c2 == sample
        assert mock_read_one.call_count == 1


def test_update_city_invalidates_cache():
    sample = cities.TEST_CITY.copy()
    name = sample[cities.CITY_NAME]
    state_code = sample[cities.STATE_CODE]

    city_by_name_state_cache.set((name, state_code), sample)

    with patch("data.cities.get_city_by_name_and_state", return_value=True), \
         patch("data.db_connect.update") as mock_update:
        mock_update.return_value = MagicMock(modified_count=1)
        ok = cities.update_city(name, state_code, {"population": 999})

    assert ok is True
    assert city_by_name_state_cache.get((name, state_code)) is None
