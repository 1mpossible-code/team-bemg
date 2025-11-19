# Local MongoDB Testing With Sample Country/State/City Data

Use this guide to spin up MongoDB locally (via Docker), import a tiny slice of the [Countries States Cities Database](https://github.com/dr5hn/countries-states-cities-database/tree/master), and exercise the CRUD endpoints.

## 1. Start MongoDB in Docker

1. Copy any required secrets for `docker-compose.yml` (only needed if you want a root user):
   ```sh
   setx MONGO_ROOT_USERNAME root
   setx MONGO_ROOT_PASSWORD someStrongPassword
   ```
2. From the repo root run:
   ```sh
   docker compose up -d mongodb
   ```
   This publishes Mongo on `localhost:27017`.
3. Verify the container is healthy:
   ```sh
   docker ps --filter name=mongodb
   ```

## 2. Download Sample JSON Files

Use the GitHub API (rather than raw.githubusercontent) so you can authenticate and avoid rate limits. Any personal access token with no scopes works.

```sh
mkdir -p tmp/csc && cd tmp/csc
export GITHUB_TOKEN=ghp_yourTokenHere
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -o countries.json \
     https://api.github.com/repos/dr5hn/countries-states-cities-database/contents/json/countries.json
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -o states.json \
     https://api.github.com/repos/dr5hn/countries-states-cities-database/contents/json/states.json
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github.v3.raw" \
     -o cities.json.gz \
     https://api.github.com/repos/dr5hn/countries-states-cities-database/contents/json/cities.json.gz
gunzip -f cities.json.gz
```

PowerShell equivalent:

```powershell
mkdir tmp\csc; cd tmp\csc
$env:GITHUB_TOKEN = "ghp_yourTokenHere"
Invoke-WebRequest -Headers @{Authorization = "Bearer $env:GITHUB_TOKEN"; Accept = "application/vnd.github.v3.raw"} `
    -Uri https://api.github.com/repos/dr5hn/countries-states-cities-database/contents/json/countries.json `
    -OutFile countries.json
Invoke-WebRequest -Headers @{Authorization = "Bearer $env:GITHUB_TOKEN"; Accept = "application/vnd.github.v3.raw"} `
    -Uri https://api.github.com/repos/dr5hn/countries-states-cities-database/contents/json/states.json `
    -OutFile states.json
Invoke-WebRequest -Headers @{Authorization = "Bearer $env:GITHUB_TOKEN"; Accept = "application/vnd.github.v3.raw"} `
    -Uri https://api.github.com/repos/dr5hn/countries-states-cities-database/contents/json/cities.json.gz `
    -OutFile cities.json.gz
tar -xf cities.json.gz  # or use 7zip / gzip -d; rename the result to cities.json if needed
```

## 3. Create Consistent Samples

We want US data every time, so slice the files with `jq` (bash) or `ConvertFrom-Json` (PowerShell) before normalizing:

```sh
# Countries: include US plus the first 25 records
jq '([.[] | select(.iso2 == "US")] + .[:25]) | unique_by(.iso2)' \
    countries.json > countries.sample.json
# States: include 100 US states plus 50 generic entries (dedupe by iso2)
jq '([.[] | select(.country_code == "US")] | .[:100]) + (.[:50])
    | unique_by(.iso2)' \
    states.json > states.sample.json
# Cities: include 100 US cities plus 100 generic entries (keep state_code per data/cities.py)
jq '([.[] | select(.country_code == "US")] | .[:100]) + (.[:100])
    | unique_by({country_code, state_code, name})' \
    cities.json > cities.sample.json
```

PowerShell version (roughly equivalent):

```powershell
$countries = Get-Content countries.json | ConvertFrom-Json
($countries | Where-Object iso2 -eq 'US') + ($countries | Select-Object -First 25) |
    Group-Object iso2 | ForEach-Object { $_.Group[0] } |
    ConvertTo-Json | Set-Content countries.sample.json

$states = Get-Content states.json | ConvertFrom-Json
($states | Where-Object country_code -eq 'US' | Select-Object -First 100) +
($states | Select-Object -First 50) |
    Group-Object iso2 | ForEach-Object { $_.Group[0] } |
    ConvertTo-Json | Set-Content states.sample.json

$cities = Get-Content cities.json | ConvertFrom-Json
($cities | Where-Object country_code -eq 'US' | Select-Object -First 100) +
($cities | Select-Object -First 100) |
    Group-Object { "$($_.name)|$($_.state_code)" } | ForEach-Object { $_.Group[0] } |
    ConvertTo-Json | Set-Content cities.sample.json
```

## 4. Normalize to Our Schema

Run the helper script (`tmp/csc/transform.py`) to map the dr5hn field names to the schema enforced by `data/models.py`. It produces `*.transformed.json`.

```sh
python tmp/csc/transform.py
```

Per `data/cities.py`, `state_code` is required for most lookups, so the transform keeps the raw `state_code` from `cities.json` whenever possible and falls back to the `state_id`→code mapping derived from `states.json` when needed. You should now see `state_code` populated for every city whose upstream data includes it.

> **Known limitation:** the upstream dr5hn dataset does not provide reliable `population`, `area_km2`, or `capital` data for states and cities (and even for countries the `area_km2` field is often missing). For now these values are zero-filled in the sample import strictly to exercise the API and connection logic. If we want meaningful analytics, we either need to relax the validators in `data/states.py` / `data/cities.py` / `data/countries.py` or source richer reference data that includes those fields.

## 5. Import Into MongoDB

Reset the database (optional but recommended between runs), then import the transformed payloads:

Point the samples at your local database (`seDB` is the default configured by the app):

```sh
mongosh "mongodb://localhost:27017/seDB" --eval "db.dropDatabase()"   # optional reset
mongoimport --uri "mongodb://localhost:27017" --db seDB --collection countries \
  --file countries.sample.transformed.json --jsonArray
mongoimport --uri "mongodb://localhost:27017" --db seDB --collection states \
  --file states.sample.transformed.json --jsonArray
mongoimport --uri "mongodb://localhost:27017" --db seDB --collection cities \
  --file cities.sample.transformed.json --jsonArray
```

## 6. Inspect Your Data

Use `mongosh` to verify what’s loaded:

```sh
mongosh "mongodb://localhost:27017"
use seDB
db.countries.countDocuments()
db.states.findOne({ country_code: "US" })
db.cities.find({ country_code: "US" }).limit(3)
```

## 7. Run the API Against Local Mongo

1. Create a `.env` in the repo root (or export variables):
   ```sh
   echo "MONGO_URI=mongodb://localhost:27017" >> .env
   echo "DB_NAME=seDB" >> .env
   ```
   The server will automatically pick up `MONGO_URI`; `DB_NAME` defaults to `seDB` if unset.
2. Start the Flask server:
   ```sh
   python -m flask --app server.app:app run
   ```
3. Hit readiness to ensure the API can reach Mongo:
   ```
   curl http://127.0.0.1:5000/readyz
   ```

## 8. Exercise CRUD Endpoints

```sh
# List countries
curl http://127.0.0.1:5000/countries
# Insert a new state
curl -X POST http://127.0.0.1:5000/states -H "Content-Type: application/json" -d '{"state_name":"Test State","state_code":"TS","country_code":"US","capital":"Testville","population":1000,"area_km2":10}'
# Update a city
curl -X PUT http://127.0.0.1:5000/cities/NY/New%20York -H "Content-Type: application/json" -d '{"population":9999999}'
# Delete a city
curl -X DELETE http://127.0.0.1:5000/cities/NY/New%20York
```

Because the sample dataset is tiny, you can freely create/update/delete records without affecting production data. When you want a clean slate, drop the database and re-run the `mongoimport` commands.

