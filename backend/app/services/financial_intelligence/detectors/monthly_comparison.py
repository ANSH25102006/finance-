# ============================================================
#  detectors/monthly_comparison.py
#  Compares current month totals (income, expenses, savings rate)
#  against the previous month and generates a summary insight.
# ============================================================

from __future__ import annotations

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_month,
    total_amount,
    safe_pct_change,
    fmt_currency,
    fmt_pct,
    prev_month,
)


class MonthlyComparisonDetector(BaseDetector):
    """
    Compares key metrics between the current month and the prior month:
    - Total income
    - Total expenses
    - Savings (income − expenses)
    - Savings rate

    Generates a single summary insight per run.
    """

    name = "MonthlyComparisonDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        today = ctx.today
        curr_year, curr_month = today.year, today.month
        prev_year, prev_mo = prev_month(curr_year, curr_month)

        expenses = filter_by_type(ctx.transactions, "expense")
        income_txs = filter_by_type(ctx.transactions, "income")

        curr_exp = total_amount(filter_by_month(expenses, curr_year, curr_month))
        prev_exp = total_amount(filter_by_month(expenses, prev_year, prev_mo))
        curr_inc = total_amount(filter_by_month(income_txs, curr_year, curr_month))
        prev_inc = total_amount(filter_by_month(income_txs, prev_year, prev_mo))

        # Need at least some data from both months
        if (curr_exp == 0 and curr_inc == 0) or (prev_exp == 0 and prev_inc == 0):
            return insights

        curr_savings = curr_inc - curr_exp
        prev_savings = prev_inc - prev_exp
        curr_savings_rate = (curr_savings / curr_inc * 100) if curr_inc > 0 else 0
        prev_savings_rate = (prev_savings / prev_inc * 100) if prev_inc > 0 else 0

        exp_change_pct = safe_pct_change(prev_exp, curr_exp)
        inc_change_pct = safe_pct_change(prev_inc, curr_inc)
        savings_rate_delta = curr_savings_rate - prev_savings_rate

        # ── Determine overall severity ─────────────────────────────────
        if curr_savings_rate >= prev_savings_rate and curr_exp <= prev_exp:
            severity = InsightSeverity.SUCCESS
        elif curr_savings_rate < 0:
            severity = InsightSeverity.CRITICAL
        elif exp_change_pct > 15 or savings_rate_delta < -10:
            severity = InsightSeverity.WARNING
        else:
            severity = InsightSeverity.INFO

        # ── Build human-readable summary lines ─────────────────────────
        lines = []

        # Income line
        if abs(inc_change_pct) < 1:
            lines.append("Income unchanged.")
        elif inc_change_pct > 0:
            lines.append(f"Income increased {fmt_pct(inc_change_pct)} to {fmt_currency(curr_inc)}.")
        else:
            lines.append(f"Income decreased {fmt_pct(abs(inc_change_pct))} to {fmt_currency(curr_inc)}.")

        # Expense line
        if abs(exp_change_pct) < 1:
            lines.append("Total spending unchanged.")
        elif exp_change_pct > 0:
            lines.append(f"Total spending increased {fmt_pct(exp_change_pct)} to {fmt_currency(curr_exp)}.")
        else:
            lines.append(f"Total spending decreased {fmt_pct(abs(exp_change_pct))} to {fmt_currency(curr_exp)}.")

        # Savings rate line
        if abs(savings_rate_delta) < 0.5:
            lines.append(f"Savings rate stable at {fmt_pct(curr_savings_rate)}.")
        elif savings_rate_delta > 0:
            lines.append(
                f"Savings rate improved by {fmt_pct(savings_rate_delta)} "
                f"to {fmt_pct(curr_savings_rate)}."
            )
        else:
            lines.append(
                f"Savings rate declined by {fmt_pct(abs(savings_rate_delta))} "
                f"to {fmt_pct(curr_savings_rate)}."
            )

        summary = "  ".join(lines)

        rec_parts = []
        if exp_change_pct > 10:
            rec_parts.append("identify what drove the spending increase")
        if savings_rate_delta < -5:
            rec_parts.append("take steps to rebuild your savings rate")
        if curr_savings_rate < 10:
            rec_parts.append("aim to save at least 10–20% of income each month")
        if curr_savings_rate > prev_savings_rate:
            rec_parts.append("keep up the momentum and consider directing savings towards your goals")

        recommendation = (
            "Consider reviewing this month's transactions to " + " and ".join(rec_parts) + "."
            if rec_parts
            else "Your financial metrics are looking steady this month."
        )

        import calendar as cal
        month_name = cal.month_name[curr_month]

        insights.append(
            FinancialInsight(
                type=InsightType.MONTHLY_COMPARISON,
                severity=severity,
                title=f"{month_name} vs previous month summary",
                summary=summary,
                recommendation=recommendation,
                score=max(0.0, min(curr_savings_rate, 100.0)),
                category=None,
                metadata={
                    "current_month": {"year": curr_year, "month": curr_month},
                    "previous_month": {"year": prev_year, "month": prev_mo},
                    "current_income": round(curr_inc, 2),
                    "previous_income": round(prev_inc, 2),
                    "income_change_pct": round(inc_change_pct, 2),
                    "current_expenses": round(curr_exp, 2),
                    "previous_expenses": round(prev_exp, 2),
                    "expense_change_pct": round(exp_change_pct, 2),
                    "current_savings": round(curr_savings, 2),
                    "previous_savings": round(prev_savings, 2),
                    "current_savings_rate": round(curr_savings_rate, 2),
                    "previous_savings_rate": round(prev_savings_rate, 2),
                    "savings_rate_delta": round(savings_rate_delta, 2),
                },
            )
        )

        return insights
