from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.schemas.audit import FinancialFinding

class ProfileContext(BaseModel):
    current_month: str = Field(..., description="Name of the current baseline month (e.g. 'July 2026')")
    previous_month: str = Field(..., description="Name of the previous baseline month (e.g. 'June 2026')")
    currency: str = Field(..., description="Standard currency code (e.g. 'INR')")
    account_count: int = Field(..., description="Total number of accounts owned by the user")
    transaction_count: int = Field(..., description="Total transaction count in user's history")


class IncomeContext(BaseModel):
    total_income: float = Field(..., description="All-time total income received")
    monthly_income: float = Field(..., description="Total income received in the current month")
    recurring_income: float = Field(..., description="Identified recurring monthly salary income")
    average_income: float = Field(..., description="Average amount of income transactions")


class ExpenseContext(BaseModel):
    total_expenses: float = Field(..., description="All-time total expenses recorded")
    monthly_expenses: float = Field(..., description="Total expenses recorded in the current month")
    previous_month_expenses: float = Field(..., description="Total expenses in the previous baseline month")
    percentage_change: float = Field(..., description="MoM percentage change of expenses")
    daily_average: float = Field(..., description="Average daily spending in the current month")
    weekly_average: float = Field(..., description="Average weekly spending in the current month")
    largest_transaction: float = Field(..., description="Largest expense amount recorded")
    smallest_transaction: float = Field(..., description="Smallest expense amount recorded")
    median_transaction: float = Field(..., description="Median expense amount")
    average_transaction: float = Field(..., description="Average expense amount")


class CategoryComparison(BaseModel):
    category_name: str
    current_month_spend: float
    previous_month_spend: float
    change_pct: Optional[float] = None


class BudgetUtilization(BaseModel):
    category_name: str
    budget_amount: float
    spent_amount: float
    utilization_pct: float
    remaining_amount: float
    is_exceeded: bool


class CategoryContext(BaseModel):
    top_categories: List[Dict[str, Any]] = Field(..., description="Top spending categories sorted by amount desc")
    category_percentages: Dict[str, float] = Field(..., description="Percentage share of each category in total spending")
    monthly_category_comparison: List[CategoryComparison] = Field(..., description="MoM comparison of category spending")
    budget_utilization: List[BudgetUtilization] = Field(..., description="Budget utilization statistics for current month")
    remaining_budget: float = Field(..., description="Sum of remaining budget across all budgeted categories")
    exceeded_budgets: List[str] = Field(..., description="List of category names that exceeded their budgets")


class MerchantContext(BaseModel):
    top_merchants: List[Dict[str, Any]] = Field(..., description="Top merchants sorted by total spending amount desc")
    merchant_concentration: Dict[str, float] = Field(..., description="Percentage share of top merchants in total spending")
    frequent_merchants: List[Dict[str, Any]] = Field(..., description="Top merchants sorted by transaction frequency desc")
    new_merchants: List[str] = Field(..., description="Merchants appearing for the first time in the current month")
    repeat_merchants: List[str] = Field(..., description="Merchants with >= 2 transactions all-time")


class SubscriptionItem(BaseModel):
    merchant: str
    monthly_amount: float
    yearly_cost: float
    first_payment: str
    last_payment: str


class SubscriptionPriceIncreaseItem(BaseModel):
    merchant: str
    old_price: float
    new_price: float
    increase_amount: float
    increase_percentage: float


class SubscriptionContext(BaseModel):
    active_subscriptions: List[SubscriptionItem] = Field(..., description="List of recognized monthly subscriptions")
    monthly_subscription_cost: float = Field(..., description="Sum of monthly cost of active subscriptions")
    annual_subscription_cost: float = Field(..., description="Sum of annual cost of active subscriptions")
    price_increases: List[SubscriptionPriceIncreaseItem] = Field(..., description="List of pricing increases in subscriptions")


class HealthContext(BaseModel):
    savings_rate: float = Field(..., description="Savings rate percentage in current month")
    expense_ratio: float = Field(..., description="Expense-to-income ratio in current month")
    liquidity_ratio: float = Field(..., description="Ratio of total balance to current monthly expense")
    emergency_fund_months: float = Field(..., description="Months of expenses covered by current cash balance")
    recurring_percentage: float = Field(..., description="Percentage share of subscriptions in monthly expenses")


class SavingsOpportunityContext(BaseModel):
    potential_savings_subscriptions: float = Field(..., description="Potential yearly savings from forgotten subscriptions")
    weekend_spend_reduction: float = Field(..., description="Potential monthly savings by reducing weekend daily average spend to weekday level")
    duplicate_charges_total: float = Field(..., description="Sum of duplicate charge amounts")
    budget_overrun_total: float = Field(..., description="Sum of budget overruns across all exceeded categories")


class FinancialContext(BaseModel):
    profile: ProfileContext
    income: IncomeContext
    expenses: ExpenseContext
    categories: CategoryContext
    merchants: MerchantContext
    subscriptions: SubscriptionContext
    rules_engine: List[FinancialFinding]
    health: HealthContext
    savings: SavingsOpportunityContext
    patterns: Optional[Dict[str, Any]] = None
    recommendations_list: List[Dict[str, Any]] = Field(default_factory=list)
    report: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
