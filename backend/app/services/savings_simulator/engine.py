# ============================================================
#  engine.py — Simulator Engine
# ============================================================

from decimal import Decimal
from datetime import date
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.services.savings_simulator.models import SimulationRequest, SimulationResult, ScenarioType
from app.services.predictive_intelligence.engine import PredictiveIntelligenceEngine
from app.services.predictive_intelligence.models import ForecastPeriod, PredictionType

logger = logging.getLogger(__name__)

class SavingsSimulatorEngine:
    """
    Executes what-if scenarios and investment compounding projections deterministically.
    """
    def __init__(self, db: Session, user_id: UUID) -> None:
        self.db = db
        self.user_id = user_id

    def run(self, request: SimulationRequest) -> SimulationResult:
        # Get baseline cashflow projection using Predictive Intelligence
        pi_engine = PredictiveIntelligenceEngine(db=self.db, user_id=self.user_id)
        predictions = pi_engine.run(forecast_period=ForecastPeriod.DAYS_30)
        
        cashflow_prediction = next((p for p in predictions if p.type == PredictionType.CASHFLOW), None)
        baseline_balance = cashflow_prediction.forecast_value if cashflow_prediction else 0.0

        monthly_savings = 0.0
        methodology = "Static projection."
        meta = {}

        if request.scenario == ScenarioType.CANCEL_SUBSCRIPTION:
            amount = float(request.params.get("amount", 0))
            monthly_savings = amount
            methodology = f"Direct elimination of ₹{amount:,.0f} recurring monthly cost."
            
        elif request.scenario == ScenarioType.REDUCE_CATEGORY_SPEND:
            cat_id = request.params.get("category_id")
            reduction_pct = float(request.params.get("reduction_pct", 0))
            
            txs = self.db.query(Transaction).filter(
                Transaction.user_id == self.user_id,
                Transaction.category_id == cat_id,
                Transaction.transaction_type == 'expense'
            ).all()
            
            if txs:
                total_spend = sum(float(tx.amount) for tx in txs)
                avg_monthly = total_spend / 3.0 if total_spend > 0 else 0
                monthly_savings = avg_monthly * (reduction_pct / 100.0)
                methodology = f"Reduced historical average category spend (₹{avg_monthly:,.0f}/mo) by {reduction_pct}%."
                meta["historical_monthly_avg"] = round(avg_monthly, 2)
                
        elif request.scenario == ScenarioType.CUSTOM_SAVINGS:
            monthly_savings = float(request.params.get("amount", 0))
            methodology = "User-defined custom monthly savings applied to projection."

        # Compute investment compounding parameters
        annual_return_pct = float(request.params.get("annual_return_pct", 7.0))
        target_years = int(request.params.get("time_period_years", 3))

        # Build 1, 3, and 5 year compounding projections
        projections_by_year = {}
        for yrs in [1, 3, 5]:
            months = yrs * 12
            rate_per_month = (annual_return_pct / 100.0) / 12.0
            
            if rate_per_month > 0:
                future_value = monthly_savings * (((1.0 + rate_per_month) ** months - 1.0) / rate_per_month)
            else:
                future_value = monthly_savings * months

            total_contributed = monthly_savings * months
            growth_earned = future_value - total_contributed

            projections_by_year[f"{yrs}_year"] = {
                "years": yrs,
                "monthly_contribution": round(monthly_savings, 2),
                "total_contributions": round(total_contributed, 2),
                "growth_earned": round(growth_earned, 2),
                "final_projected_value": round(future_value, 2)
            }

        selected_projection = projections_by_year.get(f"{target_years}_year", projections_by_year["3_year"])

        meta["compounding"] = {
            "annual_return_pct": annual_return_pct,
            "target_years": target_years,
            "selected_summary": selected_projection,
            "projections_by_year": projections_by_year
        }

        # Calculate basic results
        annual_savings = monthly_savings * 12
        new_balance = baseline_balance + monthly_savings

        return SimulationResult(
            scenario=request.scenario,
            monthly_savings=round(monthly_savings, 2),
            annual_savings=round(annual_savings, 2),
            projected_balance_before=round(baseline_balance, 2),
            projected_balance_after=round(new_balance, 2),
            methodology=methodology,
            metadata=meta,
        )
