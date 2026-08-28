# ============================================================
#  registry.py — Singleton registry for predictors
# ============================================================

from typing import TypeVar, Type

from app.services.predictive_intelligence.predictor_base import BasePredictor

T = TypeVar("T", bound=BasePredictor)

class PredictorRegistry:
    """Singleton registry holding all predictors."""

    def __init__(self) -> None:
        self.predictors: list[BasePredictor] = []
        self._registered_types: set[Type[BasePredictor]] = set()

    def register(self, predictor: BasePredictor) -> None:
        """Register a predictor instance if its type hasn't been registered yet."""
        predictor_type = type(predictor)
        if predictor_type not in self._registered_types:
            self.predictors.append(predictor)
            self._registered_types.add(predictor_type)

    def clear(self) -> None:
        """Clear all registered predictors (useful for tests)."""
        self.predictors.clear()
        self._registered_types.clear()

registry = PredictorRegistry()
