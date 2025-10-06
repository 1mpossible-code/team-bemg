# flask-api
An example flask rest API server.

To build production, type `make prod`.

To create the env for a new developer, run `make dev_env`.

## Getting started (local dev)

1. Python virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

2. Install dependencies
```
pip install -r requirements.txt
```

3. Run the API (from repo root)
```
python -m flask --app server.app:app run
```
Visit `http://127.0.0.1:5000/healthz` and Swagger docs at the Flask-RESTX UI (root or `/` depending on config).

### Health and readiness
- `GET /healthz` → simple liveness check returns `{"status": "ok"}`
- `GET /readyz` → pings MongoDB and returns 200 if reachable (implemented in `server/app.py`)

## Testing
Run the test suite from the repo root:
```
pytest -q
```
If Python cannot import top-level packages during tests, ensure `pytest.ini` exists with `pythonpath = .` and run from the project root.

## MongoDB configuration
The app uses `data/db_connect.py`.

- Local (default): connects to a local `mongod` without auth.
- Cloud (Atlas): set environment variables before running:
```
export CLOUD_MONGO=1
export MONGO_PASSWD=<your_password>
```
- Custom URI (recommended if your local Mongo requires auth):
```
export MONGO_URI='mongodb://<user>:<pass>@localhost:27017/?authSource=admin'
```

## Common issues
- Module import errors (e.g., `No module named server`): run commands from the repo root or set `PYTHONPATH=.`
- Wheel/architecture mismatch on macOS: recreate the virtualenv with your native Python and reinstall deps (see troubleshooting in PRs or ask a teammate).

## CI
GitHub Actions workflow runs tests on push/PR (see `.github/workflows/`). Ensure the suite passes locally before pushing.

## Deployment (Heroku)
1. Add a Procfile:
```
web: gunicorn server.app:app
```
2. Add `gunicorn` to `requirements.txt` and push to Heroku (GitHub integration or `git push heroku master`).
3. Configure env vars in Heroku Settings → Config Vars (e.g., `MONGO_URI` or `CLOUD_MONGO`, `MONGO_PASSWD`).

## Project structure (high-level)
- `server/app.py`: Flask app factory, health/ready endpoints
- `server/endpoints.py`: example endpoints (Hello, endpoints list)
- `data/db_connect.py`: Mongo connection and CRUD helpers
- `server/tests/`: API tests
- `examples/`, `security/`: example modules and tests

