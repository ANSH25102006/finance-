# ============================================================
#  models.py — Core data model for financial insights
# ============================================================

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.financial_intelligence.enums import InsightSeverity, InsightType


@dataclass
class FinancialInsight:
    """
    A single structured financial insight produced by a detector.

    Every detector must return instances of this model so the engine
    can aggregate, deduplicate, and sort them uniformly.
    """

    type: InsightType
    severity: InsightSeverity
    title: str
    summary: str
    recommendation: str

    # Optional fields with sensible defaults
    score: float = 0.0                   # Detector-specific numeric signal (0–100)
    category: str | None = None          # Category name the insight relates to, if any
    metadata: dict[str, Any] = field(default_factory=dict)

    # Auto-generated
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ------------------------------------------------------------------ #
    # Serialisation helpers
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "summary": self.summary,
            "recommendation": self.recommendation,
            "score": self.score,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    # ------------------------------------------------------------------ #
    # Deduplication key — used by the engine to remove duplicates
    # ------------------------------------------------------------------ #

    @property
    def dedup_key(self) -> tuple[str, str | None]:
        """Insights with the same (type, category) are considered duplicates."""
        return (self.type.value, self.category)
