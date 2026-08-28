# ============================================================
#  detectors/weekend_spending.py
#  Compares average daily spending on weekends (Sat/Sun)
#  versus weekdays over the past 30 days.
# ============================================================

from __future__ import annotations

from datetime import timedelta

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_date_range,
    is_weekend,
    total_amount,
    fmt_currency,
    fmt_pct,
)

_LOOK_BACK_DAYS = 30
_RATIO_THRESHOLD = 2.0   # weekend spend/day > 2× weekday → INFO insight
_MIN_TOTAL_SPEND = 1000.0


class WeekendSpendingDetector(BaseDetector):
    """
    Analyses the last 30 days of expense transactions.

    Splits them into weekend (Sat/Sun) and weekday transactions,
    computes average daily spending for each, and flags if weekend
    daily spend is significantly higher than weekday daily spend.
    """

    name = "WeekendSpendingDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        today = ctx.today
        start = today - timedelta(days=_LOOK_BACK_DAYS)

        expenses = filter_by_type(ctx.transactions, "expense")
        window = filter_by_date_range(expenses, start, today)

        if not window:
            return insights

        total = total_amount(window)
        if total < _MIN_TOTAL_SPEND:
            return insights

        # Split by weekend / weekday
        weekend_txs = [tx for tx in window if is_weekend(tx.transaction_date)]
        weekday_txs = [tx for tx in window if not is_weekend(tx.transaction_date)]

        weekend_total = total_amount(weekend_txs)
        weekday_total = total_amount(weekday_txs)

        # Count unique weekend and weekday days in the window
        all_dates = {tx.transaction_date for tx in window}
        weekend_days = sum(1 for d in all_dates if is_weekend(d)) or 1
        weekday_days = sum(1 for d in all_dates if not is_weekend(d)) or 1

        # Fall back to calendar day count if no transactions on those days
        import calendar as cal
        if weekend_days == 0:
            weekend_days = sum(
                1 for i in range(_LOOK_BACK_DAYS + 1)
                if is_weekend(start + timedelta(days=i))
            )
        if weekday_days == 0:
            weekday_days = _LOOK_BACK_DAYS + 1 - weekend_days

        avg_weekend = weekend_total / weekend_days
        avg_weekday = weekday_total / weekday_days if weekday_days > 0 else 0

        if avg_weekday == 0:
            return insights

        ratio = avg_weekend / avg_weekday
        pct_of_total = (weekend_total / total * 100) if total > 0 else 0

        if ratio >= _RATIO_THRESHOLD:
            insights.append(
                FinancialInsight(
                    type=InsightType.WEEKEND_SPENDING,
                    severity=InsightSeverity.INFO,
                    title="Weekend spending significantly higher than weekdays",
                    summary=(
                        f"Over the past {_LOOK_BACK_DAYS} days, your average weekend spending "
                        f"({fmt_currency(avg_weekend)}/day) is {ratio:.1f}× higher than "
                        f"your weekday average ({fmt_currency(avg_weekday)}/day). "
                        f"Weekends account for {fmt_pct(pct_of_total)} of total spend."
                    ),
                    recommendation=(
                        "Weekend spending on dining, entertainment, and shopping can add up. "
                        "Consider planning weekend activities with a set budget."
                    ),
                    score=min(ratio * 25, 100.0),
                    category=None,
                    metadata={
                        "weekend_total": round(weekend_total, 2),
                        "weekday_total": round(weekday_total, 2),
                        "avg_weekend_per_day": round(avg_weekend, 2),
                        "avg_weekday_per_day": round(avg_weekday, 2),
                        "ratio": round(ratio, 2),
                        "pct_of_total": round(pct_of_total, 2),
                        "look_back_days": _LOOK_BACK_DAYS,
                    },
                )
            )

        return insights
