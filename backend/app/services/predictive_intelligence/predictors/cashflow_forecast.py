# ============================================================
#  cashflow_forecast.py — Predicts end of month balance
# ============================================================

from decimal import Decimal
from collections import defaultdict

from app.services.predictive_intelligence.models import Prediction, PredictionType, ConfidenceLevel
from app.services.predictive_intelligence.predictor_base import BasePredictor, PredictionContext
from app.services.predictive_intelligence.utils import simple_moving_average

class CashflowPredictor(BasePredictor):
    name = "CashflowPredictor"

    def predict(self, ctx: PredictionContext) -> list[Prediction]:
        if not ctx.transactions:
            return []

        # Group by month (YYYY-MM)
        monthly_net = defaultdict(Decimal)
        for tx in ctx.transactions:
            month_key = tx.transaction_date.strftime("%Y-%m")
            if tx.transaction_type == 'income':
                monthly_net[month_key] += tx.amount
            elif tx.transaction_type == 'expense':
                monthly_net[month_key] -= tx.amount

        # Sort months
        sorted_months = sorted(monthly_net.keys())
        if len(sorted_months) < 2:
            return []  # Need some history

        # Calculate average monthly net cash flow (excluding current month as it's partial)
        historical_net_flows = [float(monthly_net[m]) for m in sorted_months[:-1]]
        avg_net_flow = simple_moving_average(historical_net_flows, window=3)

        # Current month so far
        current_month_key = ctx.today.strftime("%Y-%m")
        current_net = float(monthly_net[current_month_key])

        # Very simplistic: assume the rest of the month behaves like the average historical month
        # This could be improved significantly by checking days remaining, but keeps it simple for now.
        projected_net = current_net + (avg_net_flow * 0.5) # heuristic assumption
        
        # We don't have total cash balance in this context easily without Accounts, 
        # so we predict net cash flow for the period instead of absolute balance.
        
        confidence = ConfidenceLevel.MEDIUM if len(historical_net_flows) >= 3 else ConfidenceLevel.LOW
        
        return [
            Prediction(
                type=PredictionType.CASHFLOW,
                title="Projected Monthly Cash Flow",
                summary=f"Expected net cash flow by end of {ctx.today.strftime('%B')}.",
                confidence=confidence,
                methodology="Simple Moving Average (3-month window)",
                forecast_value=projected_net,
                forecast_period=ctx.forecast_period,
                recommendation="Review discretionary spending if this projection is lower than expected.",
                metadata={
                    "historical_average_net": avg_net_flow,
                    "current_month_net": current_net,
                }
            )
        ]
