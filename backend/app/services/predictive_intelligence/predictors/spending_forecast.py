# ============================================================
#  spending_forecast.py — Predicts total spending
# ============================================================

from decimal import Decimal
from collections import defaultdict

from app.services.predictive_intelligence.models import Prediction, PredictionType, ConfidenceLevel
from app.services.predictive_intelligence.predictor_base import BasePredictor, PredictionContext
from app.services.predictive_intelligence.utils import linear_trend_forecast

class SpendingPredictor(BasePredictor):
    name = "SpendingPredictor"

    def predict(self, ctx: PredictionContext) -> list[Prediction]:
        if not ctx.transactions:
            return []

        # Monthly expenses
        monthly_expenses = defaultdict(Decimal)
        for tx in ctx.transactions:
            if tx.transaction_type == 'expense':
                month_key = tx.transaction_date.strftime("%Y-%m")
                monthly_expenses[month_key] += tx.amount

        sorted_months = sorted(monthly_expenses.keys())
        if len(sorted_months) < 2:
            return []

        # Exclude current month for historical trend
        historical_expenses = [float(monthly_expenses[m]) for m in sorted_months[:-1]]
        
        # Predict 1 period ahead (current month)
        projected_spend = linear_trend_forecast(historical_expenses, periods_ahead=1)

        # Current month spend
        current_month_key = ctx.today.strftime("%Y-%m")
        current_spend = float(monthly_expenses[current_month_key])

        # If current is already higher, update prediction
        final_projection = max(projected_spend, current_spend)

        confidence = ConfidenceLevel.HIGH if len(historical_expenses) >= 6 else ConfidenceLevel.MEDIUM

        return [
            Prediction(
                type=PredictionType.SPENDING,
                title="Forecasted Total Spending",
                summary=f"Expected total spending for {ctx.today.strftime('%B')}.",
                confidence=confidence,
                methodology="Linear Trend Forecast",
                forecast_value=final_projection,
                forecast_period=ctx.forecast_period,
                recommendation="Your spending trend is stable." if projected_spend <= sum(historical_expenses)/len(historical_expenses) else "Spending is trending upward. Watch your discretionary categories.",
                metadata={
                    "current_month_spend": current_spend,
                    "projected_spend": final_projection,
                    "historical_average": sum(historical_expenses) / len(historical_expenses)
                }
            )
        ]
