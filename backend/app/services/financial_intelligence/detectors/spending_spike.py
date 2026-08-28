# ============================================================
#  detectors/spending_spike.py
#  Detects categories whose current-month spend exceeds the
#  3-month historical average by a configurable threshold.
# ============================================================

from __future__ import annotations

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    group_by_category,
    filter_by_month,
    total_amount,
    safe_pct_change,
    fmt_currency,
    fmt_pct,
    last_n_months,
)

# Thresholds
_WARN_PCT = 25.0    # spending is 25 %+ above historical average → WARNING
_CRIT_PCT = 50.0    # spending is 50 %+ above historical average → CRITICAL
_MIN_HISTORICAL_AMOUNT = 100.0  # ignore categories with negligible history


class SpendingSpikeDetector(BaseDetector):
    """
    Compares current-month category spending against the 3-month
    historical average.  Only expense transactions are considered.
    """

    name = "SpendingSpikeDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        expenses = filter_by_type(ctx.transactions, "expense")
        if not expenses:
            return insights

        today = ctx.today
        curr_year, curr_month = today.year, today.month

        # Historical window: the 3 months before the current month
        hist_months = last_n_months(today, 4)[:-1]  # excludes current month

        # Group all expenses by category then by month
        by_category = group_by_category(expenses)

        for cat_name, cat_txs in by_category.items():
            if cat_name == "__uncategorised__":
                continue

            # Current month spend
            curr_txs = filter_by_month(cat_txs, curr_year, curr_month)
            curr_spend = total_amount(curr_txs)

            if curr_spend == 0:
                continue

            # Historical monthly totals
            hist_totals = [
                total_amount(filter_by_month(cat_txs, ym[0], ym[1]))
                for ym in hist_months
            ]
            non_zero_hist = [v for v in hist_totals if v > 0]

            if not non_zero_hist:
                continue  # no history → skip

            hist_avg = sum(non_zero_hist) / len(non_zero_hist)
            if hist_avg < _MIN_HISTORICAL_AMOUNT:
                continue

            pct_change = safe_pct_change(hist_avg, curr_spend)

            if pct_change >= _CRIT_PCT:
                severity = InsightSeverity.CRITICAL
            elif pct_change >= _WARN_PCT:
                severity = InsightSeverity.WARNING
            else:
                continue  # normal variation

            insights.append(
                FinancialInsight(
                    type=InsightType.SPENDING_SPIKE,
                    severity=severity,
                    title=f"{cat_name} spending spike detected",
                    summary=(
                        f"Your {cat_name} spending this month is {fmt_currency(curr_spend)}, "
                        f"which is {fmt_pct(pct_change)} above your 3-month average of "
                        f"{fmt_currency(hist_avg)}."
                    ),
                    recommendation=(
                        f"Review your {cat_name} transactions this month to identify "
                        f"any unexpected or avoidable expenses."
                    ),
                    score=min(pct_change, 100.0),
                    category=cat_name,
                    metadata={
                        "current_spend": round(curr_spend, 2),
                        "historical_average": round(hist_avg, 2),
                        "pct_change": round(pct_change, 2),
                        "historical_months": [f"{ym[0]}-{ym[1]:02d}" for ym in hist_months],
                    },
                )
            )

        return insights
