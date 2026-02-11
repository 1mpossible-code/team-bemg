"""Tests for the scripts.seed_db helper.

These tests focus on behaviour that is independent of a real MongoDB
instance by mocking out the database connection and filesystem.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import scripts.seed_db as seed


def test_load_json_file_list(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    path.write_text('[{"a": 1}, {"b": 2}]', encoding="utf-8")

    docs = list(seed.load_json_file(path))
    assert docs == [{"a": 1}, {"b": 2}]


def test_load_json_file_single_object(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    path.write_text('{"a": 1}', encoding="utf-8")

    docs = list(seed.load_json_file(path))
    assert docs == [{"a": 1}]


def test_seed_collection_inserts_docs(monkeypatch, tmp_path: Path) -> None:
    # Arrange: temporary backup directory with a small JSON file
    backup_dir = tmp_path / "data" / "bkup"
    backup_dir.mkdir(parents=True)
    json_path = backup_dir / "countries.json"
    json_path.write_text(
        '[{"country_name": "Testland", "country_code": "TL", "continent": "Europe", "capital": "Test City"}]',
        encoding="utf-8",
    )

    # Patch Path resolution inside seed_db so it points to our temp dir
    def fake_resolve(self):  # pragma: no cover - trivial shim
        # pretend that __file__ lives under tmp_path/scripts/seed_db.py
        return tmp_path / "scripts" / "seed_db.py"

    monkeypatch.setattr(Path, "resolve", fake_resolve, raising=False)

    # Mock DB connection
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_client.__getitem__.return_value = mock_db

    with patch("data.db_connect.connect_db", return_value=mock_client):
        inserted = seed.seed_collection("countries", dry_run=False)

    assert inserted == 1
    mock_client.__getitem__.assert_called_once_with(seed.dbc.SE_DB)
    mock_db.__getitem__.assert_called_once_with("countries")
    mock_coll.insert_many.assert_called_once()
    args, _ = mock_coll.insert_many.call_args
    assert args[0] == [
        {
            "country_name": "Testland",
            "country_code": "TL",
            "continent": "Europe",
            "capital": "Test City",
        }
    ]


def test_seed_collection_dry_run(monkeypatch, tmp_path: Path) -> None:
    backup_dir = tmp_path / "data" / "bkup"
    backup_dir.mkdir(parents=True)
    json_path = backup_dir / "states.json"
    json_path.write_text(
        '[{"state_name": "Foo", "state_code": "FO", "country_code": "TL"}, {"state_name": "Bar", "state_code": "BA", "country_code": "TL"}]',
        encoding="utf-8",
    )

    def fake_resolve(self):  # pragma: no cover - trivial shim
        return tmp_path / "scripts" / "seed_db.py"

    monkeypatch.setattr(Path, "resolve", fake_resolve, raising=False)

    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_client.__getitem__.return_value = mock_db

    with patch("data.db_connect.connect_db", return_value=mock_client):
        inserted = seed.seed_collection("states", dry_run=True)
    assert inserted == 2


def test_seed_all_skips_missing_files(monkeypatch, tmp_path: Path) -> None:
    # Only create countries.json so other files are missing
    backup_dir = tmp_path / "data" / "bkup"
    backup_dir.mkdir(parents=True)
    json_path = backup_dir / "countries.json"
    json_path.write_text(
        '[{"country_name": "Testland", "country_code": "TL", "continent": "Europe", "capital": "Test City"}]',
        encoding="utf-8",
    )

    def fake_resolve(self):  # pragma: no cover - trivial shim
        return tmp_path / "scripts" / "seed_db.py"

    monkeypatch.setattr(Path, "resolve", fake_resolve, raising=False)

    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_client.__getitem__.return_value = mock_db

    with patch("data.db_connect.connect_db", return_value=mock_client):
        total = seed.seed_all(dry_run=False)

    # Only countries.json should have been inserted
    assert total == 1
    mock_client.__getitem__.assert_called_once_with(seed.dbc.SE_DB)
    mock_db.__getitem__.assert_called_once_with("countries")
    mock_coll.insert_many.assert_called_once()  # for countries only
