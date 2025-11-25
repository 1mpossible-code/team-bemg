"""
Pytest configuration and shared fixtures for all tests.
This ensures database connections are properly mocked for all tests.
"""
import pytest
from unittest.mock import MagicMock, patch

# Global patch that stays active for the entire test session
_connect_db_patcher = None
_default_mock_client = None


def pytest_configure(config):
    """
    Called before tests are collected - set up global mocks.
    This runs early enough to patch before modules are imported.
    """
    global _connect_db_patcher, _default_mock_client

    # Create a default mock client with proper chain setup
    _default_mock_client = MagicMock()
    default_mock_db = MagicMock()
    default_mock_collection = MagicMock()

    _default_mock_client.__getitem__.return_value = default_mock_db
    default_mock_db.__getitem__.return_value = default_mock_collection

    # Mock the admin.command for readyz endpoint (used by server tests)
    _default_mock_client.admin.command.return_value = {"ok": 1}

    # Patch connect_db at the module level so it's ALWAYS mocked
    # This must happen before any imports that use db_connect
    _connect_db_patcher = patch(
        'data.db_connect.connect_db', return_value=_default_mock_client
    )
    _connect_db_patcher.start()

    # Also set the global client to our mock
    import data.db_connect as dbc
    dbc.client = _default_mock_client


def pytest_unconfigure(config):
    """Called after all tests - clean up global mocks."""
    global _connect_db_patcher
    if _connect_db_patcher:
        _connect_db_patcher.stop()
        _connect_db_patcher = None
    import data.db_connect as dbc
    dbc.client = None


@pytest.fixture(autouse=True)
def ensure_mock_client():
    """
    Ensure client is set to a mock before each test.
    This runs before every test and ensures client is not None.
    """
    import data.db_connect as dbc

    # Ensure client is set (tests that patch client will override this)
    if dbc.client is None and _default_mock_client:
        dbc.client = _default_mock_client
    yield
    # Reset after test
    if dbc.client is None and _default_mock_client:
        dbc.client = _default_mock_client
