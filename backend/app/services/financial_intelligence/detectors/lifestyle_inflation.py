# ============================================================
#  detectors/lifestyle_inflation.py
#  Detects sustained increases in discretionary spending over
#  the last 6 months (3+ consecutive monthly increases).
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
    detect_consecutive_direction,
    fmt_currency,
    last_n_months,
)

# Categories considered "discretionary"
_DISCRETIONARY_KEYWORDS = {
    "dining", "food", "restaurant", "entertainment", "shopping", "fashion",
    "travel", "leisure", "bar", "cafe", "coffee", "beauty", "personal care",
    "hobby", "subscription", "streaming",
}

_LOOK_BACK_MONTHS = 6
_MIN_STREAK = 3           # consecutive months increasing
_MIN_AVG_SPEND = 500.0    # ignore tiny categories


def _is_discretionary(cat_name: str) -> bool:
    lower = cat_name.lower()
    return any(kw in lower for kw in _DISCRETIONARY_KEYWORDS)


class LifestyleInflationDetector(BaseDetector):
    """
    Detects sustained month-over-month increases in discretionary
    spending over the past 6 months.

    One-off spikes are ignored — only sustained trends (3+ consecutive
    monthly increases) trigger an insight.
    """

    name = "LifestyleInflationDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        expenses = filter_by_type(ctx.transactions, "expense")
        if not expenses:
            return insights

        months = last_n_months(ctx.today, _LOOK_BACK_MONTHS)
        by_category = group_by_category(expenses)

        # Also roll up into a single "Total Discretionary" series
        total_series: list[float] = []
        for ym in months:
            month_disc = sum(
                total_amount(filter_by_month(cat_txs, ym[0], ym[1]))
                for cat_name, cat_txs in by_category.items()
                if _is_discretionary(cat_name)
            )
            total_series.append(month_disc)

        # Per-category inflation
        for cat_name, cat_txs in by_category.items():
            if not _is_discretionary(cat_name):
                continue
            if cat_name == "__uncategorised__":
                continue

            series = [
                total_amount(filter_by_month(cat_txs, ym[0], ym[1]))
                for ym in months
            ]

            avg = sum(s for s in series if s > 0) / max(1, sum(1 for s in series if s > 0))
            if avg < _MIN_AVG_SPEND:
                continue

            if detect_consecutive_direction(series, direction="up", min_streak=_MIN_STREAK):
                start_val = next((v for v in series if v > 0), 0)
                end_val = series[-1]
                pct_growth = ((end_val - start_val) / start_val * 100) if start_val > 0 else 0

                insights.append(
                    FinancialInsight(
                        type=InsightType.LIFESTYLE_INFLATION,
                        severity=InsightSeverity.WARNING,
                        title=f"Lifestyle inflation detected in {cat_name}",
                        summary=(
                            f"Your {cat_name} spending has increased for "
                            f"{_MIN_STREAK}+ consecutive months, growing from "
                            f"{fmt_currency(start_val)} to {fmt_currency(end_val)} "
                            f"({pct_growth:.1f}% increase)."
                        ),
                        recommendation=(
                            f"Review your {cat_name} habits. Gradual increases in "
                            f"discretionary spending can erode savings over time."
                        ),
                        score=min(pct_growth, 100.0),
                        category=cat_name,
                        metadata={
                            "monthly_series": {
                                f"{ym[0]}-{ym[1]:02d}": round(v, 2)
                                for ym, v in zip(months, series)
                            },
                            "pct_growth": round(pct_growth, 2),
                        },
                    )
                )

        # Aggregate discretionary inflation
        if detect_consecutive_direction(total_series, direction="up", min_streak=_MIN_STREAK):
            start_val = next((v for v in total_series if v > 0), 0)
            end_val = total_series[-1]
            pct_growth = ((end_val - start_val) / start_val * 100) if start_val > 0 else 0

            if pct_growth > 10 and end_val > _MIN_AVG_SPEND:
                insights.append(
                    FinancialInsight(
                        type=InsightType.LIFESTYLE_INFLATION,
                        severity=InsightSeverity.WARNING,
                        title="Overall lifestyle inflation trend detected",
                        summary=(
                            f"Your total discretionary spending has risen continuously "
                            f"for the past {_LOOK_BACK_MONTHS} months, now at "
                            f"{fmt_currency(end_val)}/month."
                        ),
                        recommendation=(
                            "Your overall discretionary spending is on a sustained upward trend. "
                            "Consider setting a fixed monthly discretionary budget."
                        ),
                        score=min(pct_growth, 100.0),
                        category="Discretionary (Total)",
                        metadata={
                            "monthly_totals": {
                                f"{ym[0]}-{ym[1]:02d}": round(v, 2)
                                for ym, v in zip(months, total_series)
                            },
                            "pct_growth": round(pct_growth, 2),
                        },
                    )
                )

        return insights
