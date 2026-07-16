from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.services.audit_service import AuditService
from app.schemas.audit import AuditResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.post("/preview", response_model=AuditResponse)
def get_audit_preview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and return the structured financial audit analysis."""
    service = AuditService(db, current_user.id)
    return service.run_financial_audit()
