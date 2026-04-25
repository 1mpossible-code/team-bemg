"""In-memory protocol manager for team-bemg security."""

from __future__ import annotations

from copy import deepcopy

from security.models import SecProtocol, protocol_from_legacy
from server.auth import authenticate_request

protocols: dict[str, SecProtocol] = {}
legacy_records: dict[str, dict] = {}


def clear() -> None:
    protocols.clear()
    legacy_records.clear()


def load_legacy_records(records: dict[str, dict]) -> dict[str, SecProtocol]:
    clear()
    legacy_records.update(deepcopy(records))
    for feature_name, feature_record in legacy_records.items():
        protocols[feature_name] = protocol_from_legacy(feature_name, feature_record)
    return protocols


def add_protocol(protocol: SecProtocol) -> None:
    if protocol.name in protocols:
        raise ValueError(f"Duplicate protocol: {protocol.name}")
    protocols[protocol.name] = protocol


def get_protocol(name: str) -> SecProtocol | None:
    return protocols.get(name)


def exists(name: str) -> bool:
    return name in protocols


def _auth_payload_from_inputs(
    auth_header: str | None = None,
    auth_payload: dict | None = None,
) -> dict:
    if auth_payload is not None:
        return auth_payload
    if not auth_header:
        return {}
    try:
        return authenticate_request(auth_header)
    except PermissionError:
        return {}


def is_permitted(
    feature_name: str,
    action: str,
    user_id: str = "",
    auth_header: str | None = None,
    auth_payload: dict | None = None,
    api_key: str = "",
    phrase: str = "",
    code: str | None = None,
) -> bool:
    protocol = get_protocol(feature_name)
    if protocol is None:
        return True

    payload = _auth_payload_from_inputs(auth_header=auth_header, auth_payload=auth_payload)
    effective_user_id = user_id or payload.get("sub", "")
    check_vals = {
        "role": payload.get("role"),
        "api_key": api_key,
        "phrase": phrase,
        "code": code,
    }
    return protocol.is_permitted(action, user_id=effective_user_id, check_vals=check_vals)
