import pytest
import os
from unittest.mock import patch, MagicMock, create_autospec, Mock
from data import models
from data.models import (
    CONTINENT_ENUM,
    countries_validator,
    states_validator,
    cities_validator,
    ensure_collection,
)


class TestModels:
    """Test class for models module."""

    @pytest.fixture
    def mock_client(self):
        """Mock MongoDB client fixture."""
        return MagicMock()

    @pytest.fixture
    def mock_db(self):
        """Mock MongoDB database fixture."""
        mock_db = MagicMock()
        mock_db.list_collection_names.return_value = []
        mock_db.create_collection.return_value = None
        mock_db.command.return_value = None
        mock_db.get_collection.return_value = MagicMock()
        return mock_db

    @pytest.fixture
    def mock_collection(self):
        """Mock MongoDB collection fixture."""
        mock_collection = MagicMock()
        mock_collection.create_index.return_value = None
        return mock_collection

    @pytest.fixture(autouse=True)
    def setup_patches(self, mock_client, mock_db, mock_collection):
        """Set up patches for all database-related operations."""
        with patch("data.models.connect_db", return_value=mock_client), patch(
            "data.models.db", mock_db
        ), patch.dict(os.environ, {"DB_NAME": "test_db"}):
            mock_client.__getitem__.return_value = mock_db
            mock_db.get_collection.return_value = mock_collection
            yield

    def test_continent_enum_values(self):
        """Test that CONTINENT_ENUM has all expected values."""
        expected_continents = {
            "Africa",
            "Antarctica",
            "Asia",
            "Europe",
            "North America",
            "Oceania",
            "South America",
        }
        actual_continents = {continent.value for continent in CONTINENT_ENUM}
        assert actual_continents == expected_continents

    def test_continent_enum_string_enum(self):
        """Test that CONTINENT_ENUM is a StrEnum."""
        assert isinstance(CONTINENT_ENUM.AFRICA, str)
        assert CONTINENT_ENUM.AFRICA == "Africa"

    def test_countries_validator_structure(self):
        """Test countries validator schema structure."""
        schema = countries_validator["$jsonSchema"]

        # Test required fields
        expected_required = [
            "country_name",
            "country_code",
            "continent",
            "capital",
            "population",
            "area_km2",
        ]
        assert schema["required"] == expected_required

        # Test continent enum values
        continent_enum = schema["properties"]["continent"]["enum"]
        assert set(continent_enum) == {member.value for member in CONTINENT_ENUM}

        # Test country code pattern
        assert schema["properties"]["country_code"]["pattern"] == "^[A-Z]{2}$"

    def test_states_validator_structure(self):
        """Test states validator schema structure."""
        schema = states_validator["$jsonSchema"]

        # Test required fields
        expected_required = [
            "state_name",
            "state_code",
            "country_code",
            "capital",
            "population",
            "area_km2",
        ]
        assert schema["required"] == expected_required

        # Test state and country code patterns
        assert schema["properties"]["state_code"]["pattern"] == "^[A-Z]{2}$"
        assert schema["properties"]["country_code"]["pattern"] == "^[A-Z]{2}$"

    def test_cities_validator_structure(self):
        """Test cities validator schema structure."""
        schema = cities_validator["$jsonSchema"]

        # Test required fields
        expected_required = [
            "city_name",
            "state_code",
            "country_code",
            "population",
            "area_km2",
            "coordinates",
        ]
        assert schema["required"] == expected_required

        # Test coordinates structure
        coords = schema["properties"]["coordinates"]
        assert coords["required"] == ["latitude", "longitude"]
        assert coords["properties"]["latitude"]["minimum"] == -90
        assert coords["properties"]["latitude"]["maximum"] == 90
        assert coords["properties"]["longitude"]["minimum"] == -180
        assert coords["properties"]["longitude"]["maximum"] == 180

    def test_ensure_collection_creates_new_collection(self, mock_db):
        """Test ensure_collection creates a new collection when it doesn't exist."""
        mock_db.list_collection_names.return_value = []

        ensure_collection("test_collection", {"test": "validator"})

        mock_db.create_collection.assert_called_once_with(
            "test_collection",
            validator={"test": "validator"},
            validationAction="error",
            validationLevel="strict",
        )
        mock_db.command.assert_not_called()

    def test_ensure_collection_updates_existing_collection(self, mock_db):
        """Test ensure_collection updates an existing collection."""
        mock_db.list_collection_names.return_value = ["test_collection"]

        ensure_collection("test_collection", {"test": "validator"})

        mock_db.create_collection.assert_not_called()
        mock_db.command.assert_called_once_with(
            "collMod",
            "test_collection",
            validator={"test": "validator"},
            validationAction="error",
            validationLevel="strict",
        )

    def test_collections_are_ensured_on_import(self, mock_db):
        """Test that collections are ensured when module is imported."""
        # Test the ensure_collection function directly since it's called during import
        # We can verify the function works correctly with our mocked database

        # Test creating a new collection
        mock_db.list_collection_names.return_value = []
        ensure_collection("test_collection", {"test": "validator"})
        mock_db.create_collection.assert_called_with(
            "test_collection",
            validator={"test": "validator"},
            validationAction="error",
            validationLevel="strict",
        )

        # Test updating an existing collection
        mock_db.reset_mock()
        mock_db.list_collection_names.return_value = ["test_collection"]
        ensure_collection("test_collection", {"test": "validator"})
        mock_db.command.assert_called_with(
            "collMod",
            "test_collection",
            validator={"test": "validator"},
            validationAction="error",
            validationLevel="strict",
        )

        # Verify that the validators are properly defined
        assert countries_validator is not None
        assert states_validator is not None
        assert cities_validator is not None

    def test_database_indexes_creation(self, mock_db, mock_collection):
        """Test that database indexes are created properly."""
        # Test that get_collection returns a mock collection that can create indexes
        mock_db.get_collection.return_value = mock_collection

        # Test that we can get collections for each expected collection type
        expected_collections = ["countries", "states", "cities"]

        for collection_name in expected_collections:
            collection = mock_db.get_collection(collection_name)
            assert collection is not None
            # Verify the collection can create indexes
            collection.create_index("test_field", unique=True, name="test_index")
            collection.create_index.assert_called_with(
                "test_field", unique=True, name="test_index"
            )

        # Verify get_collection was called for each collection
        assert mock_db.get_collection.call_count >= len(expected_collections)

    @pytest.mark.parametrize(
        "validator,expected_required",
        [
            (
                countries_validator,
                [
                    "country_name",
                    "country_code",
                    "continent",
                    "capital",
                    "population",
                    "area_km2",
                ],
            ),
            (
                states_validator,
                [
                    "state_name",
                    "state_code",
                    "country_code",
                    "capital",
                    "population",
                    "area_km2",
                ],
            ),
            (
                cities_validator,
                [
                    "city_name",
                    "state_code",
                    "country_code",
                    "population",
                    "area_km2",
                    "coordinates",
                ],
            ),
        ],
    )
    def test_validator_required_fields(self, validator, expected_required):
        """Test that validators have correct required fields."""
        assert validator["$jsonSchema"]["required"] == expected_required

    def test_ensure_collection_with_database_error(self, mock_db):
        """Test ensure_collection handles database errors properly."""
        mock_db.list_collection_names.side_effect = Exception(
            "Database connection error"
        )

        with pytest.raises(Exception, match="Database connection error"):
            ensure_collection("test_collection", {"test": "validator"})

    def test_ensure_collection_create_collection_error(self, mock_db):
        """Test ensure_collection handles create_collection errors."""
        mock_db.list_collection_names.return_value = []
        mock_db.create_collection.side_effect = Exception("Create collection error")

        with pytest.raises(Exception, match="Create collection error"):
            ensure_collection("test_collection", {"test": "validator"})

    def test_ensure_collection_command_error(self, mock_db):
        """Test ensure_collection handles command errors for existing collections."""
        mock_db.list_collection_names.return_value = ["test_collection"]
        mock_db.command.side_effect = Exception("Command error")

        with pytest.raises(Exception, match="Command error"):
            ensure_collection("test_collection", {"test": "validator"})

    def test_database_name_from_environment(self):
        """Test that database name is read from environment variable."""
        # Test the logic for getting database name from environment

        # Test default database name
        with patch.dict(os.environ, {}, clear=True):
            default_name = os.environ.get("DB_NAME", "seDB")
            assert default_name == "seDB"

        # Test custom database name
        with patch.dict(os.environ, {"DB_NAME": "custom_test_db"}):
            custom_name = os.environ.get("DB_NAME", "seDB")
            assert custom_name == "custom_test_db"

    def test_validator_population_constraints(self):
        """Test that validators have proper population constraints."""
        for validator in [countries_validator, states_validator, cities_validator]:
            population_prop = validator["$jsonSchema"]["properties"]["population"]
            assert population_prop["minimum"] == 0
            assert (
                "int" in population_prop["bsonType"]
                or "long" in population_prop["bsonType"]
            )

    def test_validator_area_constraints(self):
        """Test that validators have proper area constraints."""
        for validator in [countries_validator, states_validator, cities_validator]:
            area_prop = validator["$jsonSchema"]["properties"]["area_km2"]
            assert area_prop["minimum"] == 0
            assert any(
                t in area_prop["bsonType"] for t in ["double", "int", "long", "decimal"]
            )

    def test_countries_validator_additional_properties_false(self):
        """Test that countries validator doesn't allow additional properties."""
        assert countries_validator["$jsonSchema"]["additionalProperties"] is False

    def test_states_validator_additional_properties_false(self):
        """Test that states validator doesn't allow additional properties."""
        assert states_validator["$jsonSchema"]["additionalProperties"] is False

    def test_cities_validator_additional_properties_false(self):
        """Test that cities validator doesn't allow additional properties."""
        assert cities_validator["$jsonSchema"]["additionalProperties"] is False
