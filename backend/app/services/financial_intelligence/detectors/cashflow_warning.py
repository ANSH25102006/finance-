# ============================================================
#  detectors/cashflow_warning.py
#  Projects month-end expenses using the current daily burn rate
#  and warns when projected expenses will exceed monthly income.
# ============================================================

from __future__ import annotations

import calendar

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_month,
    total_amount,
    fmt_currency,
    fmt_pct,
)

_WARN_RATIO = 0.90     # projected expenses > 90 % of income → WARNING
_CRIT_RATIO = 1.00     # projected expenses > 100 % of income → CRITICAL
_MIN_DAYS_ELAPSED = 7  # need at least 7 days of data to project


class CashflowWarningDetector(BaseDetector):
    """
    Extrapolates current-month spending to end-of-month using the
    daily burn rate so far.  Compares against total income for the month.

    Generates WARNING if projected expenses will exceed 90 % of income,
    CRITICAL if they will exceed income entirely.
    """

    name = "CashflowWarningDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        today = ctx.today
        curr_year, curr_month = today.year, today.month
        days_elapsed = today.day
        _, days_in_month = calendar.monthrange(curr_year, curr_month)

        if days_elapsed < _MIN_DAYS_ELAPSED:
            return insights  # too early in the month to project

        expenses = filter_by_type(ctx.transactions, "expense")
        income_txs = filter_by_type(ctx.transactions, "income")

        curr_expenses = filter_by_month(expenses, curr_year, curr_month)
        curr_income = total_amount(filter_by_month(income_txs, curr_year, curr_month))

        actual_expense = total_amount(curr_expenses)

        if actual_expense == 0 or curr_income == 0:
            return insights

        # Daily burn rate → project to end of month
        daily_burn = actual_expense / days_elapsed
        projected_expense = daily_burn * days_in_month

        days_remaining = days_in_month - days_elapsed
        projected_additional = daily_burn * days_remaining

        ratio = projected_expense / curr_income

        if ratio >= _CRIT_RATIO:
            severity = InsightSeverity.CRITICAL
            overspend = projected_expense - curr_income
            summary = (
                f"Based on your spending pace ({fmt_currency(daily_burn)}/day), "
                f"projected month-end expenses of {fmt_currency(projected_expense)} "
                f"will exceed your income of {fmt_currency(curr_income)} "
                f"by {fmt_currency(overspend)}."
            )
            recommendation = (
                f"You need to reduce spending by {fmt_currency(overspend)} to break even "
                f"this month. Focus on deferring non-essential purchases."
            )
        elif ratio >= _WARN_RATIO:
            severity = InsightSeverity.WARNING
            buffer = curr_income - projected_expense
            summary = (
                f"Your projected month-end expenses ({fmt_currency(projected_expense)}) "
                f"will consume {fmt_pct(ratio * 100)} of your {fmt_currency(curr_income)} income, "
                f"leaving only {fmt_currency(buffer)} as buffer."
            )
            recommendation = (
                f"Trim discretionary spending over the next {days_remaining} days "
                f"to maintain a healthy savings buffer this month."
            )
        else:
            return insights  # healthy cashflow, no insight needed

        insights.append(
            FinancialInsight(
                type=InsightType.CASHFLOW_WARNING,
                severity=severity,
                title="Cashflow warning this month",
                summary=summary,
                recommendation=recommendation,
                score=min(ratio * 100, 100.0),
                category=None,
                metadata={
                    "days_elapsed": days_elapsed,
                    "days_remaining": days_remaining,
                    "days_in_month": days_in_month,
                    "actual_expense": round(actual_expense, 2),
                    "daily_burn_rate": round(daily_burn, 2),
                    "projected_expense": round(projected_expense, 2),
                    "current_income": round(curr_income, 2),
                    "expense_to_income_ratio": round(ratio, 4),
                },
            )
        )

        return insights
