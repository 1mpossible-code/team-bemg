"""
Data layer operations for continents.
All continent-related database operations should go through this module.
"""

from datetime import UTC, datetime

import data.db_connect as dbc
from data.countries import VALID_CONTINENTS

CONTINENTS_COLLECT = "continents"
CONTINENT_NAME = "continent_name"

REQUIRED_FIELDS = [CONTINENT_NAME]

TEST_CONTINENT = {
    CONTINENT_NAME: "North America",
}


def get_continents() -> list:
    return dbc.read(CONTINENTS_COLLECT)


def get_continent_by_name(name: str) -> dict:
    return dbc.read_one(CONTINENTS_COLLECT, {CONTINENT_NAME: name})


def add_continent(continent_data: dict) -> bool:
    for field in REQUIRED_FIELDS:
        if field not in continent_data:
            raise ValueError(f"Missing required field: {field}")

    if continent_data[CONTINENT_NAME] not in VALID_CONTINENTS:
        raise ValueError(
            f"Invalid continent: {continent_data[CONTINENT_NAME]}. Must be one of {VALID_CONTINENTS}"
        )

    if get_continent_by_name(continent_data[CONTINENT_NAME]):
        raise ValueError(f"Continent '{continent_data[CONTINENT_NAME]}' already exists")

    continent_data.pop("created_at", None)
    continent_data.pop("updated_at", None)
    now = datetime.now(UTC)
    continent_data["created_at"] = now
    continent_data["updated_at"] = now

    result = dbc.create(CONTINENTS_COLLECT, continent_data)
    return result.acknowledged


def update_continent(name: str, update_data: dict) -> bool:
    if not get_continent_by_name(name):
        return False

    update_data.pop("created_at", None)
    update_data[CONTINENT_NAME] = name  # name is not editable via PUT
    update_data["updated_at"] = datetime.now(UTC)

    result = dbc.update(CONTINENTS_COLLECT, {CONTINENT_NAME: name}, update_data)
    return result.modified_count > 0


def delete_continent(name: str) -> bool:
    from data.countries import get_countries_by_continent

    countries = get_countries_by_continent(name)
    if countries:
        raise ValueError(
            f"Cannot delete: {len(countries)} country/countries reference this continent"
        )

    result = dbc.delete(CONTINENTS_COLLECT, {CONTINENT_NAME: name})
    return result > 0
