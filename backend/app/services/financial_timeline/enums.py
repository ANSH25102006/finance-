# ============================================================
#  enums.py — Severity and type enumerations for timeline events
# ============================================================

from enum import Enum

class TimelineEventSeverity(str, Enum):
    """Severity levels for timeline events, ordering matches insights."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    SUCCESS = "SUCCESS"


class TimelineEventType(str, Enum):
    """Recognised timeline event types."""
    # Transaction-based events
    SALARY_CREDITED = "SALARY_CREDITED"
    LARGE_PURCHASE = "LARGE_PURCHASE"
    LARGE_REFUND = "LARGE_REFUND"
    
    # Insight-based events
    SPENDING_SPIKE = "SPENDING_SPIKE"
    BUDGET_WARNING = "BUDGET_WARNING"
    SUBSCRIPTION_DETECTED = "SUBSCRIPTION_DETECTED"
    PRICE_INCREASE = "PRICE_INCREASE"
    GOAL_MILESTONE = "GOAL_MILESTONE"
    EMERGENCY_FUND_MILESTONE = "EMERGENCY_FUND_MILESTONE"
    CASHFLOW_WARNING = "CASHFLOW_WARNING"
    SAVINGS_OPPORTUNITY = "SAVINGS_OPPORTUNITY"
    CATEGORY_TREND = "CATEGORY_TREND"
    LIFESTYLE_INFLATION = "LIFESTYLE_INFLATION"
    MONTHLY_COMPARISON = "MONTHLY_COMPARISON"

# For sorting based on severity
SEVERITY_ORDER: dict[TimelineEventSeverity, int] = {
    TimelineEventSeverity.CRITICAL: 0,
    TimelineEventSeverity.WARNING: 1,
    TimelineEventSeverity.INFO: 2,
    TimelineEventSeverity.SUCCESS: 3,
}
