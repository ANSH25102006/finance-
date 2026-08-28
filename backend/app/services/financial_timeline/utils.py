# ============================================================
#  utils.py — Helper functions for the timeline engine
# ============================================================

from collections import defaultdict
from typing import Any
from datetime import datetime, time

def group_insights_by_type(insights: list[Any]) -> dict[str, list[Any]]:
    """Group financial insights by their type."""
    result = defaultdict(list)
    for insight in insights:
        result[insight.type.value].append(insight)
    return dict(result)

def index_transactions_by_id(transactions: list[Any]) -> dict[str, Any]:
    """Create a fast lookup dictionary for transactions by ID."""
    return {str(tx.id): tx for tx in transactions}

def to_datetime(d: Any) -> datetime:
    """Convert date to datetime at midnight."""
    import datetime as dt
    if isinstance(d, dt.datetime):
        return d
    return dt.datetime.combine(d, time.min)
