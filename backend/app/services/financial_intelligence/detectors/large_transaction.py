# ============================================================
#  detectors/large_transaction.py
#  Flags individual transactions above a configurable amount
#  threshold or a significant share of monthly income/spend.
# ============================================================

from __future__ import annotations

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_month,
    total_amount,
    fmt_currency,
    fmt_pct,
    prev_month,
)

_ABSOLUTE_THRESHOLD = 10_000.0      # ₹10,000 — always flag above this
_PCT_OF_MONTHLY_SPEND_THRESHOLD = 20.0  # 20 % of monthly spend → flag
_MAX_INSIGHTS = 5                    # surface at most 5 large transactions


class LargeTransactionDetector(BaseDetector):
    """
    Flags individual expense transactions that are:
    - Above the absolute threshold (₹10,000), OR
    - Above 20 % of the total monthly expense spend

    Shows merchant, category, amount, and percentage of monthly spend.
    Returns at most 5 insights (the largest transactions first).
    """

    name = "LargeTransactionDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        today = ctx.today
        curr_year, curr_month = today.year, today.month

        expenses = filter_by_type(ctx.transactions, "expense")
        curr_expenses = filter_by_month(expenses, curr_year, curr_month)

        if not curr_expenses:
            return insights

        monthly_total = total_amount(curr_expenses)

        # Also look at the previous month for context
        prev_year, prev_mo = prev_month(curr_year, curr_month)
        prev_expenses = filter_by_month(expenses, prev_year, prev_mo)
        prev_total = total_amount(prev_expenses)
        reference_total = prev_total if prev_total > 0 else monthly_total

        flagged = []
        for tx in curr_expenses:
            amount = float(tx.amount)
            pct_of_monthly = (amount / monthly_total * 100) if monthly_total > 0 else 0

            if amount >= _ABSOLUTE_THRESHOLD or pct_of_monthly >= _PCT_OF_MONTHLY_SPEND_THRESHOLD:
                flagged.append((amount, pct_of_monthly, tx))

        # Sort by amount descending, take top N
        flagged.sort(key=lambda x: x[0], reverse=True)
        flagged = flagged[:_MAX_INSIGHTS]

        for amount, pct_of_monthly, tx in flagged:
            merchant = (tx.merchant or "").strip() or tx.description
            cat_name = tx.category.name if tx.category else "Uncategorised"

            insights.append(
                FinancialInsight(
                    type=InsightType.LARGE_TRANSACTION,
                    severity=InsightSeverity.WARNING,
                    title=f"Large transaction: {fmt_currency(amount)} at {merchant}",
                    summary=(
                        f"A {fmt_currency(amount)} expense was recorded at {merchant} "
                        f"({cat_name}) on {tx.transaction_date.strftime('%d %b %Y')}, "
                        f"representing {fmt_pct(pct_of_monthly)} of your monthly spending."
                    ),
                    recommendation=(
                        f"Verify this transaction at {merchant} is expected and authorised. "
                        f"If it was unplanned, consider adjusting your budget for the month."
                    ),
                    score=min(pct_of_monthly, 100.0),
                    category=cat_name,
                    metadata={
                        "transaction_id": str(tx.id),
                        "amount": amount,
                        "merchant": merchant,
                        "category": cat_name,
                        "date": tx.transaction_date.isoformat(),
                        "pct_of_monthly_spend": round(pct_of_monthly, 2),
                        "monthly_total": round(monthly_total, 2),
                    },
                )
            )

        return insights
