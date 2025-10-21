from enum import StrEnum
from typing import Any

from .db_connect import connect_db

# --- Connection (set concerns at DB-level) ---
client = connect_db()


db = client["project_db"]


class CONTINENT_ENUM(StrEnum):
    AFRICA = "Africa"
    ANTARCTICA = "Antarctica"
    ASIA = "Asia"
    EUROPE = "Europe"
    NORTH_AMERICA = "North America"
    OCEANIA = "Oceania"
    SOUTH_AMERICA = "South America"


# =========================
# Countries validator
# =========================
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

# =========================
# States validator
# =========================
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

# =========================
# Cities validator
# =========================
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
            # MongoDB JSON Schema requires enum values to be BSON-encodable scalars.
            # Convert the StrEnum to a list of strings and declare the type.
            "continent": {
                "bsonType": "string",
                "enum": [e.value for e in CONTINENT_ENUM],
            },
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


# -------------------------
# Idempotent collection setup
# -------------------------
def ensure_collection(name: str, validator: dict[str, Any]):
    exists = name in db.list_collection_names()
    if not exists:
        db.create_collection(
            name,
            validator=validator,
            validationAction="error",
            validationLevel="strict",
        )
        print(f"Created collection '{name}' with validation.")
    else:
        db.command(
            "collMod",
            name,
            validator=validator,
            validationAction="error",
            validationLevel="strict",
        )
        print(
            f"Updated validator for existing collection '{name}'."
        )  # Apply validators


ensure_collection("countries", countries_validator)
ensure_collection("states", states_validator)
ensure_collection("cities", cities_validator)

# -------------------------
# Idempotent indexes
# -------------------------
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

# If you later store GeoJSON, use this 2dsphere index; for the current lat/long object, skip it.
# db.get_collection("cities").create_index([("location", "2dsphere")], name="geo_idx")

print("Schema validators and indexes are in place.")
# Create a global MongoEngine instance; initialized in app factory via db.init_app(app)

#
# Countries!
# TEST_COUNTRY = {
#     COUNTRY_NAME: 'United States',
#     COUNTRY_CODE: 'US',
#     CONTINENT: 'North America',
#     CAPITAL: 'Washington D.C.',
#     POPULATION: 331000000,
#     AREA_KM2: 9833517
# }
#
#
# ====================================
# CITIES
# TEST_CITY = {
#     CITY_NAME: 'Springfield',
#     STATE_CODE: 'IL',
#     COUNTRY_CODE: 'US',
#     POPULATION: 116000,
#     AREA_KM2: 160,
#     COORDINATES: {
#         LATITUDE: 39.78,
#         LONGITUDE: -89.64
#     }
# }
#
# ====================================
#
# STATES
# TEST_STATE = {
#     STATE_NAME: 'New York',
#     STATE_CODE: 'NY',
#     COUNTRY_CODE: 'US',
#     CAPITAL: 'Albany',
#     POPULATION: 20201249,
#     AREA_KM2: 141297,
# }

#
# ====================================
# CITIES
# TEST_CITY = {
#     CITY_NAME: 'Springfield',
#     STATE_CODE: 'IL',
#     COUNTRY_CODE: 'US',
#     POPULATION: 116000,
#     AREA_KM2: 160,
#     COORDINATES: {
#         LATITUDE: 39.78,
#         LONGITUDE: -89.64
#     }
# }
