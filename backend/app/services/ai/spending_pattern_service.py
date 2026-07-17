import calendar
from collections import defaultdict
from datetime import date, timedelta
from typing import List, Dict, Any
from app.models.transaction import Transaction
from app.models.category import Category

class SpendingPatternService:
    """
    Analyzes transaction patterns to detect:
    - Largest category / merchant spending
    - Fastest-growing / declining categories (MoM)
    - Weekday vs weekend spending behavior
    - Weekly trends & spending spikes (>3x median)
    - Spending concentration & lifestyle changes
    """

    def analyze_patterns(self, transactions: List[Transaction], categories: List[Category]) -> Dict[str, Any]:
        # Helper map for category names
        cat_map = {cat.id: cat.name for cat in categories}
        expenses = [tx for tx in transactions if tx.transaction_type == "expense"]

        if not expenses:
            return self._empty_analysis()

        # Determine baseline dates from the latest transaction date
        latest_date = max(tx.transaction_date for tx in expenses)
        curr_month = latest_date.month
        curr_year = latest_date.year

        prev_month = curr_month - 1 if curr_month > 1 else 12
        prev_year = curr_year if curr_month > 1 else curr_year - 1

        # Group transactions
        curr_txs = [tx for tx in expenses if tx.transaction_date.month == curr_month and tx.transaction_date.year == curr_year]
        prev_txs = [tx for tx in expenses if tx.transaction_date.month == prev_month and tx.transaction_date.year == prev_year]

        # Calculate category spending
        curr_cat_spend = defaultdict(float)
        for tx in curr_txs:
            name = cat_map.get(tx.category_id, "Other")
            curr_cat_spend[name] += float(tx.amount)

        prev_cat_spend = defaultdict(float)
        for tx in prev_txs:
            name = cat_map.get(tx.category_id, "Other")
            prev_cat_spend[name] += float(tx.amount)

        # 1. Largest Spending Category (Current Month)
        largest_category = "None"
        largest_cat_amount = 0.0
        if curr_cat_spend:
            largest_category = max(curr_cat_spend, key=curr_cat_spend.get)
            largest_cat_amount = round(curr_cat_spend[largest_category], 2)

        # 2. Fastest-growing / Declining Categories
        growing_categories = []
        declining_categories = []
        lifestyle_changes = []

        all_cats = set(curr_cat_spend.keys()).union(prev_cat_spend.keys())
        for cat in all_cats:
            c_spend = curr_cat_spend.get(cat, 0.0)
            p_spend = prev_cat_spend.get(cat, 0.0)
            
            if p_spend > 0:
                change_pct = ((c_spend - p_spend) / p_spend) * 100
                if change_pct > 0:
                    growing_categories.append({"category": cat, "growth_pct": round(change_pct, 2), "increase_amount": round(c_spend - p_spend, 2)})
                    # Lifestyle change definition: increase > 50% and volume > 1500
                    if change_pct > 50 and (c_spend - p_spend) > 1500:
                        lifestyle_changes.append({"category": cat, "growth_pct": round(change_pct, 2), "increase_amount": round(c_spend - p_spend, 2)})
                elif change_pct < 0:
                    declining_categories.append({"category": cat, "decline_pct": round(abs(change_pct), 2), "decrease_amount": round(p_spend - c_spend, 2)})
            elif c_spend > 1500:
                # Category didn't exist in prev month but has large spend now
                growing_categories.append({"category": cat, "growth_pct": 100.0, "increase_amount": round(c_spend, 2)})
                lifestyle_changes.append({"category": cat, "growth_pct": 100.0, "increase_amount": round(c_spend, 2)})

        fastest_growing = max(growing_categories, key=lambda x: x["growth_pct"], default=None)
        fastest_declining = max(declining_categories, key=lambda x: x["decline_pct"], default=None)

        # 3. Monthly Trends
        total_curr_spend = sum(float(tx.amount) for tx in curr_txs)
        total_prev_spend = sum(float(tx.amount) for tx in prev_txs)
        mom_change_pct = 0.0
        if total_prev_spend > 0:
            mom_change_pct = round(((total_curr_spend - total_prev_spend) / total_prev_spend) * 100, 2)

        # 4. Weekly Trends (Current Month)
        weekly_spend = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        for tx in curr_txs:
            day = tx.transaction_date.day
            if day <= 7:
                weekly_spend[1] += float(tx.amount)
            elif day <= 14:
                weekly_spend[2] += float(tx.amount)
            elif day <= 21:
                weekly_spend[3] += float(tx.amount)
            else:
                weekly_spend[4] += float(tx.amount)
        for w in weekly_spend:
            weekly_spend[w] = round(weekly_spend[w], 2)

        # 5. Weekend vs Weekday Spending
        weekday_txs = [tx for tx in curr_txs if tx.transaction_date.weekday() < 5]
        weekend_txs = [tx for tx in curr_txs if tx.transaction_date.weekday() >= 5]

        weekday_dates = {tx.transaction_date for tx in weekday_txs}
        weekend_dates = {tx.transaction_date for tx in weekend_txs}

        weekday_count = len(weekday_dates) if weekday_dates else 1
        weekend_count = len(weekend_dates) if weekend_dates else 1

        avg_weekday_spend = sum(float(tx.amount) for tx in weekday_txs) / weekday_count
        avg_weekend_spend = sum(float(tx.amount) for tx in weekend_txs) / weekend_count

        # 6. Spending Concentration
        sorted_cats = sorted(curr_cat_spend.items(), key=lambda x: x[1], reverse=True)
        top_3_sum = sum(val for _, val in sorted_cats[:3])
        concentration_ratio = round((top_3_sum / total_curr_spend * 100), 2) if total_curr_spend > 0 else 0.0

        # 7. Highest-Value Purchases
        highest_value_purchases = sorted(
            [{"description": tx.description or "Transaction", "merchant": tx.merchant or "Unknown", "amount": round(float(tx.amount), 2), "date": str(tx.transaction_date)} for tx in curr_txs],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]

        # 8. Spending Spikes
        # Spikes: purchases > 3x the median expense transaction size all-time
        all_amounts = [float(tx.amount) for tx in expenses]
        median_tx = self._get_median(all_amounts)
        spike_threshold = median_tx * 3.0
        spikes = []
        for tx in curr_txs:
            amt = float(tx.amount)
            if amt > spike_threshold and amt > 100.0:  # ignore trivial charges
                spikes.append({
                    "description": tx.description or "Transaction",
                    "merchant": tx.merchant or "Unknown",
                    "amount": round(amt, 2),
                    "date": str(tx.transaction_date),
                    "threshold_multiple": round(amt / median_tx, 1) if median_tx > 0 else 0.0
                })

        # 9. Top / Frequent Merchants
        merchant_spend = defaultdict(float)
        merchant_counts = defaultdict(int)
        for tx in curr_txs:
            if tx.merchant:
                m_name = tx.merchant.strip()
                merchant_spend[m_name] += float(tx.amount)
                merchant_counts[m_name] += 1

        top_merchants = sorted(
            [{"merchant": name, "amount": round(amt, 2)} for name, amt in merchant_spend.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]

        frequent_merchants = sorted(
            [{"merchant": name, "count": count} for name, count in merchant_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]

        return {
            "largest_category": largest_category,
            "largest_cat_amount": largest_cat_amount,
            "fastest_growing_category": fastest_growing["category"] if fastest_growing else None,
            "fastest_growing_pct": fastest_growing["growth_pct"] if fastest_growing else 0.0,
            "fastest_declining_category": fastest_declining["category"] if fastest_declining else None,
            "fastest_declining_pct": fastest_declining["decline_pct"] if fastest_declining else 0.0,
            "mom_change_pct": mom_change_pct,
            "weekly_trends": weekly_spend,
            "avg_weekday_daily_spend": round(avg_weekday_spend, 2),
            "avg_weekend_daily_spend": round(avg_weekend_spend, 2),
            "concentration_ratio": concentration_ratio,
            "lifestyle_changes": lifestyle_changes,
            "highest_value_purchases": highest_value_purchases,
            "spikes": spikes,
            "top_merchants": top_merchants,
            "frequent_merchants": frequent_merchants
        }

    def _empty_analysis(self) -> Dict[str, Any]:
        return {
            "largest_category": "None",
            "largest_cat_amount": 0.0,
            "fastest_growing_category": None,
            "fastest_growing_pct": 0.0,
            "fastest_declining_category": None,
            "fastest_declining_pct": 0.0,
            "mom_change_pct": 0.0,
            "weekly_trends": {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0},
            "avg_weekday_daily_spend": 0.0,
            "avg_weekend_daily_spend": 0.0,
            "concentration_ratio": 0.0,
            "lifestyle_changes": [],
            "highest_value_purchases": [],
            "spikes": [],
            "top_merchants": [],
            "frequent_merchants": []
        }

    def _get_median(self, data: List[float]) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        n = len(sorted_data)
        if n % 2 == 1:
            return sorted_data[n // 2]
        return (sorted_data[(n // 2) - 1] + sorted_data[n // 2]) / 2.0
