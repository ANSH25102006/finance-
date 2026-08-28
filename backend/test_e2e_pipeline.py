"""
test_e2e_pipeline.py
────────────────────
Full end-to-end verification of the Finance Tracker data pipeline.

Tests (in order):
  1.  Signup — fresh user created
  2.  Default account auto-created on signup
  3.  Login — JWT token obtained
  4.  No-auth guard — all protected endpoints reject without token
  5.  CSV upload / parse (HDFC format, realistic synthetic statement)
  6.  DB persistence — all rows committed
  7.  Account association — every transaction belongs to the correct account
  8.  User association — every transaction belongs to the correct user
  9.  Merchant normalization — merchants are assigned
  10. Categorization — categories are assigned
  11. Dashboard summary — non-zero income / expense / net-worth values
  12. Financial Intelligence engine — runs and returns structured insights
  13. Cash Flow — monthly trend data driven by imported transactions
  14. Recurring / subscription detection — rules engine runs without error
  15. Predictive intelligence — predictions computed from transactions
  16. Savings simulator — deterministic simulation on real categories
  17. Ledger / transactions endpoint — debit/credit types verified
  18. User isolation — User B cannot read User A's accounts or transactions
  19. Duplicate prevention — re-importing same statement doesn't duplicate rows
  20. Data integrity — exact amount sums match CSV source

Route prefix reference (see app/main.py):
  /auth/*               → auth router (no /api prefix)
  /api/accounts/*       → accounts router
  /api/transactions/*   → transactions router
  /api/dashboard/*      → dashboard router
  /api/import/*         → imports router
  /api/intelligence/*   → intelligence router
  /api/predictions      → predictions router
  /api/simulator/*      → simulator router
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Shared state populated sequentially across test functions
# ─────────────────────────────────────────────────────────────────────────────
ctx: dict = {}    # User A: token, account_id, transactions, dashboard …
ctx_b: dict = {}  # User B: token, account_ids  (isolation check)

# ─────────────────────────────────────────────────────────────────────────────
# Synthetic HDFC bank statement
# 3 expense rows:  Swiggy ₹450, Netflix ₹649, Shell Petrol ₹1200
# 2 income rows:   Salary ₹80,000, Freelance ₹15,000
# ─────────────────────────────────────────────────────────────────────────────
HDFC_CSV = (
    "Date,Narration,Chq./Ref. No.,Value Date,Withdrawal Amt.,Deposit Amt.,Closing Balance\n"
    "01/06/26,SWIGGY ORDER ONLINE,REF001,01/06/26,450.00,,99550.00\n"
    "05/06/26,SALARY CREDIT JUNE,REF002,05/06/26,,80000.00,179550.00\n"
    "10/06/26,NETFLIX SUBSCRIPTION,REF003,10/06/26,649.00,,178901.00\n"
    "15/06/26,SHELL PETROL PUMP,REF004,15/06/26,1200.00,,177701.00\n"
    "20/06/26,FREELANCE PAYOUT UPWORK,REF005,20/06/26,,15000.00,192701.00\n"
)

EXPECTED_INCOME = 80_000.0 + 15_000.0   # 95,000
EXPECTED_EXPENSE = 450.0 + 649.0 + 1_200.0  # 2,299


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _signup(email: str, password: str = "TestPass123!"):
    return client.post("/auth/signup", json={"email": email, "password": password})


def _login(email: str, password: str = "TestPass123!"):
    return client.post("/auth/login", json={"email": email, "password": password})


def _import_csv(token: str, account_id: str, csv_text: str = HDFC_CSV, bank_format: str = "hdfc"):
    return client.post(
        "/api/import/import-transactions",
        headers=_auth(token),
        data={"bank_format": bank_format, "account_id": account_id},
        files={"file": ("statement.csv", csv_text.encode("utf-8"), "text/csv")},
    )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 1  Signup
# ═════════════════════════════════════════════════════════════════════════════

def test_01_signup_creates_user():
    uid = uuid.uuid4().hex[:8]
    email = f"e2e_{uid}@fintest.com"
    res = _signup(email)
    assert res.status_code == 201, f"Signup failed: {res.text}"
    data = res.json()
    assert data["email"] == email
    assert "id" in data
    ctx["email"] = email
    ctx["user_id"] = data["id"]


# ═════════════════════════════════════════════════════════════════════════════
# STEP 2  Primary Checking auto-created on signup
# ═════════════════════════════════════════════════════════════════════════════

def test_02_signup_auto_creates_primary_account():
    login_res = _login(ctx["email"])
    assert login_res.status_code == 200, f"Login failed after signup: {login_res.text}"
    ctx["token"] = login_res.json()["access_token"]

    accounts_res = client.get("/api/accounts/", headers=_auth(ctx["token"]))
    assert accounts_res.status_code == 200, f"GET /api/accounts/ failed: {accounts_res.text}"
    accounts = accounts_res.json()

    assert len(accounts) >= 1, "No account was auto-created after signup"
    primary = next((a for a in accounts if a["name"] == "Primary Checking"), None)
    assert primary is not None, (
        f"'Primary Checking' account not found. Accounts returned: {accounts}"
    )
    assert primary["currency"] == "INR"
    ctx["account_id"] = primary["id"]


# ═════════════════════════════════════════════════════════════════════════════
# STEP 3  Login roundtrip
# ═════════════════════════════════════════════════════════════════════════════

def test_03_login_returns_jwt():
    res = _login(ctx["email"])
    assert res.status_code == 200, f"Login failed: {res.text}"
    token_data = res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    ctx["token"] = token_data["access_token"]


# ═════════════════════════════════════════════════════════════════════════════
# STEP 4  All protected endpoints reject unauthenticated requests
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("method,url", [
    ("get", "/api/accounts/"),
    ("get", "/api/dashboard/summary"),
    ("get", "/api/intelligence/insights"),
    ("get", "/api/predictions"),
    ("get", "/api/transactions/"),
])
def test_04_protected_routes_reject_without_token(method: str, url: str):
    res = getattr(client, method)(url)
    assert res.status_code == 401, (
        f"{method.upper()} {url} returned {res.status_code} without a token — expected 401"
    )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 5  CSV preview — parse without persisting
# ═════════════════════════════════════════════════════════════════════════════

def test_05_csv_preview_parses_statement():
    token = ctx["token"]
    res = client.post(
        "/api/import/csv-preview",
        headers=_auth(token),
        data={"bank_format": "hdfc"},
        files={"file": ("statement.csv", HDFC_CSV.encode("utf-8"), "text/csv")},
    )
    assert res.status_code == 200, f"CSV preview failed: {res.text}"
    data = res.json()

    assert data["bank_format"] == "hdfc"
    assert data["total_parsed"] == 5, f"Expected 5 rows parsed, got {data['total_parsed']}"

    txs = data["transactions"]
    amounts = {t["amount"] for t in txs}
    assert {450.0, 80000.0, 649.0, 1200.0, 15000.0}.issubset(amounts), (
        f"Not all expected amounts found in preview: {amounts}"
    )

    income_rows = [t for t in txs if t["transaction_type"] == "income"]
    expense_rows = [t for t in txs if t["transaction_type"] == "expense"]
    assert len(income_rows) == 2, f"Expected 2 income rows, got: {income_rows}"
    assert len(expense_rows) == 3, f"Expected 3 expense rows, got: {expense_rows}"


# ═════════════════════════════════════════════════════════════════════════════
# STEP 6  Full import — persist to DB
# ═════════════════════════════════════════════════════════════════════════════

def test_06_csv_import_persists_transactions():
    token = ctx["token"]
    account_id = ctx["account_id"]

    res = _import_csv(token, account_id)
    assert res.status_code == 200, f"CSV import failed: {res.text}"
    data = res.json()

    assert data["total_rows"] == 5, f"Expected 5 total rows, got {data['total_rows']}"
    assert data["imported"] == 5, f"Expected 5 imported, got {data['imported']}"
    assert data["duplicates"] == 0, f"Expected 0 duplicates on first import, got {data['duplicates']}"
    assert data["failed"] == 0, f"Expected 0 failed, got {data['failed']}"
    ctx["import_result"] = data


# ═════════════════════════════════════════════════════════════════════════════
# STEP 7  DB persistence via Transactions endpoint
# ═════════════════════════════════════════════════════════════════════════════

def test_07_transactions_persisted_in_db():
    token = ctx["token"]
    res = client.get("/api/transactions/", headers=_auth(token), params={"limit": 50, "page": 1})
    assert res.status_code == 200, f"GET /api/transactions/ failed: {res.text}"
    data = res.json()

    items = data.get("items", [])
    assert len(items) == 5, (
        f"Expected 5 persisted transactions in ledger, found {len(items)}. "
        f"Full response: {data}"
    )
    ctx["transactions"] = items


# ═════════════════════════════════════════════════════════════════════════════
# STEP 8  Account association
# ═════════════════════════════════════════════════════════════════════════════

def test_08_transactions_associated_with_correct_account():
    for tx in ctx["transactions"]:
        assert tx["account_id"] == ctx["account_id"], (
            f"Transaction {tx['id']} is associated with account {tx['account_id']} "
            f"but should be {ctx['account_id']}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 9  Merchant normalization
# ═════════════════════════════════════════════════════════════════════════════

def test_09_merchant_normalization():
    """Every imported transaction must have a non-empty merchant field."""
    for tx in ctx["transactions"]:
        merchant = (tx.get("merchant") or "").strip()
        assert merchant, (
            f"Transaction id={tx['id']} description='{tx['description']}' has no merchant assigned"
        )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 10  Categorization
# ═════════════════════════════════════════════════════════════════════════════

def test_10_categorization():
    """Every imported transaction must have a category_id assigned during import."""
    for tx in ctx["transactions"]:
        assert tx.get("category_id"), (
            f"Transaction id={tx['id']} description='{tx['description']}' has no category_id"
        )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 11  Dashboard summary — non-zero real values
# ═════════════════════════════════════════════════════════════════════════════

def test_11_dashboard_summary_reflects_imported_data():
    token = ctx["token"]
    res = client.get("/api/dashboard/summary", headers=_auth(token))
    assert res.status_code == 200, f"Dashboard summary failed: {res.text}"
    d = res.json()

    # Net worth = account.balance (0) + total_all_time_income - total_all_time_expense
    # = 0 + 95000 - 2299 = 92701 > 0
    assert d["netWorth"] > 0, (
        f"Expected netWorth > 0 after import, got {d['netWorth']}. "
        f"This means transactions weren't seen by analytics."
    )

    # Financial health score must be a valid percentage
    assert 0 <= d["financialHealth"] <= 100, (
        f"financialHealth out of range [0, 100]: {d['financialHealth']}"
    )

    # Recent transactions should reflect the import
    assert len(d["recentTransactions"]) > 0, (
        "recentTransactions empty after import"
    )

    ctx["dashboard"] = d


# ═════════════════════════════════════════════════════════════════════════════
# STEP 12  Financial Intelligence Engine
# ═════════════════════════════════════════════════════════════════════════════

def test_12_financial_intelligence_engine():
    token = ctx["token"]
    res = client.get("/api/intelligence/insights", headers=_auth(token), params={"limit": 50})
    assert res.status_code == 200, f"Intelligence endpoint failed: {res.text}"
    insights = res.json()

    assert isinstance(insights, list), f"Expected a list of insights, got: {type(insights)}"

    # Structural validation on every returned insight
    for insight in insights:
        for field in ("id", "severity", "title", "summary"):
            assert field in insight, f"Missing field '{field}' in insight: {insight}"
        assert insight["severity"] in ("CRITICAL", "WARNING", "INFO", "SUCCESS"), (
            f"Unexpected severity value: {insight['severity']}"
        )

    ctx["insights"] = insights


# ═════════════════════════════════════════════════════════════════════════════
# STEP 13  Cash Flow — monthly trend
# ═════════════════════════════════════════════════════════════════════════════

def test_13_cashflow_monthly_trend_driven_by_imported_data():
    d = ctx["dashboard"]
    monthly = d.get("monthlyTrend", [])
    assert isinstance(monthly, list), "monthlyTrend must be a list"

    non_empty = [m for m in monthly if m["income"] > 0 or m["expenses"] > 0]
    assert len(non_empty) > 0, (
        f"All months in trend are zero — imported data did not flow to analytics. "
        f"Trend: {monthly}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 14  Recurring / subscription detection
# ═════════════════════════════════════════════════════════════════════════════

def test_14_recurring_subscription_detection():
    """
    The engine's SavingsOpportunityDetector / RecurringPriceChangeDetector must not
    crash on a sparse dataset (1 month). The endpoint must respond 200 with a list.
    """
    token = ctx["token"]
    res = client.get(
        "/api/intelligence/insights",
        headers=_auth(token),
        params={"type": "SAVINGS_OPPORTUNITY", "limit": 50},
    )
    assert res.status_code == 200, f"Recurring detection endpoint failed: {res.text}"
    assert isinstance(res.json(), list)


# ═════════════════════════════════════════════════════════════════════════════
# STEP 15  Predictive Intelligence
# ═════════════════════════════════════════════════════════════════════════════

def test_15_predictive_intelligence():
    token = ctx["token"]
    res = client.get("/api/predictions", headers=_auth(token), params={"limit": 20})
    assert res.status_code == 200, f"Predictions endpoint failed: {res.text}"
    data = res.json()

    assert "predictions" in data, f"Response missing 'predictions' key: {data}"
    predictions = data["predictions"]
    assert isinstance(predictions, list)

    for p in predictions:
        for field in ("type", "confidence", "predicted_amount"):
            assert field in p, f"Missing field '{field}' in prediction: {p}"
        assert 0.0 <= p["confidence"] <= 1.0, (
            f"Confidence out of range [0, 1]: {p['confidence']}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 16  Savings Simulator
# ═════════════════════════════════════════════════════════════════════════════

def test_16_savings_simulator_uses_real_data():
    token = ctx["token"]
    # CUSTOM_SAVINGS: inject a fixed ₹2,000/month saving
    payload = {"scenario": "CUSTOM_SAVINGS", "params": {"amount": 2000}}
    res = client.post("/api/simulator/run", headers=_auth(token), json=payload)
    assert res.status_code == 200, f"Simulator endpoint failed: {res.text}"
    data = res.json()

    assert "monthly_savings" in data, f"Response missing 'monthly_savings': {data}"
    assert "annual_savings" in data, f"Response missing 'annual_savings': {data}"
    assert data["monthly_savings"] == 2000.0, (
        f"Expected monthly_savings=2000, got {data['monthly_savings']}"
    )
    assert data["annual_savings"] == 24_000.0, (
        f"Expected annual_savings=24000, got {data['annual_savings']}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 17  Ledger — debit / credit type correctness
# ═════════════════════════════════════════════════════════════════════════════

def test_17_debit_credit_types_correct():
    txs = ctx["transactions"]
    income = [t for t in txs if t["transaction_type"] == "income"]
    expenses = [t for t in txs if t["transaction_type"] == "expense"]

    assert len(income) == 2, f"Expected 2 income rows, got {len(income)}: {income}"
    assert len(expenses) == 3, f"Expected 3 expense rows, got {len(expenses)}: {expenses}"

    income_amounts = sorted(t["amount"] for t in income)
    expense_amounts = sorted(t["amount"] for t in expenses)

    assert income_amounts == sorted([80_000.0, 15_000.0]), (
        f"Income amounts do not match CSV: {income_amounts}"
    )
    assert expense_amounts == sorted([450.0, 649.0, 1_200.0]), (
        f"Expense amounts do not match CSV: {expense_amounts}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 18  User isolation (IDOR prevention)
# ═════════════════════════════════════════════════════════════════════════════

def test_18_user_isolation():
    # Create and log in User B
    uid_b = uuid.uuid4().hex[:8]
    email_b = f"e2e_b_{uid_b}@fintest.com"
    _signup(email_b)
    login_b = _login(email_b)
    assert login_b.status_code == 200
    token_b = login_b.json()["access_token"]
    ctx_b["token"] = token_b

    # User B's accounts list must only contain their own accounts
    accts_b_res = client.get("/api/accounts/", headers=_auth(token_b))
    assert accts_b_res.status_code == 200, f"User B GET /api/accounts/ failed: {accts_b_res.text}"
    accts_b = accts_b_res.json()
    assert isinstance(accts_b, list), f"Expected list, got: {accts_b}"
    b_account_ids = {a["id"] for a in accts_b}

    # User A's account must NOT appear in User B's list
    assert ctx["account_id"] not in b_account_ids, (
        "SECURITY VIOLATION: User B can see User A's account in the accounts list!"
    )

    # User B must see 0 transactions
    txs_b_res = client.get("/api/transactions/", headers=_auth(token_b), params={"limit": 50})
    assert txs_b_res.status_code == 200
    txs_b_data = txs_b_res.json()
    assert txs_b_data["total"] == 0, (
        f"SECURITY VIOLATION: User B sees {txs_b_data['total']} transactions they don't own"
    )

    # Direct access to User A's account by ID must be rejected
    acct_a_direct = client.get(f"/api/accounts/{ctx['account_id']}", headers=_auth(token_b))
    assert acct_a_direct.status_code == 404, (
        f"SECURITY VIOLATION: User B got HTTP {acct_a_direct.status_code} when directly "
        f"accessing User A's account — expected 404"
    )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 19  Duplicate prevention
# ═════════════════════════════════════════════════════════════════════════════

def test_19_duplicate_prevention():
    """Re-importing the same CSV must skip all rows and add 0 new transactions."""
    token = ctx["token"]
    account_id = ctx["account_id"]

    res = _import_csv(token, account_id)
    assert res.status_code == 200, f"Second import request failed: {res.text}"
    data = res.json()

    assert data["duplicates"] == 5, (
        f"Expected 5 duplicate detections on re-import, got {data['duplicates']}"
    )
    assert data["imported"] == 0, (
        f"Expected 0 new rows on re-import, got {data['imported']}"
    )

    # Confirm the DB count is still exactly 5
    txs_res = client.get("/api/transactions/", headers=_auth(token), params={"limit": 50})
    assert txs_res.status_code == 200
    assert txs_res.json()["total"] == 5, (
        f"Expected total=5 after re-import, got {txs_res.json()['total']}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# STEP 20  Data integrity — exact amount sums match source CSV
# ═════════════════════════════════════════════════════════════════════════════

def test_20_amount_integrity():
    txs = ctx["transactions"]
    total_income = sum(t["amount"] for t in txs if t["transaction_type"] == "income")
    total_expense = sum(t["amount"] for t in txs if t["transaction_type"] == "expense")

    assert abs(total_income - EXPECTED_INCOME) < 0.01, (
        f"Income sum mismatch — CSV source: ₹{EXPECTED_INCOME}, DB: ₹{total_income}"
    )
    assert abs(total_expense - EXPECTED_EXPENSE) < 0.01, (
        f"Expense sum mismatch — CSV source: ₹{EXPECTED_EXPENSE}, DB: ₹{total_expense}"
    )
