from flask import Flask
from flask_restx import Api
from flask_cors import CORS

from data.db_connect import connect_db


def create_app():
    app = Flask(__name__)
    client = connect_db()

    CORS(app)
    api = Api(
        app, title="Geo API",
        version="1.0.0",
        description="CRUD for countries, states, cities")

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.route("/readyz")
    def readyz():
        try:
            # Cheap connectivity check; does not require auth if server allows ping
            client.admin.command("ping")
            return {"status": "ok"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}, 500

    return app


app = create_app()

