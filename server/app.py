from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_restx import Api

from data import db_connect

import logging


def register_namespaces(api: Api) -> None:
    """
    Central place to register all Flask-RESTX namespaces.

    This keeps app creation clean and makes it easy to see what routes exist.
    """
    from server.countries_endpoints import countries_ns
    from server.endpoints import general_ns
    from server.states_endpoints import states_ns
    from server.cities_endpoints import cities_ns

    api.add_namespace(countries_ns, path="/countries")
    api.add_namespace(general_ns, path="/")
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

    CORS(app)
    api = Api(
        app,
        title="Geographic Database API",
        version="1.0.0",
        description="CRUD for countries, states, cities",
    )

    # Register API namespaces in one place
    register_namespaces(api)

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.route("/readyz")
    def readyz():
        try:
            # Ensure client is initialized, then ping using the returned client
            client = db_connect.connect_db()
            client.admin.command("ping")
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}, 500

    @app.route("/ui/states")
    def ui_states():
        return send_from_directory("static", "states.html")

    @app.route("/ui/geo")
    def ui_geo():
        return send_from_directory("static", "geo.html")

    return app


app = create_app()
