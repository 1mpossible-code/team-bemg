"""
Tests for the countries data module.
"""
import pytest
from unittest.mock import patch, MagicMock
from data import countries


class TestCountries:
    """Test class for countries module."""

    def test_get_countries(self):
        """Test getting all countries."""
        with patch('data.db_connect.read') as mock_read:
            mock_read.return_value = [countries.TEST_COUNTRY]
            result = countries.get_countries()
            mock_read.assert_called_once_with(countries.COUNTRIES_COLLECT)
            assert result == [countries.TEST_COUNTRY]

    def test_get_country_dict(self):
        """Test getting countries as dictionary."""
        with patch('data.db_connect.read_dict') as mock_read_dict:
            expected = {'US': countries.TEST_COUNTRY}
            mock_read_dict.return_value = expected
            result = countries.get_country_dict()
            mock_read_dict.assert_called_once_with(countries.COUNTRIES_COLLECT, countries.COUNTRY_CODE)
            assert result == expected

    def test_get_country_by_code(self):
        """Test getting a country by its code."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = countries.TEST_COUNTRY
            result = countries.get_country_by_code('US')
            mock_read_one.assert_called_once_with(countries.COUNTRIES_COLLECT, {countries.COUNTRY_CODE: 'US'})
            assert result == countries.TEST_COUNTRY

    def test_get_country_by_name(self):
        """Test getting a country by its name."""
        with patch('data.db_connect.read_one') as mock_read_one:
            mock_read_one.return_value = countries.TEST_COUNTRY
            result = countries.get_country_by_name('United States')
            mock_read_one.assert_called_once_with(countries.COUNTRIES_COLLECT, {countries.COUNTRY_NAME: 'United States'})
            assert result == countries.TEST_COUNTRY

    def test_add_country_success(self):
        """Test successfully adding a new country."""
        with patch('data.countries.get_country_by_code') as mock_get, \
             patch('data.db_connect.create') as mock_create:
            mock_get.return_value = None  # Country doesn't exist
            mock_result = MagicMock()
            mock_result.acknowledged = True
            mock_create.return_value = mock_result
            
            result = countries.add_country(countries.TEST_COUNTRY)
            assert result is True
            mock_create.assert_called_once_with(countries.COUNTRIES_COLLECT, countries.TEST_COUNTRY)

    def test_add_country_missing_required_field(self):
        """Test adding a country with missing required field."""
        incomplete_country = {countries.COUNTRY_NAME: 'Test Country'}
        
        with pytest.raises(ValueError, match="Missing required field"):
            countries.add_country(incomplete_country)

    def test_add_country_already_exists(self):
        """Test adding a country that already exists."""
        with patch('data.countries.get_country_by_code') as mock_get:
            mock_get.return_value = countries.TEST_COUNTRY  # Country exists
            
            with pytest.raises(ValueError, match="already exists"):
                countries.add_country(countries.TEST_COUNTRY)

    def test_update_country_success(self):
        """Test successfully updating a country."""
        update_data = {countries.POPULATION: 332000000}
        
        with patch('data.countries.get_country_by_code') as mock_get, \
             patch('data.db_connect.update') as mock_update:
            mock_get.return_value = countries.TEST_COUNTRY
            mock_result = MagicMock()
            mock_result.modified_count = 1
            mock_update.return_value = mock_result
            
            result = countries.update_country('US', update_data)
            assert result is True
            mock_update.assert_called_once_with(countries.COUNTRIES_COLLECT, {countries.COUNTRY_CODE: 'US'}, update_data)

    def test_update_country_not_found(self):
        """Test updating a country that doesn't exist."""
        with patch('data.countries.get_country_by_code') as mock_get:
            mock_get.return_value = None  # Country doesn't exist
            
            result = countries.update_country('XX', {})
            assert result is False

    def test_delete_country_success(self):
        """Test successfully deleting a country."""
        with patch('data.db_connect.delete') as mock_delete:
            mock_delete.return_value = 1  # One document deleted
            
            result = countries.delete_country('US')
            assert result is True
            mock_delete.assert_called_once_with(countries.COUNTRIES_COLLECT, {countries.COUNTRY_CODE: 'US'})

    def test_delete_country_not_found(self):
        """Test deleting a country that doesn't exist."""
        with patch('data.db_connect.delete') as mock_delete:
            mock_delete.return_value = 0  # No documents deleted
            
            result = countries.delete_country('XX')
            assert result is False

    def test_country_exists_true(self):
        """Test checking if a country exists - returns True."""
        with patch('data.countries.get_country_by_code') as mock_get:
            mock_get.return_value = countries.TEST_COUNTRY
            
            result = countries.country_exists('US')
            assert result is True

    def test_country_exists_false(self):
        """Test checking if a country exists - returns False."""
        with patch('data.countries.get_country_by_code') as mock_get:
            mock_get.return_value = None
            
            result = countries.country_exists('XX')
            assert result is False
