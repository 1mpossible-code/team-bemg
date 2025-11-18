"""
This module provides data layer operations for countries
All country-related database operations should go through this module
"""

import data.db_connect as dbc
from data.utils import sanitize_string, sanitize_code
from datetime import datetime

COUNTRIES_COLLECT = 'countries'

COUNTRY_NAME = 'country_name'
COUNTRY_CODE = 'country_code'
CONTINENT = 'continent'
POPULATION = 'population'
AREA_KM2 = 'area_km2'
CAPITAL = 'capital'

# Continent constants
AFRICA = 'Africa'
ANTARCTICA = 'Antarctica'
ASIA = 'Asia'
EUROPE = 'Europe'
NORTH_AMERICA = 'North America'
OCEANIA = 'Oceania'
SOUTH_AMERICA = 'South America'

VALID_CONTINENTS = [
    AFRICA,
    ANTARCTICA,
    ASIA,
    EUROPE,
    NORTH_AMERICA,
    OCEANIA,
    SOUTH_AMERICA
]

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


def get_countries_by_continent(continent: str) -> list:
    """
    Returns a list of all countries within a specific continent
    """
    return dbc.read_filtered(COUNTRIES_COLLECT, {CONTINENT: continent})


def get_countries_by_population_range(min_pop: int = None, max_pop: int = None) -> list:
    """
    Returns a list of all countries filtered by population range
    """
    query = {}
    if min_pop is not None or max_pop is not None:
        pop_query = {}
        if min_pop is not None:
            pop_query["$gte"] = min_pop
        if max_pop is not None:
            pop_query["$lte"] = max_pop
        query[POPULATION] = pop_query

    return dbc.read_filtered(COUNTRIES_COLLECT, query)


def search_countries_by_name(name_query: str) -> list:
    """
    Search countries by name using partial matching (case-insensitive)
    Returns a list of countries whose names contain the search query
    """
    if not name_query or not name_query.strip():
        return []
    
    # Use MongoDB regex for case-insensitive partial matching
    search_pattern = {"$regex": name_query.strip(), "$options": "i"}
    query = {COUNTRY_NAME: search_pattern}
    
    return dbc.read_filtered(COUNTRIES_COLLECT, query)


def add_country(country_data: dict) -> bool:
    """
    Add a new country to the database
    Returns True if successful, False otherwise
    """
    for field in REQUIRED_FIELDS:
        if field not in country_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Sanitize string fields
    if COUNTRY_NAME in country_data:
        country_data[COUNTRY_NAME] = sanitize_string(country_data[COUNTRY_NAME])
    if COUNTRY_CODE in country_data:
        country_data[COUNTRY_CODE] = sanitize_code(country_data[COUNTRY_CODE])
    if CAPITAL in country_data:
        country_data[CAPITAL] = sanitize_string(country_data[CAPITAL])
    if CONTINENT in country_data:
        country_data[CONTINENT] = sanitize_string(country_data[CONTINENT])
    
    # Validate continent
    if country_data[CONTINENT] not in VALID_CONTINENTS:
        raise ValueError(f"Invalid continent: {country_data[CONTINENT]}. Must be one of {VALID_CONTINENTS}")
    
    if get_country_by_code(country_data[COUNTRY_CODE]):
        raise ValueError(f"Country with code {country_data[COUNTRY_CODE]} already exists")
    
    # Timestamps
    now = datetime.utcnow()
    country_data['created_at'] = now
    country_data['updated_at'] = now

    result = dbc.create(COUNTRIES_COLLECT, country_data)
    return result.acknowledged


def update_country(code: str, update_data: dict) -> bool:
    """
    Update a country by its code
    Returns True if successful, False otherwise
    """
    if not get_country_by_code(code):
        return False
    
    # Sanitize string fields in update
    if COUNTRY_NAME in update_data:
        update_data[COUNTRY_NAME] = sanitize_string(update_data[COUNTRY_NAME])
    if CAPITAL in update_data:
        update_data[CAPITAL] = sanitize_string(update_data[CAPITAL])
    if CONTINENT in update_data:
        update_data[CONTINENT] = sanitize_string(update_data[CONTINENT])
    
    if COUNTRY_CODE in update_data:
        del update_data[COUNTRY_CODE]

    # Set updated_at timestamp
    from datetime import datetime as _dt
    update_data['updated_at'] = _dt.utcnow()

    result = dbc.update(COUNTRIES_COLLECT, {COUNTRY_CODE: code}, update_data)
    return result.modified_count > 0


def get_dependent_states_count(country_code: str) -> int:
    """
    Check how many states belong to this country.
    """
    import data.states as states
    states_list = states.get_states_by_country(country_code)
    return len(states_list)


def can_delete_country(country_code: str) -> tuple[bool, str]:
    """
    Check if country can be safely deleted.
    Returns (can_delete: bool, reason: str)
    """
    dependent_count = get_dependent_states_count(country_code)
    if dependent_count > 0:
        return False, f"Cannot delete: {dependent_count} state(s) depend on this country"
    return True, ""


def delete_country(code: str) -> bool:
    """
    Delete a country by its code.
    Checks for dependent states first.
    Returns True if successful, False otherwise.
    """
    can_delete, reason = can_delete_country(code)
    if not can_delete:
        raise ValueError(reason)
    
    result = dbc.delete(COUNTRIES_COLLECT, {COUNTRY_CODE: code})
    return result > 0


def country_exists(code: str) -> bool:
    """
    Check if a country exists by its code
    """
    return get_country_by_code(code) is not None
