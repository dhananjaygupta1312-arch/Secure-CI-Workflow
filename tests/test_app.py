from app.app import app

def test_health():
    resp = app.test_client().get("/health")
    assert resp.status_code == 200
    assert resp.data == b"ok"