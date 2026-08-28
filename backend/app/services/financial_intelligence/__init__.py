# ============================================================
#  financial_intelligence/__init__.py
#  Package public API
# ============================================================

from app.services.financial_intelligence.engine import FinancialIntelligenceEngine
from app.services.financial_intelligence.models import FinancialInsight
from app.services.financial_intelligence.enums import InsightSeverity, InsightType
from app.services.financial_intelligence.detector_base import BaseDetector, DetectionContext
from app.services.financial_intelligence.detector_registry import registry

__all__ = [
    "FinancialIntelligenceEngine",
    "FinancialInsight",
    "InsightSeverity",
    "InsightType",
    "BaseDetector",
    "DetectionContext",
    "registry",
]
