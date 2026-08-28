# ============================================================
#  engine.py — Predictive Engine Orchestrator
# ============================================================

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.services.predictive_intelligence.predictor_base import PredictionContext
from app.services.predictive_intelligence.models import Prediction, ForecastPeriod

logger = logging.getLogger(__name__)

class PredictiveIntelligenceEngine:
    """
    Orchestrates building the predictive forecasts.
    1. Loads transactions, budgets, goals.
    2. Builds PredictionContext.
    3. Runs all predictors.
    4. Deduplicates and sorts.
    """

    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def run(self, forecast_period: ForecastPeriod = ForecastPeriod.DAYS_30) -> list[Prediction]:
        # Import predictors to trigger auto-registration
        import app.services.predictive_intelligence.predictors  # noqa: F401
        from app.services.predictive_intelligence.registry import registry
        
        ctx = self._build_context(forecast_period)
        raw_predictions = self._run_predictors(ctx, registry)
        deduped = self._deduplicate(raw_predictions)
        sorted_predictions = self._sort_predictions(deduped)

        logger.info(
            "PredictiveIntelligenceEngine: %d predictions for user %s",
            len(sorted_predictions),
            self.user_id,
        )
        return sorted_predictions

    def _load_transactions(self) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == self.user_id)
            .order_by(Transaction.transaction_date.desc())
            .all()
        )

    def _load_budgets(self) -> list[Budget]:
        return (
            self.db.query(Budget)
            .filter(Budget.user_id == self.user_id)
            .all()
        )

    def _load_goals(self) -> list[Goal]:
        return (
            self.db.query(Goal)
            .filter(Goal.user_id == self.user_id)
            .all()
        )

    def _build_context(self, forecast_period: ForecastPeriod) -> PredictionContext:
        transactions = self._load_transactions()
        budgets = self._load_budgets()
        goals = self._load_goals()
        
        return PredictionContext(
            user_id=str(self.user_id),
            today=date.today(),
            forecast_period=forecast_period,
            transactions=transactions,
            budgets=budgets,
            goals=goals,
        )

    def _run_predictors(self, ctx: PredictionContext, registry) -> list[Prediction]:
        predictions = []
        for predictor in registry.predictors:
            try:
                results = predictor.predict(ctx)
                predictions.extend(results)
            except Exception:
                logger.exception("Predictor %s raised an unexpected error", predictor.name)
        return predictions

    def _deduplicate(self, predictions: list[Prediction]) -> list[Prediction]:
        """Deduplicate based on the prediction's dedup_key."""
        seen = {}
        for p in predictions:
            key = p.dedup_key
            if key not in seen:
                seen[key] = p
            else:
                # If duplicate, keep the one with higher confidence
                from app.services.predictive_intelligence.models import ConfidenceLevel
                conf_order = {ConfidenceLevel.LOW: 0, ConfidenceLevel.MEDIUM: 1, ConfidenceLevel.HIGH: 2}
                existing = seen[key]
                if conf_order[p.confidence] > conf_order[existing.confidence]:
                    seen[key] = p
        return list(seen.values())

    def _sort_predictions(self, predictions: list[Prediction]) -> list[Prediction]:
        """Sort by prediction type or value magnitude (simplistic sort for now)."""
        return sorted(predictions, key=lambda p: (p.type.value, -p.forecast_value))
