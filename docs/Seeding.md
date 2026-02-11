# Seeding MongoDB

Simple steps to load the bundled sample geo data into your local MongoDB.

## Prereqs
- Python deps installed (`pip install -r requirements.txt`)
- MongoDB running locally on `mongodb://localhost:27017` (or set `MONGO_URI` to point elsewhere)

## Seed commands
Run from the repo root with your virtualenv active:

```bash
python scripts/seed_db.py --dry-run           # counts inserts, no writes
python scripts/seed_db.py                    # seed all backups
python scripts/seed_db.py --only countries   # seed a single stem
```

Backups live in `data/bkup/`:
- `countries.json`
- `states.json`
- `cities.json`

Each file is an array of documents matching the API spec. Missing files are skipped automatically.

## Reset the database (optional)
Start fresh before reseeding:

```bash
mongosh "mongodb://localhost:27017" --eval "db.getSiblingDB('seDB').dropDatabase()"
```

## Verify
- API readiness (pings Mongo): `curl http://127.0.0.1:5000/readyz`
- Inspect counts in Mongo if desired: `mongosh --eval "db.getSiblingDB('seDB').countries.countDocuments()"`

## Custom data
If you want different fixtures, drop replacement JSON files under `data/bkup/` with the same stems and rerun the seeder. For a full walkthrough (including downloading and transforming the larger Countries/States/Cities dataset), see `docs/LocalMongoTesting.md`.
