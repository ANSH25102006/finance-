from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

class SavingsRecommendation(BaseModel):
    title: str = Field(..., description="Actionable recommendation title")
    description: str = Field(..., description="Actionable recommendation details")
    action_steps: List[str] = Field(..., description="Bullet points outlining exact steps to take")


class SavingsOpportunity(BaseModel):
    id: str = Field(..., description="Unique opportunity identifier (UUID)")
    opportunity_type: str = Field(..., description="Type of savings opportunity (e.g. 'subscriptions', 'duplicates', 'weekend_spend', 'budget_overruns', 'merchant_concentration')")
    title: str = Field(..., description="Human-readable title describing the savings opportunity")
    description: str = Field(..., description="Detailed description of the leakage and potential resolution")
    potential_monthly_savings: float = Field(..., description="Estimated potential monthly savings")
    potential_yearly_savings: float = Field(..., description="Estimated potential annual savings")
    confidence_score: int = Field(..., description="Confidence rating of the calculation (0-100)")
    affected_transactions: List[Any] = Field(..., description="List of UUIDs representing affected transaction records")
    recommendation: SavingsRecommendation = Field(..., description="Specific recommendation detailing action steps")
    metadata: Dict[str, Any] = Field(..., description="Contextual parameters about calculations")


class SavingsSummary(BaseModel):
    monthly_savings: float = Field(..., description="Sum of all monthly potential savings")
    yearly_savings: float = Field(..., description="Sum of all yearly potential savings")
    confidence: int = Field(..., description="Weighted average confidence score across all opportunities (0-100)")
    opportunities: List[SavingsOpportunity] = Field(..., description="List of specific identified savings opportunities")

    model_config = ConfigDict(from_attributes=True)
