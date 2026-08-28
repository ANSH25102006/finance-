# ============================================================
#  detectors/budget_drift.py
#  Compares current-month category spending against configured
#  budgets and warns when the user is approaching or over limit.
# ============================================================

from __future__ import annotations

import calendar
from datetime import date

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

_WARN_THRESHOLD = 0.75   # 75 % budget used → WARNING
_CRIT_THRESHOLD = 1.00   # 100 % budget used → CRITICAL


class BudgetDriftDetector(BaseDetector):
    """
    Compares current month spending per category against the user's
    configured Budget records.

    Generates:
    - WARNING  → 75 %–99 % of budget consumed
    - CRITICAL → 100 %+ of budget consumed (over-budget)
    """

    name = "BudgetDriftDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        if not ctx.budgets:
            return insights

        today = ctx.today
        curr_year, curr_month = today.year, today.month
        _, days_in_month = calendar.monthrange(curr_year, curr_month)
        days_remaining = days_in_month - today.day

        expenses = filter_by_type(ctx.transactions, "expense")
        curr_expenses = filter_by_month(expenses, curr_year, curr_month)

        # Build a quick lookup: category_id → total spent this month
        spent_by_cat: dict[str, float] = {}
        for tx in curr_expenses:
            if tx.category_id is None:
                continue
            cat_id = str(tx.category_id)
            spent_by_cat[cat_id] = spent_by_cat.get(cat_id, 0.0) + float(tx.amount)

        for budget in ctx.budgets:
            if budget.month != curr_month or budget.year != curr_year:
                continue

            cat_id = str(budget.category_id)
            budget_amount = float(budget.amount)
            if budget_amount <= 0:
                continue

            spent = spent_by_cat.get(cat_id, 0.0)
            usage_ratio = spent / budget_amount

            if usage_ratio >= _CRIT_THRESHOLD:
                severity = InsightSeverity.CRITICAL
            elif usage_ratio >= _WARN_THRESHOLD:
                severity = InsightSeverity.WARNING
            else:
                continue

            cat_name = budget.category.name if budget.category else "Unknown"
            pct_used = usage_ratio * 100
            remaining = max(0.0, budget_amount - spent)

            if usage_ratio >= _CRIT_THRESHOLD:
                overspend = spent - budget_amount
                summary = (
                    f"You have exceeded your {cat_name} budget by "
                    f"{fmt_currency(overspend)} ({fmt_pct(pct_used - 100)} over limit)."
                )
                recommendation = (
                    f"You have spent {fmt_currency(spent)} against a budget of "
                    f"{fmt_currency(budget_amount)}. Consider reducing {cat_name} "
                    f"expenses for the remaining {days_remaining} days of the month."
                )
            else:
                summary = (
                    f"You have used {fmt_pct(pct_used)} of your {cat_name} budget "
                    f"with {days_remaining} day{'s' if days_remaining != 1 else ''} remaining."
                )
                recommendation = (
                    f"Only {fmt_currency(remaining)} left in your {cat_name} budget. "
                    f"Pace your spending to avoid going over."
                )

            insights.append(
                FinancialInsight(
                    type=InsightType.BUDGET_DRIFT,
                    severity=severity,
                    title=f"{cat_name} budget {'exceeded' if usage_ratio >= _CRIT_THRESHOLD else 'nearing limit'}",
                    summary=summary,
                    recommendation=recommendation,
                    score=min(pct_used, 100.0),
                    category=cat_name,
                    metadata={
                        "budget_amount": budget_amount,
                        "spent": round(spent, 2),
                        "usage_pct": round(pct_used, 2),
                        "remaining": round(remaining, 2),
                        "days_remaining": days_remaining,
                    },
                )
            )

        return insights
