# ============================================================
#  models.py — Data models for Savings Simulator
# ============================================================

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class ScenarioType(str, Enum):
    CANCEL_SUBSCRIPTION = "CANCEL_SUBSCRIPTION"
    REDUCE_CATEGORY_SPEND = "REDUCE_CATEGORY_SPEND"
    REDUCE_MERCHANT_SPEND = "REDUCE_MERCHANT_SPEND"
    INCREASE_GOAL_CONTRIBUTION = "INCREASE_GOAL_CONTRIBUTION"
    CUSTOM_SAVINGS = "CUSTOM_SAVINGS"

@dataclass
class SimulationRequest:
    scenario: ScenarioType
    # Scenario parameters e.g., {"subscription_id": "...", "reduction_pct": 20, "merchant_name": "Starbucks"}
    params: dict[str, Any]

@dataclass
class SimulationResult:
    scenario: ScenarioType
    monthly_savings: float
    annual_savings: float
    
    # Impacts on existing predictions (before vs after)
    projected_balance_before: float
    projected_balance_after: float
    
    methodology: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario.value,
            "monthly_savings": self.monthly_savings,
            "annual_savings": self.annual_savings,
            "projected_balance_before": self.projected_balance_before,
            "projected_balance_after": self.projected_balance_after,
            "methodology": self.methodology,
            "metadata": self.metadata,
        }
