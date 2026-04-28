import os
from enum import StrEnum
from typing import Any

from dotenv import load_dotenv

from .db_connect import connect_db

load_dotenv()

db_name = os.environ.get("DB_NAME", "seDB")


class CONTINENT_ENUM(StrEnum):
    AFRICA = "Africa"
    ANTARCTICA = "Antarctica"
    ASIA = "Asia"
    EUROPE = "Europe"
    NORTH_AMERICA = "North America"
    OCEANIA = "Oceania"
    SOUTH_AMERICA = "South America"


countries_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "country_name",
            "country_code",
            "continent",
            "capital",
            "population",
            "area_km2",
        ],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": ["objectId", "string"]},
            "country_name": {"bsonType": "string", "minLength": 1},
            "country_code": {"bsonType": "string", "pattern": "^[A-Z]{2}$"},
            "continent": {"enum": [member.value for member in CONTINENT_ENUM]},
            "capital": {"bsonType": "string", "minLength": 1},
            "population": {"bsonType": ["int", "long", "decimal"], "minimum": 0},
            "area_km2": {
                "bsonType": ["double", "int", "long", "decimal"],
                "minimum": 0,
            },
            "created_at": {"bsonType": ["date"], "description": "Creation timestamp"},
            "updated_at": {"bsonType": ["date"], "description": "Last update timestamp"},
        },
    }
}

states_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "state_name",
            "state_code",
            "country_code",
            "capital",
            "population",
            "area_km2",
        ],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": ["objectId", "string"]},
            "state_name": {"bsonType": "string", "minLength": 1},
            "state_code": {"bsonType": "string", "pattern": "^[A-Z]{2}$"},
            "country_code": {"bsonType": "string", "pattern": "^[A-Z]{2}$"},
            "capital": {"bsonType": "string", "minLength": 1},
            "population": {"bsonType": ["int", "long", "decimal"], "minimum": 0},
            "area_km2": {
                "bsonType": ["double", "int", "long", "decimal"],
                "minimum": 0,
            },
            "created_at": {"bsonType": ["date"], "description": "Creation timestamp"},
            "updated_at": {"bsonType": ["date"], "description": "Last update timestamp"},
        },
    }
}

cities_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "city_name",
            "state_code",
            "country_code",
            "population",
            "area_km2",
            "coordinates",
        ],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": ["objectId", "string"]},
            "city_name": {"bsonType": "string", "minLength": 1},
            "state_code": {"bsonType": "string", "pattern": "^[A-Z]{2}$"},
            "country_code": {"bsonType": "string", "pattern": "^[A-Z]{2}$"},
            "population": {"bsonType": ["int", "long", "decimal"], "minimum": 0},
            "area_km2": {
                "bsonType": ["double", "int", "long", "decimal"],
                "minimum": 0,
            },
            "coordinates": {
                "bsonType": "object",
                "required": ["latitude", "longitude"],
                "additionalProperties": False,
                "properties": {
                    "latitude": {
                        "bsonType": ["double", "decimal", "int", "long"],
                        "minimum": -90,
                        "maximum": 90,
                    },
                    "longitude": {
                        "bsonType": ["double", "decimal", "int", "long"],
                        "minimum": -180,
                        "maximum": 180,
                    },
                },
            },
            "created_at": {"bsonType": ["date"], "description": "Creation timestamp"},
            "updated_at": {"bsonType": ["date"], "description": "Last update timestamp"},
        },
    }
}

continents_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["continent_name"],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": ["objectId", "string"]},
            "continent_name": {"enum": [m.value for m in CONTINENT_ENUM]},
            "created_at": {"bsonType": ["date"], "description": "Creation timestamp"},
            "updated_at": {"bsonType": ["date"], "description": "Last update timestamp"},
        },
    }
}


def get_db():
    client = connect_db()
    return client[db_name]


def ensure_collection(name: str, validator: dict[str, Any], db=None):
    database = db or get_db()
    exists = name in database.list_collection_names()
    if not exists:
        database.create_collection(
            name,
            validator=validator,
            validationAction="error",
            validationLevel="strict",
        )
    else:
        database.command(
            "collMod",
            name,
            validator=validator,
            validationAction="error",
            validationLevel="strict",
        )


def ensure_indexes(db=None):
    database = db or get_db()
    database.get_collection("continents").create_index(
        "continent_name", unique=True, name="uniq_continent_name"
    )
    database.get_collection("countries").create_index(
        "country_code", unique=True, name="uniq_country_code"
    )
    database.get_collection("states").create_index(
        [("country_code", 1), ("state_code", 1)],
        unique=True,
        name="uniq_state_in_country",
    )
    database.get_collection("cities").create_index(
        [("country_code", 1), ("state_code", 1), ("city_name", 1)],
        unique=True,
        name="uniq_city_name_in_state",
    )


def initialize_database_schema(db=None):
    database = db or get_db()
    ensure_collection("continents", continents_validator, db=database)
    ensure_collection("countries", countries_validator, db=database)
    ensure_collection("states", states_validator, db=database)
    ensure_collection("cities", cities_validator, db=database)
    ensure_indexes(db=database)
