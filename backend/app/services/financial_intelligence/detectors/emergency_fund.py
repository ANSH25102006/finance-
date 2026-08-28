# ============================================================
#  detectors/emergency_fund.py
#  Calculates monthly expense coverage from cash balance and
#  generates insights based on months of runway.
# ============================================================

from __future__ import annotations

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_month,
    total_amount,
    average,
    fmt_currency,
    last_n_months,
)

_LOOK_BACK_MONTHS = 3     # months used to compute average monthly expenses
_CRIT_MONTHS = 1.0        # < 1 month coverage → CRITICAL
_WARN_MONTHS = 3.0        # < 3 months coverage → WARNING
_GOOD_MONTHS = 6.0        # ≥ 6 months coverage → SUCCESS


class EmergencyFundDetector(BaseDetector):
    """
    Computes how many months of expenses the user's current cash
    balance covers, based on the 3-month average of expenses.

    Coverage < 1 month  → CRITICAL
    Coverage 1–3 months → WARNING
    Coverage 3–6 months → INFO
    Coverage ≥ 6 months → SUCCESS
    """

    name = "EmergencyFundDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        cash_balance = ctx.total_cash_balance
        if cash_balance <= 0:
            insights.append(
                FinancialInsight(
                    type=InsightType.EMERGENCY_FUND,
                    severity=InsightSeverity.CRITICAL,
                    title="No emergency fund available",
                    summary="Your total cash balance is zero or negative.",
                    recommendation=(
                        "Start building an emergency fund immediately. "
                        "Aim to save at least 1 month of expenses as a first milestone."
                    ),
                    score=100.0,
                    category=None,
                    metadata={"cash_balance": round(cash_balance, 2), "months_covered": 0.0},
                )
            )
            return insights

        expenses = filter_by_type(ctx.transactions, "expense")
        months = last_n_months(ctx.today, _LOOK_BACK_MONTHS + 1)[:-1]  # exclude current

        monthly_totals = [
            total_amount(filter_by_month(expenses, ym[0], ym[1]))
            for ym in months
        ]
        non_zero = [v for v in monthly_totals if v > 0]

        if not non_zero:
            # No expense history — can't compute coverage
            return insights

        avg_monthly_expense = average(non_zero)
        if avg_monthly_expense == 0:
            return insights

        months_covered = cash_balance / avg_monthly_expense

        if months_covered < _CRIT_MONTHS:
            severity = InsightSeverity.CRITICAL
            title = "Emergency fund critically low"
        elif months_covered < _WARN_MONTHS:
            severity = InsightSeverity.WARNING
            title = "Emergency fund below recommended level"
        elif months_covered < _GOOD_MONTHS:
            severity = InsightSeverity.INFO
            title = "Emergency fund building up"
        else:
            severity = InsightSeverity.SUCCESS
            title = "Emergency fund is healthy"

        target_amount = avg_monthly_expense * _GOOD_MONTHS
        shortfall = max(0.0, target_amount - cash_balance)

        insights.append(
            FinancialInsight(
                type=InsightType.EMERGENCY_FUND,
                severity=severity,
                title=title,
                summary=(
                    f"Your emergency fund covers {months_covered:.1f} month"
                    f"{'s' if months_covered != 1 else ''} of expenses "
                    f"(cash balance: {fmt_currency(cash_balance)}, "
                    f"avg monthly expenses: {fmt_currency(avg_monthly_expense)})."
                ),
                recommendation=(
                    f"The recommended target is {_GOOD_MONTHS:.0f} months of expenses "
                    f"({fmt_currency(target_amount)}). "
                    + (
                        f"You need {fmt_currency(shortfall)} more to reach the target."
                        if shortfall > 0
                        else "You have met the recommended emergency fund target!"
                    )
                ),
                score=min((months_covered / _GOOD_MONTHS) * 100, 100.0),
                category=None,
                metadata={
                    "cash_balance": round(cash_balance, 2),
                    "avg_monthly_expense": round(avg_monthly_expense, 2),
                    "months_covered": round(months_covered, 2),
                    "target_months": _GOOD_MONTHS,
                    "target_amount": round(target_amount, 2),
                    "shortfall": round(shortfall, 2),
                },
            )
        )

        return insights
