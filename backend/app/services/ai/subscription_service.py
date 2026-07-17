import math
from collections import defaultdict
from datetime import date, timedelta
from typing import List, Dict, Any
from app.models.transaction import Transaction

class SubscriptionService:
    """
    Analyzes transactions to identify and audit subscriptions.
    Features:
    - Automatically detects recurring cycles (spaced 25 to 35 days).
    - Classifies subscription keywords (Netflix, Spotify, EMIs, SIPs, etc.).
    - Computes monthly/annual costs, first/last payment dates, consistency.
    - Flags price hikes, missed cycles, and duplicate subscription overlaps.
    """

    CATALOG_KEYWORDS = [
        "netflix", "spotify", "amazon prime", "apple", "google", 
        "microsoft", "adobe", "chatgpt", "youtube", "gym", 
        "insurance", "emi", "sip"
    ]

    def detect_subscriptions(self, transactions: List[Transaction]) -> Dict[str, Any]:
        expenses = [tx for tx in transactions if tx.transaction_type == "expense" and tx.merchant]
        if not expenses:
            return self._empty_response()

        latest_date = max(tx.transaction_date for tx in expenses)

        # Group by merchant name (case-insensitive)
        merchant_groups = defaultdict(list)
        for tx in expenses:
            merchant_groups[tx.merchant.strip().lower()].append(tx)

        active_subs = []
        inactive_subs = []
        potential_savings = 0.0

        merchant_runs = {}

        for m_key, txs in merchant_groups.items():
            if len(txs) < 3:
                continue

            sorted_txs = sorted(txs, key=lambda t: t.transaction_date)
            runs = self._find_monthly_runs(sorted_txs)

            for idx, run in enumerate(runs):
                first_tx = run[0]
                last_tx = run[-1]
                avg_amount = sum(float(t.amount) for t in run) / len(run)
                yearly_cost = avg_amount * 12

                # 1. Catalog service identification
                identified_name = first_tx.merchant
                matched_catalog = False
                for kw in self.CATALOG_KEYWORDS:
                    if kw in m_key:
                        matched_catalog = True
                        break

                # 2. Payment consistency calculation
                intervals = []
                for i in range(1, len(run)):
                    delta = (run[i].transaction_date - run[i - 1].transaction_date).days
                    intervals.append(delta)

                consistency_score = 100.0
                if len(intervals) > 0:
                    avg_int = sum(intervals) / len(intervals)
                    variance = sum((x - avg_int) ** 2 for x in intervals) / len(intervals)
                    stddev = math.sqrt(variance)
                    consistency_score = max(0.0, 100.0 - stddev * 6.5)

                # 3. Price hikes
                price_hike = False
                hike_amount = 0.0
                first_price = float(first_tx.amount)
                last_price = float(last_tx.amount)
                if last_price > first_price:
                    price_hike = True
                    hike_amount = round(last_price - first_price, 2)

                # 4. Missed cycles (inactive/missed if last payment was > 38 days ago)
                days_since_last = (latest_date - last_tx.transaction_date).days
                missed_payment = days_since_last > 38
                unused_or_inactive = days_since_last > 45

                sub_item = {
                    "merchant": first_tx.merchant,
                    "monthly_amount": round(avg_amount, 2),
                    "yearly_cost": round(yearly_cost, 2),
                    "first_payment": str(first_tx.transaction_date),
                    "last_payment": str(last_tx.transaction_date),
                    "payment_consistency": round(consistency_score, 1),
                    "price_increase": price_hike,
                    "price_increase_amount": hike_amount,
                    "missed_payment": missed_payment,
                    "days_since_last": days_since_last,
                    "matched_catalog": matched_catalog
                }

                if unused_or_inactive:
                    inactive_subs.append(sub_item)
                else:
                    active_subs.append(sub_item)
                    # Accumulate savings potential if user cancels
                    potential_savings += yearly_cost

                # Track runs to detect duplicates later
                run_key = f"{m_key}_{idx}"
                merchant_runs[run_key] = sub_item

        # 5. Duplicate subscriptions detection
        # Flag if there are multiple active subscriptions for the same merchant prefix
        duplicate_subs = []
        active_by_merchant = defaultdict(list)
        for sub in active_subs:
            active_by_merchant[sub["merchant"].lower().strip()].append(sub)

        for m_name, items in active_by_merchant.items():
            if len(items) > 1:
                duplicate_subs.append({
                    "merchant": items[0]["merchant"],
                    "count": len(items),
                    "items": items,
                    "potential_savings_monthly": round(sum(it["monthly_amount"] for it in items[1:]), 2)
                })

        total_monthly_cost = sum(sub["monthly_amount"] for sub in active_subs)
        total_annual_cost = total_monthly_cost * 12

        return {
            "active_subscriptions": active_subs,
            "inactive_subscriptions": inactive_subs,
            "duplicate_subscriptions": duplicate_subs,
            "monthly_subscription_cost": round(total_monthly_cost, 2),
            "annual_subscription_cost": round(total_annual_cost, 2),
            "potential_savings": round(potential_savings, 2)
        }

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
                mean_amt = sum(float(t.amount) for t in current_run) / len(current_run)
                if all(abs(float(t.amount) - mean_amt) / mean_amt <= 0.30 for t in current_run):
                    runs.append(current_run)
                    for t in current_run:
                        idx = sorted_txs.index(t)
                        used[idx] = True

        return runs

    def _empty_response(self) -> Dict[str, Any]:
        return {
            "active_subscriptions": [],
            "inactive_subscriptions": [],
            "duplicate_subscriptions": [],
            "monthly_subscription_cost": 0.0,
            "annual_subscription_cost": 0.0,
            "potential_savings": 0.0
        }
