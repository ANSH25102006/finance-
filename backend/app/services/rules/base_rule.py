from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.transaction import Transaction

class BaseRule(ABC):
    """
    Base class representing a deterministic financial audit rule.
    """
    def __init__(self):
        pass

    @abstractmethod
    def evaluate(self, transactions: List[Transaction], **kwargs) -> List[Dict[str, Any]]:
        """
        Evaluate the rule against the transaction list.
        Returns a list of dicts conforming to Pydantic FinancialFinding structure.
        """
        pass
