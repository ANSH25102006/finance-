# ============================================================
#  builders/__init__.py — Auto-registers predictors
# ============================================================

from app.services.predictive_intelligence.registry import registry
from app.services.predictive_intelligence.predictors.cashflow_forecast import CashflowPredictor
from app.services.predictive_intelligence.predictors.spending_forecast import SpendingPredictor
from app.services.predictive_intelligence.predictors.budget_projection import BudgetProjectionPredictor
from app.services.predictive_intelligence.predictors.goal_projection import GoalProjectionPredictor

def register_all_predictors() -> None:
    registry.register(CashflowPredictor())
    registry.register(SpendingPredictor())
    registry.register(BudgetProjectionPredictor())
    registry.register(GoalProjectionPredictor())

register_all_predictors()
