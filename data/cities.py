"""
This module provides data layer operations for cities.
All city-related database operations should go through this module.
"""
import data.db_connect as dbc
from data.utils import sanitize_string, sanitize_code

CITIES_COLLECT = 'cities'

CITY_NAME = 'city_name'
COUNTRY_CODE = 'country_code'
STATE_CODE = 'state_code'
POPULATION = 'population'
AREA_KM2 = 'area_km2'
COORDINATES = 'coordinates'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'

REQUIRED_FIELDS = [CITY_NAME, COUNTRY_CODE]
OPTIONAL_FIELDS = [STATE_CODE, POPULATION, AREA_KM2, COORDINATES]

TEST_CITY = {
    CITY_NAME: 'Springfield',
    STATE_CODE: 'IL',
    COUNTRY_CODE: 'US',
    POPULATION: 116000,
    AREA_KM2: 160,
    COORDINATES: {
        LATITUDE: 39.78,
        LONGITUDE: -89.64
    }
}


def get_cities() -> list:
    """
    Returns a list of all cities
    """
    return dbc.read(CITIES_COLLECT)


def get_cities_by_country(country_code: str) -> list:
    """
    Returns a list of all cities within a specific country
    """
    return dbc.read_filtered(CITIES_COLLECT, {COUNTRY_CODE: country_code})


def get_cities_by_state(state_code: str) -> list:
    """
    Returns a list of all cities within a specific state
    """
    return dbc.read_filtered(CITIES_COLLECT, {STATE_CODE: state_code})


def get_cities_by_population_range(
        min_pop: int = None,
        max_pop: int = None) -> list:
    """
    Returns a list of all cities filtered by population range
    """
    query = {}
    if min_pop is not None or max_pop is not None:
        pop_query = {}
        if min_pop is not None:
            pop_query["$gte"] = min_pop
        if max_pop is not None:
            pop_query["$lte"] = max_pop
        query[POPULATION] = pop_query

    return dbc.read_filtered(CITIES_COLLECT, query)


def get_city_by_name(name: str) -> dict | None:
    """
    Get a specific city by its name.
    Note: If multiple cities have the same name, only the first one is returned.
    """
    return dbc.read_one(CITIES_COLLECT, {CITY_NAME: name})


def get_city_by_name_and_country(name: str, country_code: str) -> dict | None:
    """
    Get a specific city by its name and country code.
    This is more precise than get_city_by_name when multiple cities share a name.
    """
    return dbc.read_one(
        CITIES_COLLECT, {
            CITY_NAME: name, COUNTRY_CODE: country_code})


def get_city_by_name_and_state(name: str, state_code: str) -> dict | None:
    """
    Get a specific city by its name and state code.
    This is the most precise lookup for cities within states.
    """
    return dbc.read_one(
        CITIES_COLLECT, {
            CITY_NAME: name, STATE_CODE: state_code})


def add_city(city_data: dict) -> bool:
    """
    Add a new city to the database
    Returns True if successful, False otherwise
    """
    for field in REQUIRED_FIELDS:
        if field not in city_data:
            raise ValueError(f"Missing required field: {field}")

    # Sanitize string fields
    if CITY_NAME in city_data:
        city_data[CITY_NAME] = sanitize_string(city_data[CITY_NAME])
    if STATE_CODE in city_data:
        city_data[STATE_CODE] = sanitize_code(city_data[STATE_CODE])
    if COUNTRY_CODE in city_data:
        city_data[COUNTRY_CODE] = sanitize_code(city_data[COUNTRY_CODE])

    # Check for duplicate: same name in same state (if state provided)
    if STATE_CODE in city_data:
        existing = get_city_by_name_and_state(
            city_data[CITY_NAME], city_data[STATE_CODE])
        if existing:
            raise ValueError(
                f"City '{
                    city_data[CITY_NAME]}' already exists in state '{
                    city_data[STATE_CODE]}'")
    else:
        # If no state, check by name and country
        existing = get_city_by_name_and_country(
            city_data[CITY_NAME], city_data[COUNTRY_CODE])
        if existing:
            raise ValueError(
                f"City '{
                    city_data[CITY_NAME]}' already exists in country '{
                    city_data[COUNTRY_CODE]}'")

    result = dbc.create(CITIES_COLLECT, city_data)
    return result.acknowledged


def update_city(name: str, state_code: str, update_data: dict) -> bool:
    """
    Update a city by its name and state code
    Returns True if successful, False otherwise
    """
    if not get_city_by_name_and_state(name, state_code):
        return False

    # Sanitize string fields in update
    if COUNTRY_CODE in update_data:
        update_data[COUNTRY_CODE] = sanitize_code(update_data[COUNTRY_CODE])

    # Prevent updating the name or state_code fields directly
    if CITY_NAME in update_data:
        del update_data[CITY_NAME]
    if STATE_CODE in update_data:
        del update_data[STATE_CODE]

    result = dbc.update(
        CITIES_COLLECT, {
            CITY_NAME: name, STATE_CODE: state_code}, update_data)
    return result.modified_count > 0


def update_city_by_name_and_country(
        name: str,
        country_code: str,
        update_data: dict) -> bool:
    """
    Update a city by its name and country code (for cities without state_code)
    Returns True if successful, False otherwise
    """
    if not get_city_by_name_and_country(name, country_code):
        return False

    # Sanitize string fields in update
    if STATE_CODE in update_data:
        update_data[STATE_CODE] = sanitize_code(update_data[STATE_CODE])

    # Prevent updating the name or country_code fields directly
    if CITY_NAME in update_data:
        del update_data[CITY_NAME]
    if COUNTRY_CODE in update_data:
        del update_data[COUNTRY_CODE]

    result = dbc.update(
        CITIES_COLLECT, {
            CITY_NAME: name, COUNTRY_CODE: country_code}, update_data)
    return result.modified_count > 0


def delete_city(name: str, state_code: str) -> bool:
    """
    Delete a city by its name and state code
    Returns True if successful, False otherwise
    """
    result = dbc.delete(
        CITIES_COLLECT, {
            CITY_NAME: name, STATE_CODE: state_code})
    return result > 0


def delete_city_by_name_and_country(name: str, country_code: str) -> bool:
    """
    Delete a city by its name and country code (for cities without state_code)
    Returns True if successful, False otherwise
    """
    result = dbc.delete(
        CITIES_COLLECT, {
            CITY_NAME: name, COUNTRY_CODE: country_code})
    return result > 0


def city_exists(name: str, state_code: str = None,
                country_code: str = None) -> bool:
    """
    Check if a city exists
    If state_code is provided, checks by name + state
    Otherwise checks by name + country if country_code is provided
    """
    if state_code:
        return get_city_by_name_and_state(name, state_code) is not None
    elif country_code:
        return get_city_by_name_and_country(name, country_code) is not None
    else:
        return get_city_by_name(name) is not None


def get_cities_by_name(name_query: str) -> list:
    """
    Search cities by name using partial matching (case-insensitive).
    e.g., 'york' will match 'New York'.
    """
    # Create a case-insensitive regex pattern
    # $regex matches anywhere in the string by default
    query = {CITY_NAME: {"$regex": name_query, "$options": "i"}}
    return dbc.read_filtered(CITIES_COLLECT, query)
