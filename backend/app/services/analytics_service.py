from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from datetime import date, timedelta
import calendar
from uuid import UUID

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category


class AnalyticsService:
    def __init__(self, db: Session, user_id: UUID):
        self.db = db
        self.user_id = user_id

    def get_dashboard_summary(self):
        """Aggregate current balance, total all-time income/expense, counts, averages, and extreme values."""
        balance = self.db.query(func.sum(Account.balance)).filter(Account.user_id == self.user_id).scalar()
        
        total_income = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'income'
        ).scalar()
        
        total_expense = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()
        
        income_val = float(total_income) if total_income is not None else 0.0
        expense_val = float(total_expense) if total_expense is not None else 0.0
        
        count = self.db.query(func.count(Transaction.id)).filter(Transaction.user_id == self.user_id).scalar() or 0
        avg_value = self.db.query(func.avg(Transaction.amount)).filter(Transaction.user_id == self.user_id).scalar()
        
        highest_expense = self.db.query(func.max(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()
        
        highest_income = self.db.query(func.max(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'income'
        ).scalar()
        
        return {
            "current_balance": float(balance) if balance is not None else 0.0,
            "total_income": income_val,
            "total_expenses": expense_val,
            "net_cash_flow": income_val - expense_val,
            "total_transaction_count": count,
            "average_transaction_value": float(avg_value) if avg_value is not None else 0.0,
            "highest_expense": float(highest_expense) if highest_expense is not None else 0.0,
            "highest_income": float(highest_income) if highest_income is not None else 0.0
        }

    def get_monthly_trends(self, months_count=12):
        """Aggregate last N months of income, expenses, and cash flow."""
        trends = []
        today = date.today()
        current_year = today.year
        current_month = today.month
        
        for i in range(months_count - 1, -1, -1):
            m = current_month - i
            y = current_year
            while m <= 0:
                m += 12
                y -= 1
            
            _, last_day = calendar.monthrange(y, m)
            start_d = date(y, m, 1)
            end_d = date(y, m, last_day)
            
            inc = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type == 'income',
                Transaction.transaction_date >= start_d,
                Transaction.transaction_date <= end_d
            ).scalar()
            
            exp = self.db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type == 'expense',
                Transaction.transaction_date >= start_d,
                Transaction.transaction_date <= end_d
            ).scalar()
            
            inc_val = float(inc) if inc is not None else 0.0
            exp_val = float(exp) if exp is not None else 0.0
            
            trends.append({
                "month": start_d.strftime("%b %Y"),
                "income": inc_val,
                "expense": exp_val,
                "net_cash_flow": inc_val - exp_val
            })
        return trends

    def get_category_breakdown(self):
        """Aggregate spending by categories and compute percentages."""
        total_expenses = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()
        
        total_expenses_val = float(total_expenses) if total_expenses is not None else 0.0
        
        rows = self.db.query(
            Category.name,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).outerjoin(Category, Transaction.category_id == Category.id) \
         .filter(
             Transaction.user_id == self.user_id,
             Transaction.transaction_type == 'expense'
         ).group_by(Category.name) \
         .order_by(desc("total")).all()
         
        result = []
        for name, total, count in rows:
            amount_val = float(total) if total is not None else 0.0
            percent = (amount_val / total_expenses_val * 100) if total_expenses_val > 0 else 0.0
            result.append({
                "category_name": name or "Uncategorized",
                "total_amount": amount_val,
                "percentage": round(percent, 2),
                "transaction_count": count
            })
        return result

    def get_top_merchants(self, limit=10):
        """Aggregate expenses by merchant name."""
        rows = self.db.query(
            Transaction.merchant,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.merchant.isnot(None),
            Transaction.merchant != ""
        ).group_by(Transaction.merchant) \
         .order_by(desc("total")).limit(limit).all()
         
        result = []
        for merchant, total, count in rows:
            result.append({
                "merchant_name": merchant,
                "total_amount": float(total) if total is not None else 0.0,
                "transaction_count": count
            })
        return result

    def get_largest_expenses(self, limit=10):
        """Fetch the top N largest expense transactions."""
        rows = self.db.query(
            Transaction.merchant,
            Transaction.amount,
            Category.name,
            Transaction.transaction_date,
            Transaction.description
        ).outerjoin(Category, Transaction.category_id == Category.id) \
         .filter(
             Transaction.user_id == self.user_id,
             Transaction.transaction_type == 'expense'
         ).order_by(desc(Transaction.amount)).limit(limit).all()
         
        result = []
        for merchant, amount, category_name, tx_date, descr in rows:
            result.append({
                "merchant": merchant or "No Merchant",
                "amount": float(amount) if amount is not None else 0.0,
                "category": category_name or "Uncategorized",
                "date": tx_date.isoformat(),
                "description": descr
            })
        return result

    def get_daily_spending(self, days=365):
        """Aggregate expense values grouped by transaction day."""
        start_date = date.today() - timedelta(days=days)
        rows = self.db.query(
            Transaction.transaction_date,
            func.sum(Transaction.amount).label("total")
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_date
        ).group_by(Transaction.transaction_date) \
         .order_by(Transaction.transaction_date.asc()).all()
         
        result = []
        for tx_date, total in rows:
            result.append({
                "date": tx_date.isoformat(),
                "total_spend": float(total) if total is not None else 0.0
            })
        return result

    def get_spending_trends(self):
        """Calculate averages and median values for spend trends analysis."""
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        one_year_ago = today - timedelta(days=365)
        
        spend_30 = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= thirty_days_ago
        ).scalar()
        
        spend_365 = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= one_year_ago
        ).scalar()
        
        avg_tx_expense = self.db.query(func.avg(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()
        
        # Dialect agnostic median check
        if self.db.bind.dialect.name == 'sqlite':
            amounts = [float(r[0]) for r in self.db.query(Transaction.amount).filter(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type == 'expense'
            ).all()]
            if not amounts:
                median_val = 0.0
            else:
                amounts.sort()
                n = len(amounts)
                if n % 2 == 1:
                    median_val = amounts[n // 2]
                else:
                    median_val = (amounts[n // 2 - 1] + amounts[n // 2]) / 2.0
        else:
            median_val = self.db.query(
                func.percentile_cont(0.5).within_group(Transaction.amount)
            ).filter(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type == 'expense'
            ).scalar()
            
        return {
            "average_daily_spend": float(spend_30) / 30.0 if spend_30 is not None else 0.0,
            "average_monthly_spend": float(spend_365) / 12.0 if spend_365 is not None else 0.0,
            "average_transaction_amount": float(avg_tx_expense) if avg_tx_expense is not None else 0.0,
            "median_transaction_amount": float(median_val) if median_val is not None else 0.0
        }

    def get_financial_health_score(self):
        """Compute user financial health score (0-100) using savings rate, ratios, and consistency logs."""
        today = date.today()
        ninety_days_ago = today - timedelta(days=90)
        
        income = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'income',
            Transaction.transaction_date >= ninety_days_ago
        ).scalar()
        
        expenses = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= ninety_days_ago
        ).scalar()
        
        income_val = float(income) if income is not None else 0.0
        expenses_val = float(expenses) if expenses is not None else 0.0
        
        savings_rate = ((income_val - expenses_val) / income_val * 100) if income_val > 0 else 0.0
        expense_ratio = (expenses_val / income_val * 100) if income_val > 0 else 0.0
        
        # Savings Rate Score (Max 30)
        score_savings = 0
        if savings_rate >= 30:
            score_savings = 30
        elif savings_rate >= 15:
            score_savings = 20
        elif savings_rate > 0:
            score_savings = 10
            
        # Expense-to-Income Ratio Score (Max 30)
        score_ratio = 0
        if income_val > 0:
            if expense_ratio < 50:
                score_ratio = 30
            elif expense_ratio < 75:
                score_ratio = 20
            elif expense_ratio < 90:
                score_ratio = 10
                
        # Income consistency in last 90 days (Max 20)
        # Fallback to query distinct months
        if self.db.bind.dialect.name == 'postgresql':
            month_expr = func.extract('month', Transaction.transaction_date)
        else:
            month_expr = func.strftime('%m', Transaction.transaction_date)
            
        income_months = self.db.query(func.count(func.distinct(month_expr))).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'income',
            Transaction.transaction_date >= ninety_days_ago
        ).scalar() or 0
        
        score_consistency = 10
        if income_months >= 3:
            score_consistency = 20
        elif income_months >= 2:
            score_consistency = 15
            
        # Spending transactions consistency (Max 20)
        tx_count = self.db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_date >= ninety_days_ago
        ).scalar() or 0
        
        score_spending = 10
        if tx_count >= 15:
            score_spending = 20
        elif tx_count >= 5:
            score_spending = 15
            
        total_score = score_savings + score_ratio + score_consistency + score_spending
        
        if total_score >= 80:
            rating = "Excellent"
        elif total_score >= 60:
            rating = "Good"
        elif total_score >= 40:
            rating = "Fair"
        else:
            rating = "Needs Improvement"
            
        explanations = []
        if income_val == 0:
            explanations.append("No recent income detected. Record monthly income to compute complete savings health.")
        else:
            explanations.append(f"Savings rate is {savings_rate:.1f}% over the last 90 days.")
            if savings_rate < 15:
                explanations.append("Your savings rate is lower than the recommended 15%. Try tracking category budgets.")
            else:
                explanations.append("Healthy savings buffer. You are keeping a nice portion of your income.")
                
        if expense_ratio > 80:
            explanations.append("High expense-to-income ratio. We recommend checking your top merchant details.")
        elif income_val > 0:
            explanations.append("Your spending is well within standard budget targets.")
            
        if tx_count < 5:
            explanations.append("Low logging volume. Log more transactions to ensure a more accurate representation of your financial health.")
            
        return {
            "score": total_score,
            "rating": rating,
            "explanations": explanations
        }
