from pydantic import BaseModel, Field, ConfigDict
from typing import List

class ScoreFactor(BaseModel):
    name: str = Field(..., description="Short name of the scoring factor")
    category: str = Field(..., description="Category of factor (e.g. 'Budgeting', 'Savings', 'Spending')")
    impact: int = Field(..., description="Score change (+ for bonuses, - for deductions)")
    reason: str = Field(..., description="Contextual explanation for the change")
    severity: str = Field(..., description="Severity level of the factor ('low', 'medium', 'high')")


class HealthSummary(BaseModel):
    score: int = Field(..., description="Calculated financial health score (0-100)")
    grade: str = Field(..., description="Calculated rating grade (A, B, C, D, F)")
    summary: str = Field(..., description="Deterministic financial summary statement")
    risk_level: str = Field(..., description="Assessed risk level ('Low', 'Medium', 'High', 'Critical')")
    score_color: str = Field(..., description="Visual rating color code ('green', 'yellow', 'orange', 'red')")


class HealthScore(BaseModel):
    score: int = Field(..., description="Calculated financial health score (0-100)")
    grade: str = Field(..., description="Calculated rating grade (A, B, C, D, F)")
    summary: str = Field(..., description="Deterministic financial summary statement")
    positive_factors: List[ScoreFactor] = Field(..., description="List of positive bonuses applied")
    negative_factors: List[ScoreFactor] = Field(..., description="List of negative deductions applied")
    recommendations: List[str] = Field(..., description="List of actionable recommendations based on deductions")
    score_color: str = Field(..., description="Visual rating color code ('green', 'yellow', 'orange', 'red')")
    progress_percentage: int = Field(..., description="Visual progress bar percentage (matches score)")
    risk_level: str = Field(..., description="Assessed risk level ('Low', 'Medium', 'High', 'Critical')")

    model_config = ConfigDict(from_attributes=True)
