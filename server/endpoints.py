"""General-purpose API endpoints."""

import os
from http import HTTPStatus

from flask_restx import Resource, Namespace

import data.countries as countries_db
import data.states as states_db
from data.db_connect import CLOUD, LOCAL, SE_DB
from server.app import (
    APP_NAME,
    get_cache_enabled,
    get_runtime_environment,
    get_runtime_log_level,
    get_runtime_port,
    get_runtime_version,
)

# Create namespace for each resource
general_ns = Namespace("general", description="General API operations")
countries_ns = Namespace("countries", description="Operations related to countries")
states_ns = Namespace("states", description="Operations related to states")

# Constants for endpoints and responses
HELLO_EP = "/hello"
HELLO_RESP = "hello"


def _parse_feature_flag(raw_value: str) -> bool | int | str:
    lowered = raw_value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if raw_value.isdigit():
        return int(raw_value)
    return raw_value


def _get_feature_flags() -> dict[str, bool | int | str]:
    feature_flags = {}
    for key, value in os.environ.items():
        if key.startswith("FEATURE_"):
            feature_name = key.removeprefix("FEATURE_").lower()
            feature_flags[feature_name] = _parse_feature_flag(value)
    return dict(sorted(feature_flags.items()))


def _get_build_metadata() -> dict[str, str]:
    metadata_fields = {
        "commit_sha": os.getenv("GIT_SHA"),
        "build_id": os.getenv("BUILD_ID"),
        "release_id": os.getenv("RELEASE_ID"),
        "deploy_id": os.getenv("DEPLOY_ID"),
    }
    return {key: value for key, value in metadata_fields.items() if value}


def _get_safe_database_config() -> dict[str, str | bool]:
    return {
        "name": os.getenv("DB_NAME", SE_DB),
        "mode": "cloud" if os.getenv("CLOUD_MONGO", LOCAL) == CLOUD else "local",
    }


@general_ns.route("/hello")
class HelloWorld(Resource):
    """
    The purpose of the HelloWorld class is to have a simple test to see if the
    app is working at all.
    """

    @general_ns.doc("hello_world")
    def get(self):
        """
        A trivial endpoint to see if the server is running.
        """
        return {"hello": "world"}, HTTPStatus.OK


@countries_ns.route("/")
class CountryList(Resource):
    """
    Handles the endpoint for retrieving a list of all countries.
    """

    def get(self):
        """
        Returns a list of all countries from the data layer.
        """
        return countries_db.get_countries(), HTTPStatus.OK


@states_ns.route("/")
class StateList(Resource):
    """
    Handles the endpoint for retrieving a list of all states
    """

    def get(self):
        """
        Returns a list of all states from the data layer.
        """
        return states_db.get_states(), HTTPStatus.OK


@general_ns.route("/endpoints")
class Endpoints(Resource):
    """
    This class will serve as live, fetchable documentation of what endpoints
    are available in the system.
    """

    @general_ns.doc("list_endpoints")
    def get(self):
        """
        The `get()` method will return a sorted list of available endpoints.
        """
        from flask import current_app

        endpoints = sorted(rule.rule for rule in current_app.url_map.iter_rules())
        return {"Available endpoints": endpoints}


@general_ns.route("/dev/config")
class DevConfig(Resource):
    """Return curated runtime configuration that is safe to expose."""

    def get(self):
        payload = {
            "app_name": APP_NAME,
            "environment": get_runtime_environment(),
            "version": get_runtime_version(),
            "port": get_runtime_port(),
            "log_level": get_runtime_log_level(),
            "feature_flags": _get_feature_flags(),
            "database": _get_safe_database_config(),
            "cache_enabled": get_cache_enabled(),
        }
        build_metadata = _get_build_metadata()
        if build_metadata:
            payload["build"] = build_metadata
        return payload, HTTPStatus.OK
