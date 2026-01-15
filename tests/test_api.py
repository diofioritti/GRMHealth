from fastapi.testclient import TestClient


def test_status_ok():
    # Import local para permitir execução sem instalar como pacote.
    from main import app

    client = TestClient(app)
    resp = client.get("/api/v1/health/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "model_loaded" in body
    assert "model_id" in body

