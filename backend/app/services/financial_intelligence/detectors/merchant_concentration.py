# ============================================================
#  detectors/merchant_concentration.py
#  Detects when a single merchant dominates spending in a
#  category, indicating dependency or lack of alternatives.
# ============================================================

from __future__ import annotations

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_month,
    group_by_category,
    group_by_merchant,
    total_amount,
    fmt_currency,
    fmt_pct,
    last_n_months,
)

_CONCENTRATION_THRESHOLD = 0.40   # 40 % of category spend from one merchant → WARNING
_DOMINANT_THRESHOLD = 0.70        # 70 % → CRITICAL
_MIN_CATEGORY_SPEND = 500.0       # ignore small categories
_LOOK_BACK_MONTHS = 3


class MerchantConcentrationDetector(BaseDetector):
    """
    For each expense category, calculates the share of spending attributable
    to each merchant over the last 3 months.

    Generates WARNING if a single merchant accounts for ≥40 % of category spend,
    or CRITICAL if ≥70 %.
    """

    name = "MerchantConcentrationDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        expenses = filter_by_type(ctx.transactions, "expense")
        if not expenses:
            return insights

        months = last_n_months(ctx.today, _LOOK_BACK_MONTHS)
        start_ym = months[0]
        end_ym = months[-1]

        # Filter to the look-back window
        from datetime import date
        from app.services.financial_intelligence.utils import month_start, month_end
        window_start = month_start(*start_ym)
        window_end = month_end(*end_ym)
        window_txs = [
            tx for tx in expenses
            if window_start <= tx.transaction_date <= window_end
        ]

        if not window_txs:
            return insights

        by_category = group_by_category(window_txs)

        for cat_name, cat_txs in by_category.items():
            if cat_name == "__uncategorised__":
                continue

            cat_total = total_amount(cat_txs)
            if cat_total < _MIN_CATEGORY_SPEND:
                continue

            by_merchant = group_by_merchant(cat_txs)
            if not by_merchant:
                continue

            # Sort merchants by spend descending
            merchant_spend = sorted(
                [(m, total_amount(txs)) for m, txs in by_merchant.items()],
                key=lambda x: x[1],
                reverse=True,
            )

            top_merchant, top_spend = merchant_spend[0]
            if top_merchant == "__unknown__":
                continue

            concentration = top_spend / cat_total

            if concentration >= _DOMINANT_THRESHOLD:
                severity = InsightSeverity.CRITICAL
            elif concentration >= _CONCENTRATION_THRESHOLD:
                severity = InsightSeverity.WARNING
            else:
                continue

            insights.append(
                FinancialInsight(
                    type=InsightType.MERCHANT_CONCENTRATION,
                    severity=severity,
                    title=f"High merchant concentration in {cat_name}",
                    summary=(
                        f"{fmt_pct(concentration * 100)} of your {cat_name} spending "
                        f"({fmt_currency(top_spend)} of {fmt_currency(cat_total)}) "
                        f"comes from a single merchant: {top_merchant}."
                    ),
                    recommendation=(
                        f"Consider diversifying your {cat_name} spending or "
                        f"negotiating a better deal with {top_merchant}."
                    ),
                    score=concentration * 100,
                    category=cat_name,
                    metadata={
                        "top_merchant": top_merchant,
                        "top_merchant_spend": round(top_spend, 2),
                        "category_total": round(cat_total, 2),
                        "concentration_pct": round(concentration * 100, 2),
                        "all_merchants": [
                            {"merchant": m, "spend": round(s, 2), "pct": round(s / cat_total * 100, 2)}
                            for m, s in merchant_spend[:5]
                        ],
                    },
                )
            )

        return insights
