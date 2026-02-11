"""Minimal script to seed MongoDB with sample data.

This script loads JSON files from `data/bkup/` and inserts them into
MongoDB collections using the existing `data.db_connect` helpers.

It is intentionally small and dependency-free so it can be used as a
quick demo/assignment helper.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

# Ensure repository root is on sys.path so "data" imports work when run directly
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data import db_connect as dbc


# Map JSON filenames (without extension) to Mongo collection names.
# Backups are expected at data/bkup/<stem>.json for each entry here.
FILE_TO_COLLECTION = {
    # Geo data used by the main API
    "countries": "countries",
    "states": "states",
    "cities": "cities",
}


def load_json_file(path: Path) -> Iterable[dict[str, Any]]:
    """Load a JSON file expected to contain a list of documents.

    If the file contains a single object, it is wrapped in a list
    so callers can treat everything as an iterable of documents.
    """

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    return [data]


def seed_collection(json_stem: str, dry_run: bool = False) -> int:
    """Seed a single collection from `data/bkup/<stem>.json`.

    Returns the number of documents that would be/are inserted.
    """

    if json_stem not in FILE_TO_COLLECTION:
        raise ValueError(
            f"Unknown backup stem '{json_stem}'. Update FILE_TO_COLLECTION to map it."
        )

    base_dir = Path(__file__).resolve().parent.parent / "data" / "bkup"
    json_path = base_dir / f"{json_stem}.json"

    if not json_path.exists():
        raise FileNotFoundError(f"Backup file not found: {json_path}")

    docs = list(load_json_file(json_path))
    if not docs:
        return 0

    if dry_run:
        # Just report how many docs would be inserted.
        return len(docs)

    collection = FILE_TO_COLLECTION[json_stem]
    client = dbc.connect_db()
    db = client[dbc.SE_DB]
    coll = db[collection]

    # Use insert_many for efficiency; ignore the returned IDs.
    coll.insert_many(docs)
    return len(docs)


def seed_all(dry_run: bool = False) -> int:
    """Seed all known collections from their JSON backups.

    Returns the total number of documents inserted (or that would be
    inserted in dry-run mode).
    """

    total = 0
    for stem in FILE_TO_COLLECTION:
        try:
            count = seed_collection(stem, dry_run=dry_run)
        except FileNotFoundError:
            # Silently skip missing files so the script works even if
            # some backups are not present.
            continue
        total += count
    return total


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed MongoDB from data/bkup JSON files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not insert anything, just report how many docs would be inserted.",
    )
    parser.add_argument(
        "--only",
        metavar="NAME",
        help=(
            "Only seed the given backup stem (e.g. 'countries', 'states', 'cities'). "
            "Defaults to seeding all known stems."
        ),
    )

    args = parser.parse_args()

    if args.only:
        count = seed_collection(args.only, dry_run=args.dry_run)
    else:
        count = seed_all(dry_run=args.dry_run)

    mode = "(dry run) " if args.dry_run else ""
    print(f"Seeded {count} document(s) {mode}into MongoDB.")


if __name__ == "__main__":  # pragma: no cover
    main()
