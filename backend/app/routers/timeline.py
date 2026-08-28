from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.services.financial_timeline.engine import FinancialTimelineEngine
from app.services.financial_timeline.enums import TimelineEventSeverity, TimelineEventType

router = APIRouter(
    prefix="/api/timeline",
    tags=["timeline"],
    responses={404: {"description": "Not found"}},
)

from app.models.user import User

@router.get("")
def get_timeline(
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[TimelineEventSeverity] = None,
    event_type: Optional[TimelineEventType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the chronological financial timeline for the current user.
    Generated dynamically by the FinancialTimelineEngine.
    """
    engine = FinancialTimelineEngine(db=db, user_id=current_user.id)
    events = engine.run()
    
    # Simple in-memory filtering (could push to builders in future if it gets large, 
    # but currently builder needs context for deduping properly)
    if severity:
        events = [e for e in events if e.severity == severity]
        
    if event_type:
        events = [e for e in events if e.type == event_type]
        
    # Apply limit
    events = events[:limit]
    
    return {
        "events": [e.to_dict() for e in events]
    }
