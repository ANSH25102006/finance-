from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, datetime, timezone, timedelta
import calendar
from uuid import UUID
from typing import List, Dict, Any

from app.models.budget import Budget
from app.models.goal import Goal
from app.models.category import Category
from app.models.transaction import Transaction
from app.services.analytics_service import AnalyticsService


class AuditService:
    def __init__(self, db: Session, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self.analytics = AnalyticsService(db, user_id)

    def run_financial_audit(self) -> Dict[str, Any]:
        """Core coordinator that aggregates all audit details."""
        # 1. Fetch Shared Analytics
        summary_data = self.analytics.get_dashboard_summary()
        trends = self.analytics.get_monthly_trends(months_count=12)
        category_alltime = self.analytics.get_category_breakdown()
        top_merchants = self.analytics.get_top_merchants()
        largest_expenses = self.analytics.get_largest_expenses()
        daily_spending = self.analytics.get_daily_spending()
        spending_trends = self.analytics.get_spending_trends()
        health_score = self.analytics.get_financial_health_score()

        # Dates definitions
        today = date.today()
        current_year = today.year
        current_month = today.month

        # Generate current and previous month dates
        _, last_day_curr = calendar.monthrange(current_year, current_month)
        start_d_curr = date(current_year, current_month, 1)
        end_d_curr = date(current_year, current_month, last_day_curr)

        prev_month = current_month - 1
        prev_year = current_year
        if prev_month <= 0:
            prev_month = 12
            prev_year -= 1
        _, last_day_prev = calendar.monthrange(prev_year, prev_month)
        start_d_prev = date(prev_year, prev_month, 1)
        end_d_prev = date(prev_year, prev_month, last_day_prev)

        # 2. Income and Expense Growth MoM
        curr_month_income = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'income',
            Transaction.transaction_date >= start_d_curr,
            Transaction.transaction_date <= end_d_curr
        ).scalar() or 0.0

        prev_month_income = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'income',
            Transaction.transaction_date >= start_d_prev,
            Transaction.transaction_date <= end_d_prev
        ).scalar() or 0.0

        curr_month_expense = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_d_curr,
            Transaction.transaction_date <= end_d_curr
        ).scalar() or 0.0

        prev_month_expense = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_d_prev,
            Transaction.transaction_date <= end_d_prev
        ).scalar() or 0.0

        curr_month_income_f = float(curr_month_income)
        prev_month_income_f = float(prev_month_income)
        curr_month_expense_f = float(curr_month_expense)
        prev_month_expense_f = float(prev_month_expense)

        income_growth = ((curr_month_income_f - prev_month_income_f) / prev_month_income_f * 100) if prev_month_income_f > 0 else 0.0
        expense_growth = ((curr_month_expense_f - prev_month_expense_f) / prev_month_expense_f * 100) if prev_month_expense_f > 0 else 0.0

        # Calculate savings rate & expense ratio over the last 90 days for consistency
        ninety_days_ago = today - timedelta(days=90)
        total_income_90 = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'income',
            Transaction.transaction_date >= ninety_days_ago
        ).scalar() or 0.0

        total_expense_90 = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= ninety_days_ago
        ).scalar() or 0.0

        total_income_90_f = float(total_income_90)
        total_expense_90_f = float(total_expense_90)

        savings_rate = ((total_income_90_f - total_expense_90_f) / total_income_90_f * 100) if total_income_90_f > 0 else 0.0
        expense_ratio = (total_expense_90_f / total_income_90_f * 100) if total_income_90_f > 0 else 0.0

        # 3. Budget Analysis
        budgets_data = self._calculate_budgets()

        # 4. Goals Analysis
        goals_data = self._calculate_goals()

        # 5. Category Insights (including MoM changes)
        category_insights = self._calculate_category_insights(start_d_curr, end_d_curr, start_d_prev, end_d_prev)

        # 6. Merchant Analysis
        merchant_analysis = self._calculate_merchants(top_merchants)

        # 7. Cash Flow Analysis
        cashflow_analysis = self._calculate_cashflow(trends)

        # 8. Risks detection
        risks = self._detect_risks(
            curr_month_income_f,
            curr_month_expense_f,
            savings_rate,
            budgets_data,
            category_alltime,
            expense_growth,
            goals_data,
            spending_trends
        )

        # 9. Rules and Insights engine
        insights = self._generate_insights_rules(
            savings_rate,
            expense_ratio,
            category_alltime,
            income_growth,
            expense_growth,
            summary_data["current_balance"],
            spending_trends,
            budgets_data,
            goals_data,
            trends,
            curr_month_income_f
        )

        # Output payload
        return {
            "summary": {
                "current_balance": summary_data["current_balance"],
                "total_income": summary_data["total_income"],
                "total_expenses": summary_data["total_expenses"],
                "net_cash_flow": summary_data["net_cash_flow"],
                "savings_rate": round(savings_rate, 2),
                "expense_ratio": round(expense_ratio, 2),
                "income_growth": round(income_growth, 2),
                "expense_growth": round(expense_growth, 2),
                "financial_health_score": float(health_score["score"]),
                "financial_rating": health_score["rating"]
            },
            "health": health_score,
            "budgets": budgets_data,
            "goals": goals_data,
            "categories": category_insights,
            "merchants": merchant_analysis,
            "cashflow": cashflow_analysis,
            "risks": risks,
            "insights": insights,
            "metadata": {
                "generated_at": datetime.now(timezone.utc),
                "user_id": self.user_id,
                "currency": "INR",
                "analysis_period": "Trailing 12 Months",
                "version": "1.0.0"
            }
        }

    def _calculate_budgets(self) -> List[Dict[str, Any]]:
        """Query and calculate all budget allocations and utilization."""
        budgets = self.db.query(Budget).filter(Budget.user_id == self.user_id).all()
        if not budgets:
            return []

        # Find sums of expenses grouped by category, month, year to avoid N+1
        tx_sums = self.db.query(
            Transaction.category_id,
            func.extract('month', Transaction.transaction_date).label('month'),
            func.extract('year', Transaction.transaction_date).label('year'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).group_by(
            Transaction.category_id,
            'month',
            'year'
        ).all()

        sums_map = {}
        for cat_id, m, y, total in tx_sums:
            if cat_id:
                m_val = int(m) if m is not None else 0
                y_val = int(y) if y is not None else 0
                sums_map[(cat_id, m_val, y_val)] = float(total) if total is not None else 0.0

        result = []
        for b in budgets:
            category_name = b.category.name if b.category else "Uncategorized"
            spent = sums_map.get((b.category_id, b.month, b.year), 0.0)
            remaining = b.amount - spent
            remaining_pct = (remaining / b.amount * 100) if b.amount > 0 else 0.0
            utilization_pct = (spent / b.amount * 100) if b.amount > 0 else 0.0

            if utilization_pct <= 80:
                status = "Healthy"
            elif utilization_pct <= 100:
                status = "Warning"
            else:
                status = "Exceeded"

            result.append({
                "category_name": category_name,
                "budget": float(b.amount),
                "spent": spent,
                "remaining": remaining,
                "remaining_pct": round(remaining_pct, 2),
                "utilization_pct": round(utilization_pct, 2),
                "status": status
            })
        return result

    def _calculate_goals(self) -> List[Dict[str, Any]]:
        """Analyze goals target, completion ratios, deadlines and pacing status."""
        goals = self.db.query(Goal).filter(Goal.user_id == self.user_id).all()
        if not goals:
            return []

        result = []
        for g in goals:
            target = float(g.target_amount)
            current = float(g.current_amount)
            remaining = max(0.0, target - current)
            pct = (current / target * 100) if target > 0 else 0.0

            # Estimate completion
            contr = float(g.monthly_contribution)
            if current >= target:
                est = "Completed"
                status = "Completed"
            else:
                if contr > 0:
                    months = remaining / contr
                    est = f"{round(months, 1)} months"
                else:
                    est = "Indefinite (No monthly contributions)"

                # Pace status
                if g.deadline:
                    # Parse local/UTC bounds
                    deadline_date = g.deadline.date() if isinstance(g.deadline, datetime) else g.deadline
                    today = date.today()
                    months_left = (deadline_date.year - today.year) * 12 + deadline_date.month - today.month
                    months_left = max(1, months_left)
                    required = remaining / months_left
                    if contr >= required:
                        status = "On Track"
                    else:
                        status = "Behind"
                else:
                    status = "On Track" if contr > 0 else "Behind"

            result.append({
                "name": g.name,
                "target_amount": target,
                "current_amount": current,
                "remaining_amount": remaining,
                "completion_pct": round(pct, 2),
                "estimated_completion": est,
                "status": status
            })
        return result

    def _calculate_category_insights(self, start_d_curr, end_d_curr, start_d_prev, end_d_prev) -> Dict[str, Any]:
        """Aggregate MoM changes, fastest growing categories and overall allocations."""
        total_expenses = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()
        total_expenses_val = float(total_expenses) if total_expenses is not None else 0.0

        # Current Month sums
        curr_sums = self.db.query(
            Category.name,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).outerjoin(Category, Transaction.category_id == Category.id) \
         .filter(
             Transaction.user_id == self.user_id,
             Transaction.transaction_type == 'expense',
             Transaction.transaction_date >= start_d_curr,
             Transaction.transaction_date <= end_d_curr
         ).group_by(Category.name).all()

        # Previous Month sums
        prev_sums = self.db.query(
            Category.name,
            func.sum(Transaction.amount).label("total")
        ).outerjoin(Category, Transaction.category_id == Category.id) \
         .filter(
             Transaction.user_id == self.user_id,
             Transaction.transaction_type == 'expense',
             Transaction.transaction_date >= start_d_prev,
             Transaction.transaction_date <= end_d_prev
         ).group_by(Category.name).all()

        prev_map = {name or "Uncategorized": float(total) for name, total in prev_sums if total is not None}

        items = []
        fastest_growing = None
        max_growth_pct = -9999.0
        largest_cat = None
        max_spent = 0.0
        least_used_cat = None
        min_spent = 999999999.0

        for name_raw, total, count in curr_sums:
            name = name_raw or "Uncategorized"
            amount_val = float(total) if total is not None else 0.0
            percent = (amount_val / total_expenses_val * 100) if total_expenses_val > 0 else 0.0

            # MoM
            prev_amount = prev_map.get(name, 0.0)
            mom_change = None
            if prev_amount > 0:
                mom_change = ((amount_val - prev_amount) / prev_amount) * 100

            items.append({
                "category_name": name,
                "total_amount": amount_val,
                "percentage": round(percent, 2),
                "transaction_count": count,
                "mom_change_pct": round(mom_change, 2) if mom_change is not None else None
            })

            # Growth tracker
            if mom_change is not None and mom_change > max_growth_pct:
                max_growth_pct = mom_change
                fastest_growing = name

            # Size tracker
            if amount_val > max_spent:
                max_spent = amount_val
                largest_cat = name

            if amount_val < min_spent:
                min_spent = amount_val
                least_used_cat = name

        return {
            "items": items,
            "fastest_growing": fastest_growing,
            "largest_category": largest_cat,
            "least_used_category": least_used_cat if least_used_cat != largest_cat else None
        }

    def _calculate_merchants(self, top_merchants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate merchant interactions, frequencies and extreme limits."""
        # Top expenses limits
        largest_tx = self.db.query(func.max(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()

        smallest_tx = self.db.query(func.min(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()

        total_spent = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()

        count = self.db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar() or 0

        # Query all repeat merchants (count >= 2)
        repeat_rows = self.db.query(
            Transaction.merchant
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense',
            Transaction.merchant.isnot(None),
            Transaction.merchant != ""
        ).group_by(Transaction.merchant) \
         .having(func.count(Transaction.id) >= 2).all()

        repeat_list = [r[0] for r in repeat_rows]

        largest_merchant = None
        most_frequent_merchant = None
        max_freq = 0
        max_merchant_spent = 0.0

        items = []
        for m in top_merchants:
            m_name = m["merchant_name"]
            m_amt = m["total_amount"]
            m_count = m["transaction_count"]

            items.append({
                "merchant_name": m_name,
                "total_amount": m_amt,
                "transaction_count": m_count
            })

            if m_amt > max_merchant_spent:
                max_merchant_spent = m_amt
                largest_merchant = m_name

            if m_count > max_freq:
                max_freq = m_count
                most_frequent_merchant = m_name

        avg_val = (float(total_spent) / count) if count > 0 and total_spent is not None else 0.0

        return {
            "items": items,
            "largest_merchant": largest_merchant,
            "most_frequent_merchant": most_frequent_merchant,
            "repeat_merchants": repeat_list,
            "average_transaction_value": avg_val,
            "largest_transaction": float(largest_tx) if largest_tx is not None else 0.0,
            "smallest_transaction": float(smallest_tx) if smallest_tx is not None else 0.0
        }

    def _calculate_cashflow(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determine historical monthly aggregates and overall directions."""
        best_month = None
        max_flow = -9999999.0
        worst_month = None
        min_flow = 9999999.0
        sum_spend = 0.0
        sum_inc = 0.0
        valid_months = 0

        history = []
        for t in trends:
            m = t["month"]
            inc = t["income"]
            exp = t["expense"]
            flow = t["net_cash_flow"]

            history.append({
                "month": m,
                "income": inc,
                "expense": exp,
                "net_cash_flow": flow
            })

            if flow > max_flow:
                max_flow = flow
                best_month = m

            if flow < min_flow:
                min_flow = flow
                worst_month = m

            sum_spend += exp
            sum_inc += inc
            valid_months += 1

        avg_spend = (sum_spend / valid_months) if valid_months > 0 else 0.0
        avg_inc = (sum_inc / valid_months) if valid_months > 0 else 0.0

        # Calculate cash flow trend: Compare last 2 months
        trend_direction = "Stable"
        if len(trends) >= 2:
            last = trends[-1]["expense"]
            prev = trends[-2]["expense"]
            if last > 1.05 * prev:
                trend_direction = "Increasing"
            elif last < 0.95 * prev:
                trend_direction = "Decreasing"

        return {
            "monthly_history": history,
            "best_month": best_month if valid_months > 0 else None,
            "worst_month": worst_month if valid_months > 0 else None,
            "average_monthly_spending": avg_spend,
            "average_monthly_income": avg_inc,
            "current_trend": trend_direction
        }

    def _detect_risks(
        self,
        income: float,
        expense: float,
        savings_rate: float,
        budgets: List[Dict[str, Any]],
        categories: List[Dict[str, Any]],
        expense_growth: float,
        goals: List[Dict[str, Any]],
        spending_trends: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify critical risk markers based on transaction records."""
        risks = []

        # 1. Negative cash flow
        if income < expense:
            risks.append({
                "type": "Negative Cash Flow",
                "severity": "High",
                "description": f"You spent more than you earned this month. Net outflow: ₹{round(expense - income, 2)}"
            })

        # 2. Overspent budgets
        overspent = [b for b in budgets if b["status"] == "Exceeded"]
        if overspent:
            categories_list = ", ".join([b["category_name"] for b in overspent])
            risks.append({
                "type": "Overspent Budgets",
                "severity": "High",
                "description": f"You exceeded spending limits in: {categories_list}."
            })

        # 3. Very low savings rate
        if savings_rate < 10.0 and income > 0:
            risks.append({
                "type": "Low Savings Rate",
                "severity": "Medium",
                "description": f"Your 90-day savings rate is {round(savings_rate, 1)}%. Target minimum is 15%."
            })

        # 4. High spending concentration
        if categories:
            top_cat = categories[0]
            if top_cat["percentage"] > 50.0:
                risks.append({
                    "type": "High Spending Concentration",
                    "severity": "Medium",
                    "description": f"Over 50% of your total expenses are concentrated in '{top_cat['category_name']}'."
                })

        # 5. Rapid expense growth
        if expense_growth > 15.0:
            risks.append({
                "type": "Rapid Expense Growth",
                "severity": "Medium",
                "description": f"Expenses grew by {round(expense_growth, 1)}% MoM. Review major purchases."
            })

        # 6. Inactive goals
        inactive_goals = [g for g in goals if g["status"] == "Behind" and g["remaining_amount"] > 0]
        if inactive_goals:
            risks.append({
                "type": "Inactive or Slow Goals",
                "severity": "Low",
                "description": f"You have {len(inactive_goals)} saving goals currently behind schedule."
            })

        # 7. Large one-time purchases
        avg_tx = spending_trends["average_transaction_amount"]
        if avg_tx > 0:
            largest = self.db.query(func.max(Transaction.amount)).filter(
                Transaction.user_id == self.user_id,
                Transaction.transaction_type == 'expense'
            ).scalar()
            if largest is not None and float(largest) > 3.0 * avg_tx:
                risks.append({
                    "type": "Large Spike Purchase",
                    "severity": "Low",
                    "description": f"A transaction of ₹{float(largest)} was detected. This exceeds 3x your average expense size (₹{round(avg_tx, 2)})."
                })

        return risks

    def _generate_insights_rules(
        self,
        savings_rate: float,
        expense_ratio: float,
        categories: List[Dict[str, Any]],
        income_growth: float,
        expense_growth: float,
        balance: float,
        spending_trends: Dict[str, Any],
        budgets: List[Dict[str, Any]],
        goals: List[Dict[str, Any]],
        trends: List[Dict[str, Any]],
        income: float
    ) -> List[Dict[str, Any]]:
        """Deterministic financial advisor engine containing 20 precise rule matrices."""
        insights = []

        # Rule 1: Savings rate < 0%
        if savings_rate < 0:
            insights.append({
                "rule_id": "SR1_NEG",
                "title": "Negative Savings Deficit",
                "description": "Your spending exceeds your total incoming deposits.",
                "recommendation": "Identify and slash non-essential categories (e.g. Shopping, Dining) immediately."
            })

        # Rule 2: Savings rate < 15%
        if 0 <= savings_rate < 15:
            insights.append({
                "rule_id": "SR1_LOW",
                "title": "Savings Rate Below Target",
                "description": f"Your current savings rate is {round(savings_rate, 1)}%. Target minimum is 15%.",
                "recommendation": "Automate a 10% cash transfer to a savings account on your salary day."
            })

        # Rule 3: Savings rate > 30%
        if savings_rate >= 30:
            insights.append({
                "rule_id": "SR1_EXC",
                "title": "Outstanding Savings Rate",
                "description": f"You are saving a healthy {round(savings_rate, 1)}% of your income.",
                "recommendation": "Invest your surplus cash in mutual funds or equity assets to grow wealth."
            })

        # Rule 4: Critical Expense Ratio
        if expense_ratio > 85:
            insights.append({
                "rule_id": "ER1_HIGH",
                "title": "High Operating Outflows",
                "description": f"Expenses absorb {round(expense_ratio, 1)}% of your earnings.",
                "recommendation": "Avoid credit balances and set absolute weekly limits on dining and shopping."
            })

        # Rule 5: Growth imbalance
        if expense_growth > income_growth:
            insights.append({
                "rule_id": "GI1_IMB",
                "title": "Expense Growth Outpacing Earnings",
                "description": f"Expense growth ({round(expense_growth, 1)}%) exceeds income growth ({round(income_growth, 1)}%).",
                "recommendation": "Re-evaluate non-recurring luxury spending logged recently."
            })

        # Rule 6: Food/Dining Concentration
        dining_cat = next((c for c in categories if "food" in c["category_name"].lower() or "dining" in c["category_name"].lower()), None)
        if dining_cat and dining_cat["percentage"] > 35:
            insights.append({
                "rule_id": "DC1_CONC",
                "title": "High Restaurant Allocation",
                "description": f"Dining and restaurant categories represent {round(dining_cat['percentage'], 1)}% of expenses.",
                "recommendation": "Limit dining out to twice a week and explore grocery cooking alternatives."
            })

        # Rule 7: Low Liquidity Cushion
        avg_spend_30 = spending_trends["average_daily_spend"] * 30
        if balance < 1.5 * avg_spend_30 and avg_spend_30 > 0:
            insights.append({
                "rule_id": "ES1_LOW",
                "title": "Weak Emergency Cushion",
                "description": "Your liquid balances cover less than 1.5 months of typical spending.",
                "recommendation": "Build a liquid savings fund to cover at least 3-6 months of overhead costs."
            })

        # Rule 8: High Merchant Dependency
        if top_merchants := self.analytics.get_top_merchants(limit=1):
            top_m = top_merchants[0]
            total_exp = sum(c["total_amount"] for c in categories)
            if total_exp > 0 and (top_m["total_amount"] / total_exp) > 0.3:
                insights.append({
                    "rule_id": "CC1_DEP",
                    "title": "High Merchant Concentration",
                    "description": f"A single merchant ({top_m['merchant_name']}) accounts for over 30% of expenses.",
                    "recommendation": "Look for competitor discounts or bulk buying alternatives to reduce dependency."
                })

        # Rule 9: Goal Pace
        behind_goals = [g for g in goals if g["status"] == "Behind"]
        if behind_goals:
            insights.append({
                "rule_id": "GM1_PACE",
                "title": "Savings Goals Lagging",
                "description": f"You are behind target completion schedules on {len(behind_goals)} goals.",
                "recommendation": "Increase your goal contribution by ₹1,000 monthly or extend deadline targets."
            })

        # Rule 10: Inactive Goals
        inactive = [g for g in goals if g["estimated_completion"].startswith("Indefinite")]
        if inactive:
            insights.append({
                "rule_id": "GIA1_INACT",
                "title": "Inactive Saving Goals",
                "description": f"Goal '{inactive[0]['name']}' has no active monthly contributions.",
                "recommendation": "Assign a small, auto-recurring contribution to keep the goal active."
            })

        # Rule 11: Budget Overruns
        overspent = [b for b in budgets if b["status"] == "Exceeded"]
        if len(overspent) >= 2:
            insights.append({
                "rule_id": "COV1_SPIKE",
                "title": "Multiple Budget Violations",
                "description": f"You exceeded limits in {len(overspent)} budget categories this month.",
                "recommendation": "Re-allocate remaining funds from positive categories to buffer overruns."
            })

        # Rule 12: Uncategorized leaks
        uncat = next((c for c in categories if "uncategorized" in c["category_name"].lower()), None)
        if uncat and uncat["percentage"] > 15:
            insights.append({
                "rule_id": "UL1_LEAK",
                "title": "High Uncategorized Spending",
                "description": f"Over 15% of your expenses are logged under uncategorized items.",
                "recommendation": "Classify transactions regularly to maintain integrity in auditing statistics."
            })

        # Rule 13: Large expense spike
        max_tx = spending_trends["median_transaction_amount"]
        largest_expense = self.db.query(func.max(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'expense'
        ).scalar()
        if largest_expense is not None and max_tx > 0 and float(largest_expense) > 5.0 * max_tx:
            insights.append({
                "rule_id": "LP1_SPIKE",
                "title": "Abnormal Transaction Size",
                "description": f"Your largest transaction (₹{float(largest_expense)}) is 5x your median transaction value.",
                "recommendation": "Determine if this purchase represents a recurring commitment or simple one-time spike."
            })

        # Rule 14: Deficit Monthly trends
        negative_months = [t for t in trends if t["net_cash_flow"] < 0]
        if len(negative_months) >= 3:
            insights.append({
                "rule_id": "HNO1_DEF",
                "title": "Persistent Monthly Deficits",
                "description": "Your monthly net cash flow was negative multiple times in the last 12 months.",
                "recommendation": "Lower your fixed spending baseline immediately to build cash safety reserves."
            })

        # Rule 15: High Volume transaction counts
        all_time_tx_count = self.db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == self.user_id
        ).scalar() or 0
        if all_time_tx_count > 60:
            insights.append({
                "rule_id": "STV1_VOL",
                "title": "High Spending Volume",
                "description": "You logged a high volume of transactions recently.",
                "recommendation": "Consolidate micro-purchases or combine online delivery orders to optimize courier/bill surcharges."
            })

        # Rule 16: Goal completion
        completed_goals = [g for g in goals if g["status"] == "Completed"]
        if completed_goals:
            insights.append({
                "rule_id": "GC1_COMP",
                "title": "Goal Target Achieved",
                "description": f"Congratulations! You completed savings targets for '{completed_goals[0]['name']}'.",
                "recommendation": "Redirect those contribution flows to your emergency fund or long-term investments."
            })

        # Rule 17: Savings rate improvement
        if len(trends) >= 2:
            cur_sr = ((trends[-1]["income"] - trends[-1]["expense"]) / trends[-1]["income"] * 100) if trends[-1]["income"] > 0 else 0
            prv_sr = ((trends[-2]["income"] - trends[-2]["expense"]) / trends[-2]["income"] * 100) if trends[-2]["income"] > 0 else 0
            if cur_sr > prv_sr + 5:
                insights.append({
                    "rule_id": "SRI1_UP",
                    "title": "Improved Savings Efficiency",
                    "description": "Your current month savings rate is significantly better than the previous month.",
                    "recommendation": "Capture this performance by keeping your discretionary allocations locked."
                })

        # Rule 18: Zero Income recorded
        if income == 0:
            insights.append({
                "rule_id": "INC1_ZERO",
                "title": "No Current Month Income",
                "description": "We did not detect any income transactions for the current calendar period.",
                "recommendation": "Ensure you log external payments, cash receipts or salary earnings to maintain accurate balance tracking."
            })

        # Rule 19: High discretionary spending
        discretionary_total = 0.0
        discretionary_categories = ["shopping", "entertainment", "dining", "travel", "leisure"]
        for c in categories:
            if any(dc in c["category_name"].lower() for dc in discretionary_categories):
                discretionary_total += c["total_amount"]
        total_exp_val = sum(c["total_amount"] for c in categories)
        if total_exp_val > 0 and (discretionary_total / total_exp_val) > 0.4:
            insights.append({
                "rule_id": "HDS1_DISC",
                "title": "High Discretionary Spending",
                "description": f"Discretionary categories represent {round(discretionary_total / total_exp_val * 100, 1)}% of your outflows.",
                "recommendation": "Create strict budget targets for shopping and entertainment to save cash."
            })

        # Rule 20: Liquidity security benchmark
        if balance > 30000:
            insights.append({
                "rule_id": "LS1_BENCH",
                "title": "Strong Cash Liquidity",
                "description": "You maintain a solid buffer of cash reserves.",
                "recommendation": "Allocate any excess surplus into fixed deposit accounts or conservative treasury funds."
            })

        return insights
