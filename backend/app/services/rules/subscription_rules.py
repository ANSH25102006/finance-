import uuid
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from app.services.rules.base_rule import BaseRule
from app.models.transaction import Transaction

class SubscriptionRules(BaseRule):
    """
    Evaluates transactions for:
    1. Forgotten subscriptions (monthly recurring charges for >= 3 cycles).
    2. Subscription price increases.
    """

    def evaluate(self, transactions: List[Transaction], **kwargs) -> List[Dict[str, Any]]:
        findings = []

        # Filter only expense transactions
        expenses = [tx for tx in transactions if tx.transaction_type == "expense" and tx.merchant]

        # Group by merchant name (case-insensitive)
        merchant_groups = defaultdict(list)
        for tx in expenses:
            merchant_groups[tx.merchant.strip().lower()].append(tx)

        # Process each merchant group
        for merchant_key, txs in merchant_groups.items():
            if len(txs) < 3:
                continue

            # Sort by transaction date ascending
            sorted_txs = sorted(txs, key=lambda t: t.transaction_date)

            # Find recurring runs where dates are spaced roughly monthly (~25 to ~35 days)
            # and amounts are within 30% of the average of the run
            runs = self._find_monthly_runs(sorted_txs)

            for run in runs:
                # 1. Forgotten Subscription Finding
                first_tx = run[0]
                last_tx = run[-1]
                avg_amount = sum(float(t.amount) for t in run) / len(run)
                yearly_cost = avg_amount * 12

                finding_id = str(uuid.uuid4())
                findings.append({
                    "id": finding_id,
                    "rule_type": "forgotten_subscription",
                    "severity": "medium",
                    "title": "Forgotten Subscription Detected",
                    "description": f"We detected a recurring monthly charge for '{first_tx.merchant}' of approximately {avg_amount:.2f}.",
                    "recommendation": f"Review if you still use this subscription. Cancelling it could save you {yearly_cost:.2f} annually.",
                    "confidence_score": 95,
                    "affected_transactions": [t.id for t in run],
                    "metadata": {
                        "merchant": first_tx.merchant,
                        "monthly_amount": round(avg_amount, 2),
                        "yearly_cost": round(yearly_cost, 2),
                        "first_payment": str(first_tx.transaction_date),
                        "last_payment": str(last_tx.transaction_date)
                    }
                })

                # 2. Subscription Price Increase Finding
                old_price = float(first_tx.amount)
                new_price = float(last_tx.amount)
                if new_price > old_price:
                    increase_amount = new_price - old_price
                    increase_pct = (increase_amount / old_price) * 100

                    findings.append({
                        "id": str(uuid.uuid4()),
                        "rule_type": "subscription_price_increase",
                        "severity": "medium",
                        "title": f"Subscription Price Increase for {first_tx.merchant}",
                        "description": f"Your subscription for '{first_tx.merchant}' has increased from {old_price:.2f} to {new_price:.2f}.",
                        "recommendation": f"Verify if the price increase of {increase_amount:.2f} ({increase_pct:.1f}%) is justified, or consider alternative plans.",
                        "confidence_score": 100,
                        "affected_transactions": [t.id for t in run],
                        "metadata": {
                            "merchant": first_tx.merchant,
                            "old_price": round(old_price, 2),
                            "new_price": round(new_price, 2),
                            "increase_amount": round(increase_amount, 2),
                            "increase_percentage": round(increase_pct, 2)
                        }
                    })

        return findings

    def _find_monthly_runs(self, sorted_txs: List[Transaction]) -> List[List[Transaction]]:
        runs = []
        n = len(sorted_txs)
        used = [False] * n

        for i in range(n):
            if used[i]:
                continue

            current_run = [sorted_txs[i]]
            last_idx = i

            for j in range(i + 1, n):
                if used[j]:
                    continue

                diff = (sorted_txs[j].transaction_date - sorted_txs[last_idx].transaction_date).days
                if 25 <= diff <= 35:
                    current_run.append(sorted_txs[j])
                    last_idx = j

            if len(current_run) >= 3:
                # Verify that amounts in the run are relatively stable (within 30% of mean)
                mean_amt = sum(float(t.amount) for t in current_run) / len(current_run)
                if all(abs(float(t.amount) - mean_amt) / mean_amt <= 0.30 for t in current_run):
                    runs.append(current_run)
                    # Mark all items in this run as used so they aren't duplicate-counted
                    for t in current_run:
                        idx = sorted_txs.index(t)
                        used[idx] = True

        return runs
