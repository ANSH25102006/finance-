# ============================================================
#  builders/__init__.py — Auto-registers builders
# ============================================================

from app.services.financial_timeline.registry import registry
from app.services.financial_timeline.builders.transaction_events import (
    SalaryEventBuilder,
    LargeTransactionEventBuilder,
)
from app.services.financial_timeline.builders.insight_events import (
    InsightEventBuilder,
)

def register_all_builders() -> None:
    registry.register(SalaryEventBuilder())
    registry.register(LargeTransactionEventBuilder())
    registry.register(InsightEventBuilder())

register_all_builders()
