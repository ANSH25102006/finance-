from typing import List, Dict, Any

class RecommendationService:
    """
    Generates deterministic, evidence-backed financial recommendations based on:
    - Duplicate subscriptions
    - Budget overruns
    - Weekend spending spikes
    - Transaction spikes (>3x median)
    """

    def generate_recommendations(
        self,
        patterns: Dict[str, Any],
        subs_data: Dict[str, Any],
        budget_utilization: List[Any]
    ) -> List[Dict[str, Any]]:
        recommendations = []

        # 1. Duplicate Subscriptions Recommendation
        for dup in subs_data.get("duplicate_subscriptions", []):
            expected_annual_savings = dup["potential_savings_monthly"] * 12.0
            recommendations.append({
                "problem": f"Duplicate active plan detected for {dup['merchant']}.",
                "impact": "Unnecessary double-billing for the same provider.",
                "evidence": f"Found {dup['count']} active recurring charge runs for {dup['merchant']} costing {dup['potential_savings_monthly']:.2f} monthly in excess.",
                "suggested_action": f"Review and cancel the duplicate subscriptions for {dup['merchant']}.",
                "expected_savings": round(expected_annual_savings, 2),
                "confidence": "High",
                "priority": "High"
            })

        # 2. Budget Overruns Recommendation
        for b in budget_utilization:
            # We assume b is a dictionary or an object with attributes
            # Let's support both dictionary and object formats
            is_exceeded = b.is_exceeded if hasattr(b, 'is_exceeded') else b.get('is_exceeded', False)
            if is_exceeded:
                cat_name = b.category_name if hasattr(b, 'category_name') else b.get('category_name', 'Unknown')
                spent = b.spent_amount if hasattr(b, 'spent_amount') else b.get('spent_amount', 0.0)
                budget = b.budget_amount if hasattr(b, 'budget_amount') else b.get('budget_amount', 0.0)
                overrun = spent - budget
                expected_annual_savings = overrun * 12.0

                recommendations.append({
                    "problem": f"Budget exceeded in category '{cat_name}'.",
                    "impact": "Reduces your monthly savings potential and overall health score.",
                    "evidence": f"Spent {spent:.2f} against a budget of {budget:.2f} (overrun of {overrun:.2f} this month).",
                    "suggested_action": f"Set a weekly spending alert or cap for '{cat_name}' at {budget / 4:.2f}.",
                    "expected_savings": round(expected_annual_savings, 2),
                    "confidence": "High",
                    "priority": "High"
                })

        # 3. Weekend Spending Spikes Recommendation
        avg_weekday = patterns.get("avg_weekday_daily_spend", 0.0)
        avg_weekend = patterns.get("avg_weekend_daily_spend", 0.0)
        if avg_weekend > avg_weekday * 1.2:
            excess = avg_weekend - avg_weekday
            # 8 weekend days in a month
            monthly_excess = excess * 8
            annual_excess = monthly_excess * 12
            recommendations.append({
                "problem": "Weekend daily spend is significantly higher than weekdays.",
                "impact": "Increases discretionary spend leaks.",
                "evidence": f"Average weekend daily spend is {avg_weekend:.2f} compared to weekday daily spend of {avg_weekday:.2f} (Excess of {excess:.2f}/day).",
                "suggested_action": "Establish weekend spending limits or consolidate shopping lists into weekdays.",
                "expected_savings": round(annual_excess, 2),
                "confidence": "Medium",
                "priority": "Medium"
            })

        # 4. Large Transaction Spikes Recommendation
        spikes = patterns.get("spikes", [])
        if len(spikes) > 0:
            spike_sum = sum(s["amount"] for s in spikes)
            # Assume reducing spikes by 25% if cooling-off rule is enforced
            annual_savings = spike_sum * 0.25 * 12.0
            recommendations.append({
                "problem": f"High value single purchases (spikes) detected.",
                "impact": "Reduces immediate balance liquidity.",
                "evidence": f"Detected {len(spikes)} transaction(s) exceeding 3x the typical median purchase size, totaling {spike_sum:.2f} in value.",
                "suggested_action": "Implement a mandatory 24-hour cooling-off rule before purchasing any items above the spike threshold.",
                "expected_savings": round(annual_savings, 2),
                "confidence": "Medium",
                "priority": "Medium"
            })

        # Fallback if no specific recommendations were compiled
        if not recommendations:
            recommendations.append({
                "problem": "No immediate savings opportunities found.",
                "impact": "Current spending structure is stable.",
                "evidence": "All budget targets are met and no duplicates or spikes were detected.",
                "suggested_action": "Continue tracking your weekly targets and keep saving.",
                "expected_savings": 0.0,
                "confidence": "High",
                "priority": "Low"
            })

        return recommendations
