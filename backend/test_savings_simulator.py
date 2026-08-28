"""
test_savings_simulator.py
──────────────────────────
Comprehensive unit and API tests for Savings Simulator and Investment Compounding Projections.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

def _signup_and_login(prefix: str):
    uid = uuid.uuid4().hex[:8]
    email = f"{prefix}_{uid}@fintest.com"
    password = "TestPass123!"
    res_sign = client.post("/auth/signup", json={"email": email, "password": password})
    assert res_sign.status_code == 201

    res_log = client.post("/auth/login", json={"email": email, "password": password})
    assert res_log.status_code == 200
    token = res_log.json()["access_token"]
    return token


def test_compounding_projections_api():
    token = _signup_and_login("sim_compound")

    payload = {
        "scenario": "CUSTOM_SAVINGS",
        "params": {
            "amount": 2000.0,
            "annual_return_pct": 8.0,
            "time_period_years": 3
        }
    }

    res = client.post("/api/simulator/run", headers=_auth(token), json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["monthly_savings"] == 2000.0
    assert data["annual_savings"] == 24000.0

    compounding = data["compounding"]
    assert compounding["annual_return_pct"] == 8.0
    assert compounding["target_years"] == 3

    projections = compounding["projections_by_year"]
    assert "1_year" in projections
    assert "3_year" in projections
    assert "5_year" in projections

    # 3-year projection check
    p3 = projections["3_year"]
    assert p3["monthly_contribution"] == 2000.0
    assert p3["total_contributions"] == 72000.0  # 2000 * 36
    assert p3["final_projected_value"] > 72000.0  # Includes growth
    assert p3["growth_earned"] == round(p3["final_projected_value"] - 72000.0, 2)


def test_zero_and_invalid_param_compounding_handling():
    token = _signup_and_login("sim_zero")

    # 0% interest rate
    payload = {
        "scenario": "CUSTOM_SAVINGS",
        "params": {
            "amount": 1000.0,
            "annual_return_pct": 0.0,
            "time_period_years": 5
        }
    }

    res = client.post("/api/simulator/run", headers=_auth(token), json=payload)
    assert res.status_code == 200
    data = res.json()

    p5 = data["compounding"]["projections_by_year"]["5_year"]
    assert p5["total_contributions"] == 60000.0  # 1000 * 60
    assert p5["final_projected_value"] == 60000.0  # No growth at 0%
    assert p5["growth_earned"] == 0.0
