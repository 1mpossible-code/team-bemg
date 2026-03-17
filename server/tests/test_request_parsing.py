from http import HTTPStatus

import pytest
from flask import Flask, request

from server.request_parsing import get_json_object_or_abort


class AbortCalled(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


@pytest.fixture
def app():
    return Flask(__name__)


def abort_func(status, message):
    raise AbortCalled(status, message)


def test_get_json_object_or_abort_returns_payload_for_valid_json_object(app):
    with app.test_request_context(
        '/',
        method='POST',
        json={'city_name': 'Gotham'},
    ):
        payload = get_json_object_or_abort(request, abort_func)

    assert payload == {'city_name': 'Gotham'}


def test_get_json_object_or_abort_allows_empty_object(app):
    with app.test_request_context('/', method='PUT', json={}):
        payload = get_json_object_or_abort(request, abort_func)

    assert payload == {}


def test_get_json_object_or_abort_rejects_malformed_json(app):
    with app.test_request_context(
        '/',
        method='POST',
        data='{"city_name": "Broken"',
        content_type='application/json',
    ):
        with pytest.raises(AbortCalled) as exc_info:
            get_json_object_or_abort(request, abort_func)

    assert exc_info.value.status == HTTPStatus.BAD_REQUEST
    assert exc_info.value.message == 'Request body must be a valid JSON object'


def test_get_json_object_or_abort_rejects_non_object_json(app):
    with app.test_request_context('/', method='POST', json=['not', 'an', 'object']):
        with pytest.raises(AbortCalled) as exc_info:
            get_json_object_or_abort(request, abort_func)

    assert exc_info.value.status == HTTPStatus.BAD_REQUEST
    assert exc_info.value.message == 'Request body must be a valid JSON object'
