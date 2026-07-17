import uuid
from typing import List, Dict, Any
from datetime import date
from collections import defaultdict
from app.services.rules.base_rule import BaseRule
from app.models.transaction import Transaction
from app.services.rules.statistics import calculate_iqr_threshold, calculate_std_dev_threshold

class SpendingRules(BaseRule):
    """
    Evaluates:
    1. Spending Spikes (MoM category/merchant increases >= 50% and >= 500).
    2. Large Transaction Alerts (using IQR or SD outlier analysis).
    3. Weekend Spending concentration (weekend average daily spend >= 1.5x weekdays).
    """

    def evaluate(self, transactions: List[Transaction], **kwargs) -> List[Dict[str, Any]]:
        findings = []
        if not transactions:
            return findings

        # Cache categories mapping for Spike and Concentration rules
        categories_map = kwargs.get("categories_map", {})

        # Filter only expense transactions
        expenses = [tx for tx in transactions if tx.transaction_type == "expense"]

        if not expenses:
            return findings

        # Run Sub-Rules
        findings.extend(self._evaluate_spending_spike(expenses, categories_map))
        findings.extend(self._evaluate_large_transactions(expenses))
        findings.extend(self._evaluate_weekend_spending(expenses))

        return findings

    def _evaluate_spending_spike(self, expenses: List[Transaction], categories_map: Dict[Any, str]) -> List[Dict[str, Any]]:
        findings = []
        
        # 1. Determine baseline date range (latest transaction month/year as current)
        latest_tx_date = max(t.transaction_date for t in expenses)
        curr_month = latest_tx_date.month
        curr_year = latest_tx_date.year

        # Previous month
        prev_month = curr_month - 1 if curr_month > 1 else 12
        prev_year = curr_year if curr_month > 1 else curr_year - 1

        # Isolate transactions
        curr_txs = [t for t in expenses if t.transaction_date.month == curr_month and t.transaction_date.year == curr_year]
        prev_txs = [t for t in expenses if t.transaction_date.month == prev_month and t.transaction_date.year == prev_year]

        if not curr_txs:
            return findings

        # --- Category Spike Check ---
        curr_cat_spend = defaultdict(float)
        curr_cat_txs = defaultdict(list)
        for t in curr_txs:
            cat_name = categories_map.get(t.category_id, "Unknown")
            curr_cat_spend[cat_name] += float(t.amount)
            curr_cat_txs[cat_name].append(t)

        prev_cat_spend = defaultdict(float)
        for t in prev_txs:
            cat_name = categories_map.get(t.category_id, "Unknown")
            prev_cat_spend[cat_name] += float(t.amount)

        for cat_name, curr_spend in curr_cat_spend.items():
            if cat_name == "Unknown":
                continue
            prev_spend = prev_cat_spend[cat_name]
            
            is_spike = False
            pct_inc = 0.0
            inc_amt = curr_spend - prev_spend

            if prev_spend > 0:
                pct_inc = (inc_amt / prev_spend) * 100
                if pct_inc >= 50.0 and inc_amt >= 500.0:
                    is_spike = True
            elif curr_spend >= 1000.0:
                # No baseline spend, but current spend is substantial
                is_spike = True
                pct_inc = 100.0

            if is_spike:
                findings.append({
                    "id": str(uuid.uuid4()),
                    "rule_type": "spending_spike",
                    "severity": "high" if pct_inc >= 100.0 else "medium",
                    "title": f"Significant Spending Spike in {cat_name}",
                    "description": f"Your spending in '{cat_name}' increased by {pct_inc:.1f}% from {prev_spend:.2f} to {curr_spend:.2f} this month.",
                    "recommendation": "Analyze what caused this category spending spike and check if it aligns with your budget goals.",
                    "confidence_score": 90,
                    "affected_transactions": [t.id for t in curr_cat_txs[cat_name]],
                    "metadata": {
                        "type": "category",
                        "name": cat_name,
                        "prev_amount": round(prev_spend, 2),
                        "curr_amount": round(curr_spend, 2),
                        "increase_amount": round(inc_amt, 2),
                        "increase_percentage": round(pct_inc, 2)
                    }
                })

        # --- Merchant Spike Check ---
        curr_merch_spend = defaultdict(float)
        curr_merch_txs = defaultdict(list)
        for t in curr_txs:
            if t.merchant:
                curr_merch_spend[t.merchant] += float(t.amount)
                curr_merch_txs[t.merchant].append(t)

        prev_merch_spend = defaultdict(float)
        for t in prev_txs:
            if t.merchant:
                prev_merch_spend[t.merchant] += float(t.amount)

        for merchant, curr_spend in curr_merch_spend.items():
            prev_spend = prev_merch_spend[merchant]
            is_spike = False
            pct_inc = 0.0
            inc_amt = curr_spend - prev_spend

            if prev_spend > 0:
                pct_inc = (inc_amt / prev_spend) * 100
                if pct_inc >= 50.0 and inc_amt >= 500.0:
                    is_spike = True
            elif curr_spend >= 1000.0:
                is_spike = True
                pct_inc = 100.0

            if is_spike:
                findings.append({
                    "id": str(uuid.uuid4()),
                    "rule_type": "spending_spike",
                    "severity": "high" if pct_inc >= 100.0 else "medium",
                    "title": f"Significant Spending Spike at {merchant}",
                    "description": f"Your spending at '{merchant}' increased by {pct_inc:.1f}% from {prev_spend:.2f} to {curr_spend:.2f} this month.",
                    "recommendation": "Review if this increase represents a one-off purchase or a persistent habit.",
                    "confidence_score": 90,
                    "affected_transactions": [t.id for t in curr_merch_txs[merchant]],
                    "metadata": {
                        "type": "merchant",
                        "name": merchant,
                        "prev_amount": round(prev_spend, 2),
                        "curr_amount": round(curr_spend, 2),
                        "increase_amount": round(inc_amt, 2),
                        "increase_percentage": round(pct_inc, 2)
                    }
                })

        return findings

    def _evaluate_large_transactions(self, expenses: List[Transaction]) -> List[Dict[str, Any]]:
        findings = []
        amounts = [float(t.amount) for t in expenses]
        if len(amounts) < 5:
            return findings

        # Try IQR first
        threshold = calculate_iqr_threshold(amounts)
        if threshold == float('inf') or threshold == 0.0 or len(set(amounts)) == 1:
            # Fallback to standard deviation (mean + 2 * std_dev)
            threshold = calculate_std_dev_threshold(amounts, num_std_dev=2.0)

        if threshold == float('inf'):
            return findings

        # Check for outliers
        for t in expenses:
            amt_val = float(t.amount)
            if amt_val > threshold:
                severity = "high" if amt_val > threshold * 1.5 else "medium"
                findings.append({
                    "id": str(uuid.uuid4()),
                    "rule_type": "large_transaction",
                    "severity": severity,
                    "title": f"Unusually Large Transaction at {t.merchant or 'Unknown'}",
                    "description": f"We detected a transaction of {amt_val:.2f} which exceeds your statistical large transaction threshold of {threshold:.2f}.",
                    "recommendation": "Verify that this transaction is legitimate and check if a refund or budget correction is needed.",
                    "confidence_score": 95,
                    "affected_transactions": [t.id],
                    "metadata": {
                        "merchant": t.merchant or "Unknown",
                        "amount": amt_val,
                        "threshold": round(threshold, 2),
                        "date": str(t.transaction_date)
                    }
                })

        return findings

    def _evaluate_weekend_spending(self, expenses: List[Transaction]) -> List[Dict[str, Any]]:
        findings = []
        
        weekday_spend = 0.0
        weekend_spend = 0.0

        weekday_dates = set()
        weekend_dates = set()

        weekday_txs = []
        weekend_txs = []

        for t in expenses:
            # weekday() returns 0 for Monday, 6 for Sunday
            day_idx = t.transaction_date.weekday()
            amt_val = float(t.amount)
            if day_idx < 5:
                weekday_spend += amt_val
                weekday_dates.add(t.transaction_date)
                weekday_txs.append(t)
            else:
                weekend_spend += amt_val
                weekend_dates.add(t.transaction_date)
                weekend_txs.append(t)

        num_weekdays = len(weekday_dates)
        num_weekend_days = len(weekend_dates)

        avg_weekday = weekday_spend / num_weekdays if num_weekdays > 0 else 0.0
        avg_weekend = weekend_spend / num_weekend_days if num_weekend_days > 0 else 0.0

        if avg_weekday > 0 and avg_weekend >= 1.5 * avg_weekday and weekend_spend >= 1000.0:
            ratio = avg_weekend / avg_weekday
            findings.append({
                "id": str(uuid.uuid4()),
                "rule_type": "weekend_spending",
                "severity": "medium" if ratio >= 2.0 else "low",
                "title": "Weekend Spending Concentration",
                "description": f"Your average daily spending on weekends ({avg_weekend:.2f}) is {ratio:.1f}x higher than weekdays ({avg_weekday:.2f}).",
                "recommendation": "Consider planning your weekend outings in advance or setting a weekend-specific budget limit.",
                "confidence_score": 90,
                "affected_transactions": [t.id for t in weekend_txs],
                "metadata": {
                    "total_weekday": round(weekday_spend, 2),
                    "total_weekend": round(weekend_spend, 2),
                    "avg_weekday": round(avg_weekday, 2),
                    "avg_weekend": round(avg_weekend, 2),
                    "ratio": round(ratio, 2)
                }
            })

        return findings
