from server.app import create_app

def test_health():
    app = create_app()
    with app.test_client() as c:
        r = c.get("/healthz")
        assert r.status_code == 200
        assert r.get_json() == {"status": "ok"}