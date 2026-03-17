"""Helpers for parsing and validating JSON request bodies."""

from http import HTTPStatus
from typing import Any, Callable

from flask import Request

AbortFunc = Callable[[HTTPStatus, str], None]


def get_json_object_or_abort(request: Request, abort_func: AbortFunc) -> dict[str, Any]:
    """Return a JSON object payload or abort with a consistent 400 error."""
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort_func(
            HTTPStatus.BAD_REQUEST,
            'Request body must be a valid JSON object',
        )
    return payload
