# ============================================================
#  budget_projection.py — Predicts budget overruns
# ============================================================

from decimal import Decimal

from app.services.predictive_intelligence.models import Prediction, PredictionType, ConfidenceLevel
from app.services.predictive_intelligence.predictor_base import BasePredictor, PredictionContext
from app.services.predictive_intelligence.utils import days_in_current_month, days_remaining_in_month

class BudgetProjectionPredictor(BasePredictor):
    name = "BudgetProjectionPredictor"

    def predict(self, ctx: PredictionContext) -> list[Prediction]:
        if not ctx.budgets:
            return []

        predictions = []
        days_total = days_in_current_month(ctx.today)
        days_passed = ctx.today.day
        
        # Prevent division by zero if it's the very first day of the month
        if days_passed == 0:
            days_passed = 1

        for budget in ctx.budgets:
            # We assume budget amount and spent are available on the model, or we compute from transactions.
            # In our schema, Budget usually has `amount` (Decimal) and we can compute spent or it has a property.
            # We'll calculate spent directly from transactions matching the category.
            spent = Decimal('0')
            for tx in ctx.transactions:
                if tx.transaction_type == 'expense' and str(tx.category_id) == str(budget.category_id):
                    # Check if it's in the current month
                    if tx.transaction_date.year == ctx.today.year and tx.transaction_date.month == ctx.today.month:
                        spent += tx.amount
                        
            daily_burn_rate = float(spent) / days_passed
            projected_final_spend = daily_burn_rate * days_total
            
            # Prediction logic
            is_overrun = projected_final_spend > float(budget.amount)
            
            predictions.append(
                Prediction(
                    type=PredictionType.BUDGET,
                    title=f"Projected Spend: {budget.category.name if budget.category else 'Budget'}",
                    summary=f"Expected to {'exceed' if is_overrun else 'stay under'} budget this month.",
                    confidence=ConfidenceLevel.MEDIUM,
                    methodology="Linear Daily Burn Rate Extrapolation",
                    forecast_value=projected_final_spend,
                    forecast_period=ctx.forecast_period,
                    related_entity_id=str(budget.id),
                    recommendation="Reduce spending in this category to stay within budget." if is_overrun else "You are on track to meet your budget.",
                    metadata={
                        "budget_amount": float(budget.amount),
                        "current_spent": float(spent),
                        "daily_burn_rate": daily_burn_rate,
                        "projected_overrun": max(0, projected_final_spend - float(budget.amount))
                    }
                )
            )

        return predictions
