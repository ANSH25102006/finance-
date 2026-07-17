import uuid
from typing import List, Dict, Any
from collections import defaultdict
from app.services.rules.base_rule import BaseRule
from app.models.transaction import Transaction

class MerchantRules(BaseRule):
    """
    Evaluates:
    1. Merchant Concentration: Identifies merchants consuming >= 25% of total expenses.
    """

    def evaluate(self, transactions: List[Transaction], **kwargs) -> List[Dict[str, Any]]:
        findings = []
        if not transactions:
            return findings

        # Filter only expense transactions
        expenses = [tx for tx in transactions if tx.transaction_type == "expense" and tx.merchant]

        if not expenses:
            return findings

        total_expenses = sum(float(t.amount) for t in expenses)
        if total_expenses <= 0:
            return findings

        # Group spending by merchant
        merchant_spend = defaultdict(float)
        merchant_txs = defaultdict(list)
        for t in expenses:
            merchant_spend[t.merchant] += float(t.amount)
            merchant_txs[t.merchant].append(t)

        for merchant, spend in merchant_spend.items():
            percentage = (spend / total_expenses) * 100
            
            # Threshold: >= 25% of total spending and at least 1,000 INR/currency
            if percentage >= 25.0 and spend >= 1000.0:
                findings.append({
                    "id": str(uuid.uuid4()),
                    "rule_type": "merchant_concentration",
                    "severity": "medium",
                    "title": f"High Spending Concentration at {merchant}",
                    "description": f"Spending at '{merchant}' accounts for {percentage:.1f}% of your total expenses ({spend:.2f} out of {total_expenses:.2f}).",
                    "recommendation": f"Review your purchases at '{merchant}' to see if you can cut costs, buy in bulk, or negotiate discounts.",
                    "confidence_score": 100,
                    "affected_transactions": [t.id for t in merchant_txs[merchant]],
                    "metadata": {
                        "merchant": merchant,
                        "merchant_spend": round(spend, 2),
                        "total_spend": round(total_expenses, 2),
                        "percentage": round(percentage, 2)
                    }
                })

        return findings
