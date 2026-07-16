from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import calendar
from uuid import UUID

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.category import Category
from app.services.analytics_service import AnalyticsService

class DashboardService:
    def __init__(self, db: Session, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self.analytics = AnalyticsService(db, user_id)
        
        now = datetime.now()
        self.current_month = now.month
        self.current_year = now.year
        
        # Calculate start and end of current month
        _, last_day = calendar.monthrange(self.current_year, self.current_month)
        self.start_date = datetime(self.current_year, self.current_month, 1).date()
        self.end_date = datetime(self.current_year, self.current_month, last_day).date()
        
        # Last month calculations
        if self.current_month == 1:
            self.last_month = 12
            self.last_year = self.current_year - 1
        else:
            self.last_month = self.current_month - 1
            self.last_year = self.current_year
            
        _, last_day_prev = calendar.monthrange(self.last_year, self.last_month)
        self.start_date_prev = datetime(self.last_year, self.last_month, 1).date()
        self.end_date_prev = datetime(self.last_year, self.last_month, last_day_prev).date()

    def get_summary(self):
        """Aggregate all dashboard data into a single payload."""
        
        income_current = self.calculate_income(self.start_date, self.end_date)
        income_prev = self.calculate_income(self.start_date_prev, self.end_date_prev)
        
        expense_current = self.calculate_expenses(self.start_date, self.end_date)
        expense_prev = self.calculate_expenses(self.start_date_prev, self.end_date_prev)
        
        cash_flow_current = income_current - expense_current
        savings_rate_current = (cash_flow_current / income_current * 100) if income_current > 0 else 0
        
        return {
            "netWorth": self.calculate_net_worth(),
            "income": {
                "current": income_current,
                "previous": income_prev,
                "change": self._calc_pct_change(income_prev, income_current)
            },
            "expenses": {
                "current": expense_current,
                "previous": expense_prev,
                "change": self._calc_pct_change(expense_prev, expense_current)
            },
            "cashFlow": cash_flow_current,
            "savingsRate": savings_rate_current,
            "financialHealth": self.calculate_financial_health(savings_rate_current),
            "budgets": self.calculate_budget_utilization(),
            "goals": self.calculate_goal_progress(),
            "recentTransactions": self.get_recent_activity(5),
            "categoryBreakdown": self.calculate_category_breakdown(),
            "monthlyTrend": self.get_monthly_trend()
        }

    def _calc_pct_change(self, prev, current):
        if prev == 0:
            return 100 if current > 0 else 0
        return ((current - prev) / prev) * 100

    def calculate_net_worth(self):
        return self.analytics.get_dashboard_summary()["current_balance"]

    def calculate_income(self, start_d, end_d):
        result = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'income',
            Transaction.transaction_date >= start_d,
            Transaction.transaction_date <= end_d
        ).scalar()
        return float(result) if result is not None else 0.0

    def calculate_expenses(self, start_d, end_d):
        result = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_d,
            Transaction.transaction_date <= end_d
        ).scalar()
        return float(result) if result is not None else 0.0

    def calculate_financial_health(self, savings_rate):
        return self.analytics.get_financial_health_score()["score"]

    def calculate_budget_utilization(self):
        budgets = self.db.query(Budget).filter(
            Budget.user_id == self.user_id,
            Budget.month == self.current_month,
            Budget.year == self.current_year
        ).all()
        
        result = []
        for b in budgets:
            category = self.db.query(Category).filter(Category.id == b.category_id).first()
            spent_val = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == self.user_id,
                Transaction.category_id == b.category_id,
                Transaction.transaction_type == 'expense',
                Transaction.transaction_date >= self.start_date,
                Transaction.transaction_date <= self.end_date
            ).scalar()
            spent = float(spent_val) if spent_val is not None else 0.0
            
            percent = (spent / b.amount * 100) if b.amount > 0 else 0
            
            result.append({
                "id": str(b.id),
                "title": category.name if category else "Unknown",
                "icon": category.icon if category else "Circle",
                "color": category.color if category else "#ffffff",
                "target": b.amount,
                "current": spent,
                "percent": min(percent, 100),
                "isExceeded": spent > b.amount
            })
        return result

    def calculate_goal_progress(self):
        goals = self.db.query(Goal).filter(Goal.user_id == self.user_id).all()
        result = []
        for g in goals:
            percent = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0
            result.append({
                "id": str(g.id),
                "title": g.name,
                "target": g.target_amount,
                "current": g.current_amount,
                "percent": min(percent, 100),
                "icon": g.icon or "Star",
                "color": g.color or "#ffffff",
                "date": g.deadline.strftime("%b '%y") if g.deadline else "No date"
            })
        return result

    def get_recent_activity(self, limit=5):
        txs = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc()).limit(limit).all()
        result = []
        for tx in txs:
            cat = self.db.query(Category).filter(Category.id == tx.category_id).first()
            result.append({
                "id": str(tx.id),
                "merchant": tx.merchant or tx.description,
                "category": cat.name if cat else "Uncategorized",
                "date": tx.transaction_date.isoformat(),
                "amount": float(tx.amount),
                "type": tx.transaction_type,
                "logo": cat.icon[0] if cat and cat.icon else (tx.merchant[0] if tx.merchant else "?"),
                "color": cat.color if cat else "#ffffff",
                "status": "Cleared"
            })
        return result

    def calculate_category_breakdown(self):
        # Top 5 expense categories for current month
        rows = self.db.query(
            Transaction.category_id, 
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= self.start_date,
            Transaction.transaction_date <= self.end_date
        ).group_by(Transaction.category_id).order_by(func.sum(Transaction.amount).desc()).limit(5).all()
        
        total_expenses = self.calculate_expenses(self.start_date, self.end_date)
        result = []
        
        for row in rows:
            cat_id, amt = row
            amt_float = float(amt) if amt is not None else 0.0
            cat = self.db.query(Category).filter(Category.id == cat_id).first()
            if cat:
                percent = (amt_float / total_expenses * 100) if total_expenses > 0 else 0
                result.append({
                    "name": cat.name,
                    "value": round(percent, 1),
                    "amount": amt_float,
                    "color": cat.color or "#ffffff"
                })
        return result

    def get_monthly_trend(self):
        # Retrieve 6 months trends from AnalyticsService and map keys
        trends = self.analytics.get_monthly_trends(months_count=6)
        return [
            {
                "month": t["month"].split(" ")[0],
                "income": t["income"],
                "expenses": t["expense"]
            }
            for t in trends
        ]
