"""Opt-in route security helpers.

Enforcement is disabled by default to preserve current API behavior.
"""

from __future__ import annotations

import logging
import os
from functools import wraps
from http import HTTPStatus

from flask import g, request

from security.manager import is_permitted

LOGGER = logging.getLogger(__name__)


def security_enforcement_enabled() -> bool:
    return os.getenv("SECURITY_ENFORCEMENT", "false").lower() in {"1", "true", "yes", "on"}


def security_audit_only() -> bool:
    return os.getenv("SECURITY_AUDIT_ONLY", "false").lower() in {"1", "true", "yes", "on"}


def require_protocol(feature_name: str, action: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            permitted = is_permitted(
                feature_name,
                action,
                auth_header=request.headers.get("Authorization"),
            )
            g.security_result = {
                "feature": feature_name,
                "action": action,
                "permitted": permitted,
            }
            if not security_enforcement_enabled():
                return fn(*args, **kwargs)
            if security_audit_only():
                LOGGER.info("Security audit result: %s", g.security_result)
                return fn(*args, **kwargs)
            if not permitted:
                return {"message": "forbidden"}, HTTPStatus.FORBIDDEN
            return fn(*args, **kwargs)

        return wrapper

    return decorator
