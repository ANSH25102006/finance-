# ============================================================
#  detectors/income_change.py
#  Detects income increases, decreases, missed salary, and
#  irregular income patterns across monthly deposits.
# ============================================================

from __future__ import annotations

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    filter_by_type,
    filter_by_month,
    total_amount,
    average,
    safe_pct_change,
    fmt_currency,
    fmt_pct,
    last_n_months,
    prev_month,
)

_LOOK_BACK_MONTHS = 6
_CHANGE_THRESHOLD_PCT = 10.0    # 10 % change is considered significant
_IRREGULAR_CV_THRESHOLD = 0.35  # coefficient of variation > 35 % → irregular


class IncomeChangeDetector(BaseDetector):
    """
    Analyses income transactions to detect:
    - Salary increase / decrease (>10% change vs prior month)
    - Missed salary (no income recorded for the current month)
    - Irregular income patterns (high variance across months)
    """

    name = "IncomeChangeDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        income_txs = filter_by_type(ctx.transactions, "income")
        if not income_txs:
            return insights

        today = ctx.today
        curr_year, curr_month = today.year, today.month
        prev_year, prev_mo = prev_month(curr_year, curr_month)

        curr_income = total_amount(filter_by_month(income_txs, curr_year, curr_month))
        prev_income = total_amount(filter_by_month(income_txs, prev_year, prev_mo))

        # ── Missed salary ──────────────────────────────────────────────
        # Only flag as missed if there was income last month but none this month
        # and we're past day 10 of the current month (enough time for it to appear).
        if curr_income == 0 and prev_income > 0 and today.day >= 10:
            insights.append(
                FinancialInsight(
                    type=InsightType.INCOME_CHANGE,
                    severity=InsightSeverity.CRITICAL,
                    title="No income recorded this month",
                    summary=(
                        f"No income has been recorded for {today.strftime('%B %Y')}. "
                        f"Last month's income was {fmt_currency(prev_income)}."
                    ),
                    recommendation=(
                        "Check if your salary or income has been received. "
                        "If you've switched jobs or are self-employed, make sure "
                        "to log income transactions when received."
                    ),
                    score=100.0,
                    category=None,
                    metadata={
                        "current_month_income": 0.0,
                        "previous_month_income": round(prev_income, 2),
                    },
                )
            )
            return insights  # no point checking MoM change if there's no current income

        # ── Month-over-month income change ─────────────────────────────
        if prev_income > 0 and curr_income > 0:
            pct_change = safe_pct_change(prev_income, curr_income)

            if abs(pct_change) >= _CHANGE_THRESHOLD_PCT:
                if pct_change > 0:
                    severity = InsightSeverity.SUCCESS
                    direction = "increased"
                    rec = (
                        "Great news! Your income has increased. Consider directing "
                        "the extra income towards your financial goals or emergency fund."
                    )
                else:
                    severity = InsightSeverity.WARNING
                    direction = "decreased"
                    rec = (
                        "Your income has decreased this month. Review your budget and "
                        "prioritise essential expenses."
                    )

                insights.append(
                    FinancialInsight(
                        type=InsightType.INCOME_CHANGE,
                        severity=severity,
                        title=f"Income {direction} by {fmt_pct(abs(pct_change))}",
                        summary=(
                            f"Your income {direction} from {fmt_currency(prev_income)} "
                            f"to {fmt_currency(curr_income)} this month "
                            f"({fmt_pct(abs(pct_change))} {'increase' if pct_change > 0 else 'decrease'})."
                        ),
                        recommendation=rec,
                        score=min(abs(pct_change), 100.0),
                        category=None,
                        metadata={
                            "previous_income": round(prev_income, 2),
                            "current_income": round(curr_income, 2),
                            "pct_change": round(pct_change, 2),
                        },
                    )
                )

        # ── Irregular income detection ─────────────────────────────────
        months = last_n_months(today, _LOOK_BACK_MONTHS)
        monthly_totals = [
            total_amount(filter_by_month(income_txs, ym[0], ym[1]))
            for ym in months
        ]
        non_zero = [v for v in monthly_totals if v > 0]

        if len(non_zero) >= 3:
            avg = average(non_zero)
            if avg > 0:
                std = (sum((v - avg) ** 2 for v in non_zero) / len(non_zero)) ** 0.5
                cv = std / avg  # coefficient of variation

                if cv >= _IRREGULAR_CV_THRESHOLD:
                    insights.append(
                        FinancialInsight(
                            type=InsightType.INCOME_CHANGE,
                            severity=InsightSeverity.INFO,
                            title="Irregular income pattern detected",
                            summary=(
                                f"Your monthly income has been highly variable over "
                                f"the past {_LOOK_BACK_MONTHS} months "
                                f"(avg {fmt_currency(avg)}, variability {cv * 100:.0f}%)."
                            ),
                            recommendation=(
                                "With irregular income, build a 3–6 month emergency fund "
                                "and budget based on your lowest expected monthly income."
                            ),
                            score=min(cv * 100, 100.0),
                            category=None,
                            metadata={
                                "average_monthly_income": round(avg, 2),
                                "coefficient_of_variation": round(cv, 4),
                                "monthly_totals": {
                                    f"{ym[0]}-{ym[1]:02d}": round(v, 2)
                                    for ym, v in zip(months, monthly_totals)
                                },
                            },
                        )
                    )

        return insights
