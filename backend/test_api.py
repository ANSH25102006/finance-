from fastapi.testclient import TestClient
from app.main import app

def test_docs_endpoint():
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200
