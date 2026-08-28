"""
test_budget_recommendations.py
──────────────────────────────
Tests for Budget Recommendation Engine (Priority 1).
"""

import uuid
from datetime import date, timedelta
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
    user_id = res_sign.json()["id"]

    res_log = client.post("/auth/login", json={"email": email, "password": password})
    assert res_log.status_code == 200
    token = res_log.json()["access_token"]

    accts = client.get("/api/accounts/", headers=_auth(token)).json()
    account_id = accts[0]["id"]

    return user_id, token, account_id

def _fmt_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def test_budget_recommendations_empty_history():
    user_id, token, account_id = _signup_and_login("rec_empty")
    res = client.get("/api/budgets/recommendations", headers=_auth(token))
    assert res.status_code == 200
    assert res.json() == []


def test_budget_recommendations_rolling_average_and_trims():
    user_id, token, account_id = _signup_and_login("rec_rolling")

    today = date.today()
    d1 = _fmt_date(today - timedelta(days=60)) # Month -2
    d2 = _fmt_date(today - timedelta(days=30)) # Month -1

    # Upload Swiggy (Food Delivery - discretionary) & BSES (Utilities - non-discretionary)
    csv_data = (
        "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        f"{d1},SWIGGY ORDER ONLINE,REF1, {d1},2000.00,,50000.00\n"
        f"{d2},SWIGGY ORDER ONLINE,REF2, {d2},4000.00,,46000.00\n"
        f"{d1},BSES RAJDHANI BILL,REF3, {d1},1000.00,,45000.00\n"
        f"{d2},BSES RAJDHANI BILL,REF4, {d2},1000.00,,44000.00\n"
    )

    client.post(
        "/api/import/import-transactions",
        headers=_auth(token),
        data={"bank_format": "hdfc", "account_id": account_id},
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")}
    )

    res = client.get("/api/budgets/recommendations", headers=_auth(token))
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) >= 2

    # Check Swiggy (Food Delivery) -> historical avg (2000+4000)/2 = 3000.0
    swiggy_rec = next(r for r in recs if r["category_name"] == "Food Delivery")
    assert swiggy_rec["historical_monthly_average"] == 3000.0
    assert swiggy_rec["is_discretionary"] is True
    # 15% trim -> 3000 * 0.85 = 2550.0
    assert swiggy_rec["recommended_budget"] == 2550.0
    assert swiggy_rec["potential_monthly_savings"] == 450.0
    assert swiggy_rec["potential_annual_savings"] == 5400.0

    # Check BSES (Utilities) -> historical avg 1000.0
    bses_rec = next(r for r in recs if r["category_name"] == "Utilities")
    assert bses_rec["historical_monthly_average"] == 1000.0
    assert bses_rec["is_discretionary"] is False
    # 5% trim -> 1000 * 0.95 = 950.0
    assert bses_rec["recommended_budget"] == 950.0
    assert bses_rec["potential_monthly_savings"] == 50.0


def test_budget_recommendations_user_isolation():
    u_a, token_a, acct_a = _signup_and_login("rec_user_a")
    u_b, token_b, acct_b = _signup_and_login("rec_user_b")

    today = date.today()
    d1 = _fmt_date(today - timedelta(days=30))
    csv_data = (
        "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        f"{d1},SWIGGY ORDER ONLINE,REF1, {d1},5000.00,,50000.00\n"
    )

    client.post(
        "/api/import/import-transactions",
        headers=_auth(token_a),
        data={"bank_format": "hdfc", "account_id": acct_a},
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")}
    )

    # User B checks recommendations
    res_b = client.get("/api/budgets/recommendations", headers=_auth(token_b))
    assert res_b.status_code == 200
    assert res_b.json() == []
