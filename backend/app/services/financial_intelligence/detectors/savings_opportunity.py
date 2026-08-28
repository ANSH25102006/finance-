# ============================================================
#  detectors/savings_opportunity.py
#  Identifies potential savings from subscriptions, expensive
#  merchants, and recurring purchases.
# ============================================================

from __future__ import annotations

from collections import defaultdict

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_month,
    group_by_merchant,
    total_amount,
    average,
    fmt_currency,
    last_n_months,
    month_start,
    month_end,
)

# Keywords that suggest a subscription service
_SUBSCRIPTION_KEYWORDS = {
    "netflix", "spotify", "amazon prime", "disney", "hotstar", "zee5",
    "apple", "google", "youtube", "linkedin", "github", "dropbox",
    "adobe", "microsoft", "office", "canva", "notion", "slack",
    "gym", "fitness", "membership", "subscription", "annual",
}

_MIN_SAVINGS_THRESHOLD = 200.0    # Only report if potential annual savings > ₹200
_LOOK_BACK_MONTHS = 3
_HIGH_FREQUENCY_THRESHOLD = 8     # 8+ transactions/month at same merchant → flag


class SavingsOpportunityDetector(BaseDetector):
    """
    Identifies savings opportunities from:
    1. Low-cost subscription alternatives
    2. High-frequency small merchant transactions (e.g. daily coffee)
    3. Unused/rarely-used recurring charges
    """

    name = "SavingsOpportunityDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        expenses = filter_by_type(ctx.transactions, "expense")
        if not expenses:
            return insights

        months = last_n_months(ctx.today, _LOOK_BACK_MONTHS)
        window_start = month_start(*months[0])
        window_end = month_end(*months[-1])

        window_txs = [
            tx for tx in expenses
            if window_start <= tx.transaction_date <= window_end
        ]
        if not window_txs:
            return insights

        # ── 1. Subscriptions ──────────────────────────────────────────
        subscription_txs = [
            tx for tx in window_txs
            if tx.recurring or any(
                kw in (tx.merchant or tx.description or "").lower()
                for kw in _SUBSCRIPTION_KEYWORDS
            )
        ]

        by_merchant = group_by_merchant(subscription_txs)
        subscription_details = []

        for merchant, txs in by_merchant.items():
            if merchant == "__unknown__":
                continue
            avg_amount = average([float(tx.amount) for tx in txs])
            # Check how many different months it appears
            months_active = len({(tx.transaction_date.year, tx.transaction_date.month) for tx in txs})

            if months_active < 2 or avg_amount < 50:
                continue  # not consistent enough

            annual_cost = avg_amount * 12
            subscription_details.append({
                "merchant": merchant,
                "avg_monthly": round(avg_amount, 2),
                "annual_cost": round(annual_cost, 2),
                "months_active": months_active,
            })

        if subscription_details:
            total_annual = sum(s["annual_cost"] for s in subscription_details)
            top = sorted(subscription_details, key=lambda x: x["annual_cost"], reverse=True)

            if total_annual >= _MIN_SAVINGS_THRESHOLD:
                insights.append(
                    FinancialInsight(
                        type=InsightType.SAVINGS_OPPORTUNITY,
                        severity=InsightSeverity.INFO,
                        title=f"Subscriptions costing {fmt_currency(total_annual)}/year",
                        summary=(
                            f"You have {len(subscription_details)} active subscription(s) "
                            f"totalling {fmt_currency(total_annual)} per year. "
                            f"Largest: {top[0]['merchant']} at {fmt_currency(top[0]['annual_cost'])}/year."
                        ),
                        recommendation=(
                            "Review your subscriptions. Cancel any you no longer actively use. "
                            "Even cancelling one medium subscription can save you thousands per year."
                        ),
                        score=min(total_annual / 100, 100.0),
                        category="Subscriptions",
                        metadata={
                            "total_annual_cost": round(total_annual, 2),
                            "subscription_count": len(subscription_details),
                            "subscriptions": top[:10],
                        },
                    )
                )

        # ── 2. High-frequency small purchases ─────────────────────────
        # e.g., daily coffee / snacks from the same merchant
        for month_ym in months:
            month_txs = filter_by_month(window_txs, month_ym[0], month_ym[1])
            by_merch = group_by_merchant(month_txs)

            for merchant, txs in by_merch.items():
                if merchant == "__unknown__":
                    continue
                if len(txs) < _HIGH_FREQUENCY_THRESHOLD:
                    continue

                avg_tx = average([float(tx.amount) for tx in txs])
                monthly_total = total_amount(txs)
                annual_est = monthly_total * 12

                if annual_est < _MIN_SAVINGS_THRESHOLD:
                    continue

                insights.append(
                    FinancialInsight(
                        type=InsightType.SAVINGS_OPPORTUNITY,
                        severity=InsightSeverity.INFO,
                        title=f"Frequent small purchases at {merchant}",
                        summary=(
                            f"You made {len(txs)} transactions at {merchant} in "
                            f"{month_ym[0]}-{month_ym[1]:02d} "
                            f"(avg {fmt_currency(avg_tx)}/transaction, total {fmt_currency(monthly_total)}/month). "
                            f"Estimated annual cost: {fmt_currency(annual_est)}."
                        ),
                        recommendation=(
                            f"Consider reducing the frequency of visits to {merchant}. "
                            f"Small daily purchases add up significantly over a year."
                        ),
                        score=min(annual_est / 500, 100.0),
                        category=None,
                        metadata={
                            "merchant": merchant,
                            "transaction_count": len(txs),
                            "avg_transaction": round(avg_tx, 2),
                            "monthly_total": round(monthly_total, 2),
                            "annual_estimate": round(annual_est, 2),
                        },
                    )
                )

        return insights
