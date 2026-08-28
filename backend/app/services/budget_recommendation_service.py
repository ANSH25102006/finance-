# ============================================================
#  app/services/budget_recommendation_service.py
#  Calculates rolling 3-6 month category averages and generates
#  deterministic budget recommendations and discretionary savings trims.
# ============================================================

from typing import List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.transaction import Transaction
from app.models.category import Category

DISCRETIONARY_CATEGORIES = {
    "food delivery", "shopping", "entertainment",
    "travel", "dining", "leisure", "subscriptions"
}

class BudgetRecommendationService:
    def __init__(self, db: Session, user_id: UUID):
        self.db = db
        self.user_id = user_id

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Calculates rolling monthly averages per category and suggests target budget allocations.
        """
        # Fetch user's categories
        categories = self.db.query(Category).filter(
            or_(Category.user_id == self.user_id, Category.user_id.is_(None))
        ).all()
        cat_map = {c.id: c for c in categories}

        # Fetch expense transactions
        expenses = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == "expense"
        ).all()

        if not expenses:
            return []

        # Group by category_id -> month_str -> total_amount
        cat_monthly = defaultdict(lambda: defaultdict(float))
        current_month_spend = defaultdict(float)

        today = date.today()
        current_month_key = today.strftime("%Y-%m")

        for tx in expenses:
            if not tx.category_id:
                continue
            month_key = tx.transaction_date.strftime("%Y-%m")
            cat_monthly[tx.category_id][month_key] += float(tx.amount)
            if month_key == current_month_key:
                current_month_spend[tx.category_id] += float(tx.amount)

        recommendations = []

        for cat_id, month_data in cat_monthly.items():
            cat = cat_map.get(cat_id)
            cat_name = cat.name if cat else "Uncategorized"
            cat_name_lower = cat_name.lower()

            # Exclude current partial month from historical baseline if we have prior months
            all_months = sorted(month_data.keys())
            historical_months = [m for m in all_months if m != current_month_key]
            if not historical_months:
                historical_months = all_months

            # Limit to last 6 months
            recent_months = historical_months[-6:]
            totals = [month_data[m] for m in recent_months]
            hist_avg = sum(totals) / len(totals) if totals else 0.0

            if hist_avg <= 0:
                continue

            is_disc = any(d in cat_name_lower for d in DISCRETIONARY_CATEGORIES)
            trim_pct = 0.15 if is_disc else 0.05
            rec_budget = round(hist_avg * (1.0 - trim_pct), 2)
            suggested_reduction = round(hist_avg - rec_budget, 2)
            monthly_savings = suggested_reduction
            annual_savings = round(monthly_savings * 12, 2)

            curr_spend = round(current_month_spend.get(cat_id, 0.0), 2)

            if is_disc:
                explanation = (
                    f"Discretionary category with a rolling historical average of ₹{hist_avg:,.2f}/mo. "
                    f"Trimming 15% yields a recommended budget of ₹{rec_budget:,.2f}/mo, saving ₹{annual_savings:,.2f}/yr."
                )
            else:
                explanation = (
                    f"Essential category with a rolling historical average of ₹{hist_avg:,.2f}/mo. "
                    f"A conservative 5% optimization targets a budget of ₹{rec_budget:,.2f}/mo."
                )

            recommendations.append({
                "category_id": str(cat_id),
                "category_name": cat_name,
                "historical_monthly_average": round(hist_avg, 2),
                "recommended_budget": rec_budget,
                "current_month_spend": curr_spend,
                "suggested_reduction": suggested_reduction,
                "potential_monthly_savings": monthly_savings,
                "potential_annual_savings": annual_savings,
                "is_discretionary": is_disc,
                "explanation": explanation
            })

        # Sort by potential annual savings descending
        return sorted(recommendations, key=lambda r: r["potential_annual_savings"], reverse=True)
