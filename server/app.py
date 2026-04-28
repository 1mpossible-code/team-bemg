import logging
import os
from collections import deque
from datetime import datetime, timezone
from http import HTTPStatus
from time import monotonic

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_restx import Api

from data import db_connect
from security.security import read as load_security_records

APP_NAME = "Geographic Database API"
APP_VERSION = "v1"
APP_DESCRIPTION = "CRUD for countries, states, cities"
DEFAULT_PORT = 8000
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
APP_START_TIME = monotonic()
LOG_BUFFER = deque(maxlen=200)


class InMemoryLogHandler(logging.Handler):
    """Keep recent log records available for developer diagnostics."""

    def emit(self, record):
        LOG_BUFFER.append(
            {
                "timestamp": datetime.fromtimestamp(record.created, timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
        )


def get_runtime_version() -> str:
    return os.getenv("APP_VERSION", APP_VERSION)


def get_runtime_environment() -> str:
    return os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development"


def get_runtime_port() -> int:
    port_value = os.getenv("PORT", str(DEFAULT_PORT))
    try:
        return int(port_value)
    except ValueError:
        return DEFAULT_PORT


def get_runtime_log_level() -> str:
    log_level = os.getenv("LOG_LEVEL")
    if log_level:
        return log_level.upper()
    return logging.getLevelName(logging.getLogger().getEffectiveLevel())


def get_runtime_cors_origins() -> list[str]:
    return os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")


def get_cache_enabled() -> bool:
    return os.getenv("CACHE_ENABLED", "true").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def get_recent_logs(limit: int = 100) -> list[dict[str, str]]:
    return list(LOG_BUFFER)[-max(1, min(limit, 200)):]


def _database_dependency_status() -> str:
    try:
        client = db_connect.connect_db()
        client.admin.command("ping")
        return "UP"
    except Exception:
        return "DOWN"


def _cache_dependency_status() -> str:
    return "UP" if get_cache_enabled() else "DOWN"


def get_health_payload() -> tuple[dict, HTTPStatus]:
    database_status = _database_dependency_status()
    cache_status = _cache_dependency_status()
    overall_status = "UP" if database_status == "UP" else "DOWN"
    status_code = (
        HTTPStatus.OK if overall_status == "UP" else HTTPStatus.SERVICE_UNAVAILABLE
    )

    payload = {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "uptime_seconds": int(monotonic() - APP_START_TIME),
        "version": get_runtime_version(),
        "dependencies": {
            "database": database_status,
            "cache": cache_status,
        },
    }
    return payload, status_code


def should_initialize_db_schema_on_startup() -> bool:
    return os.getenv("INIT_DB_SCHEMA_ON_STARTUP", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def initialize_db_schema_if_enabled() -> None:
    if not should_initialize_db_schema_on_startup():
        return

    from data.models import initialize_database_schema

    initialize_database_schema()


def register_namespaces(api: Api) -> None:
    """
    Central place to register all Flask-RESTX namespaces.

    This keeps app creation clean and makes it easy to see what routes exist.
    """
    from server.continents_endpoints import continents_ns
    from server.countries_endpoints import countries_ns
    from server.endpoints import general_ns
    from server.states_endpoints import states_ns
    from server.cities_endpoints import cities_ns

    api.add_namespace(continents_ns, path="/continents")
    api.add_namespace(countries_ns, path="/countries")
    api.add_namespace(general_ns, path="")
    api.add_namespace(states_ns, path="/states")
    api.add_namespace(cities_ns, path="/cities")


def create_app():
    app = Flask(__name__)
    # Connection will be established automatically by @ensure_connection
    # when database operations are first used.

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root_logger = logging.getLogger()
    if not any(isinstance(handler, InMemoryLogHandler) for handler in root_logger.handlers):
        root_logger.addHandler(InMemoryLogHandler())

    load_security_records()

    cors_origins = get_runtime_cors_origins()
    CORS(app, resources={r"/*": {"origins": cors_origins}})
    api = Api(
        app,
        title=APP_NAME,
        version=get_runtime_version(),
        description=APP_DESCRIPTION,
    )

    initialize_db_schema_if_enabled()

    # Register API namespaces in one place
    register_namespaces(api)

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, HTTPStatus.OK

    @app.route("/readyz")
    def readyz():
        try:
            # Ensure client is initialized, then ping using the returned client
            client = db_connect.connect_db()
            client.admin.command("ping")
            return {"status": "ok"}, HTTPStatus.OK
        except Exception as exc:
            return (
                {"status": "error", "detail": str(exc)},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    @app.route("/ui/states")
    def ui_states():
        return send_from_directory("static", "states.html"), HTTPStatus.OK

    @app.route("/ui/geo")
    def ui_geo():
        return send_from_directory("static", "geo.html"), HTTPStatus.OK

    return app


app = create_app()
