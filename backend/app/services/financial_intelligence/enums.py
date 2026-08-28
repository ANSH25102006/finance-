# ============================================================
#  enums.py — Severity and type enumerations for insights
# ============================================================

from enum import Enum


class InsightSeverity(str, Enum):
    """Severity levels for financial insights, ordered from most to least critical."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    SUCCESS = "SUCCESS"


class InsightType(str, Enum):
    """All recognised financial insight types produced by the engine."""
    SPENDING_SPIKE = "SPENDING_SPIKE"
    BUDGET_DRIFT = "BUDGET_DRIFT"
    PRICE_INCREASE = "PRICE_INCREASE"
    GOAL_PROGRESS = "GOAL_PROGRESS"
    INCOME_CHANGE = "INCOME_CHANGE"
    EMERGENCY_FUND = "EMERGENCY_FUND"
    SAVINGS_OPPORTUNITY = "SAVINGS_OPPORTUNITY"
    CATEGORY_TREND = "CATEGORY_TREND"
    LARGE_TRANSACTION = "LARGE_TRANSACTION"
    MERCHANT_CONCENTRATION = "MERCHANT_CONCENTRATION"
    CASHFLOW_WARNING = "CASHFLOW_WARNING"
    LIFESTYLE_INFLATION = "LIFESTYLE_INFLATION"
    MONTHLY_COMPARISON = "MONTHLY_COMPARISON"
    WEEKEND_SPENDING = "WEEKEND_SPENDING"


# Severity ordering map — used for sorting insights (lower = more severe)
SEVERITY_ORDER: dict[InsightSeverity, int] = {
    InsightSeverity.CRITICAL: 0,
    InsightSeverity.WARNING: 1,
    InsightSeverity.INFO: 2,
    InsightSeverity.SUCCESS: 3,
}
