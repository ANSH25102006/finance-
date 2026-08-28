from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.services.predictive_intelligence.engine import PredictiveIntelligenceEngine
from app.services.predictive_intelligence.models import ForecastPeriod, PredictionType

router = APIRouter(
    prefix="/api/predictions",
    tags=["predictions"],
    responses={404: {"description": "Not found"}},
)

from app.models.user import User

@router.get("")
def get_predictions(
    limit: int = Query(50, ge=1, le=100),
    forecast_period: ForecastPeriod = ForecastPeriod.DAYS_30,
    prediction_type: Optional[PredictionType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get deterministic financial predictions for the current user.
    """
    engine = PredictiveIntelligenceEngine(db=db, user_id=current_user.id)
    predictions = engine.run(forecast_period=forecast_period)
    
    if prediction_type:
        predictions = [p for p in predictions if p.type == prediction_type]
        
    predictions = predictions[:limit]
    
    return {
        "predictions": [p.to_dict() for p in predictions],
        "summary": {}
    }
