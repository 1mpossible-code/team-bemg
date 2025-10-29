"""
Tests for the data utils module.
"""
import pytest
from data.utils import sanitize_string, sanitize_code


class TestUtils:
    """Test class for utility functions."""

    # ===== sanitize_string tests =====

    def test_sanitize_string_strips_leading_whitespace(self):
        """Test that leading whitespace is removed."""
        assert sanitize_string("  Hello") == "Hello"

    def test_sanitize_string_strips_trailing_whitespace(self):
        """Test that trailing whitespace is removed."""
        assert sanitize_string("Hello  ") == "Hello"

    def test_sanitize_string_strips_both_whitespace(self):
        """Test that both leading and trailing whitespace are removed."""
        assert sanitize_string("  Hello  ") == "Hello"

    def test_sanitize_string_collapses_multiple_spaces(self):
        """Test that multiple consecutive spaces are collapsed to one."""
        assert sanitize_string("Hello  World") == "Hello World"
        assert sanitize_string("Hello   World") == "Hello World"
        assert sanitize_string("Hello    World") == "Hello World"

    def test_sanitize_string_handles_tabs(self):
        """Test that tabs are normalized to single space."""
        assert sanitize_string("Hello\tWorld") == "Hello World"
        assert sanitize_string("Hello\t\tWorld") == "Hello World"

    def test_sanitize_string_handles_newlines(self):
        """Test that newlines are normalized to single space."""
        assert sanitize_string("Hello\nWorld") == "Hello World"
        assert sanitize_string("Hello\n\nWorld") == "Hello World"

    def test_sanitize_string_handles_mixed_whitespace(self):
        """Test that mixed whitespace types are normalized."""
        assert sanitize_string("  Hello \t\n World  ") == "Hello World"

    def test_sanitize_string_empty_string(self):
        """Test that empty string remains empty."""
        assert sanitize_string("") == ""

    def test_sanitize_string_only_whitespace(self):
        """Test that string with only whitespace becomes empty."""
        assert sanitize_string("   ") == ""
        assert sanitize_string("\t\n") == ""

    def test_sanitize_string_preserves_single_words(self):
        """Test that single words are preserved correctly."""
        assert sanitize_string("Hello") == "Hello"

    def test_sanitize_string_non_string_returns_as_is(self):
        """Test that non-string values are returned unchanged."""
        assert sanitize_string(123) == 123
        assert sanitize_string(None) is None
        assert sanitize_string([1, 2, 3]) == [1, 2, 3]

    # ===== sanitize_code tests =====

    def test_sanitize_code_converts_to_uppercase(self):
        """Test that lowercase is converted to uppercase."""
        assert sanitize_code("us") == "US"
        assert sanitize_code("ny") == "NY"

    def test_sanitize_code_strips_whitespace(self):
        """Test that whitespace is stripped."""
        assert sanitize_code("  us  ") == "US"
        assert sanitize_code(" ny ") == "NY"

    def test_sanitize_code_mixed_case(self):
        """Test that mixed case is normalized to uppercase."""
        assert sanitize_code("Us") == "US"
        assert sanitize_code("Ny") == "NY"
        assert sanitize_code("nY") == "NY"

    def test_sanitize_code_strips_and_uppercases(self):
        """Test that both stripping and uppercasing happen."""
        assert sanitize_code(" us ") == "US"
        assert sanitize_code("  ny  ") == "NY"

    def test_sanitize_code_preserves_uppercase(self):
        """Test that already uppercase codes are preserved."""
        assert sanitize_code("US") == "US"
        assert sanitize_code("NY") == "NY"

    def test_sanitize_code_empty_string(self):
        """Test that empty string remains empty."""
        assert sanitize_code("") == ""

    def test_sanitize_code_only_whitespace(self):
        """Test that string with only whitespace becomes empty."""
        assert sanitize_code("   ") == ""

    def test_sanitize_code_non_string_returns_as_is(self):
        """Test that non-string values are returned unchanged."""
        assert sanitize_code(123) == 123
        assert sanitize_code(None) is None
        assert sanitize_code([1, 2, 3]) == [1, 2, 3]

