#!/usr/bin/env python3
"""
Normalize dr5hn Countries/States/Cities JSON into the schema enforced by
data/models.py (countries/state/city validators).
"""
from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT  # adjust if you keep the raw files elsewhere

COUNTRIES_SRC = INPUT_DIR / "countries.sample.json"
STATES_SRC = INPUT_DIR / "states.sample.json"
CITIES_SRC = INPUT_DIR / "cities.sample.json"

COUNTRIES_OUT = INPUT_DIR / "countries.sample.transformed.json"
STATES_OUT = INPUT_DIR / "states.sample.transformed.json"
CITIES_OUT = INPUT_DIR / "cities.sample.transformed.json"

# Map dr5hn “region” strings into the enum enforced by CONTINENT_ENUM
CONTINENT_MAP = {
    "Africa": "Africa",
    "Asia": "Asia",
    "Europe": "Europe",
    "Oceania": "Oceania",
    "Americas": "North America",   # refined below using subregion
    "Polar": "Antarctica",
    "": "Antarctica",
    None: "Antarctica",
}
AMERICAS_SUBREGION_MAP = {
    "Central America": "North America",
    "Northern America": "North America",
    "Caribbean": "North America",
    "South America": "South America",
}
DEFAULT_CONTINENT = "North America"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: Path, payload):
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)


def safe_number(value, cast=float):
    if value in (None, "", "null"):
        return cast(0)
    try:
        num = cast(value)
    except (TypeError, ValueError):
        return cast(0)
    if isinstance(num, float) and math.isnan(num):
        return cast(0)
    return num


def normalize_countries(raw):
    cleaned = []
    for doc in raw:
        region = doc.get("region")
        subregion = doc.get("subregion")
        continent = CONTINENT_MAP.get(region, DEFAULT_CONTINENT)
        if continent == "North America" and subregion in AMERICAS_SUBREGION_MAP:
            continent = AMERICAS_SUBREGION_MAP[subregion]

        cleaned.append(
            {
                "country_name": doc["name"],
                "country_code": doc["iso2"],
                "continent": continent,
                "capital": doc.get("capital") or "Unknown",
                "population": safe_number(doc.get("population"), int),
                "area_km2": safe_number(doc.get("area") or doc.get("surface_area"), float),
            }
        )
    return cleaned


def normalize_state_code(code, fallback_seed, used):
    letters = "".join(ch for ch in (code or "").upper() if ch.isalpha())
    if len(letters) >= 2:
        base = letters[:2]
    elif letters:
        base = (letters + "X")[:2]
    else:
        base = (fallback_seed[:2].upper() or "XX")
        base = base.ljust(2, "X")

    candidate = base
    suffix = ord("A")
    while candidate in used:
        candidate = base[0] + chr(suffix)
        suffix += 1
        if suffix > ord("Z"):
            candidate = base  # saturate; better dup than crash
            break
    used.add(candidate)
    return candidate


def sanitize_state_code(value: str | None):
    if not value:
        return None
    letters = "".join(ch for ch in str(value).upper() if ch.isalpha())
    if len(letters) >= 2:
        return letters[:2]
    if letters:
        return letters.ljust(2, "X")
    return None


def normalize_states(raw, country_codes):
    cleaned = []
    used_codes = set()
    code_map = {}
    id_map = {}
    for doc in raw:
        country_code = doc.get("country_code")
        if country_code not in country_codes:
            continue  # skip states with unknown parent country

        raw_code = sanitize_state_code(doc.get("state_code") or doc.get("iso2"))
        normalized_code = normalize_state_code(
            raw_code, doc.get("name", ""), used_codes
        )
        if raw_code:
            code_map[(country_code, raw_code)] = normalized_code
        state_id = doc.get("id") or doc.get("state_id")
        if state_id is not None:
            id_map[state_id] = normalized_code
        cleaned.append(
            {
                "state_name": doc["name"],
                "state_code": normalized_code,
                "country_code": country_code,
                "capital": doc.get("capital") or "Unknown",
                "population": safe_number(doc.get("population"), int),
                "area_km2": safe_number(doc.get("area") or doc.get("surface_area"), float),
            }
        )
    return cleaned, code_map, id_map


def normalize_cities(raw, state_code_map, state_id_map):
    cleaned = []
    for doc in raw:
        country_code = doc.get("country_code")
        raw_state_code = sanitize_state_code(doc.get("state_code"))
        normalized_state_code = None
        if raw_state_code:
            normalized_state_code = state_code_map.get(
                (country_code, raw_state_code)
            )
        if not normalized_state_code:
            state_id = doc.get("state_id")
            if state_id is not None:
                normalized_state_code = state_id_map.get(state_id)
        if not normalized_state_code and raw_state_code:
            normalized_state_code = raw_state_code

        coords = {
            "latitude": safe_number(doc.get("latitude"), float),
            "longitude": safe_number(doc.get("longitude"), float),
        }
        cleaned.append(
            {
                "city_name": doc["name"],
                "country_code": doc.get("country_code"),
                **({"state_code": normalized_state_code} if normalized_state_code else {}),
                "population": safe_number(doc.get("population"), int),
                "area_km2": safe_number(doc.get("area") or doc.get("surface_area"), float),
                "coordinates": coords,
            }
        )
    return cleaned


def main():
    countries_raw = load_json(COUNTRIES_SRC)
    states_raw = load_json(STATES_SRC)
    cities_raw = load_json(CITIES_SRC)

    countries = normalize_countries(countries_raw)
    country_codes = {c["country_code"] for c in countries}
    states, state_code_map, state_id_map = normalize_states(states_raw, country_codes)
    cities = normalize_cities(cities_raw, state_code_map, state_id_map)

    dump_json(COUNTRIES_OUT, countries)
    dump_json(STATES_OUT, states)
    dump_json(CITIES_OUT, cities)

    print(f"Wrote {len(countries)} countries -> {COUNTRIES_OUT}")
    print(f"Wrote {len(states)} states     -> {STATES_OUT}")
    print(f"Wrote {len(cities)} cities     -> {CITIES_OUT}")


if __name__ == "__main__":
    main()