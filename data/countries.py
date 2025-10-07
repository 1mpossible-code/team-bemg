"""
This module provides data layer operations for countries
All country-related database operations should go through this module
"""

import data.db_connect as dbc

COUNTRIES_COLLECT = 'countries'

COUNTRY_NAME = 'name'
COUNTRY_CODE = 'code'
CONTINENT = 'continent'
POPULATION = 'population'
AREA_KM2 = 'area_km2'
CAPITAL = 'capital'

REQUIRED_FIELDS = [COUNTRY_NAME, COUNTRY_CODE, CONTINENT, CAPITAL]
OPTIONAL_FIELDS = [POPULATION, AREA_KM2]

TEST_COUNTRY = {
    COUNTRY_NAME: 'United States',
    COUNTRY_CODE: 'US',
    CONTINENT: 'North America',
    CAPITAL: 'Washington D.C.',
    POPULATION: 331000000,
    AREA_KM2: 9833517
}


def get_countries() -> list:
    """
    Returns a list of all countries
    """
    return dbc.read(COUNTRIES_COLLECT)


def get_country_dict() -> dict:
    """
    Returns countries as a dictionary with country code as key
    """
    return dbc.read_dict(COUNTRIES_COLLECT, COUNTRY_CODE)


def get_country_by_code(code: str) -> dict:
    """
    Get a specific country by its ISO country code
    """
    return dbc.read_one(COUNTRIES_COLLECT, {COUNTRY_CODE: code})


def get_country_by_name(name: str) -> dict:
    """
    Get a specific country by its name.
    """
    return dbc.read_one(COUNTRIES_COLLECT, {COUNTRY_NAME: name})


def add_country(country_data: dict) -> bool:
    """
    Add a new country to the database
    Returns True if successful, False otherwise
    """
    for field in REQUIRED_FIELDS:
        if field not in country_data:
            raise ValueError(f"Missing required field: {field}")
    
    if get_country_by_code(country_data[COUNTRY_CODE]):
        raise ValueError(f"Country with code {country_data[COUNTRY_CODE]} already exists")
    
    result = dbc.create(COUNTRIES_COLLECT, country_data)
    return result.acknowledged


def update_country(code: str, update_data: dict) -> bool:
    """
    Update a country by its code
    Returns True if successful, False otherwise
    """
    if not get_country_by_code(code):
        return False
    
    if COUNTRY_CODE in update_data:
        del update_data[COUNTRY_CODE]
    
    result = dbc.update(COUNTRIES_COLLECT, {COUNTRY_CODE: code}, update_data)
    return result.modified_count > 0


def delete_country(code: str) -> bool:
    """
    Delete a country by its code
    Returns True if successful, False otherwise
    """
    result = dbc.delete(COUNTRIES_COLLECT, {COUNTRY_CODE: code})
    return result > 0


def country_exists(code: str) -> bool:
    """
    Check if a country exists by its code
    """
    return get_country_by_code(code) is not None
