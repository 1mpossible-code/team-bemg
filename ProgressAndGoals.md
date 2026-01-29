# Progress and Goals

## What’s Completed

### Endpoints and CRUD

- Status: Complete
- Evidence: `server/countries_endpoints.py`, `server/states_endpoints.py`,
  `server/cities_endpoints.py`, `server/endpoints.py`, `server/app.py`
  register CRUD routes for countries, states, and cities with a dozen-plus
  endpoints.
- Requirements met: Create an API server for a geographic database; Implement
  CRUD operations on a related set of data; A dozen or more endpoints.

### MongoDB (Local and Cloud)

- Status: Complete
- Evidence: `data/db_connect.py` connects locally by default and supports Atlas
  via `CLOUD_MONGO`/`ATLAS_MONGO_DB_URI`; `docker-compose.yml` provisions local
  Mongo; `docs/LocalMongoTesting.md` documents setup.
- Requirements met: Use MongoDB locally; Connect to MongoDB in the cloud.

### CI/CD

- Status: Complete
- Evidence: `.github/workflows/main.yml` runs CI with a Mongo service on
  push/PR; deployments are executed through the GitHub Actions workflow to a
  cloud host.
- Requirements met: GitHub Actions; Deployable to the cloud using CI/CD.

### Swagger/OpenAPI

- Status: Complete
- Evidence: Flask-RESTX `Api` in `server/app.py` exposes Swagger UI; detailed
  models and `@doc` usage across `server/countries_endpoints.py`,
  `server/states_endpoints.py`, `server/cities_endpoints.py`.
- Requirements met: Each endpoint documented for Swagger.

### Testing Coverage

- Status: Complete
- Evidence: API tests in `server/tests/` (covering CRUD, timestamps, pagination
  and error paths); data-layer tests in `data/tests/` (including cache
  integration); uses pytest fixtures and `unittest.mock` for isolation.
- Requirements met: Each endpoint and other functions have unit tests; Fancier
  Testing (fixtures and mocking present).

### Caching in RAM

- Status: Complete
- Evidence: `data/cache.py` defines caches used in `data.countries`,
  `data.states`, `data.cities`; caching verified in
  `data/tests/test_cache_integration.py`.
- Requirements met: Data cached in RAM.

### Python Decorators

- Status: Complete
- Evidence: `data/db_connect.ensure_connection` decorator enforces Mongo
  connectivity with reconnect logic; applied to CRUD helpers across
  `data/db_connect.py`.
- Requirements met: Use Python decorators.

### Developer Environment

- Status: Complete
- Evidence: `make dev_env`, `requirements*.txt`, `README.md` setup steps;
  `docker-compose.yml` for Mongo; manual `flask` run instructions.
- Requirements met: Group Dev Env Working.

### Cloud Run / Hosting

- Status: Complete
- Evidence: Deployed and running in the cloud via the CI workflow and cloud
  host configuration.
- Requirements met: Run your API server in the cloud.

# Goals for This Semester

## Frontend

- The application includes a React-based frontend for interacting with the API.
- The application uses environment variables to determine which backend server to connect to.
- The application includes automated tests to verify core UI functionality.

## Backend Enhancements

- The system exposes at least one HATEOAS-style response that includes navigational links to related resources.
- The system provides a developer-only endpoint that is restricted from general users.

## Developer Experience

- The system includes a load script that can populate the database with sample data for development and testing.
