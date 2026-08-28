# ============================================================
#  event_base.py — Abstract base class for all event builders
# ============================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.services.financial_intelligence.models import FinancialInsight
    from app.services.financial_timeline.models import TimelineEvent

@dataclass
class TimelineContext:
    """
    Immutable data bag built once by the engine and passed to every builder.
    Includes raw transactions and computed financial insights.
    """
    user_id: str
    today: date

    # Raw DB rows
    transactions: list[Any] = field(default_factory=list)   # List[Transaction]
    insights: list[Any] = field(default_factory=list)       # List[FinancialInsight]

    # Pre-computed views
    transactions_by_id: dict[str, Any] = field(default_factory=dict)
    insights_by_type: dict[str, list[Any]] = field(default_factory=dict)

    extras: dict[str, Any] = field(default_factory=dict)


class BaseEventBuilder(ABC):
    """
    Abstract base class for all timeline event builders.
    Stateless, pure function.
    """
    name: str = "BaseEventBuilder"

    @abstractmethod
    def build(self, ctx: TimelineContext) -> list[TimelineEvent]:
        """
        Analyse the context and return zero or more TimelineEvent instances.
        """
        ...
