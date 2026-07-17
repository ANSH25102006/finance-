import uuid
from typing import List, Dict, Any
from datetime import date
from collections import defaultdict
from app.services.rules.base_rule import BaseRule
from app.models.transaction import Transaction
from app.models.budget import Budget

class CategoryRules(BaseRule):
    """
    Evaluates:
    1. Category Concentration: Consuming >= 80% (Medium) or >= 100% (High) of the monthly budget.
       Falls back to checking categories consuming > 40% of total monthly expenses if no budgets are set.
    """

    def evaluate(self, transactions: List[Transaction], **kwargs) -> List[Dict[str, Any]]:
        findings = []
        if not transactions:
            return findings

        # Filter only expense transactions
        expenses = [tx for tx in transactions if tx.transaction_type == "expense"]
        if not expenses:
            return findings

        # Retrieve budgets and categories map from kwargs
        budgets: List[Budget] = kwargs.get("budgets", [])
        categories_map = kwargs.get("categories_map", {})

        # Determine reference current month/year based on latest transaction
        latest_tx_date = max(t.transaction_date for t in expenses)
        curr_month = latest_tx_date.month
        curr_year = latest_tx_date.year

        # Filter current month expenses
        curr_expenses = [
            t for t in expenses
            if t.transaction_date.month == curr_month and t.transaction_date.year == curr_year
        ]
        if not curr_expenses:
            return findings

        total_curr_spend = sum(float(t.amount) for t in curr_expenses)

        # Group current spending by category ID
        category_spend = defaultdict(float)
        category_txs = defaultdict(list)
        for t in curr_expenses:
            category_spend[t.category_id] += float(t.amount)
            category_txs[t.category_id].append(t)

        # Map budgets for current month
        curr_budgets = {
            b.category_id: b
            for b in budgets
            if b.month == curr_month and b.year == curr_year
        }

        if curr_budgets:
            # Evaluate budget usage
            for cat_id, b in curr_budgets.items():
                spend = category_spend.get(cat_id, 0.0)
                cat_name = categories_map.get(cat_id, "Unknown")
                
                percentage = (spend / b.amount) * 100
                
                if percentage >= 80.0:
                    severity = "high" if percentage >= 100.0 else "medium"
                    alert_type = "Exceeded" if percentage >= 100.0 else "Nearly Consumed"
                    
                    findings.append({
                        "id": str(uuid.uuid4()),
                        "rule_type": "category_concentration",
                        "severity": severity,
                        "title": f"Category Budget {alert_type}: {cat_name}",
                        "description": f"Your spending in '{cat_name}' has reached {spend:.2f}, consuming {percentage:.1f}% of your monthly budget of {b.amount:.2f}.",
                        "recommendation": f"Reduce discretionary spending in '{cat_name}' immediately to stay within your limits.",
                        "confidence_score": 100,
                        "affected_transactions": [t.id for t in category_txs[cat_id]],
                        "metadata": {
                            "category": cat_name,
                            "spent": round(spend, 2),
                            "budget": round(b.amount, 2),
                            "percentage": round(percentage, 2)
                        }
                    })
        else:
            # Fallback: flag categories consuming > 40% of total monthly spend
            if total_curr_spend > 0:
                for cat_id, spend in category_spend.items():
                    percentage = (spend / total_curr_spend) * 100
                    if percentage >= 40.0 and spend >= 1000.0:
                        cat_name = categories_map.get(cat_id, "Unknown")
                        findings.append({
                            "id": str(uuid.uuid4()),
                            "rule_type": "category_concentration",
                            "severity": "medium",
                            "title": f"High Spending Concentration in {cat_name}",
                            "description": f"Spending in '{cat_name}' accounts for {percentage:.1f}% of your total spending ({spend:.2f} out of {total_curr_spend:.2f}) this month.",
                            "recommendation": "Review this category to see if you can allocate your funds more evenly across other categories.",
                            "confidence_score": 90,
                            "affected_transactions": [t.id for t in category_txs[cat_id]],
                            "metadata": {
                                "category": cat_name,
                                "spent": round(spend, 2),
                                "total_spent": round(total_curr_spend, 2),
                                "percentage": round(percentage, 2)
                            }
                        })

        return findings
