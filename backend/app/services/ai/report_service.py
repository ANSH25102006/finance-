from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List
from collections import defaultdict
from app.models.goal import Goal
from app.models.account import Account

class ReportService:
    """
    Generates a structured, export-ready monthly financial report.
    Consolidates:
    - Income, Expenses, Savings, Cash Balance
    - Budget utilization, Subscriptions
    - Goal progress
    - Achievements & Warnings
    - Summary analytics
    """

    def generate_monthly_report(
        self,
        db: Session,
        user_id: UUID,
        context_data: Any,  # FinancialContext Pydantic model
        patterns: Dict[str, Any],
        subs_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 1. Fetch user goals
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        goals_list = []
        for g in goals:
            pct = (g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0.0
            goals_list.append({
                "name": g.name,
                "target_amount": round(g.target_amount, 2),
                "current_amount": round(g.current_amount, 2),
                "progress_pct": round(pct, 2),
                "monthly_contribution": round(g.monthly_contribution, 2),
                "deadline": str(g.deadline) if g.deadline else None
            })

        # 2. Fetch cash balances (Net Worth proxy)
        accounts = db.query(Account).filter(Account.user_id == user_id).all()
        net_worth = sum(float(a.balance) for a in accounts)

        # 3. Compile Achievements & Warnings
        achievements = []
        warnings = []

        # Achievements
        savings_rate = context_data.health.savings_rate
        if savings_rate > 20.0:
            achievements.append(f"Outstanding savings rate of {savings_rate:.1f}% this month (target is >20%).")
        elif savings_rate > 0.0:
            achievements.append(f"Positive savings rate of {savings_rate:.1f}% achieved.")

        if patterns.get("mom_change_pct", 0.0) < 0:
            achievements.append(f"Reduced overall spending by {abs(patterns['mom_change_pct'])}% compared to last month.")

        budget_remaining = context_data.categories.remaining_budget
        if budget_remaining > 0:
            achievements.append(f"Maintained {budget_remaining:.2f} of safety margin across budgets.")

        # Warnings
        exceeded_count = len(context_data.categories.exceeded_budgets)
        if exceeded_count > 0:
            warnings.append(f"Exceeded your budget limit in {exceeded_count} categories: {', '.join(context_data.categories.exceeded_budgets)}.")

        duplicate_count = len(subs_data.get("duplicate_subscriptions", []))
        if duplicate_count > 0:
            warnings.append(f"Detected {duplicate_count} potential duplicate subscription plans.")

        spikes_count = len(patterns.get("spikes", []))
        if spikes_count > 0:
            warnings.append(f"Identified {spikes_count} unusual spending spike(s) (>3x your median transaction size).")

        # 4. Standard Fallbacks
        if not achievements:
            achievements.append("Completed another month of tracking your financial progress.")
        if not warnings:
            warnings.append("No active alerts or overspending warnings detected.")

        # 5. Compile Monthly Summary
        monthly_summary = (
            f"During {context_data.profile.current_month}, you received a total income of "
            f"{context_data.income.monthly_income:.2f} and spent {context_data.expenses.monthly_expenses:.2f}, "
            f"yielding a savings rate of {savings_rate:.1f}%. Your largest spending category was "
            f"'{patterns.get('largest_category', 'Unknown')}' with {patterns.get('largest_cat_amount', 0.0):.2f}. "
            f"We tracked {len(context_data.subscriptions.active_subscriptions)} recurring subscriptions costing you "
            f"{context_data.subscriptions.monthly_subscription_cost:.2f} per month."
        )

        return {
            "profile": {
                "month": context_data.profile.current_month,
                "currency": context_data.profile.currency,
                "net_worth": round(net_worth, 2)
            },
            "cash_flow": {
                "income": round(context_data.income.monthly_income, 2),
                "expenses": round(context_data.expenses.monthly_expenses, 2),
                "savings": round(context_data.income.monthly_income - context_data.expenses.monthly_expenses, 2),
                "savings_rate_pct": round(savings_rate, 2)
            },
            "top_categories": patterns.get("top_merchants", [])[:3],
            "top_merchants": patterns.get("top_merchants", [])[:3],
            "largest_purchase": patterns.get("highest_value_purchases", [])[0] if patterns.get("highest_value_purchases", []) else None,
            "subscriptions": {
                "active_count": len(context_data.subscriptions.active_subscriptions),
                "monthly_cost": round(context_data.subscriptions.monthly_subscription_cost, 2),
                "annual_cost": round(context_data.subscriptions.annual_subscription_cost, 2),
                "potential_savings": round(subs_data.get("potential_savings", 0.0), 2)
            },
            "budgets": {
                "total_budgets": len(context_data.categories.budget_utilization),
                "remaining_amount": round(context_data.categories.remaining_budget, 2),
                "exceeded_categories": context_data.categories.exceeded_budgets
            },
            "goals": goals_list,
            "achievements": achievements,
            "warnings": warnings,
            "monthly_summary": monthly_summary
        }
