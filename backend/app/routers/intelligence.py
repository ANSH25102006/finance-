# ============================================================
#  routers/intelligence.py
#  GET /api/intelligence/insights
#
#  Exposes the Financial Intelligence Engine as a REST endpoint.
#  All insights are deterministically computed — no LLM involved.
# ============================================================

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.financial_intelligence.engine import FinancialIntelligenceEngine
from app.services.financial_intelligence.enums import InsightSeverity, InsightType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["Financial Intelligence"])


@router.get(
    "/insights",
    summary="Get deterministic financial insights",
    description=(
        "Runs the Financial Intelligence Engine and returns a prioritised list of "
        "deterministic insights covering spending spikes, budget drift, goal progress, "
        "income changes, emergency fund status, and more. "
        "No LLM is involved — all insights are computed from your transaction history."
    ),
    response_model=list[dict[str, Any]],
)
def get_financial_insights(
    severity: InsightSeverity | None = Query(
        default=None,
        description="Filter by severity level (CRITICAL, WARNING, INFO, SUCCESS).",
    ),
    type: InsightType | None = Query(
        default=None,
        description="Filter by insight type.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of insights to return.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """
    Execute the Financial Intelligence Engine for the authenticated user
    and return a severity-sorted list of structured insights.

    Query Parameters
    ----------------
    severity : optional
        Filter results to a specific severity level.
    type : optional
        Filter results to a specific insight type.
    limit : optional (default 50)
        Cap the number of returned insights.
    """
    engine = FinancialIntelligenceEngine(db=db, user_id=current_user.id)
    insights = engine.run()

    # Optional filters
    if severity is not None:
        insights = [i for i in insights if i.severity == severity]
    if type is not None:
        insights = [i for i in insights if i.type == type]

    # Apply limit
    insights = insights[:limit]

    logger.info(
        "Serving %d insights for user %s (severity=%s, type=%s)",
        len(insights),
        current_user.id,
        severity,
        type,
    )

    return [i.to_dict() for i in insights]
