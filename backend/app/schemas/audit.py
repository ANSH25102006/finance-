from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class AuditSummary(BaseModel):
    current_balance: float
    total_income: float
    total_expenses: float
    net_cash_flow: float
    savings_rate: float
    expense_ratio: float
    income_growth: float
    expense_growth: float
    financial_health_score: float
    financial_rating: str


class AuditBudget(BaseModel):
    category_name: str
    budget: float
    spent: float
    remaining: float
    remaining_pct: float
    utilization_pct: float
    status: str


class AuditGoal(BaseModel):
    name: str
    target_amount: float
    current_amount: float
    remaining_amount: float
    completion_pct: float
    estimated_completion: str
    status: str


class AuditCategoryMoM(BaseModel):
    category_name: str
    total_amount: float
    percentage: float
    transaction_count: int
    mom_change_pct: Optional[float] = None


class AuditCategorySection(BaseModel):
    items: List[AuditCategoryMoM]
    fastest_growing: Optional[str] = None
    largest_category: Optional[str] = None
    least_used_category: Optional[str] = None


class AuditMerchantItem(BaseModel):
    merchant_name: str
    total_amount: float
    transaction_count: int


class AuditMerchantSection(BaseModel):
    items: List[AuditMerchantItem]
    largest_merchant: Optional[str] = None
    most_frequent_merchant: Optional[str] = None
    repeat_merchants: List[str]
    average_transaction_value: float
    largest_transaction: float
    smallest_transaction: float


class CashFlowHistoryItem(BaseModel):
    month: str = ""
    income: float
    expense: float
    net_cash_flow: float

    # Allow custom keys like expenses if trends map differently
    model_config = ConfigDict(extra="allow")


class AuditCashFlow(BaseModel):
    monthly_history: List[CashFlowHistoryItem]
    best_month: Optional[str] = None
    worst_month: Optional[str] = None
    average_monthly_spending: float
    average_monthly_income: float
    current_trend: str


class AuditRisk(BaseModel):
    type: str
    severity: str
    description: str


class AuditInsight(BaseModel):
    rule_id: str
    title: str
    description: str
    recommendation: str


class AuditMetadata(BaseModel):
    generated_at: datetime
    user_id: UUID
    currency: str
    analysis_period: str
    version: str


class AuditHealth(BaseModel):
    score: float
    rating: str
    explanations: List[str]


class AuditResponse(BaseModel):
    summary: AuditSummary
    health: AuditHealth
    budgets: List[AuditBudget]
    goals: List[AuditGoal]
    categories: AuditCategorySection
    merchants: AuditMerchantSection
    cashflow: AuditCashFlow
    risks: List[AuditRisk]
    insights: List[AuditInsight]
    metadata: AuditMetadata

    model_config = ConfigDict(from_attributes=True)
