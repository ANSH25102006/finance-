import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_signup_login_get_me_flow():
    unique_id = uuid.uuid4().hex[:8]
    email = f"authtest_{unique_id}@example.com"
    password = "password123"

    # 1. Signup
    signup_res = client.post("/auth/signup", json={"email": email, "password": password})
    
    assert signup_res.status_code == 201, f"Signup failed: {signup_res.json()}"
    signup_data = signup_res.json()
    assert signup_data["email"] == email
    assert "id" in signup_data

    # 2. Login
    login_res = client.post("/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200, f"Login failed: {login_res.json()}"
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Get /auth/me
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200, f"Get /auth/me failed: {me_res.json()}"
    me_data = me_res.json()
    assert me_data["email"] == email
    assert me_data["id"] == signup_data["id"]


def test_login_invalid_credentials():
    login_res = client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "wrong"})
    assert login_res.status_code == 401
