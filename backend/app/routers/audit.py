from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.services.audit_service import AuditService
from app.schemas.audit import AuditResponse, FinancialAuditRulesResponse
from typing import Optional
from datetime import date

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.post("/preview", response_model=AuditResponse)
def get_audit_preview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and return the structured financial audit analysis."""
    service = AuditService(db, current_user.id)
    return service.run_financial_audit()


@router.get("", response_model=FinancialAuditRulesResponse)
def get_financial_audit(
    severity: Optional[str] = None,
    rule_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate financial audit rules and return findings with optional filtering."""
    service = AuditService(db, current_user.id)
    return service.run_rules_audit(
        severity_filter=severity,
        rule_type_filter=rule_type,
        start_date=start_date,
        end_date=end_date
    )
