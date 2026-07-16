from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve high level financial dashboard summary values."""
    service = AnalyticsService(db, current_user.id)
    return service.get_dashboard_summary()


@router.get("/monthly-trends")
def get_analytics_monthly_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve monthly spending and income trends for the last 12 months."""
    service = AnalyticsService(db, current_user.id)
    return service.get_monthly_trends()


@router.get("/category-breakdown")
def get_analytics_category_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve spending aggregates by category."""
    service = AnalyticsService(db, current_user.id)
    return service.get_category_breakdown()


@router.get("/top-merchants")
def get_analytics_top_merchants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve top merchants sorted by spending amount."""
    service = AnalyticsService(db, current_user.id)
    return service.get_top_merchants()


@router.get("/largest-expenses")
def get_analytics_largest_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve top 10 largest expense logs."""
    service = AnalyticsService(db, current_user.id)
    return service.get_largest_expenses()


@router.get("/cash-flow")
def get_analytics_cash_flow(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve cash flow trend details."""
    service = AnalyticsService(db, current_user.id)
    return service.get_monthly_trends()


@router.get("/daily-spending")
def get_analytics_daily_spending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve daily expense logs for the last 365 days."""
    service = AnalyticsService(db, current_user.id)
    return service.get_daily_spending()


@router.get("/spending-trend")
def get_analytics_spending_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve averages and median spending metrics."""
    service = AnalyticsService(db, current_user.id)
    return service.get_spending_trends()


@router.get("/financial-health")
def get_analytics_financial_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve financial health score and feedback logs."""
    service = AnalyticsService(db, current_user.id)
    return service.get_financial_health_score()
