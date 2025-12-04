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

### Minimal UI explorer
- `GET /ui/states` → existing state lookup page (manual testing)
- `GET /ui/geo` → “Geo Explorer” page that fetches `/countries`, `/states`, and `/cities` with the same pagination params as the API; useful for sanity checks without Postman.

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

## Seed Mongo with sample data

You can quickly load demo data from JSON backups using the small helper script in `scripts/seed_db.py`.

Backups are expected under `data/bkup/` with names like `games.json`, `users.json`, `countries.json`, `states.json`, `cities.json`. Each file should contain either a single JSON object or a list of objects.

Example usage (from the repo root, with your virtualenv activated):

```bash
python scripts/seed_db.py --dry-run           # show how many docs would be inserted
python scripts/seed_db.py                    # seed all known backups
python scripts/seed_db.py --only countries   # seed just countries from data/bkup/countries.json
```

For a more complete walkthrough (including running MongoDB in Docker and importing a larger slice of the [Countries States Cities Database](https://github.com/dr5hn/countries-states-cities-database/tree/master)), see `docs/LocalMongoTesting.md`.

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

