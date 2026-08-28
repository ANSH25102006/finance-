# ============================================================
#  goal_projection.py — Predicts goal completion
# ============================================================

from decimal import Decimal

from app.services.predictive_intelligence.models import Prediction, PredictionType, ConfidenceLevel
from app.services.predictive_intelligence.predictor_base import BasePredictor, PredictionContext

class GoalProjectionPredictor(BasePredictor):
    name = "GoalProjectionPredictor"

    def predict(self, ctx: PredictionContext) -> list[Prediction]:
        if not ctx.goals:
            return []

        predictions = []

        for goal in ctx.goals:
            # For a real implementation we'd check Goal contribution history.
            # Here we do a simple assumption based on target date if it exists, or a static rate.
            target = float(goal.target_amount)
            current = float(goal.current_amount)
            
            if current >= target:
                continue # Already completed
                
            remaining = target - current
            
            # Simple heuristic: assume they've been saving uniformly since the goal was created
            days_since_creation = (ctx.today - goal.created_at.date()).days
            if days_since_creation < 7:
                continue # Not enough history
                
            daily_saving_rate = current / days_since_creation
            
            if daily_saving_rate <= 0:
                continue
                
            days_to_complete = remaining / daily_saving_rate
            
            # Predict the value after 30 days based on this rate
            projected_value_30_days = current + (daily_saving_rate * 30)
            
            predictions.append(
                Prediction(
                    type=PredictionType.GOAL,
                    title=f"Goal Projection: {goal.name}",
                    summary=f"Expected to reach target in {int(days_to_complete)} days.",
                    confidence=ConfidenceLevel.LOW,
                    methodology="Historical Daily Saving Rate Extrapolation",
                    forecast_value=min(projected_value_30_days, target),
                    forecast_period=ctx.forecast_period,
                    related_entity_id=str(goal.id),
                    recommendation="Consider increasing contributions to reach your goal faster.",
                    metadata={
                        "target_amount": target,
                        "current_amount": current,
                        "daily_saving_rate": daily_saving_rate,
                        "estimated_days_remaining": int(days_to_complete)
                    }
                )
            )

        return predictions
