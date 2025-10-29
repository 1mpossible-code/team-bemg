"""
This module provides data layer operations for states.
All state-related database operations should go through this module.
"""
import data.db_connect as dbc
from data.utils import sanitize_string, sanitize_code

STATES_COLLECT = 'states'

STATE_NAME = 'state_name'
STATE_CODE = 'state_code'
COUNTRY_CODE = 'country_code'
CAPITAL = 'capital'
POPULATION = 'population'
AREA_KM2 = 'area_km2'

REQUIRED_FIELDS = [STATE_NAME, STATE_CODE, COUNTRY_CODE]
OPTIONAL_FIELDS = [CAPITAL, POPULATION, AREA_KM2]

TEST_STATE = {
    STATE_NAME: 'New York',
    STATE_CODE: 'NY',
    COUNTRY_CODE: 'US',
    CAPITAL: 'Albany',
    POPULATION: 20201249,
    AREA_KM2: 141297,
}


def get_state_dict() -> dict:
    """
    Returns states as a dictionary with state code as key
    """
    return dbc.read_dict(STATES_COLLECT, STATE_CODE)


def get_states() -> list:
    """
    Returns a list of all states
    """
    return dbc.read(STATES_COLLECT)


def get_states_by_country(country_code: str) -> list:
    """
    Returns a list of all states within a specific country
    """
    return dbc.read_filtered(STATES_COLLECT, {COUNTRY_CODE: country_code})


def get_states_by_population_range(min_pop: int = None, max_pop: int = None) -> list:
    """
    Returns a list of all states filtered by population range
    """
    query = {}
    if min_pop is not None or max_pop is not None:
        pop_query = {}
        if min_pop is not None:
            pop_query["$gte"] = min_pop
        if max_pop is not None:
            pop_query["$lte"] = max_pop
        query[POPULATION] = pop_query

    return dbc.read_filtered(STATES_COLLECT, query)


def get_state_by_code(code: str) -> dict | None:
    """
    Returns a state by its code
    """
    return dbc.read_one(STATES_COLLECT, {STATE_CODE: code})


def get_state_by_name(name: str) -> dict | None:
    """
    Get a specific state by its name.
    """
    return dbc.read_one(STATES_COLLECT, {STATE_NAME: name})


def add_state(state_data: dict) -> bool:
    """
    Add a new state to the database
    Returns True if successful, False otherwise
    """
    for field in REQUIRED_FIELDS:
        if field not in state_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Sanitize string fields
    if STATE_NAME in state_data:
        state_data[STATE_NAME] = sanitize_string(state_data[STATE_NAME])
    if STATE_CODE in state_data:
        state_data[STATE_CODE] = sanitize_code(state_data[STATE_CODE])
    if COUNTRY_CODE in state_data:
        state_data[COUNTRY_CODE] = sanitize_code(state_data[COUNTRY_CODE])
    if CAPITAL in state_data:
        state_data[CAPITAL] = sanitize_string(state_data[CAPITAL])
        
    if get_state_by_code(state_data[STATE_CODE]):
        raise ValueError(f"State with code {state_data[STATE_CODE]} already exists")
    
    result = dbc.create(STATES_COLLECT, state_data)
    return result.acknowledged


def update_state(code: str, update_data: dict) -> bool:
    """
    Update a state by its code
    Returns True if successful, False otherwise
    """
    if not get_state_by_code(code):
        return False
    
    # Sanitize string fields in update
    if STATE_NAME in update_data:
        update_data[STATE_NAME] = sanitize_string(update_data[STATE_NAME])
    if COUNTRY_CODE in update_data:
        update_data[COUNTRY_CODE] = sanitize_code(update_data[COUNTRY_CODE])
    if CAPITAL in update_data:
        update_data[CAPITAL] = sanitize_string(update_data[CAPITAL])
    
    if STATE_CODE in update_data:
        del update_data[STATE_CODE]

    result = dbc.update(STATES_COLLECT, {STATE_CODE: code}, update_data)
    return result.modified_count > 0


def get_dependent_cities_count(state_code: str) -> int:
    """
    Check how many cities belong to this state.
    """
    import data.cities as cities
    cities_list = cities.get_cities_by_state(state_code)
    return len(cities_list)


def can_delete_state(state_code: str) -> tuple[bool, str]:
    """
    Check if state can be safely deleted.
    Returns (can_delete: bool, reason: str)
    """
    dependent_count = get_dependent_cities_count(state_code)
    if dependent_count > 0:
        return False, f"Cannot delete: {dependent_count} city/cities depend on this state"
    return True, ""


def delete_state(code: str) -> bool:
    """
    Delete a state by its code.
    Checks for dependent cities first.
    Returns True if successful, False otherwise.
    """
    can_delete, reason = can_delete_state(code)
    if not can_delete:
        raise ValueError(reason)
    
    result = dbc.delete(STATES_COLLECT, {STATE_CODE: code})
    return result > 0


def state_exists(code: str) -> bool:
    """
    Check if a state exists by its code
    """
    return get_state_by_code(code) is not None