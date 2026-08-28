# ============================================================
#  insight_events.py — Builders that translate insights to events
# ============================================================

from app.services.financial_intelligence.enums import InsightSeverity
from app.services.financial_timeline.enums import TimelineEventSeverity, TimelineEventType
from app.services.financial_timeline.event_base import BaseEventBuilder, TimelineContext
from app.services.financial_timeline.models import TimelineEvent
from app.services.financial_timeline.utils import to_datetime


# Map Intelligence Severity to Timeline Severity
SEVERITY_MAP = {
    InsightSeverity.CRITICAL: TimelineEventSeverity.CRITICAL,
    InsightSeverity.WARNING: TimelineEventSeverity.WARNING,
    InsightSeverity.INFO: TimelineEventSeverity.INFO,
    InsightSeverity.SUCCESS: TimelineEventSeverity.SUCCESS,
}

# Map Intelligence Type to Timeline Type (some might map 1:1, others might group)
TYPE_MAP = {
    "SPENDING_SPIKE": TimelineEventType.SPENDING_SPIKE,
    "BUDGET_DRIFT": TimelineEventType.BUDGET_WARNING,
    "PRICE_INCREASE": TimelineEventType.PRICE_INCREASE,
    "GOAL_PROGRESS": TimelineEventType.GOAL_MILESTONE,
    "EMERGENCY_FUND": TimelineEventType.EMERGENCY_FUND_MILESTONE,
    "CASHFLOW_WARNING": TimelineEventType.CASHFLOW_WARNING,
    "SAVINGS_OPPORTUNITY": TimelineEventType.SAVINGS_OPPORTUNITY,
    "CATEGORY_TREND": TimelineEventType.CATEGORY_TREND,
    "LIFESTYLE_INFLATION": TimelineEventType.LIFESTYLE_INFLATION,
    "MONTHLY_COMPARISON": TimelineEventType.MONTHLY_COMPARISON,
    # Ignore others or map to INFO
}

class InsightEventBuilder(BaseEventBuilder):
    """
    Translates Financial Insights directly into Timeline Events.
    This ensures the timeline is tightly integrated with the Intelligence Engine.
    """
    name = "InsightEventBuilder"

    def build(self, ctx: TimelineContext) -> list[TimelineEvent]:
        events = []
        
        for insight in ctx.insights:
            insight_type_val = insight.type.value
            
            if insight_type_val in TYPE_MAP:
                t_type = TYPE_MAP[insight_type_val]
                
                # Derive related transactions from insight metadata if available
                related_tx_ids = []
                if "transaction_id" in insight.metadata:
                    related_tx_ids.append(insight.metadata["transaction_id"])
                
                # Some insights represent a period, we'll timestamp them to now or latest tx
                # Realistically, they should probably have a 'triggered_date', we use created_at
                
                events.append(
                    TimelineEvent(
                        type=t_type,
                        severity=SEVERITY_MAP.get(insight.severity, TimelineEventSeverity.INFO),
                        title=insight.title,
                        description=insight.summary,
                        timestamp=insight.created_at,  # Insights already have datetime
                        related_insight_ids=[insight.id],
                        related_transaction_ids=related_tx_ids,
                        metadata={
                            "recommendation": insight.recommendation,
                            **insight.metadata
                        }
                    )
                )
                
        return events
