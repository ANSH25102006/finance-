import uuid
from typing import List, Dict, Any
from collections import defaultdict
from app.services.rules.base_rule import BaseRule
from app.models.transaction import Transaction

class DuplicateRules(BaseRule):
    """
    Evaluates transactions for duplicate charges:
    - Same merchant, same amount, same day (High severity)
    - Same merchant, same amount, within 1 day (Medium severity)
    """

    def evaluate(self, transactions: List[Transaction], **kwargs) -> List[Dict[str, Any]]:
        findings = []
        
        # Only evaluate expense transactions with a merchant
        expenses = [tx for tx in transactions if tx.transaction_type == "expense" and tx.merchant]

        # Group by merchant name (case-insensitive)
        merchant_groups = defaultdict(list)
        for tx in expenses:
            merchant_groups[tx.merchant.strip().lower()].append(tx)

        # Trace and compare within each group
        for merchant_key, txs in merchant_groups.items():
            if len(txs) < 2:
                continue

            sorted_txs = sorted(txs, key=lambda t: t.transaction_date)
            n = len(sorted_txs)
            matched = set()

            for i in range(n):
                if sorted_txs[i].id in matched:
                    continue

                for j in range(i + 1, n):
                    if sorted_txs[j].id in matched:
                        continue

                    t1 = sorted_txs[i]
                    t2 = sorted_txs[j]

                    # Check same amount
                    if float(t1.amount) == float(t2.amount):
                        days_diff = abs((t1.transaction_date - t2.transaction_date).days)
                        if days_diff <= 1:
                            matched.add(t1.id)
                            matched.add(t2.id)
                            
                            severity = "high" if days_diff == 0 else "medium"
                            confidence = 95 if days_diff == 0 else 85
                            title = "Possible Duplicate Charge" if days_diff == 0 else "Potential Close-Interval Duplicate Charge"

                            findings.append({
                                "id": str(uuid.uuid4()),
                                "rule_type": "duplicate_charge",
                                "severity": severity,
                                "title": title,
                                "description": f"We detected two charges of {float(t1.amount):.2f} for '{t1.merchant}' on {t1.transaction_date} and {t2.transaction_date}.",
                                "recommendation": "Check if you were double-billed and contact the merchant for a refund if necessary.",
                                "confidence_score": confidence,
                                "affected_transactions": [t1.id, t2.id],
                                "metadata": {
                                    "merchant": t1.merchant,
                                    "amount": float(t1.amount),
                                    "date1": str(t1.transaction_date),
                                    "date2": str(t2.transaction_date),
                                    "days_interval": days_diff
                                }
                            })
                            break # Move to next outer transaction once matched

        return findings
