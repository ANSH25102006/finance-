from pydantic import BaseModel, Field
from typing import List, Dict, Any

class AIChatRequest(BaseModel):
    message: str = Field(..., description="User message or financial query.")


class AIRecommendation(BaseModel):
    problem: str = Field(..., description="Description of the financial problem identified.")
    impact: str = Field(..., description="Estimated impact or severity of the problem.")
    evidence: str = Field(..., description="Calculated support data proving the problem.")
    suggested_action: str = Field(..., description="Proposed corrective actions.")
    expected_savings: float = Field(..., description="Calculated annual savings if action is taken.")
    confidence: str = Field(..., description="Confidence level: High, Medium, Low.")
    priority: str = Field(..., description="Priority scale: High, Medium, Low.")


class AIChatResponse(BaseModel):
    answer: str = Field(..., description="The AI Financial Auditor's written response.")
    health_score: int = Field(..., description="The user's current health score (0-100).")
    grade: str = Field(..., description="The user's current health grade (A, B, C, D, F).")
    monthly_savings: float = Field(..., description="Estimated potential monthly savings.")
    yearly_savings: float = Field(..., description="Estimated potential annual savings.")
    recommendations: List[AIRecommendation] = Field(default_factory=list, description="Actionable financial improvements.")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed backend facts supporting findings.")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions contextually relevant to the user query.")
    sources: List[str] = Field(..., description="Deterministic backend components utilized to build context.")
    provider: str = Field(..., description="The LLM provider selected.")
    model: str = Field(..., description="The specific LLM model utilized.")
    generated_at: str = Field(..., description="ISO 8601 formatted generation timestamp.")
    conversation_id: str = Field(..., description="Unique conversation identifier.")
