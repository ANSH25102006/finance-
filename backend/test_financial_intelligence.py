# ============================================================
#  test_financial_intelligence.py
#
#  Comprehensive unit tests for the Financial Intelligence Engine.
#  Tests run without a database — all detectors are tested with
#  mock data only, confirming fully deterministic behaviour.
# ============================================================

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ------------------------------------------------------------------ #
# Minimal ORM stubs (no DB required)
# ------------------------------------------------------------------ #

def _uuid():
    return uuid.uuid4()


@dataclass
class FakeCategory:
    id: uuid.UUID = field(default_factory=_uuid)
    name: str = "Misc"
    type: str = "expense"


@dataclass
class FakeTx:
    """Lightweight Transaction substitute."""
    id: uuid.UUID = field(default_factory=_uuid)
    description: str = "Test tx"
    amount: float = 100.0
    transaction_type: str = "expense"
    merchant: str | None = None
    transaction_date: date = field(default_factory=date.today)
    recurring: bool = False
    category: FakeCategory | None = None
    category_id: uuid.UUID | None = None

    def __post_init__(self):
        if self.category and self.category_id is None:
            self.category_id = self.category.id


@dataclass
class FakeBudget:
    id: uuid.UUID = field(default_factory=_uuid)
    user_id: uuid.UUID = field(default_factory=_uuid)
    category_id: uuid.UUID = field(default_factory=_uuid)
    amount: float = 5000.0
    month: int = date.today().month
    year: int = date.today().year
    category: FakeCategory | None = None


@dataclass
class FakeGoal:
    id: uuid.UUID = field(default_factory=_uuid)
    user_id: uuid.UUID = field(default_factory=_uuid)
    name: str = "Emergency Fund"
    target_amount: float = 100_000.0
    current_amount: float = 50_000.0
    monthly_contribution: float = 5_000.0
    deadline: date | None = None
    color: str | None = None
    icon: str | None = None


# ------------------------------------------------------------------ #
# Helper factories
# ------------------------------------------------------------------ #

def make_ctx(
    transactions=None,
    budgets=None,
    goals=None,
    total_cash_balance=50_000.0,
    today=None,
):
    from app.services.financial_intelligence.detector_base import DetectionContext
    from app.services.financial_intelligence.utils import (
        group_by_category,
        group_by_month,
        filter_by_type,
    )
    txs = transactions or []
    ctx = DetectionContext(
        user_id=str(_uuid()),
        today=today or date.today(),
        transactions=txs,
        budgets=budgets or [],
        goals=goals or [],
        total_cash_balance=total_cash_balance,
    )
    # Pre-compute views (mirrors the engine's _build_context)
    expenses = filter_by_type(txs, "expense")
    income_txs = filter_by_type(txs, "income")
    ctx.transactions_by_month = group_by_month(txs)
    ctx.expense_transactions_by_category = group_by_category(expenses)
    ctx.income_transactions_by_month = group_by_month(income_txs)
    return ctx


def expense(amount, cat_name="Food", days_ago=0, merchant=None, recurring=False, ref_date=None):
    cat = FakeCategory(name=cat_name)
    ref = ref_date or date.today()
    d = ref - timedelta(days=days_ago)
    return FakeTx(amount=amount, transaction_type="expense", merchant=merchant,
                  transaction_date=d, category=cat, category_id=cat.id, recurring=recurring)


def income(amount, days_ago=0, merchant=None, ref_date=None):
    ref = ref_date or date.today()
    d = ref - timedelta(days=days_ago)
    return FakeTx(amount=amount, transaction_type="income",
                  transaction_date=d, category=None, merchant=merchant or "Employer")


def month_expense(amount, cat_name, year, month, day=1, merchant=None, recurring=False):
    cat = FakeCategory(name=cat_name)
    d = date(year, month, day)
    return FakeTx(amount=amount, transaction_type="expense", merchant=merchant,
                  transaction_date=d, category=cat, category_id=cat.id, recurring=recurring)


def month_income(amount, year, month, day=5):
    d = date(year, month, day)
    return FakeTx(amount=amount, transaction_type="income", transaction_date=d)


# ================================================================== #
# utils.py tests
# ================================================================== #

class TestUtils:
    def test_prev_month_basic(self):
        from app.services.financial_intelligence.utils import prev_month
        assert prev_month(2024, 3) == (2024, 2)

    def test_prev_month_year_rollover(self):
        from app.services.financial_intelligence.utils import prev_month
        assert prev_month(2024, 1) == (2023, 12)

    def test_months_ago(self):
        from app.services.financial_intelligence.utils import months_ago
        today = date(2024, 6, 15)
        assert months_ago(today, 0) == (2024, 6)
        assert months_ago(today, 3) == (2024, 3)
        assert months_ago(today, 6) == (2023, 12)

    def test_last_n_months(self):
        from app.services.financial_intelligence.utils import last_n_months
        today = date(2024, 3, 10)
        result = last_n_months(today, 3)
        assert result == [(2024, 1), (2024, 2), (2024, 3)]

    def test_is_weekend(self):
        from app.services.financial_intelligence.utils import is_weekend
        # Saturday 2024-01-06
        assert is_weekend(date(2024, 1, 6)) is True
        # Monday 2024-01-08
        assert is_weekend(date(2024, 1, 8)) is False

    def test_total_amount(self):
        from app.services.financial_intelligence.utils import total_amount
        txs = [expense(100), expense(200), expense(300)]
        assert total_amount(txs) == pytest.approx(600.0)

    def test_total_amount_empty(self):
        from app.services.financial_intelligence.utils import total_amount
        assert total_amount([]) == 0.0

    def test_safe_pct_change(self):
        from app.services.financial_intelligence.utils import safe_pct_change
        assert safe_pct_change(100, 150) == pytest.approx(50.0)
        assert safe_pct_change(0, 150) == 0.0
        assert safe_pct_change(200, 100) == pytest.approx(-50.0)

    def test_average(self):
        from app.services.financial_intelligence.utils import average
        assert average([10, 20, 30]) == pytest.approx(20.0)
        assert average([]) == 0.0

    def test_detect_consecutive_direction_up(self):
        from app.services.financial_intelligence.utils import detect_consecutive_direction
        assert detect_consecutive_direction([100, 200, 300, 400], "up", 3) is True
        assert detect_consecutive_direction([100, 200, 150, 400], "up", 3) is False

    def test_detect_consecutive_direction_down(self):
        from app.services.financial_intelligence.utils import detect_consecutive_direction
        assert detect_consecutive_direction([400, 300, 200, 100], "down", 3) is True
        assert detect_consecutive_direction([400, 300, 350, 100], "down", 3) is False

    def test_detect_consecutive_insufficient_data(self):
        from app.services.financial_intelligence.utils import detect_consecutive_direction
        assert detect_consecutive_direction([100, 200], "up", 3) is False

    def test_group_by_month(self):
        from app.services.financial_intelligence.utils import group_by_month
        t1 = expense(100, days_ago=0)
        t1.transaction_date = date(2024, 1, 5)
        t2 = expense(200, days_ago=0)
        t2.transaction_date = date(2024, 1, 20)
        t3 = expense(300, days_ago=0)
        t3.transaction_date = date(2024, 2, 10)
        result = group_by_month([t1, t2, t3])
        assert len(result[(2024, 1)]) == 2
        assert len(result[(2024, 2)]) == 1

    def test_month_start_end(self):
        from app.services.financial_intelligence.utils import month_start, month_end
        assert month_start(2024, 2) == date(2024, 2, 1)
        assert month_end(2024, 2) == date(2024, 2, 29)  # 2024 is leap year


# ================================================================== #
# SpendingSpikeDetector tests
# ================================================================== #

class TestSpendingSpikeDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.spending_spike import SpendingSpikeDetector
        return SpendingSpikeDetector()

    def test_no_transactions(self):
        d = self._detector()
        ctx = make_ctx()
        assert d.detect(ctx) == []

    def test_no_history(self):
        """Only current month data — no historical baseline."""
        d = self._detector()
        today = date.today()
        txs = [month_expense(5000, "Food", today.year, today.month)]
        ctx = make_ctx(transactions=txs)
        assert d.detect(ctx) == []

    def test_spike_detected_warning(self):
        """Current month 40% above 3-month average → WARNING."""
        d = self._detector()
        today = date.today()
        cy, cm = today.year, today.month

        def pm(n):
            from app.services.financial_intelligence.utils import months_ago
            return months_ago(today, n)

        hist = [month_expense(10_000, "Food", *pm(3)),
                month_expense(10_000, "Food", *pm(2)),
                month_expense(10_000, "Food", *pm(1))]
        curr = [month_expense(14_200, "Food", cy, cm)]
        ctx = make_ctx(transactions=hist + curr)
        results = d.detect(ctx)
        assert len(results) == 1
        assert results[0].severity.value == "WARNING"
        assert "Food" in results[0].title

    def test_spike_detected_critical(self):
        """60% above average → CRITICAL."""
        d = self._detector()
        today = date.today()

        def pm(n):
            from app.services.financial_intelligence.utils import months_ago
            return months_ago(today, n)

        hist = [month_expense(10_000, "Dining", *pm(3)),
                month_expense(10_000, "Dining", *pm(2)),
                month_expense(10_000, "Dining", *pm(1))]
        curr = [month_expense(16_500, "Dining", today.year, today.month)]
        ctx = make_ctx(transactions=hist + curr)
        results = d.detect(ctx)
        assert any(r.severity.value == "CRITICAL" for r in results)

    def test_normal_variation_ignored(self):
        """10% increase is within normal range — no insight."""
        d = self._detector()
        today = date.today()

        def pm(n):
            from app.services.financial_intelligence.utils import months_ago
            return months_ago(today, n)

        hist = [month_expense(10_000, "Food", *pm(3)),
                month_expense(10_000, "Food", *pm(2)),
                month_expense(10_000, "Food", *pm(1))]
        curr = [month_expense(11_000, "Food", today.year, today.month)]
        ctx = make_ctx(transactions=hist + curr)
        results = d.detect(ctx)
        assert results == []

    def test_uncategorised_skipped(self):
        """Transactions with no category should be skipped."""
        d = self._detector()
        today = date.today()
        tx = expense(99999, cat_name="__uncategorised__")
        ctx = make_ctx(transactions=[tx])
        assert d.detect(ctx) == []


# ================================================================== #
# BudgetDriftDetector tests
# ================================================================== #

class TestBudgetDriftDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.budget_drift import BudgetDriftDetector
        return BudgetDriftDetector()

    def _budget(self, cat, amount=5000):
        b = FakeBudget(category=cat, category_id=cat.id, amount=amount)
        return b

    def test_no_budgets(self):
        d = self._detector()
        assert d.detect(make_ctx()) == []

    def test_under_threshold(self):
        """50% usage → no insight."""
        d = self._detector()
        cat = FakeCategory(name="Groceries")
        budget = self._budget(cat, amount=5000)
        tx = expense(2500, "Groceries")
        ctx = make_ctx(transactions=[tx], budgets=[budget])
        assert d.detect(ctx) == []

    def test_warning_threshold(self):
        """80% usage → WARNING."""
        d = self._detector()
        cat = FakeCategory(name="Groceries")
        budget = FakeBudget(category=cat, category_id=cat.id, amount=5000)
        tx = FakeTx(amount=4100, transaction_type="expense",
                    transaction_date=date.today(), category=cat, category_id=cat.id)
        ctx = make_ctx(transactions=[tx], budgets=[budget])
        results = d.detect(ctx)
        assert len(results) == 1
        assert results[0].severity.value == "WARNING"

    def test_critical_threshold(self):
        """110% usage → CRITICAL."""
        d = self._detector()
        cat = FakeCategory(name="Groceries")
        budget = FakeBudget(category=cat, category_id=cat.id, amount=5000)
        tx = FakeTx(amount=5600, transaction_type="expense",
                    transaction_date=date.today(), category=cat, category_id=cat.id)
        ctx = make_ctx(transactions=[tx], budgets=[budget])
        results = d.detect(ctx)
        assert len(results) == 1
        assert results[0].severity.value == "CRITICAL"

    def test_zero_budget_ignored(self):
        """Budget of 0 should be skipped to avoid division errors."""
        d = self._detector()
        cat = FakeCategory(name="Zero Cat")
        budget = FakeBudget(category=cat, category_id=cat.id, amount=0)
        ctx = make_ctx(budgets=[budget])
        assert d.detect(ctx) == []

    def test_different_month_budget_ignored(self):
        """Budgets for other months must not trigger insights."""
        d = self._detector()
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        cat = FakeCategory(name="Shopping")
        budget = FakeBudget(category=cat, category_id=cat.id, amount=1000, month=pm_, year=py)
        tx = expense(5000, "Shopping")
        ctx = make_ctx(transactions=[tx], budgets=[budget])
        assert d.detect(ctx) == []


# ================================================================== #
# LifestyleInflationDetector tests
# ================================================================== #

class TestLifestyleInflationDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.lifestyle_inflation import LifestyleInflationDetector
        return LifestyleInflationDetector()

    def test_no_transactions(self):
        assert self._detector().detect(make_ctx()) == []

    def test_inflation_detected(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = []
        for i in range(5, -1, -1):
            ym = months_ago(today, i)
            txs.append(month_expense(1000 + (5 - i) * 300, "Food", *ym))
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        assert any("Food" in r.category or "Discretionary" in (r.category or "") for r in results)

    def test_stable_spending_no_alert(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = [month_expense(5000, "Food", *months_ago(today, i)) for i in range(6, 0, -1)]
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        # Stable spending should not trigger lifestyle inflation
        assert all(r.type.value != "LIFESTYLE_INFLATION" for r in results)


# ================================================================== #
# RecurringPriceChangeDetector tests
# ================================================================== #

class TestRecurringPriceChangeDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.recurring_price_change import RecurringPriceChangeDetector
        return RecurringPriceChangeDetector()

    def test_no_recurring(self):
        ctx = make_ctx(transactions=[expense(500)])
        assert self._detector().detect(ctx) == []

    def test_price_increase_detected(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        prev_tx = month_expense(499, "Entertainment", py, pm_, merchant="Netflix", recurring=True)
        curr_tx = month_expense(649, "Entertainment", today.year, today.month, merchant="Netflix", recurring=True)
        ctx = make_ctx(transactions=[prev_tx, curr_tx])
        results = self._detector().detect(ctx)
        assert len(results) == 1
        assert results[0].severity.value == "CRITICAL"
        assert "Netflix" in results[0].title

    def test_price_decrease_detected(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        prev_tx = month_expense(649, "Entertainment", py, pm_, merchant="Spotify", recurring=True)
        curr_tx = month_expense(299, "Entertainment", today.year, today.month, merchant="Spotify", recurring=True)
        ctx = make_ctx(transactions=[prev_tx, curr_tx])
        results = self._detector().detect(ctx)
        assert len(results) == 1
        assert results[0].severity.value == "INFO"

    def test_insignificant_change_ignored(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        prev_tx = month_expense(500, "Entertainment", py, pm_, merchant="Netflix", recurring=True)
        curr_tx = month_expense(502, "Entertainment", today.year, today.month, merchant="Netflix", recurring=True)
        ctx = make_ctx(transactions=[prev_tx, curr_tx])
        assert self._detector().detect(ctx) == []


# ================================================================== #
# IncomeChangeDetector tests
# ================================================================== #

class TestIncomeChangeDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.income_change import IncomeChangeDetector
        return IncomeChangeDetector()

    def test_no_income(self):
        ctx = make_ctx(transactions=[expense(1000)])
        assert self._detector().detect(ctx) == []

    def test_income_increase(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        prev_inc = month_income(50_000, py, pm_)
        curr_inc = month_income(60_000, today.year, today.month)
        results = self._detector().detect(make_ctx(transactions=[prev_inc, curr_inc]))
        assert any(r.severity.value == "SUCCESS" for r in results)

    def test_income_decrease(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        prev_inc = month_income(60_000, py, pm_)
        curr_inc = month_income(45_000, today.year, today.month)
        results = self._detector().detect(make_ctx(transactions=[prev_inc, curr_inc]))
        assert any(r.severity.value == "WARNING" for r in results)

    def test_missed_salary(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        prev_inc = month_income(50_000, py, pm_)
        # Force today to day 15 so missed salary trigger activates
        test_today = date(today.year, today.month, 15)
        ctx = make_ctx(transactions=[prev_inc], today=test_today)
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "CRITICAL" for r in results)

    def test_stable_income_no_insight(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        prev_inc = month_income(50_000, py, pm_)
        curr_inc = month_income(51_000, today.year, today.month)  # < 10% change
        results = self._detector().detect(make_ctx(transactions=[prev_inc, curr_inc]))
        # Stable income → no MoM insight; may still get irregular/other but not MoM
        mom_results = [r for r in results if "increased" in r.title.lower() or "decreased" in r.title.lower()]
        assert mom_results == []


# ================================================================== #
# EmergencyFundDetector tests
# ================================================================== #

class TestEmergencyFundDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.emergency_fund import EmergencyFundDetector
        return EmergencyFundDetector()

    def test_no_expenses(self):
        ctx = make_ctx(total_cash_balance=100_000)
        assert self._detector().detect(ctx) == []

    def test_zero_balance_critical(self):
        ctx = make_ctx(total_cash_balance=0)
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "CRITICAL" for r in results)

    def test_good_coverage(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = [month_expense(10_000, "Living", *months_ago(today, i)) for i in [1, 2, 3]]
        ctx = make_ctx(transactions=txs, total_cash_balance=80_000)
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "SUCCESS" for r in results)
        assert results[0].metadata["months_covered"] == pytest.approx(8.0)

    def test_low_coverage_warning(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = [month_expense(30_000, "Living", *months_ago(today, i)) for i in [1, 2, 3]]
        ctx = make_ctx(transactions=txs, total_cash_balance=60_000)
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "WARNING" for r in results)

    def test_critical_low_coverage(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = [month_expense(50_000, "Living", *months_ago(today, i)) for i in [1, 2, 3]]
        ctx = make_ctx(transactions=txs, total_cash_balance=20_000)
        results = self._detector().detect(ctx)
        assert any(r.severity.value in ["CRITICAL", "WARNING"] for r in results)


# ================================================================== #
# MerchantConcentrationDetector tests
# ================================================================== #

class TestMerchantConcentrationDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.merchant_concentration import MerchantConcentrationDetector
        return MerchantConcentrationDetector()

    def test_no_transactions(self):
        assert self._detector().detect(make_ctx()) == []

    def test_high_concentration(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        ym = months_ago(today, 1)
        txs = (
            [month_expense(4800, "Dining", *ym, merchant="Swiggy")] +
            [month_expense(200, "Dining", *ym, merchant="Zomato")]
        )
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        assert any("Dining" in r.category for r in results)

    def test_diversified_spending_no_alert(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        ym = months_ago(today, 1)
        txs = [
            month_expense(1000, "Dining", *ym, merchant="M1"),
            month_expense(900, "Dining", *ym, merchant="M2"),
            month_expense(1100, "Dining", *ym, merchant="M3"),
        ]
        ctx = make_ctx(transactions=txs)
        assert self._detector().detect(ctx) == []


# ================================================================== #
# SavingsOpportunityDetector tests
# ================================================================== #

class TestSavingsOpportunityDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.savings_opportunity import SavingsOpportunityDetector
        return SavingsOpportunityDetector()

    def test_no_transactions(self):
        assert self._detector().detect(make_ctx()) == []

    def test_subscriptions_detected(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = []
        for i in range(3):
            ym = months_ago(today, i)
            txs.append(month_expense(649, "Entertainment", *ym, merchant="Netflix", recurring=True))
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        assert any("Subscription" in r.category or "Netflix" in r.summary for r in results)

    def test_high_frequency_purchase(self):
        today = date(date.today().year, date.today().month, 20)
        # 10 coffee shop visits this month
        txs = [expense(200, "Food", days_ago=i, merchant="Starbucks", ref_date=today) for i in range(10)]
        ctx = make_ctx(transactions=txs, today=today)
        results = self._detector().detect(ctx)
        assert any("Starbucks" in r.summary for r in results)


# ================================================================== #
# CategoryTrendDetector tests
# ================================================================== #

class TestCategoryTrendDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.category_trend import CategoryTrendDetector
        return CategoryTrendDetector()

    def test_no_transactions(self):
        assert self._detector().detect(make_ctx()) == []

    def test_upward_trend(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = []
        for i, amount in enumerate([2000, 2500, 3000, 3500, 4000, 4500]):
            ym = months_ago(today, 5 - i)
            txs.append(month_expense(amount, "Entertainment", *ym))
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "WARNING" for r in results)

    def test_downward_trend(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = []
        for i, amount in enumerate([4500, 4000, 3500, 3000, 2500, 2000]):
            ym = months_ago(today, 5 - i)
            txs.append(month_expense(amount, "Shopping", *ym))
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "SUCCESS" for r in results)

    def test_no_trend_with_volatile_data(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        # Zigzag pattern → no trend
        txs = []
        for i, amount in enumerate([1000, 2000, 1000, 2000, 1000, 2000]):
            ym = months_ago(today, 5 - i)
            txs.append(month_expense(amount, "Transport", *ym))
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        assert results == []


# ================================================================== #
# LargeTransactionDetector tests
# ================================================================== #

class TestLargeTransactionDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.large_transaction import LargeTransactionDetector
        return LargeTransactionDetector()

    def test_no_transactions(self):
        assert self._detector().detect(make_ctx()) == []

    def test_large_amount_flagged(self):
        today = date.today()
        txs = [expense(25_000, "Electronics")]
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        assert len(results) >= 1
        assert results[0].metadata["amount"] == 25_000.0

    def test_small_transaction_not_flagged(self):
        """A ₹500 transaction among many should not be flagged."""
        today = date.today()
        # Add enough background spend so ₹500 is a tiny fraction of the month
        txs = [expense(500, "Food")] + [expense(2000, "Living") for _ in range(20)]
        ctx = make_ctx(transactions=txs)
        assert self._detector().detect(ctx) == []

    def test_max_five_insights(self):
        today = date.today()
        txs = [expense(15_000 + i * 1000, f"Cat{i}") for i in range(10)]
        ctx = make_ctx(transactions=txs)
        results = self._detector().detect(ctx)
        assert len(results) <= 5

    def test_single_large_transaction_metadata(self):
        today = date.today()
        cat = FakeCategory(name="Travel")
        tx = FakeTx(amount=50_000, transaction_type="expense",
                    merchant="IndiGo", transaction_date=today,
                    category=cat, category_id=cat.id)
        ctx = make_ctx(transactions=[tx])
        results = self._detector().detect(ctx)
        assert results[0].metadata["merchant"] == "IndiGo"


# ================================================================== #
# CashflowWarningDetector tests
# ================================================================== #

class TestCashflowWarningDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.cashflow_warning import CashflowWarningDetector
        return CashflowWarningDetector()

    def test_no_transactions(self):
        assert self._detector().detect(make_ctx()) == []

    def test_healthy_cashflow_no_alert(self):
        # Low spending, high income → no alert
        today = date(today_ref := date.today().year, date.today().month, 15)
        txs = (
            [month_income(100_000, today.year, today.month)] +
            [expense(1000, days_ago=i) for i in range(14)]
        )
        ctx = make_ctx(transactions=txs, today=today)
        assert self._detector().detect(ctx) == []

    def test_overspending_critical(self):
        today = date(date.today().year, date.today().month, 15)
        txs = (
            [month_income(30_000, today.year, today.month)] +
            [expense(2500, days_ago=i, ref_date=today) for i in range(14)]  # 2500/day * 30 = 75k projected
        )
        ctx = make_ctx(transactions=txs, today=today)
        results = self._detector().detect(ctx)
        assert any(r.severity.value in ["WARNING", "CRITICAL"] for r in results)

    def test_early_in_month_no_alert(self):
        """Less than 7 days of data — engine should not project."""
        today = date(date.today().year, date.today().month, 3)
        txs = [month_income(50_000, today.year, today.month), expense(10_000)]
        ctx = make_ctx(transactions=txs, today=today)
        assert self._detector().detect(ctx) == []


# ================================================================== #
# GoalProgressDetector tests
# ================================================================== #

class TestGoalProgressDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.goal_progress import GoalProgressDetector
        return GoalProgressDetector()

    def test_no_goals(self):
        assert self._detector().detect(make_ctx()) == []

    def test_completed_goal(self):
        goal = FakeGoal(target_amount=100_000, current_amount=110_000, monthly_contribution=5000)
        ctx = make_ctx(goals=[goal])
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "SUCCESS" and "achieved" in r.title.lower() for r in results)

    def test_no_contribution_critical(self):
        goal = FakeGoal(target_amount=100_000, current_amount=10_000, monthly_contribution=0)
        ctx = make_ctx(goals=[goal])
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "CRITICAL" for r in results)

    def test_on_track(self):
        today = date.today()
        deadline = date(today.year + 1, today.month, 1)
        goal = FakeGoal(target_amount=60_000, current_amount=0,
                        monthly_contribution=6000, deadline=deadline)
        ctx = make_ctx(goals=[goal])
        results = self._detector().detect(ctx)
        assert any(r.severity.value in ["SUCCESS", "INFO"] for r in results)

    def test_behind_schedule_warning(self):
        today = date.today()
        deadline = date(today.year, (today.month % 12) + 1, 1)  # next month
        goal = FakeGoal(target_amount=100_000, current_amount=0,
                        monthly_contribution=1000, deadline=deadline)
        ctx = make_ctx(goals=[goal])
        results = self._detector().detect(ctx)
        assert any(r.severity.value == "WARNING" for r in results)

    def test_zero_target_skipped(self):
        goal = FakeGoal(target_amount=0, current_amount=0)
        ctx = make_ctx(goals=[goal])
        assert self._detector().detect(ctx) == []


# ================================================================== #
# WeekendSpendingDetector tests
# ================================================================== #

class TestWeekendSpendingDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.weekend_spending import WeekendSpendingDetector
        return WeekendSpendingDetector()

    def test_no_transactions(self):
        assert self._detector().detect(make_ctx()) == []

    def test_weekend_dominance_flagged(self):
        from app.services.financial_intelligence.utils import is_weekend
        # Create weekend transactions (much higher) and weekday ones
        txs = []
        today = date.today()
        for i in range(30):
            d = today - timedelta(days=i)
            if is_weekend(d):
                t = expense(3000)
                t.transaction_date = d
            else:
                t = expense(200)
                t.transaction_date = d
            txs.append(t)
        ctx = make_ctx(transactions=txs, today=today)
        results = self._detector().detect(ctx)
        assert any(r.type.value == "WEEKEND_SPENDING" for r in results)

    def test_equal_spending_no_alert(self):
        today = date.today()
        txs = [expense(1000, days_ago=i) for i in range(30)]
        ctx = make_ctx(transactions=txs, today=today)
        # Equal daily spending → ratio close to 1 → no alert
        results = self._detector().detect(ctx)
        assert all(r.type.value != "WEEKEND_SPENDING" for r in results)


# ================================================================== #
# MonthlyComparisonDetector tests
# ================================================================== #

class TestMonthlyComparisonDetector:
    def _detector(self):
        from app.services.financial_intelligence.detectors.monthly_comparison import MonthlyComparisonDetector
        return MonthlyComparisonDetector()

    def test_no_data(self):
        assert self._detector().detect(make_ctx()) == []

    def test_comparison_generated(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        txs = [
            month_income(50_000, today.year, today.month),
            month_expense(30_000, "Living", today.year, today.month),
            month_income(50_000, py, pm_),
            month_expense(28_000, "Living", py, pm_),
        ]
        results = self._detector().detect(make_ctx(transactions=txs))
        assert len(results) == 1
        assert results[0].type.value == "MONTHLY_COMPARISON"

    def test_negative_savings_rate_critical(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        txs = [
            month_income(30_000, today.year, today.month),
            month_expense(45_000, "Living", today.year, today.month),
            month_income(30_000, py, pm_),
            month_expense(25_000, "Living", py, pm_),
        ]
        results = self._detector().detect(make_ctx(transactions=txs))
        assert any(r.severity.value in ["CRITICAL", "WARNING"] for r in results)

    def test_improved_savings_success(self):
        today = date.today()
        from app.services.financial_intelligence.utils import prev_month
        py, pm_ = prev_month(today.year, today.month)
        txs = [
            month_income(60_000, today.year, today.month),
            month_expense(20_000, "Living", today.year, today.month),
            month_income(60_000, py, pm_),
            month_expense(35_000, "Living", py, pm_),
        ]
        results = self._detector().detect(make_ctx(transactions=txs))
        assert any(r.severity.value == "SUCCESS" for r in results)


# ================================================================== #
# Engine integration tests
# ================================================================== #

class TestFinancialIntelligenceEngine:
    """Test the engine orchestration layer with a mock DB."""

    def _make_engine(self, transactions=None, budgets=None, goals=None, balance=50_000):
        from app.services.financial_intelligence.engine import FinancialIntelligenceEngine
        from sqlalchemy.orm import Session

        engine = FinancialIntelligenceEngine.__new__(FinancialIntelligenceEngine)
        engine.db = MagicMock(spec=Session)
        engine.user_id = _uuid()

        engine._load_transactions = MagicMock(return_value=transactions or [])
        engine._load_budgets = MagicMock(return_value=budgets or [])
        engine._load_goals = MagicMock(return_value=goals or [])
        engine._load_total_cash_balance = MagicMock(return_value=balance)
        return engine

    def test_empty_dataset_returns_list(self):
        engine = self._make_engine()
        results = engine.run()
        assert isinstance(results, list)

    def test_results_sorted_by_severity(self):
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago, prev_month
        py, pm_ = prev_month(today.year, today.month)

        txs = [
            month_income(50_000, today.year, today.month),
            month_expense(80_000, "Living", today.year, today.month),  # overspending
            month_income(50_000, py, pm_),
            month_expense(20_000, "Living", py, pm_),
        ]
        engine = self._make_engine(transactions=txs)
        results = engine.run()

        from app.services.financial_intelligence.enums import SEVERITY_ORDER
        severities = [SEVERITY_ORDER[r.severity] for r in results]
        assert severities == sorted(severities)

    def test_deduplication(self):
        """Multiple detectors may produce same (type, category) — only one should remain."""
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago

        # Create data likely to produce duplicate insights
        txs = [month_expense(20_000, "Food", *months_ago(today, i)) for i in range(4)]
        engine = self._make_engine(transactions=txs)
        results = engine.run()

        # Check no duplicate dedup keys
        keys = [r.dedup_key for r in results]
        assert len(keys) == len(set(keys)), "Duplicate insights found after dedup"

    def test_results_are_financial_insights(self):
        from app.services.financial_intelligence.models import FinancialInsight
        engine = self._make_engine()
        results = engine.run()
        assert all(isinstance(r, FinancialInsight) for r in results)

    def test_to_dict_serialisable(self):
        import json
        today = date.today()
        from app.services.financial_intelligence.utils import months_ago
        txs = [month_income(50_000, today.year, today.month)]
        engine = self._make_engine(transactions=txs)
        results = engine.run()
        # All insights must be JSON-serialisable
        for r in results:
            json.dumps(r.to_dict())  # should not raise

    def test_detector_error_does_not_crash_engine(self):
        """A broken detector should log and be skipped, not crash the engine."""
        from app.services.financial_intelligence.detector_base import BaseDetector
        from app.services.financial_intelligence.detector_registry import DetectorRegistry

        class BrokenDetector(BaseDetector):
            name = "BrokenDetector"
            def detect(self, ctx):
                raise RuntimeError("Intentional test error")

        test_registry = DetectorRegistry()
        test_registry.register(BrokenDetector())

        engine = self._make_engine()
        # Run with the test registry directly
        ctx = engine._build_context()
        results = engine._run_detectors(ctx, test_registry)
        assert results == []  # error swallowed, empty list returned


# ================================================================== #
# FinancialInsight model tests
# ================================================================== #

class TestFinancialInsightModel:
    def test_dedup_key(self):
        from app.services.financial_intelligence.models import FinancialInsight
        from app.services.financial_intelligence.enums import InsightType, InsightSeverity
        i = FinancialInsight(
            type=InsightType.SPENDING_SPIKE,
            severity=InsightSeverity.WARNING,
            title="Test",
            summary="S",
            recommendation="R",
            category="Food",
        )
        assert i.dedup_key == ("SPENDING_SPIKE", "Food")

    def test_to_dict_contains_all_fields(self):
        from app.services.financial_intelligence.models import FinancialInsight
        from app.services.financial_intelligence.enums import InsightType, InsightSeverity
        i = FinancialInsight(
            type=InsightType.BUDGET_DRIFT,
            severity=InsightSeverity.CRITICAL,
            title="Title",
            summary="Summary",
            recommendation="Recommendation",
            score=85.0,
            category="Groceries",
            metadata={"key": "value"},
        )
        d = i.to_dict()
        required_keys = {"id", "type", "severity", "title", "summary",
                         "recommendation", "score", "category", "created_at", "metadata"}
        assert required_keys.issubset(d.keys())
        assert d["score"] == 85.0
        assert d["category"] == "Groceries"
