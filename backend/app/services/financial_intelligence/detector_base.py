# ============================================================
#  detector_base.py — Abstract base class for all detectors
# ============================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.budget import Budget
    from app.models.goal import Goal
    from app.models.transaction import Transaction
    from app.services.financial_intelligence.models import FinancialInsight


@dataclass
class DetectionContext:
    """
    Immutable data bag built once by the engine and passed to every detector.

    Building it once avoids repeated DB queries across detectors and keeps
    each detector fully stateless — they only read from this context.
    """

    user_id: str
    today: date

    # Raw DB rows
    transactions: list[Any] = field(default_factory=list)   # List[Transaction]
    budgets: list[Any] = field(default_factory=list)         # List[Budget]
    goals: list[Any] = field(default_factory=list)           # List[Goal]

    # Pre-computed convenience views — populated by the engine
    # {(year, month): [Transaction, ...]}
    transactions_by_month: dict[tuple[int, int], list[Any]] = field(default_factory=dict)

    # {category_name: [Transaction, ...]}
    expense_transactions_by_category: dict[str, list[Any]] = field(default_factory=dict)

    # {category_name: [Transaction, ...]}
    income_transactions_by_month: dict[tuple[int, int], list[Any]] = field(default_factory=dict)

    # Total cash balance across all accounts
    total_cash_balance: float = 0.0

    # Extra engine-computed aggregates accessible to any detector
    extras: dict[str, Any] = field(default_factory=dict)


class BaseDetector(ABC):
    """
    Abstract base class that every detector must subclass.

    A detector is stateless: all state lives in the DetectionContext.
    The detect() method must be pure — same context always produces same insights.
    """

    # Human-readable name used in logging
    name: str = "BaseDetector"

    @abstractmethod
    def detect(self, ctx: DetectionContext) -> list[FinancialInsight]:
        """
        Analyse the context and return zero or more FinancialInsight instances.

        Must not:
          - Call the database
          - Call any external API or LLM
          - Mutate the context
          - Raise exceptions (return [] on unexpected data)
        """
        ...
