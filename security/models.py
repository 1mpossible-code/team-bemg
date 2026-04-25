"""Security protocol models with backward-compatible, additive checks."""

from __future__ import annotations

from copy import deepcopy

CREATE = "create"
READ = "read"
UPDATE = "update"
DELETE = "delete"
VALID_ACTIONS = [CREATE, READ, UPDATE, DELETE]

USER_LIST = "user_list"
CHECKS = "checks"
LOGIN = "login"
ALLOWED_ROLES = "allowed_roles"
API_KEY = "api_key"
API_KEYS = "api_keys"
PASS_PHRASE = "pass_phrase"
PASSWORD = "password"
CODES = "codes"


class ActionChecks:
    """Represents the checks required for one CRUD action."""

    def __init__(
        self,
        login: bool = False,
        valid_users: list[str] | None = None,
        allowed_roles: list[str] | None = None,
        api_key: bool = False,
        valid_api_keys: list[str] | None = None,
        pass_phrase: bool = False,
        phrase: str = "",
        codes: dict[str, str] | None = None,
    ):
        if not isinstance(login, bool):
            raise TypeError("login must be a bool")
        if not isinstance(api_key, bool):
            raise TypeError("api_key must be a bool")
        if not isinstance(pass_phrase, bool):
            raise TypeError("pass_phrase must be a bool")
        if valid_users is not None and not isinstance(valid_users, list):
            raise TypeError("valid_users must be a list or None")
        if allowed_roles is not None and not isinstance(allowed_roles, list):
            raise TypeError("allowed_roles must be a list or None")
        if valid_api_keys is not None and not isinstance(valid_api_keys, list):
            raise TypeError("valid_api_keys must be a list or None")
        if codes is not None and not isinstance(codes, dict):
            raise TypeError("codes must be a dict or None")

        self.login = login
        self.valid_users = list(valid_users or [])
        self.allowed_roles = list(allowed_roles or [])
        self.api_key = api_key
        self.valid_api_keys = list(valid_api_keys or [])
        self.pass_phrase = pass_phrase
        self.phrase = phrase
        self.codes = deepcopy(codes) if codes else None

    def to_json(self) -> dict:
        payload = {
            LOGIN: self.login,
            API_KEY: self.api_key,
            PASS_PHRASE: self.pass_phrase,
        }
        if self.valid_users:
            payload[USER_LIST] = list(self.valid_users)
        if self.allowed_roles:
            payload[ALLOWED_ROLES] = list(self.allowed_roles)
        if self.valid_api_keys:
            payload[API_KEYS] = list(self.valid_api_keys)
        if self.phrase:
            payload[PASSWORD] = self.phrase
        if self.codes:
            payload[CODES] = deepcopy(self.codes)
        return payload

    def is_permitted(self, user_id: str = "", check_vals: dict | None = None) -> bool:
        check_vals = check_vals or {}
        if self.login and not user_id:
            return False
        if self.valid_users and user_id not in self.valid_users:
            return False
        if self.allowed_roles and check_vals.get("role") not in self.allowed_roles:
            return False
        if self.api_key and check_vals.get("api_key") not in self.valid_api_keys:
            return False
        if self.pass_phrase and check_vals.get("phrase") != self.phrase:
            return False
        if self.codes and check_vals.get("code") not in self.codes.values():
            return False
        return True


class SecProtocol:
    """Represents security rules for a named feature/resource."""

    def __init__(
        self,
        name: str,
        create: ActionChecks | None = None,
        read: ActionChecks | None = None,
        update: ActionChecks | None = None,
        delete: ActionChecks | None = None,
    ):
        if not isinstance(name, str):
            raise TypeError("name must be a str")
        self.name = name
        self.create = create or ActionChecks()
        self.read = read or ActionChecks()
        self.update = update or ActionChecks()
        self.delete = delete or ActionChecks()

    def to_json(self) -> dict:
        return {
            "feature_name": self.name,
            CREATE: self.create.to_json(),
            READ: self.read.to_json(),
            UPDATE: self.update.to_json(),
            DELETE: self.delete.to_json(),
        }

    def is_permitted(self, action: str, user_id: str = "", check_vals: dict | None = None) -> bool:
        if action not in VALID_ACTIONS:
            raise ValueError(f"Invalid action: {action}")
        return getattr(self, action).is_permitted(user_id=user_id, check_vals=check_vals)


def checks_from_legacy(action_record: dict | None) -> ActionChecks:
    if not action_record:
        return ActionChecks()
    checks = action_record.get(CHECKS, {})
    return ActionChecks(
        login=checks.get(LOGIN, False),
        valid_users=action_record.get(USER_LIST, []),
        allowed_roles=checks.get(ALLOWED_ROLES, []),
        api_key=checks.get(API_KEY, False),
        valid_api_keys=checks.get(API_KEYS, []),
        pass_phrase=checks.get(PASS_PHRASE, False),
        phrase=checks.get(PASSWORD, ""),
        codes=checks.get(CODES),
    )


def protocol_from_legacy(feature_name: str, feature_record: dict | None) -> SecProtocol:
    feature_record = feature_record or {}
    return SecProtocol(
        feature_name,
        create=checks_from_legacy(feature_record.get(CREATE)),
        read=checks_from_legacy(feature_record.get(READ)),
        update=checks_from_legacy(feature_record.get(UPDATE)),
        delete=checks_from_legacy(feature_record.get(DELETE)),
    )
