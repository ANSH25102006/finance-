# ============================================================
#  detectors/category_trend.py
#  Compares last 6 months of spending per category and detects
#  sustained upward or downward trends (3+ consecutive months).
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

_LOOK_BACK_MONTHS = 6
_MIN_STREAK = 3
_MIN_AVG_SPEND = 200.0     # ignore negligible categories


class CategoryTrendDetector(BaseDetector):
    """
    Looks at the last 6 months of expense spending per category.
    Reports categories with a sustained upward or downward trend
    (3+ consecutive monthly changes in the same direction).
    """

    name = "CategoryTrendDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        expenses = filter_by_type(ctx.transactions, "expense")
        if not expenses:
            return insights

        months = last_n_months(ctx.today, _LOOK_BACK_MONTHS)
        by_category = group_by_category(expenses)

        for cat_name, cat_txs in by_category.items():
            if cat_name == "__uncategorised__":
                continue

            series = [
                total_amount(filter_by_month(cat_txs, ym[0], ym[1]))
                for ym in months
            ]

            non_zero = [v for v in series if v > 0]
            if not non_zero or (sum(non_zero) / len(non_zero)) < _MIN_AVG_SPEND:
                continue

            going_up = detect_consecutive_direction(series, direction="up", min_streak=_MIN_STREAK)
            going_down = detect_consecutive_direction(series, direction="down", min_streak=_MIN_STREAK)

            if not going_up and not going_down:
                continue

            direction = "up" if going_up else "down"
            start_val = next((v for v in series if v > 0), series[0])
            end_val = series[-1]
            pct = abs(end_val - start_val) / start_val * 100 if start_val > 0 else 0

            # Count actual consecutive streak
            streak = 0
            for i in range(len(series) - 1, 0, -1):
                if direction == "up" and series[i] > series[i - 1]:
                    streak += 1
                elif direction == "down" and series[i] < series[i - 1]:
                    streak += 1
                else:
                    break

            if direction == "up":
                severity = InsightSeverity.WARNING
                title = f"{cat_name} spending consistently rising"
                summary = (
                    f"{cat_name} spending has increased for {streak} consecutive "
                    f"month{'s' if streak != 1 else ''}, reaching {fmt_currency(end_val)} "
                    f"this month (up {pct:.1f}% from {fmt_currency(start_val)})."
                )
                recommendation = (
                    f"Review your {cat_name} spending and set a monthly budget "
                    f"to reverse the upward trend."
                )
            else:
                severity = InsightSeverity.SUCCESS
                title = f"{cat_name} spending declining"
                summary = (
                    f"{cat_name} spending has declined for {streak} consecutive "
                    f"month{'s' if streak != 1 else ''}, dropping to {fmt_currency(end_val)} "
                    f"(down {pct:.1f}% from {fmt_currency(start_val)})."
                )
                recommendation = (
                    f"Great work reducing {cat_name} spending! "
                    f"Consider redirecting those savings to your goals."
                )

            insights.append(
                FinancialInsight(
                    type=InsightType.CATEGORY_TREND,
                    severity=severity,
                    title=title,
                    summary=summary,
                    recommendation=recommendation,
                    score=min(pct, 100.0),
                    category=cat_name,
                    metadata={
                        "direction": direction,
                        "streak_months": streak,
                        "pct_change": round(pct, 2),
                        "monthly_series": {
                            f"{ym[0]}-{ym[1]:02d}": round(v, 2)
                            for ym, v in zip(months, series)
                        },
                    },
                )
            )

        return insights
