from functools import wraps

from security.manager import get_protocol, is_permitted as manager_is_permitted, load_legacy_records
from security.models import ALLOWED_ROLES
from server.auth import ROLE_ADMIN

# import data.db_connect as dbc

"""
Our record format to meet our requirements (see security.md) will be:

{
    feature_name1: {
        create: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        read: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        update: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
        delete: {
            user_list: [],
            checks: {
                login: True,
                ip_address: False,
                dual_factor: False,
                # etc.
            },
        },
    },
    feature_name2: # etc.
}
"""

COLLECT_NAME = 'security'
CREATE = 'create'
READ = 'read'
UPDATE = 'update'
DELETE = 'delete'
USER_LIST = 'user_list'
CHECKS = 'checks'
LOGIN = 'login'

# Features:
PEOPLE = 'people'
COUNTRIES = 'countries'

security_recs = None
# These will come from the DB soon:
temp_recs = {
    PEOPLE: {
        CREATE: {
            USER_LIST: ['ejc369@nyu.edu'],
            CHECKS: {
                LOGIN: True,
            },
        },
    },
    COUNTRIES: {
        CREATE: {
            CHECKS: {
                LOGIN: True,
                ALLOWED_ROLES: [ROLE_ADMIN],
            },
        },
        UPDATE: {
            CHECKS: {
                LOGIN: True,
                ALLOWED_ROLES: [ROLE_ADMIN],
            },
        },
        DELETE: {
            CHECKS: {
                LOGIN: True,
                ALLOWED_ROLES: [ROLE_ADMIN],
            },
        },
    },
}


def read() -> dict:
    global security_recs
    # dbc.read()
    security_recs = temp_recs
    load_legacy_records(security_recs)
    return security_recs


def needs_recs(fn):
    """
    Should be used to decorate any function that directly accesses sec recs.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global security_recs
        if not security_recs:
            security_recs = read()
        return fn(*args, **kwargs)
    return wrapper


@needs_recs
def read_feature(feature_name: str) -> dict:
    if feature_name in security_recs:
        return security_recs[feature_name]
    else:
        return None


@needs_recs
def read_protocol(feature_name: str):
    return get_protocol(feature_name)


@needs_recs
def is_permitted(
    feature_name: str,
    action: str,
    user_id: str = '',
    auth_header: str | None = None,
    auth_payload: dict | None = None,
    api_key: str = '',
    phrase: str = '',
    code: str | None = None,
) -> bool:
    return manager_is_permitted(
        feature_name,
        action,
        user_id=user_id,
        auth_header=auth_header,
        auth_payload=auth_payload,
        api_key=api_key,
        phrase=phrase,
        code=code,
    )
