import uuid
from typing import List, Dict, Any
from collections import defaultdict
from app.services.rules.base_rule import BaseRule
from app.models.transaction import Transaction

class IncomeRules(BaseRule):
    """
    Evaluates:
    1. Income Detection: Identifies probable monthly salary/stipend incomes.
    2. Refund Detection: Identifies refund, cashback, and reimbursement credits.
    """

    def evaluate(self, transactions: List[Transaction], **kwargs) -> List[Dict[str, Any]]:
        findings = []
        if not transactions:
            return findings

        categories_map = kwargs.get("categories_map", {})

        # Filter only income transactions
        incomes = [tx for tx in transactions if tx.transaction_type == "income"]

        if not incomes:
            return findings

        findings.extend(self._evaluate_income_detection(incomes, categories_map))
        findings.extend(self._evaluate_refund_detection(incomes))

        return findings

    def _evaluate_income_detection(self, incomes: List[Transaction], categories_map: Dict[Any, str]) -> List[Dict[str, Any]]:
        findings = []

        # Group by description/merchant
        groups = defaultdict(list)
        for t in incomes:
            key = (t.merchant or t.description or "").strip().lower()
            groups[key].append(t)

        for key, txs in groups.items():
            if len(txs) < 3:
                continue

            sorted_txs = sorted(txs, key=lambda t: t.transaction_date)

            # Check if this group behaves like a monthly recurrence
            runs = self._find_monthly_runs(sorted_txs)

            for run in runs:
                # Check if it matches salary keywords or has "Salary" category
                has_salary_keyword = any(
                    w in key for w in ["salary", "payroll", "stipend", "wages"]
                )
                has_salary_category = any(
                    categories_map.get(t.category_id, "") == "Salary" for t in run
                )

                if has_salary_keyword or has_salary_category:
                    avg_amount = sum(float(t.amount) for t in run) / len(run)
                    first_tx = run[0]
                    last_tx = run[-1]

                    findings.append({
                        "id": str(uuid.uuid4()),
                        "rule_type": "income_detection",
                        "severity": "low",
                        "title": "Recurring Salary Income Detected",
                        "description": f"We recognized recurring monthly income from '{first_tx.merchant or first_tx.description}' of approximately {avg_amount:.2f}.",
                        "recommendation": "Review your savings rate and consider setting up automated deposits or investments directly on pay day.",
                        "confidence_score": 99,
                        "affected_transactions": [t.id for t in run],
                        "metadata": {
                            "source": first_tx.merchant or first_tx.description,
                            "monthly_amount": round(avg_amount, 2),
                            "first_date": str(first_tx.transaction_date),
                            "last_date": str(last_tx.transaction_date)
                        }
                    })

        return findings

    def _evaluate_refund_detection(self, incomes: List[Transaction]) -> List[Dict[str, Any]]:
        findings = []
        refund_keywords = ["refund", "cashback", "reimbursement", "returned", "refd"]

        for t in incomes:
            desc_lower = (t.description or "").lower()
            merch_lower = (t.merchant or "").lower()

            is_refund = any(w in desc_lower or w in merch_lower for w in refund_keywords)

            if is_refund:
                findings.append({
                    "id": str(uuid.uuid4()),
                    "rule_type": "refund_detection",
                    "severity": "low",
                    "title": f"Refund Detected: {t.merchant or t.description}",
                    "description": f"We identified a credit transaction of {float(t.amount):.2f} likely representing a refund or cashback credit from {t.merchant or t.description}.",
                    "recommendation": "Verify that this credit matches your records for returns or cashback promotions.",
                    "confidence_score": 95,
                    "affected_transactions": [t.id],
                    "metadata": {
                        "merchant": t.merchant or "Unknown",
                        "amount": float(t.amount),
                        "date": str(t.transaction_date)
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
                runs.append(current_run)
                for t in current_run:
                    idx = sorted_txs.index(t)
                    used[idx] = True

        return runs
