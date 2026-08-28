# ============================================================
#  predictor_base.py — Abstract base class for all predictors
# ============================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.predictive_intelligence.models import Prediction, ForecastPeriod

@dataclass
class PredictionContext:
    """
    Immutable data bag built once by the engine and passed to every predictor.
    """
    user_id: str
    today: date
    forecast_period: 'ForecastPeriod'

    # Raw DB rows (avoiding tight coupling to SQLAlchemy models in type hints here for simplicity)
    transactions: list[Any] = field(default_factory=list)   
    budgets: list[Any] = field(default_factory=list)         
    goals: list[Any] = field(default_factory=list)           

    extras: dict[str, Any] = field(default_factory=dict)


class BasePredictor(ABC):
    """
    Abstract base class for all predictors.
    Stateless, purely functional.
    """
    name: str = "BasePredictor"

    @abstractmethod
    def predict(self, ctx: PredictionContext) -> list['Prediction']:
        """
        Analyse the context and return zero or more Prediction instances.
        Must use deterministic statistical methods.
        """
        ...
