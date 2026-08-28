import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_financial_endpoints_flow():
    unique_id = uuid.uuid4().hex[:8]
    email = f"endpoint_test_{unique_id}@example.com"
    password = "password123"

    # Signup
    signup_res = client.post("/auth/signup", json={"email": email, "password": password})
    assert signup_res.status_code == 201

    # Login
    login_res = client.post("/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Timeline
    timeline_res = client.get("/api/timeline", headers=headers)
    assert timeline_res.status_code == 200

    # Predictions
    pred_res = client.get("/api/predictions", headers=headers)
    assert pred_res.status_code == 200

    # Simulator run
    sim_res = client.post(
        "/api/simulator/run",
        headers=headers,
        json={"scenario": "CANCEL_SUBSCRIPTION", "params": {"amount": 50}},
    )
    assert sim_res.status_code == 200



