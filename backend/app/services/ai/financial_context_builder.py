import calendar
import logging
from collections import defaultdict
from datetime import date
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.services.audit_service import AuditService

from app.schemas.financial_context import (
    FinancialContext,
    ProfileContext,
    IncomeContext,
    ExpenseContext,
    CategoryContext,
    CategoryComparison,
    BudgetUtilization,
    MerchantContext,
    SubscriptionContext,
    SubscriptionItem,
    SubscriptionPriceIncreaseItem,
    HealthContext,
    SavingsOpportunityContext
)

from app.services.ai.spending_pattern_service import SpendingPatternService
from app.services.ai.subscription_service import SubscriptionService
from app.services.ai.recommendation_service import RecommendationService
from app.services.ai.report_service import ReportService

logger = logging.getLogger("financial_context_builder")


class FinancialContextBuilder:
    """
    FinancialContextBuilder performs a single optimized database scan for a user
    to collect accounts, transactions, categories, and budgets. It processes
    these records in-memory and executes the rules engine to assemble a
    reusable, strongly-typed, and serializable FinancialContext object.
    """

    def build_context(self, db: Session, user_id: UUID) -> FinancialContext:
        logger.info(f"Building financial context for user: {user_id}")

        # 1. Bulk DB Queries to prevent N+1 queries
        accounts = db.query(Account).filter(Account.user_id == user_id).all()
        categories = db.query(Category).filter(
            or_(Category.user_id == user_id, Category.user_id.is_(None))
        ).all()
        budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
        transactions = db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.transaction_date).all()

        categories_map = {cat.id: cat.name for cat in categories}

        # 2. Run Audit rules using AuditService
        audit_service = AuditService(db, user_id)
        rules_res = audit_service.run_rules_audit()
        findings = rules_res.get("findings", [])

        # 3. Base date determinations
        if transactions:
            latest_tx_date = max(t.transaction_date for t in transactions)
        else:
            latest_tx_date = date.today()

        curr_month = latest_tx_date.month
        curr_year = latest_tx_date.year

        prev_month = curr_month - 1 if curr_month > 1 else 12
        prev_year = curr_year if curr_month > 1 else curr_year - 1

        current_month_str = latest_tx_date.strftime("%B %Y")
        previous_month_str = date(prev_year, prev_month, 1).strftime("%B %Y")

        currency = accounts[0].currency if accounts else "INR"

        # 4. Profile Context
        profile = ProfileContext(
            current_month=current_month_str,
            previous_month=previous_month_str,
            currency=currency,
            account_count=len(accounts),
            transaction_count=len(transactions)
        )

        # 5. Income Context
        income_txs = [t for t in transactions if t.transaction_type == "income"]
        total_income = sum(float(t.amount) for t in income_txs)
        curr_income_txs = [t for t in income_txs if t.transaction_date.month == curr_month and t.transaction_date.year == curr_year]
        monthly_income = sum(float(t.amount) for t in curr_income_txs)
        
        # Gather recurring income from rules engine findings
        recurring_income = sum(
            float(f["metadata"]["monthly_amount"])
            for f in findings
            if f["rule_type"] == "income_detection"
        )
        average_income = total_income / len(income_txs) if income_txs else 0.0

        income = IncomeContext(
            total_income=round(total_income, 2),
            monthly_income=round(monthly_income, 2),
            recurring_income=round(recurring_income, 2),
            average_income=round(average_income, 2)
        )

        # 6. Expenses Context
        expense_txs = [t for t in transactions if t.transaction_type == "expense"]
        total_expenses = sum(float(t.amount) for t in expense_txs)
        
        curr_expense_txs = [t for t in expense_txs if t.transaction_date.month == curr_month and t.transaction_date.year == curr_year]
        monthly_expenses = sum(float(t.amount) for t in curr_expense_txs)

        prev_expense_txs = [t for t in expense_txs if t.transaction_date.month == prev_month and t.transaction_date.year == prev_year]
        previous_month_expenses = sum(float(t.amount) for t in prev_expense_txs)

        pct_change = 0.0
        if previous_month_expenses > 0:
            pct_change = ((monthly_expenses - previous_month_expenses) / previous_month_expenses) * 100

        # Daily / Weekly averages in current month
        days_in_month = calendar.monthrange(curr_year, curr_month)[1]
        daily_average = monthly_expenses / days_in_month
        weekly_average = daily_average * 7

        largest_tx = max(float(t.amount) for t in expense_txs) if expense_txs else 0.0
        smallest_tx = min(float(t.amount) for t in expense_txs) if expense_txs else 0.0
        median_tx = self._get_median([float(t.amount) for t in expense_txs])
        avg_expense = total_expenses / len(expense_txs) if expense_txs else 0.0

        expenses_ctx = ExpenseContext(
            total_expenses=round(total_expenses, 2),
            monthly_expenses=round(monthly_expenses, 2),
            previous_month_expenses=round(previous_month_expenses, 2),
            percentage_change=round(pct_change, 2),
            daily_average=round(daily_average, 2),
            weekly_average=round(weekly_average, 2),
            largest_transaction=round(largest_tx, 2),
            smallest_transaction=round(smallest_tx, 2),
            median_transaction=round(median_tx, 2),
            average_transaction=round(avg_expense, 2)
        )

        # 7. Categories Context
        cat_totals = defaultdict(float)
        for t in expense_txs:
            cat_name = categories_map.get(t.category_id, "Unknown")
            cat_totals[cat_name] += float(t.amount)

        top_categories = sorted(
            [{"category": name, "amount": round(val, 2)} for name, val in cat_totals.items()],
            key=lambda x: x["amount"],
            reverse=True
        )

        category_percentages = {}
        for name, val in cat_totals.items():
            category_percentages[name] = round((val / total_expenses * 100), 2) if total_expenses > 0 else 0.0

        # Monthly category comparisons
        curr_cat_spend = defaultdict(float)
        for t in curr_expense_txs:
            cat_name = categories_map.get(t.category_id, "Unknown")
            curr_cat_spend[cat_name] += float(t.amount)

        prev_cat_spend = defaultdict(float)
        for t in prev_expense_txs:
            cat_name = categories_map.get(t.category_id, "Unknown")
            prev_cat_spend[cat_name] += float(t.amount)

        monthly_cat_comparison = []
        all_cats = set(curr_cat_spend.keys()).union(prev_cat_spend.keys())
        for cat_name in all_cats:
            if cat_name == "Unknown":
                continue
            cur_s = curr_cat_spend[cat_name]
            prev_s = prev_cat_spend[cat_name]
            chg = ((cur_s - prev_s) / prev_s * 100) if prev_s > 0 else 0.0
            monthly_cat_comparison.append(CategoryComparison(
                category_name=cat_name,
                current_month_spend=round(cur_s, 2),
                previous_month_spend=round(prev_s, 2),
                change_pct=round(chg, 2)
            ))

        # Budgets utilization in current month
        budget_utilization = []
        curr_budgets = [b for b in budgets if b.month == curr_month and b.year == curr_year]
        remaining_budget = 0.0
        exceeded_budgets = []
        budget_overrun_total = 0.0

        for b in curr_budgets:
            cat_name = categories_map.get(b.category_id, "Unknown")
            spent = curr_cat_spend.get(cat_name, 0.0)
            util_pct = (spent / b.amount * 100) if b.amount > 0 else 0.0
            rem = b.amount - spent
            if rem > 0:
                remaining_budget += rem
            
            exceeded = spent > b.amount
            if exceeded:
                exceeded_budgets.append(cat_name)
                budget_overrun_total += (spent - b.amount)

            budget_utilization.append(BudgetUtilization(
                category_name=cat_name,
                budget_amount=round(b.amount, 2),
                spent_amount=round(spent, 2),
                utilization_pct=round(util_pct, 2),
                remaining_amount=round(max(0.0, rem), 2),
                is_exceeded=exceeded
            ))

        categories_ctx = CategoryContext(
            top_categories=top_categories,
            category_percentages=category_percentages,
            monthly_category_comparison=monthly_cat_comparison,
            budget_utilization=budget_utilization,
            remaining_budget=round(remaining_budget, 2),
            exceeded_budgets=exceeded_budgets
        )

        # 8. Merchants Context
        merchant_spend = defaultdict(float)
        merchant_counts = defaultdict(int)
        merchant_first_dates = {}

        for t in expense_txs:
            if not t.merchant:
                continue
            merchant_spend[t.merchant] += float(t.amount)
            merchant_counts[t.merchant] += 1
            if t.merchant not in merchant_first_dates or t.transaction_date < merchant_first_dates[t.merchant]:
                merchant_first_dates[t.merchant] = t.transaction_date

        top_merchants = sorted(
            [{"merchant": name, "amount": round(val, 2)} for name, val in merchant_spend.items()],
            key=lambda x: x["amount"],
            reverse=True
        )

        merchant_concentration = {}
        for name, val in merchant_spend.items():
            merchant_concentration[name] = round((val / total_expenses * 100), 2) if total_expenses > 0 else 0.0

        frequent_merchants = sorted(
            [{"merchant": name, "count": count} for name, count in merchant_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )

        new_merchants = []
        for name, fd in merchant_first_dates.items():
            if fd.month == curr_month and fd.year == curr_year:
                new_merchants.append(name)

        repeat_merchants = [name for name, count in merchant_counts.items() if count >= 2]

        merchants_ctx = MerchantContext(
            top_merchants=top_merchants,
            merchant_concentration=merchant_concentration,
            frequent_merchants=frequent_merchants,
            new_merchants=new_merchants,
            repeat_merchants=repeat_merchants
        )

        # 9. Subscriptions Context
        active_subscriptions = []
        price_increases = []

        for f in findings:
            if f["rule_type"] == "forgotten_subscription":
                meta = f["metadata"]
                active_subscriptions.append(SubscriptionItem(
                    merchant=meta["merchant"],
                    monthly_amount=float(meta["monthly_amount"]),
                    yearly_cost=float(meta["yearly_cost"]),
                    first_payment=meta["first_payment"],
                    last_payment=meta["last_payment"]
                ))
            elif f["rule_type"] == "subscription_price_increase":
                meta = f["metadata"]
                price_increases.append(SubscriptionPriceIncreaseItem(
                    merchant=meta["merchant"],
                    old_price=float(meta["old_price"]),
                    new_price=float(meta["new_price"]),
                    increase_amount=float(meta["increase_amount"]),
                    increase_percentage=float(meta["increase_percentage"])
                ))

        monthly_sub_cost = sum(item.monthly_amount for item in active_subscriptions)
        annual_sub_cost = monthly_sub_cost * 12

        subscriptions = SubscriptionContext(
            active_subscriptions=active_subscriptions,
            monthly_subscription_cost=round(monthly_sub_cost, 2),
            annual_subscription_cost=round(annual_sub_cost, 2),
            price_increases=price_increases
        )

        # 10. Health Context
        savings_rate = ((monthly_income - monthly_expenses) / monthly_income * 100) if monthly_income > 0 else 0.0
        expense_ratio = (monthly_expenses / monthly_income) if monthly_income > 0 else 0.0

        total_balance = sum(float(a.balance) for a in accounts)
        liquidity_ratio = (total_balance / monthly_expenses) if monthly_expenses > 0 else 0.0
        emergency_fund_months = liquidity_ratio

        recurring_pct = (monthly_sub_cost / monthly_expenses * 100) if monthly_expenses > 0 else 0.0

        health = HealthContext(
            savings_rate=round(savings_rate, 2),
            expense_ratio=round(expense_ratio, 2),
            liquidity_ratio=round(liquidity_ratio, 2),
            emergency_fund_months=round(emergency_fund_months, 2),
            recurring_percentage=round(recurring_pct, 2)
        )

        # 11. Savings Opportunity Context
        potential_savings_subs = annual_sub_cost
        
        # Weekend spend reduction potential
        weekend_savings = 0.0
        for f in findings:
            if f["rule_type"] == "weekend_spending":
                # Save by reducing average daily weekend spend to weekday level
                meta = f["metadata"]
                # 8 weekend days in a typical month
                excess_per_weekend_day = max(0.0, float(meta["avg_weekend"]) - float(meta["avg_weekday"]))
                weekend_savings = excess_per_weekend_day * 8.0

        # Duplicate charges total
        duplicate_total = sum(
            float(f["metadata"]["amount"])
            for f in findings
            if f["rule_type"] == "duplicate_charge"
        )

        savings = SavingsOpportunityContext(
            potential_savings_subscriptions=round(potential_savings_subs, 2),
            weekend_spend_reduction=round(weekend_savings, 2),
            duplicate_charges_total=round(duplicate_total, 2),
            budget_overrun_total=round(budget_overrun_total, 2)
        )

        # Convert findings to FinancialFinding schemas
        from app.schemas.audit import FinancialFinding
        rules_findings_schemas = [
            FinancialFinding(**f) for f in findings
        ]

        # Invoke pattern, subscription, and recommendation services
        pattern_service = SpendingPatternService()
        patterns_data = pattern_service.analyze_patterns(transactions, categories)

        sub_service = SubscriptionService()
        subs_data = sub_service.detect_subscriptions(transactions)

        rec_service = RecommendationService()
        recs_list = rec_service.generate_recommendations(patterns_data, subs_data, budget_utilization)

        # Build context object (excluding the report initially)
        context = FinancialContext(
            profile=profile,
            income=income,
            expenses=expenses_ctx,
            categories=categories_ctx,
            merchants=merchants_ctx,
            subscriptions=subscriptions,
            rules_engine=rules_findings_schemas,
            health=health,
            savings=savings,
            patterns=patterns_data,
            recommendations_list=recs_list,
            report=None
        )

        # Compile Monthly Financial Report using the constructed context
        report_service = ReportService()
        report_data = report_service.generate_monthly_report(db, user_id, context, patterns_data, subs_data)
        context.report = report_data

        return context

    def _get_median(self, data: List[float]) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        n = len(sorted_data)
        if n % 2 == 1:
            return sorted_data[n // 2]
        return (sorted_data[(n // 2) - 1] + sorted_data[n // 2]) / 2.0
