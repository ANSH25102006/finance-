from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.routers.auth import get_current_user
from app.services.savings_simulator.models import SimulationRequest, SimulationResult
from app.services.savings_simulator.engine import SavingsSimulatorEngine
from app.models.user import User

router = APIRouter(
    prefix="/api/simulator",
    tags=["simulator"],
)

@router.post("/run", response_model=None)
def run_simulation(
    request: SimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a deterministic savings simulation scenario with investment compounding projections.
    """
    engine = SavingsSimulatorEngine(db=db, user_id=current_user.id)
    result = engine.run(request)
    return {
        "scenario": result.scenario.value,
        "monthly_savings": result.monthly_savings,
        "annual_savings": result.annual_savings,
        "new_balance": result.projected_balance_after,
        "methodology": result.methodology,
        "compounding": result.metadata.get("compounding", {})
    }
