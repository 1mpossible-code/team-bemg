"""
Shared helpers for Flask-RESTX endpoints.

Provides:
- Consistent JSON response structure helpers.
- Shared pagination helpers used by multiple resources.
"""

from http import HTTPStatus
from typing import Any, Iterable, Tuple, TypeVar

from flask import jsonify

T = TypeVar("T")


def ok(data: Any, status: HTTPStatus = HTTPStatus.OK):
    """
    Return a standard successful JSON response.

    Keeps existing tests working by defaulting to the plain data object
    (no wrapping) while still going through Flask's jsonify for safety.
    """
    return jsonify(data), status


def error(message: str,
          status: HTTPStatus) -> Tuple[dict[str, Any], HTTPStatus]:
    """
    Return a simple error payload with a message and HTTP status code.

    Individual namespaces can still use their own abort / error models;
    this is mainly for non-RESTX routes or quick helpers.
    """
    payload = {"error": message, "code": int(status)}
    return payload, status


def apply_pagination(
    results: Iterable[T], limit: int | None, offset: int | None
) -> list[T]:
    """
    Apply simple offset/limit pagination to a sequence or iterable.

    Converts input to a list so results can be reused safely.
    """
    items = list(results)
    if offset:
        items = items[offset:]
    if limit:
        items = items[:limit]
    return items


def validate_pagination(
    limit: int | None, offset: int | None, abort_func
) -> None:
    """
    Shared validation logic for limit/offset parameters.

    `abort_func` should be a namespace-specific abort,
    e.g. `countries_ns.abort`.
    """
    if limit is not None and limit <= 0:
        abort_func(HTTPStatus.BAD_REQUEST, "limit must be a positive integer")
    if offset is not None and offset < 0:
        abort_func(
            HTTPStatus.BAD_REQUEST,
            "offset must be zero or a positive integer",
        )


def validate_range_filters(
    min_value: int | float | None,
    max_value: int | float | None,
    min_field: str,
    max_field: str,
    abort_func,
) -> None:
    """
    Shared validation for min/max numeric filters to avoid wasted DB calls.
    """
    if min_value is not None and min_value < 0:
        abort_func(
            HTTPStatus.BAD_REQUEST,
            f"{min_field} must be zero or a positive integer",
        )
    if max_value is not None and max_value < 0:
        abort_func(
            HTTPStatus.BAD_REQUEST,
            f"{max_field} must be zero or a positive integer",
        )
    if (
        min_value is not None
        and max_value is not None
        and min_value > max_value
    ):
        abort_func(
            HTTPStatus.BAD_REQUEST,
            f"{min_field} cannot be greater than {max_field}",
        )
