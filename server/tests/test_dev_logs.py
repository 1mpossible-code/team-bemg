import logging

from server.app import create_app


def test_dev_logs_requires_token(monkeypatch):
    monkeypatch.setenv('DEV_LOGS_TOKEN', 'secret-token')
    app = create_app()

    with app.test_client() as client:
        response = client.get('/dev/logs')

    assert response.status_code == 403


def test_dev_logs_returns_recent_entries(monkeypatch):
    monkeypatch.setenv('DEV_LOGS_TOKEN', 'secret-token')
    app = create_app()
    logging.getLogger('server.tests.dev_logs').warning('developer log endpoint smoke test')

    with app.test_client() as client:
        response = client.get('/dev/logs?limit=5', headers={'X-Dev-Token': 'secret-token'})

    payload = response.get_json()

    assert response.status_code == 200
    assert payload['logs']
    assert any(entry['message'] == 'developer log endpoint smoke test' for entry in payload['logs'])
    assert len(payload['logs']) <= 5
