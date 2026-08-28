# ============================================================
#  detectors/goal_progress.py
#  Computes progress towards each user financial goal and
#  generates insights about completion and trajectory.
# ============================================================

from __future__ import annotations

from datetime import date, timezone

from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import fmt_currency, fmt_pct


class GoalProgressDetector(BaseDetector):
    """
    For each user financial goal, computes:
    - % completed
    - Amount remaining
    - Months to completion based on monthly_contribution

    Severity:
    - SUCCESS   → ≥ 100 % (goal achieved)
    - SUCCESS   → on track (estimated completion before deadline)
    - INFO      → making progress, no deadline set
    - WARNING   → behind schedule (estimated completion after deadline)
    - CRITICAL  → zero contribution configured and goal incomplete
    """

    name = "GoalProgressDetector"

    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        insights: list[FinancialInsight] = []

        if not ctx.goals:
            return insights

        today = ctx.today

        for goal in ctx.goals:
            target = float(goal.target_amount)
            current = float(goal.current_amount)
            monthly_contribution = float(goal.monthly_contribution or 0)

            if target <= 0:
                continue

            pct_complete = min((current / target) * 100, 100.0)
            remaining = max(0.0, target - current)

            # ── Already achieved ───────────────────────────────────────
            if current >= target:
                insights.append(
                    FinancialInsight(
                        type=InsightType.GOAL_PROGRESS,
                        severity=InsightSeverity.SUCCESS,
                        title=f"Goal achieved: {goal.name}",
                        summary=(
                            f"Congratulations! You have reached your {goal.name} goal "
                            f"of {fmt_currency(target)}."
                        ),
                        recommendation=(
                            f"Consider setting a new target or redirecting contributions "
                            f"to your next financial priority."
                        ),
                        score=100.0,
                        category=goal.name,
                        metadata={
                            "goal_id": str(goal.id),
                            "goal_name": goal.name,
                            "target_amount": target,
                            "current_amount": round(current, 2),
                            "pct_complete": 100.0,
                        },
                    )
                )
                continue

            # ── Estimate months to completion ─────────────────────────
            if monthly_contribution > 0:
                months_to_complete = remaining / monthly_contribution
            else:
                months_to_complete = None

            # ── Deadline analysis ─────────────────────────────────────
            deadline = None
            if goal.deadline:
                dl = goal.deadline
                # Normalise to date
                if hasattr(dl, "date"):
                    deadline = dl.date()
                else:
                    deadline = dl

            on_track: bool | None = None
            if deadline and months_to_complete is not None:
                months_until_deadline = (
                    (deadline.year - today.year) * 12
                    + (deadline.month - today.month)
                )
                on_track = months_to_complete <= months_until_deadline

            # ── Build insight ─────────────────────────────────────────
            if monthly_contribution == 0:
                severity = InsightSeverity.CRITICAL
                title = f"No contribution set for goal: {goal.name}"
                summary = (
                    f"Your goal '{goal.name}' is {fmt_pct(pct_complete)} complete "
                    f"({fmt_currency(current)} of {fmt_currency(target)}) but no "
                    f"monthly contribution is configured."
                )
                recommendation = (
                    f"Set a monthly contribution of at least "
                    f"{fmt_currency(remaining / 12)}/month to reach your goal within a year."
                )
            elif on_track is False:
                severity = InsightSeverity.WARNING
                eta_str = f"{months_to_complete:.0f} months" if months_to_complete else "unknown"
                title = f"Behind schedule: {goal.name}"
                summary = (
                    f"At your current contribution of {fmt_currency(monthly_contribution)}/month, "
                    f"'{goal.name}' will take approximately {eta_str} to complete, "
                    f"which is after your deadline."
                )
                recommendation = (
                    f"Increase your monthly contribution or extend the deadline for '{goal.name}'."
                )
            elif on_track is True:
                severity = InsightSeverity.SUCCESS
                eta_str = f"{months_to_complete:.0f} months"
                title = f"On track: {goal.name}"
                summary = (
                    f"'{goal.name}' is {fmt_pct(pct_complete)} complete "
                    f"({fmt_currency(current)} of {fmt_currency(target)}). "
                    f"At {fmt_currency(monthly_contribution)}/month, you'll reach it in {eta_str}."
                )
                recommendation = (
                    f"Keep up the great work! You're on track to achieve '{goal.name}'."
                )
            else:
                # No deadline — just informational
                severity = InsightSeverity.INFO
                eta_str = f"{months_to_complete:.0f} months" if months_to_complete else "unknown"
                title = f"Goal progress: {goal.name}"
                summary = (
                    f"'{goal.name}' is {fmt_pct(pct_complete)} complete "
                    f"({fmt_currency(current)} of {fmt_currency(target)}). "
                    + (f"Estimated completion: {eta_str}." if months_to_complete else "")
                )
                recommendation = (
                    f"You need {fmt_currency(remaining)} more to reach '{goal.name}'."
                )

            insights.append(
                FinancialInsight(
                    type=InsightType.GOAL_PROGRESS,
                    severity=severity,
                    title=title,
                    summary=summary,
                    recommendation=recommendation,
                    score=pct_complete,
                    category=goal.name,
                    metadata={
                        "goal_id": str(goal.id),
                        "goal_name": goal.name,
                        "target_amount": target,
                        "current_amount": round(current, 2),
                        "remaining": round(remaining, 2),
                        "pct_complete": round(pct_complete, 2),
                        "monthly_contribution": monthly_contribution,
                        "months_to_complete": round(months_to_complete, 1) if months_to_complete else None,
                        "deadline": deadline.isoformat() if deadline else None,
                        "on_track": on_track,
                    },
                )
            )

        return insights
