import os
from enum import StrEnum
from typing import Any
from .db_connect import connect_db
from dotenv import load_dotenv

load_dotenv()

db_name = os.environ.get("DB_NAME", "seDB")
client = connect_db()

db = client[db_name]


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
        },
    }
}


def ensure_collection(name: str, validator: dict[str, Any]):
    exists = name in db.list_collection_names()
    if not exists:
        db.create_collection(
            name,
            validator=validator,
            validationAction="error",
            validationLevel="strict",
        )
    else:
        db.command(
            "collMod",
            name,
            validator=validator,
            validationAction="error",
            validationLevel="strict",
        )


ensure_collection("countries", countries_validator)
ensure_collection("states", states_validator)
ensure_collection("cities", cities_validator)

db.get_collection("countries").create_index(
    "country_code", unique=True, name="uniq_country_code"
)
db.get_collection("states").create_index(
    [("country_code", 1), ("state_code", 1)], unique=True, name="uniq_state_in_country"
)
db.get_collection("cities").create_index(
    [("country_code", 1), ("state_code", 1), ("city_name", 1)],
    unique=True,
    name="uniq_city_name_in_state",
)
