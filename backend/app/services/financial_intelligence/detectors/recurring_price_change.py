# ============================================================
#  detectors/recurring_price_change.py
#  Detects month-over-month price changes for recurring
#  merchant transactions (subscriptions, utilities, etc.).
# ============================================================

from __future__ import annotations

from collections import defaultdict

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_month,
    fmt_currency,
    prev_month,
)

_MIN_AMOUNT = 50.0          # Ignore very small recurring charges
_CHANGE_THRESHOLD = 0.05    # 5% change is considered significant


class RecurringPriceChangeDetector(BaseDetector):
    """
    Groups recurring expense transactions by merchant and compares
    average amounts between the current and previous month.

    Generates CRITICAL for price increases, INFO for price decreases.
    """

    name = "RecurringPriceChangeDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        # Only look at recurring expenses
        recurring = [
            tx for tx in ctx.transactions
            if tx.transaction_type == "expense" and tx.recurring
        ]
        if not recurring:
            return insights

        today = ctx.today
        curr_year, curr_month = today.year, today.month
        prev_year, prev_mo = prev_month(curr_year, curr_month)

        curr_txs = filter_by_month(recurring, curr_year, curr_month)
        prev_txs = filter_by_month(recurring, prev_year, prev_mo)

        # Compute average amount per merchant for each month
        def avg_by_merchant(txs: list) -> dict[str, float]:
            totals: dict[str, float] = defaultdict(float)
            counts: dict[str, int] = defaultdict(int)
            for tx in txs:
                m = (tx.merchant or "").strip() or tx.description
                totals[m] += float(tx.amount)
                counts[m] += 1
            return {m: totals[m] / counts[m] for m in totals}

        curr_avg = avg_by_merchant(curr_txs)
        prev_avg = avg_by_merchant(prev_txs)

        common_merchants = set(curr_avg.keys()) & set(prev_avg.keys())

        for merchant in sorted(common_merchants):
            old_price = prev_avg[merchant]
            new_price = curr_avg[merchant]

            if old_price < _MIN_AMOUNT:
                continue

            change_ratio = (new_price - old_price) / old_price

            if abs(change_ratio) < _CHANGE_THRESHOLD:
                continue  # insignificant change

            if change_ratio > 0:
                severity = InsightSeverity.CRITICAL
                direction = "increased"
                rec = (
                    f"Check if the price increase for {merchant} is expected. "
                    f"Consider switching to a cheaper alternative or cancelling "
                    f"if you no longer need the service."
                )
            else:
                severity = InsightSeverity.INFO
                direction = "decreased"
                rec = (
                    f"Good news! {merchant} has lowered its price. "
                    f"No action needed."
                )

            pct = abs(change_ratio) * 100
            insights.append(
                FinancialInsight(
                    type=InsightType.PRICE_INCREASE,
                    severity=severity,
                    title=f"{merchant} price {direction}",
                    summary=(
                        f"{merchant} {direction} from {fmt_currency(old_price)} to "
                        f"{fmt_currency(new_price)} ({pct:.1f}% change)."
                    ),
                    recommendation=rec,
                    score=min(pct, 100.0),
                    category=None,
                    metadata={
                        "merchant": merchant,
                        "previous_price": round(old_price, 2),
                        "current_price": round(new_price, 2),
                        "change_pct": round(change_ratio * 100, 2),
                    },
                )
            )

        return insights
