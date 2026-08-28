# ============================================================
#  engine.py — Financial Intelligence Engine
#
#  Single entry point for all financial insight generation.
#  The engine loads data once, builds a DetectionContext,
#  runs every registered detector, deduplicates the results,
#  sorts by severity, and returns the final insight list.
#
#  No LLM calls. No external APIs. Fully deterministic.
# ============================================================

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.services.financial_intelligence.detector_base import DetectionContext
from app.services.financial_intelligence.enums import SEVERITY_ORDER
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.utils import (
    group_by_category,
    filter_by_type,
    group_by_month,
)

logger = logging.getLogger(__name__)


class FinancialIntelligenceEngine:
    """
    The central orchestrator for the Financial Intelligence Engine.

    Responsibilities:
    1. Load all relevant data from the database (transactions, budgets, goals, accounts).
    2. Build a DetectionContext shared by every detector.
    3. Trigger every registered detector via the DetectorRegistry.
    4. Deduplicate insights (by type + category).
    5. Sort by severity (CRITICAL → WARNING → INFO → SUCCESS).
    6. Return the final list.

    Usage
    -----
    >>> engine = FinancialIntelligenceEngine(db=db, user_id=user.id)
    >>> insights = engine.run()
    """

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(self) -> list[FinancialInsight]:
        """Execute the full engine pipeline and return sorted insights."""
        # Import here so that all detectors auto-register on first call
        import app.services.financial_intelligence.detectors  # noqa: F401
        from app.services.financial_intelligence.detector_registry import registry

        ctx = self._build_context()
        raw_insights = self._run_detectors(ctx, registry)
        deduped = self._deduplicate(raw_insights)
        sorted_insights = self._sort_by_severity(deduped)

        logger.info(
            "FinancialIntelligenceEngine: %d raw insights → %d after dedup for user %s",
            len(raw_insights),
            len(sorted_insights),
            self.user_id,
        )
        return sorted_insights

    # ------------------------------------------------------------------ #
    # Data loading
    # ------------------------------------------------------------------ #

    def _load_transactions(self) -> list[Transaction]:
        """Load all transactions for the user with category eagerly loaded."""
        return (
            self.db.query(Transaction)
            .options(joinedload(Transaction.category))
            .filter(Transaction.user_id == self.user_id)
            .order_by(Transaction.transaction_date.asc())
            .all()
        )

    def _load_budgets(self) -> list[Budget]:
        """Load all budgets for the user with category eagerly loaded."""
        return (
            self.db.query(Budget)
            .options(joinedload(Budget.category))
            .filter(Budget.user_id == self.user_id)
            .all()
        )

    def _load_goals(self) -> list[Goal]:
        """Load all goals for the user."""
        return self.db.query(Goal).filter(Goal.user_id == self.user_id).all()

    def _load_total_cash_balance(self) -> float:
        """Sum balances across all non-archived accounts."""
        from sqlalchemy import func
        result = (
            self.db.query(func.sum(Account.balance))
            .filter(Account.user_id == self.user_id, Account.archived.is_(False))
            .scalar()
        )
        return float(result) if result is not None else 0.0

    # ------------------------------------------------------------------ #
    # Context construction
    # ------------------------------------------------------------------ #

    def _build_context(self) -> DetectionContext:
        """Load all data and assemble the DetectionContext."""
        transactions = self._load_transactions()
        budgets = self._load_budgets()
        goals = self._load_goals()
        total_cash_balance = self._load_total_cash_balance()

        today = date.today()

        # Pre-compute convenience views
        expenses = filter_by_type(transactions, "expense")
        income_txs = filter_by_type(transactions, "income")

        transactions_by_month = group_by_month(transactions)
        expense_by_category = group_by_category(expenses)
        income_by_month = group_by_month(income_txs)

        ctx = DetectionContext(
            user_id=str(self.user_id),
            today=today,
            transactions=transactions,
            budgets=budgets,
            goals=goals,
            transactions_by_month=transactions_by_month,
            expense_transactions_by_category=expense_by_category,
            income_transactions_by_month=income_by_month,
            total_cash_balance=total_cash_balance,
        )
        return ctx

    # ------------------------------------------------------------------ #
    # Detector execution
    # ------------------------------------------------------------------ #

    def _run_detectors(self, ctx: DetectionContext, registry) -> list[FinancialInsight]:
        """Iterate the registry and collect all insights."""
        all_insights: list[FinancialInsight] = []
        for detector in registry.detectors:
            try:
                results = detector.detect(ctx)
                all_insights.extend(results)
                logger.debug("Detector %s returned %d insights", detector.name, len(results))
            except Exception:
                logger.exception("Detector %s raised an unexpected error — skipping", detector.name)
        return all_insights

    # ------------------------------------------------------------------ #
    # Post-processing
    # ------------------------------------------------------------------ #

    def _deduplicate(self, insights: list[FinancialInsight]) -> list[FinancialInsight]:
        """
        Remove duplicate insights with the same (type, category) key.
        When duplicates exist, keep the one with the highest severity.
        """
        seen: dict[tuple, FinancialInsight] = {}
        for insight in insights:
            key = insight.dedup_key
            if key not in seen:
                seen[key] = insight
            else:
                existing = seen[key]
                # Keep the more severe insight
                if SEVERITY_ORDER[insight.severity] < SEVERITY_ORDER[existing.severity]:
                    seen[key] = insight
        return list(seen.values())

    def _sort_by_severity(self, insights: list[FinancialInsight]) -> list[FinancialInsight]:
        """Sort insights: CRITICAL first, then WARNING, INFO, SUCCESS."""
        return sorted(insights, key=lambda i: SEVERITY_ORDER[i.severity])
