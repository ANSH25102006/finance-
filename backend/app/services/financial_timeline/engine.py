# ============================================================
#  engine.py — Timeline Engine Orchestrator
# ============================================================

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_timeline.event_base import TimelineContext
from app.services.financial_timeline.models import TimelineEvent
from app.services.financial_timeline.utils import group_insights_by_type, index_transactions_by_id

logger = logging.getLogger(__name__)

class FinancialTimelineEngine:
    """
    Orchestrates building the chronological financial timeline.
    1. Loads transactions and insights.
    2. Builds TimelineContext.
    3. Runs all builders.
    4. Deduplicates and sorts.
    """

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def run(self) -> list[TimelineEvent]:
        # Import builders to trigger auto-registration
        import app.services.financial_timeline.builders  # noqa: F401
        from app.services.financial_timeline.registry import registry
        
        ctx = self._build_context()
        raw_events = self._run_builders(ctx, registry)
        deduped = self._deduplicate(raw_events)
        sorted_events = self._sort_chronologically(deduped)

        logger.info(
            "FinancialTimelineEngine: %d raw events -> %d after dedup for user %s",
            len(raw_events),
            len(sorted_events),
            self.user_id,
        )
        return sorted_events

    def _load_transactions(self) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == self.user_id)
            .order_by(Transaction.transaction_date.desc())
            .all()
        )

    def _load_insights(self) -> list[FinancialInsight]:
        # In a real scenario, insights might be persisted in the DB.
        # For our architecture, the intelligence engine runs dynamically.
        # We will instantiate it here to get the latest insights.
        from app.services.financial_intelligence.engine import FinancialIntelligenceEngine
        intelligence_engine = FinancialIntelligenceEngine(db=self.db, user_id=self.user_id)
        return intelligence_engine.run()

    def _build_context(self) -> TimelineContext:
        transactions = self._load_transactions()
        insights = self._load_insights()
        
        return TimelineContext(
            user_id=str(self.user_id),
            today=date.today(),
            transactions=transactions,
            insights=insights,
            transactions_by_id=index_transactions_by_id(transactions),
            insights_by_type=group_insights_by_type(insights),
        )

    def _run_builders(self, ctx: TimelineContext, registry) -> list[TimelineEvent]:
        events = []
        for builder in registry.builders:
            try:
                results = builder.build(ctx)
                events.extend(results)
            except Exception:
                logger.exception("Builder %s raised an unexpected error", builder.name)
        return events

    def _deduplicate(self, events: list[TimelineEvent]) -> list[TimelineEvent]:
        """Deduplicate based on the event's dedup_key."""
        seen = {}
        for event in events:
            key = event.dedup_key
            if key not in seen:
                seen[key] = event
            else:
                existing = seen[key]
                # If duplicate, keep the more severe one
                from app.services.financial_timeline.enums import SEVERITY_ORDER
                if SEVERITY_ORDER[event.severity] < SEVERITY_ORDER[existing.severity]:
                    seen[key] = event
        return list(seen.values())

    def _sort_chronologically(self, events: list[TimelineEvent]) -> list[TimelineEvent]:
        """Sort newest first."""
        return sorted(events, key=lambda e: e.timestamp, reverse=True)
