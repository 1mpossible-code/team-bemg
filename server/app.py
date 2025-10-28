from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_restx import Api

from data import db_connect


def create_app():
    app = Flask(__name__)
    client = db_connect.connect_db()

    CORS(app)
    api = Api(
        app,
        title="Geographic Database API",
        version="1.0.0",
        description="CRUD for countries, states, cities",
    )

    # Register API namespaces
    from server.countries_endpoints import countries_ns
    from server.endpoints import general_ns
    from server.states_endpoints import states_ns
    from server.cities_endpoints import cities_ns

    api.add_namespace(countries_ns, path="/countries")
    api.add_namespace(general_ns, path="/")
    api.add_namespace(states_ns, path="/states")
    api.add_namespace(cities_ns, path="/cities")

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.route("/readyz")
    def readyz():
        try:
            # Cheap connectivity check; does not require auth
            client.admin.command("ping")
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}, 500

    @app.route("/ui/states")
    def ui_states():
        return send_from_directory("static", "states.html")

    return app


app = create_app()
