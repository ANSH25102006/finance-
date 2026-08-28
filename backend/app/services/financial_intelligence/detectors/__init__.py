# ============================================================
#  detectors/__init__.py
#
#  Importing this package registers every detector with the
#  singleton DetectorRegistry automatically.
#
#  The engine imports this module once; it never needs to know
#  the individual detector class names.
# ============================================================

from app.services.financial_intelligence.detector_registry import registry

from app.services.financial_intelligence.detectors.spending_spike import SpendingSpikeDetector
from app.services.financial_intelligence.detectors.budget_drift import BudgetDriftDetector
from app.services.financial_intelligence.detectors.lifestyle_inflation import LifestyleInflationDetector
from app.services.financial_intelligence.detectors.recurring_price_change import RecurringPriceChangeDetector
from app.services.financial_intelligence.detectors.income_change import IncomeChangeDetector
from app.services.financial_intelligence.detectors.emergency_fund import EmergencyFundDetector
from app.services.financial_intelligence.detectors.merchant_concentration import MerchantConcentrationDetector
from app.services.financial_intelligence.detectors.savings_opportunity import SavingsOpportunityDetector
from app.services.financial_intelligence.detectors.category_trend import CategoryTrendDetector
from app.services.financial_intelligence.detectors.large_transaction import LargeTransactionDetector
from app.services.financial_intelligence.detectors.cashflow_warning import CashflowWarningDetector
from app.services.financial_intelligence.detectors.goal_progress import GoalProgressDetector
from app.services.financial_intelligence.detectors.weekend_spending import WeekendSpendingDetector
from app.services.financial_intelligence.detectors.monthly_comparison import MonthlyComparisonDetector

# ── Register detectors in priority order ──────────────────────────────────
# The order here determines the evaluation order inside the engine.
# Ordering roughly: critical financial signals first, informational last.

_DETECTORS = [
    MonthlyComparisonDetector(),      # Overall monthly snapshot
    SpendingSpikeDetector(),          # Category-level anomalies
    BudgetDriftDetector(),            # Budget compliance
    CashflowWarningDetector(),        # End-of-month projection
    IncomeChangeDetector(),           # Salary / income changes
    EmergencyFundDetector(),          # Safety net
    GoalProgressDetector(),           # Goal health
    RecurringPriceChangeDetector(),   # Subscription price changes
    LargeTransactionDetector(),       # Unusually large individual spends
    MerchantConcentrationDetector(),  # Single-merchant dominance
    LifestyleInflationDetector(),     # Long-term discretionary creep
    CategoryTrendDetector(),          # Per-category trend analysis
    SavingsOpportunityDetector(),     # Subscription & habit savings
    WeekendSpendingDetector(),        # Weekend vs weekday patterns
]

for _detector in _DETECTORS:
    registry.register(_detector)

__all__ = [
    "SpendingSpikeDetector",
    "BudgetDriftDetector",
    "LifestyleInflationDetector",
    "RecurringPriceChangeDetector",
    "IncomeChangeDetector",
    "EmergencyFundDetector",
    "MerchantConcentrationDetector",
    "SavingsOpportunityDetector",
    "CategoryTrendDetector",
    "LargeTransactionDetector",
    "CashflowWarningDetector",
    "GoalProgressDetector",
    "WeekendSpendingDetector",
    "MonthlyComparisonDetector",
]
