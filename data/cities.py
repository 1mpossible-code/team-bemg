"""
This module provides data layer operations for cities.
All city-related database operations should go through this module.
"""
import data.db_connect as dbc
from data.utils import sanitize_string, sanitize_code
from datetime import datetime
from data.cache import city_by_name_state_cache

CITIES_COLLECT = 'cities'

CITY_NAME = 'city_name'
COUNTRY_CODE = 'country_code'
STATE_CODE = 'state_code'
POPULATION = 'population'
AREA_KM2 = 'area_km2'
COORDINATES = 'coordinates'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'
CREATED_AT = 'created_at'
UPDATED_AT = 'updated_at'
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
    },
    CREATED_AT: datetime.now(),
    UPDATED_AT: datetime.now()
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
    key = (name, state_code.upper())
    cached = city_by_name_state_cache.get(key)
    if cached is not None:
        return cached

    city = dbc.read_one(
        CITIES_COLLECT, {
            CITY_NAME: name, STATE_CODE: state_code.upper()})
    if city is not None:
        city_by_name_state_cache.set(key, city)
    return city


def get_cities_filtered(
        name=None,
        state_code=None,
        country_code=None,
        min_pop=None,
        max_pop=None) -> list:
    """
    Returns a list of cities filtered by multiple optional criteria.
    """
    query = {}

    # Partial case-insensitive match
    if name and name.strip():
        query[CITY_NAME] = {"$regex": name.strip(), "$options": "i"}

    # Exact match for state code
    if state_code and state_code.strip():
        query[STATE_CODE] = state_code.upper().strip()

    # Exact match for country code
    if country_code and country_code.strip():
        query[COUNTRY_CODE] = country_code.upper().strip()

    # Population
    if min_pop is not None or max_pop is not None:
        pop_query = {}
        if min_pop is not None:
            pop_query["$gte"] = min_pop
        if max_pop is not None:
            pop_query["$lte"] = max_pop
        query[POPULATION] = pop_query

    return dbc.read_filtered(CITIES_COLLECT, query)


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

    # Validate that state_code exists if provided
    if STATE_CODE in city_data and city_data[STATE_CODE]:
        import data.states as states_module
        if not states_module.state_exists(city_data[STATE_CODE]):
            raise ValueError(
                f"State with code '{city_data[STATE_CODE]}' does not exist")

    # Validate that country_code exists
    import data.countries as countries_module
    if not countries_module.country_exists(city_data[COUNTRY_CODE]):
        raise ValueError(
            f"Country with code '{city_data[COUNTRY_CODE]}' does not exist")

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

    if city_data.get(POPULATION, 0) < 0:
        raise ValueError("Population cannot be negative")

    if city_data.get(AREA_KM2, 0) < 0:
        raise ValueError("Area cannot be negative")

    # Timestamps
    now = datetime.utcnow()
    city_data['created_at'] = now
    city_data['updated_at'] = now

    result = dbc.create(CITIES_COLLECT, city_data)
    if result.acknowledged:
        key = (city_data[CITY_NAME], city_data.get(STATE_CODE, "").upper())
        city_by_name_state_cache.set(key, city_data)
        return True
    return False


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
    # Set updated_at timestamp - strip user value first
    update_data.pop('created_at', None)
    from datetime import datetime as _dt, UTC
    update_data[UPDATED_AT] = _dt.now(UTC)

    result = dbc.update(
        CITIES_COLLECT, {
            CITY_NAME: name, STATE_CODE: state_code}, update_data)
    if result.modified_count > 0:
        city_by_name_state_cache.invalidate((name, state_code.upper()))
        return True
    return False


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
    if result > 0:
        city_by_name_state_cache.invalidate((name, state_code.upper()))
        return True
    return False


def delete_city_by_name_and_country(name: str, country_code: str) -> bool:
    """
    Delete a city by its name and country code (for cities without state_code)
    Returns True if successful, False otherwise
    """
    result = dbc.delete(
        CITIES_COLLECT, {
            CITY_NAME: name, COUNTRY_CODE: country_code})
    return result > 0


def delete_cities_by_state(state_code: str) -> int:
    """
    Delete all cities in a specific state.
    Used for cascading deletes.
    """
    return dbc.delete_many(CITIES_COLLECT, {STATE_CODE: state_code.upper()})


def delete_cities_by_country(country_code: str) -> int:
    """
    Delete all cities in a specific country.
    Used for cascading deletes.
    """
    return dbc.delete_many(CITIES_COLLECT,
                           {COUNTRY_CODE: country_code.upper()})


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
