"""
test_roadmap_verification.py
──────────────────────────────
Comprehensive feature verification test suite against the Personal Finance Auditor roadmap.
"""

import io
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.merchant.merchant_service import MerchantService

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


# ═════════════════════════════════════════════════════════════════════════════
# 1. MERCHANT NORMALIZATION & 2. CATEGORIZATION
# ═════════════════════════════════════════════════════════════════════════════

def test_01_merchant_normalization_and_categorization():
    ms = MerchantService()

    # Swiggy
    r1 = ms.recognize("SWIGGY ORDER ONLINE")
    assert r1["merchant"] == "Swiggy"
    assert r1["category"] == "Food Delivery"

    # Netflix
    r2 = ms.recognize("NETFLIX SUBSCRIPTION")
    assert r2["merchant"] == "Netflix"
    assert r2["category"] == "Entertainment"

    # Uber
    r3 = ms.recognize("UBER TRIP RIDE")
    assert r3["merchant"] == "Uber"
    assert r3["category"] == "Transport"

    # BSES Electricity
    r4 = ms.recognize("BSES RAJDHANI BILL")
    assert r4["merchant"] == "BSES"
    assert r4["category"] == "Utilities"

    # Unknown merchant with fallback keyword
    r5 = ms.recognize("MONTHLY SALARY CREDIT")
    assert r5["category"] == "Salary"


# ═════════════════════════════════════════════════════════════════════════════
# 3. RECURRING TRANSACTION DETECTION & PRICE INCREASE
# ═════════════════════════════════════════════════════════════════════════════

def test_03_recurring_transaction_detection_and_price_increase():
    user_id, token, account_id = _signup_and_login("recurring")

    today = date.today()
    # Month 1 (two months ago)
    m1_date = _fmt_date(today - timedelta(days=60))
    # Month 2 (last month)
    m2_date = _fmt_date(today - timedelta(days=30))
    # Month 3 (current month)
    m3_date = _fmt_date(today)

    csv_3months = (
        "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        f"{m1_date},NETFLIX SUBSCRIPTION,REF101,{m1_date},649.00,,10000.00\n"
        f"{m2_date},NETFLIX SUBSCRIPTION,REF102,{m2_date},649.00,,9351.00\n"
        f"{m3_date},NETFLIX SUBSCRIPTION,REF103,{m3_date},799.00,,8552.00\n"
    )

    res = client.post(
        "/api/import/import-transactions",
        headers=_auth(token),
        data={"bank_format": "hdfc", "account_id": account_id},
        files={"file": ("3months.csv", csv_3months.encode("utf-8"), "text/csv")}
    )
    assert res.status_code == 200
    assert res.json()["imported"] == 3

    # Set transactions to recurring=True to trigger detector
    tx_list = client.get("/api/transactions/", headers=_auth(token)).json()["items"]
    for tx in tx_list:
        client.put(f"/api/transactions/{tx['id']}", headers=_auth(token), json={"recurring": True})

    # Run intelligence engine
    insights_res = client.get("/api/intelligence/insights", headers=_auth(token))
    assert insights_res.status_code == 200
    insights = insights_res.json()

    price_increase_insight = next((i for i in insights if i["type"] == "PRICE_INCREASE"), None)
    assert price_increase_insight is not None, "Expected PRICE_INCREASE insight for Netflix price rise"
    assert "Netflix" in price_increase_insight["title"] or "Netflix" in price_increase_insight["summary"]


# ═════════════════════════════════════════════════════════════════════════════
# 4. SAVINGS SIMULATOR
# ═════════════════════════════════════════════════════════════════════════════

def test_04_savings_simulator_cancel_subscription():
    user_id, token, account_id = _signup_and_login("simulator")

    payload = {
        "scenario": "CANCEL_SUBSCRIPTION",
        "params": {"subscription_id": "netflix-id", "amount": 649.0}
    }
    res = client.post("/api/simulator/run", headers=_auth(token), json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["monthly_savings"] == 649.0
    assert data["annual_savings"] == 649.0 * 12


# ═════════════════════════════════════════════════════════════════════════════
# 5. PDF PARSING (SYNTHETIC REAL PDF)
# ═════════════════════════════════════════════════════════════════════════════

def test_05_pdf_parsing_end_to_end():
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors

    user_id, token, account_id = _signup_and_login("pdf_user")

    # Generate a real PDF in memory with HDFC table layout
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    today_str = _fmt_date(date.today())
    table_data = [
        ["Date", "Narration", "Chq./Ref. No.", "Value Date", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"],
        [today_str, "SWIGGY ORDER ONLINE", "REF901", today_str, "450.00", "", "99550.00"],
        [today_str, "SALARY CREDIT JUNE", "REF902", today_str, "", "80000.00", "179550.00"],
    ]
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    doc.build([t])
    pdf_bytes = pdf_buffer.getvalue()

    # Upload PDF via import endpoint
    res = client.post(
        "/api/import/import-transactions",
        headers=_auth(token),
        data={"bank_format": "hdfc", "account_id": account_id},
        files={"file": ("statement.pdf", pdf_bytes, "application/pdf")}
    )
    assert res.status_code == 200, f"PDF import failed: {res.text}"
    import_summary = res.json()
    assert import_summary["imported"] == 2

    # Verify transactions in DB
    txs = client.get("/api/transactions/", headers=_auth(token)).json()["items"]
    assert len(txs) == 2

    swiggy_tx = next(t for t in txs if "SWIGGY" in t["description"])
    salary_tx = next(t for t in txs if "SALARY" in t["description"])

    assert swiggy_tx["merchant"] == "Swiggy"
    assert swiggy_tx["transaction_type"] == "expense"
    assert salary_tx["transaction_type"] == "income"


# ═════════════════════════════════════════════════════════════════════════════
# 7. FINANCIAL INTELLIGENCE DETECTORS
# ═════════════════════════════════════════════════════════════════════════════

def test_07_financial_intelligence_detectors():
    user_id, token, account_id = _signup_and_login("fi_user")

    today = date.today()
    prev_d = _fmt_date(today - timedelta(days=30))
    curr_d = _fmt_date(today)

    # Multi-month statement with spike in Shopping
    csv_data = (
        "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        f"{prev_d},AMAZON MKTPLACE,REF201,{prev_d},1000.00,,50000.00\n"
        f"{curr_d},AMAZON MKTPLACE,REF202,{curr_d},15000.00,,35000.00\n"
    )

    client.post(
        "/api/import/import-transactions",
        headers=_auth(token),
        data={"bank_format": "hdfc", "account_id": account_id},
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")}
    )

    insights_res = client.get("/api/intelligence/insights", headers=_auth(token))
    assert insights_res.status_code == 200
    insights = insights_res.json()

    assert len(insights) > 0, "Financial Intelligence should produce insights for spending spike"


# ═════════════════════════════════════════════════════════════════════════════
# 8. PREDICTIVE INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════════════

def test_08_predictive_intelligence_forecasts():
    user_id, token, account_id = _signup_and_login("pi_user")

    today = date.today()
    d1 = _fmt_date(today - timedelta(days=35))
    d2 = _fmt_date(today - timedelta(days=5))

    csv_data = (
        "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        f"{d1},SALARY CREDIT,REF301,{d1},,50000.00,50000.00\n"
        f"{d2},RENT PAYMENT,REF302,{d2},15000.00,,35000.00\n"
    )
    client.post(
        "/api/import/import-transactions",
        headers=_auth(token),
        data={"bank_format": "hdfc", "account_id": account_id},
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")}
    )

    pred_res = client.get("/api/predictions", headers=_auth(token))
    assert pred_res.status_code == 200
    preds = pred_res.json()["predictions"]
    assert len(preds) > 0


# ═════════════════════════════════════════════════════════════════════════════
# 9. DASHBOARD ACCURACY
# ═════════════════════════════════════════════════════════════════════════════

def test_09_dashboard_accuracy():
    user_id, token, account_id = _signup_and_login("dash_user")

    today = date.today()
    d1 = _fmt_date(today - timedelta(days=2))
    d2 = _fmt_date(today - timedelta(days=1))

    csv_data = (
        "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        f"{d1},SALARY CREDIT,REF401,{d1},,100000.00,100000.00\n"
        f"{d2},RENT PAYMENT,REF402,{d2},25000.00,,75000.00\n"
    )
    client.post(
        "/api/import/import-transactions",
        headers=_auth(token),
        data={"bank_format": "hdfc", "account_id": account_id},
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")}
    )

    dash = client.get("/api/dashboard/summary", headers=_auth(token)).json()
    assert dash["netWorth"] == 75000.0
    assert dash["income"]["current"] == 100000.0
    assert dash["expenses"]["current"] == 25000.0


# ═════════════════════════════════════════════════════════════════════════════
# 10. API MONETARY CONTRACT (FRACTIONAL ACCURACY)
# ═════════════════════════════════════════════════════════════════════════════

def test_10_api_monetary_contract_fractional_precision():
    user_id, token, account_id = _signup_and_login("precision_user")

    today = date.today()
    d1 = _fmt_date(today)

    csv_data = (
        "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        f"{d1},NETFLIX SUBSCRIPTION,REF501,{d1},649.99,,9350.01\n"
    )
    client.post(
        "/api/import/import-transactions",
        headers=_auth(token),
        data={"bank_format": "hdfc", "account_id": account_id},
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")}
    )

    txs = client.get("/api/transactions/", headers=_auth(token)).json()["items"]
    assert txs[0]["amount"] == 649.99


# ═════════════════════════════════════════════════════════════════════════════
# 11. USER ISOLATION
# ═════════════════════════════════════════════════════════════════════════════

def test_11_user_isolation_full():
    user_a_id, token_a, acct_a_id = _signup_and_login("user_a")
    user_b_id, token_b, acct_b_id = _signup_and_login("user_b")

    today = date.today()
    d1 = _fmt_date(today)

    # Add transaction to User A
    csv_data = (
        "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
        f"{d1},SALARY CREDIT,REF601,{d1},,50000.00,50000.00\n"
    )
    client.post(
        "/api/import/import-transactions",
        headers=_auth(token_a),
        data={"bank_format": "hdfc", "account_id": acct_a_id},
        files={"file": ("statement.csv", csv_data.encode("utf-8"), "text/csv")}
    )

    # User B checks accounts
    b_accts = client.get("/api/accounts/", headers=_auth(token_b)).json()
    assert all(a["id"] != acct_a_id for a in b_accts)

    # User B checks transactions
    b_txs = client.get("/api/transactions/", headers=_auth(token_b)).json()
    assert b_txs["total"] == 0

    # User B checks dashboard
    b_dash = client.get("/api/dashboard/summary", headers=_auth(token_b)).json()
    assert b_dash["netWorth"] == 0.0

    # User B checks predictions
    b_preds = client.get("/api/predictions", headers=_auth(token_b)).json()["predictions"]
    # Should not contain any calculations derived from User A's 50000.0 salary
    assert all(p.get("forecast_value") != 50000.0 for p in b_preds)
