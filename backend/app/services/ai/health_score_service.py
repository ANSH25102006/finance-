import logging
from typing import List, Dict, Any
from app.schemas.financial_context import FinancialContext
from app.schemas.health_score import HealthScore, ScoreFactor

logger = logging.getLogger("health_score_service")


class HealthScoreService:
    """
    Financial Health Score Engine.
    Computes a repeatable, transparent, and explainable health score (0-100)
    for a user entirely in-memory using a pre-compiled FinancialContext.
    """

    # --- Scoring Constants (Weights) ---
    # Bonuses
    BONUS_BUDGET_ADHERENCE = 5
    BONUS_INCOME_SURPLUS = 8
    BONUS_CONSISTENT_INCOME = 6
    BONUS_LOW_SUBSCRIPTION_BURDEN = 5
    BONUS_HEALTHY_SAVINGS_OPPORTUNITY = 4
    BONUS_FEW_DUPLICATES = 2
    BONUS_LOW_MERCHANT_CONCENTRATION = 3
    BONUS_STABLE_SPENDING = 4
    BONUS_HIGH_BUDGET_ACCURACY = 2

    # Deductions
    DEDUCTION_BUDGET_EXCEEDED = -10
    DEDUCTION_MULTIPLE_BUDGET_OVERRUNS = -15
    DEDUCTION_WEEKEND_OVERSPENDING = -6
    DEDUCTION_DUPLICATE_TRANSACTIONS = -4  # Applied per occurrence
    DEDUCTION_SPENDING_SPIKE = -8
    DEDUCTION_HIGH_SUBSCRIPTION_COST = -6
    DEDUCTION_SUBSCRIPTION_PRICE_INCREASE = -3
    DEDUCTION_MERCHANT_CONCENTRATION = -5
    DEDUCTION_CATEGORY_CONCENTRATION = -6
    DEDUCTION_OUTLIER_TRANSACTION = -4
    DEDUCTION_HIGH_SPENDING_GROWTH = -5
    DEDUCTION_IMPULSE_SHOPPING = -5

    def calculate_score(self, context: FinancialContext) -> HealthScore:
        logger.info("Starting deterministic financial health score calculation")

        score = 100
        positive_factors: List[ScoreFactor] = []
        negative_factors: List[ScoreFactor] = []
        recommendations: List[str] = []

        findings = context.rules_engine

        # --- EVALUATE POSITIVE FACTORS ---

        # 1. Budget Adherence (+5)
        has_budgets = len(context.categories.budget_utilization) > 0
        no_overruns = len(context.categories.exceeded_budgets) == 0
        if has_budgets and no_overruns:
            positive_factors.append(ScoreFactor(
                name="Budget Adherence",
                category="Budgeting",
                impact=self.BONUS_BUDGET_ADHERENCE,
                reason="You adhered to all your spending budgets this month.",
                severity="low"
            ))
            score += self.BONUS_BUDGET_ADHERENCE

        # 2. Income Exceeds Expenses (+8)
        if context.income.monthly_income > context.expenses.monthly_expenses:
            positive_factors.append(ScoreFactor(
                name="Income Exceeds Expenses",
                category="Savings",
                impact=self.BONUS_INCOME_SURPLUS,
                reason="Your monthly income exceeds your monthly expenses.",
                severity="low"
            ))
            score += self.BONUS_INCOME_SURPLUS

        # 3. Consistent Monthly Income (+6)
        if context.income.recurring_income > 0.0:
            positive_factors.append(ScoreFactor(
                name="Consistent Monthly Income",
                category="Income",
                impact=self.BONUS_CONSISTENT_INCOME,
                reason="We recognized stable, recurring monthly income sources.",
                severity="low"
            ))
            score += self.BONUS_CONSISTENT_INCOME

        # 4. Low Subscription Burden (+5)
        if context.expenses.monthly_expenses > 0 and context.health.recurring_percentage <= 5.0:
            positive_factors.append(ScoreFactor(
                name="Low Subscription Burden",
                category="Spending",
                impact=self.BONUS_LOW_SUBSCRIPTION_BURDEN,
                reason="Subscriptions consume 5% or less of your monthly expenses.",
                severity="low"
            ))
            score += self.BONUS_LOW_SUBSCRIPTION_BURDEN

        # 5. Healthy Savings Opportunity (+4)
        if context.health.savings_rate >= 20.0:
            positive_factors.append(ScoreFactor(
                name="Healthy Savings Opportunity",
                category="Savings",
                impact=self.BONUS_HEALTHY_SAVINGS_OPPORTUNITY,
                reason="You saved at least 20% of your income this month.",
                severity="low"
            ))
            score += self.BONUS_HEALTHY_SAVINGS_OPPORTUNITY

        # 6. Few Duplicate Transactions (+2)
        duplicate_findings = [f for f in findings if f.rule_type == "duplicate_charge"]
        if not duplicate_findings:
            positive_factors.append(ScoreFactor(
                name="Few Duplicate Transactions",
                category="Spending",
                impact=self.BONUS_FEW_DUPLICATES,
                reason="No duplicate payment transactions were detected.",
                severity="low"
            ))
            score += self.BONUS_FEW_DUPLICATES

        # 7. Low Merchant Concentration (+3)
        concentration_findings = [f for f in findings if f.rule_type == "merchant_concentration"]
        if not concentration_findings:
            positive_factors.append(ScoreFactor(
                name="Low Merchant Concentration",
                category="Spending",
                impact=self.BONUS_LOW_MERCHANT_CONCENTRATION,
                reason="Your transactions are well diversified across merchants.",
                severity="low"
            ))
            score += self.BONUS_LOW_MERCHANT_CONCENTRATION

        # 8. Stable Monthly Spending (+4)
        has_prev_expenses = context.expenses.previous_month_expenses > 0
        is_spending_stable = -15.0 <= context.expenses.percentage_change <= 15.0
        if has_prev_expenses and is_spending_stable:
            positive_factors.append(ScoreFactor(
                name="Stable Monthly Spending",
                category="Spending",
                impact=self.BONUS_STABLE_SPENDING,
                reason="Your MoM spending change remained stable within +/-15%.",
                severity="low"
            ))
            score += self.BONUS_STABLE_SPENDING

        # 9. High Budget Utilization Accuracy (+2)
        has_accurate_budget = any(
            80.0 <= bu.utilization_pct <= 100.0
            for bu in context.categories.budget_utilization
        )
        if has_accurate_budget:
            positive_factors.append(ScoreFactor(
                name="High Budget Utilization Accuracy",
                category="Budgeting",
                impact=self.BONUS_HIGH_BUDGET_ACCURACY,
                reason="Your monthly spending utilizes budgeted targets highly accurately (80%-100%).",
                severity="low"
            ))
            score += self.BONUS_HIGH_BUDGET_ACCURACY


        # --- EVALUATE NEGATIVE FACTORS ---

        # 1. Budget Exceeded (-10) / Multiple Budget Overruns (-15)
        overrun_count = len(context.categories.exceeded_budgets)
        if overrun_count >= 2:
            negative_factors.append(ScoreFactor(
                name="Multiple Budget Overruns",
                category="Budgeting",
                impact=self.DEDUCTION_MULTIPLE_BUDGET_OVERRUNS,
                reason=f"You exceeded {overrun_count} of your monthly spending budgets.",
                severity="high"
            ))
            score += self.DEDUCTION_MULTIPLE_BUDGET_OVERRUNS
            recommendations.append("Reduce spending in exceeded budget categories.")
        elif overrun_count == 1:
            negative_factors.append(ScoreFactor(
                name="Budget Exceeded",
                category="Budgeting",
                impact=self.DEDUCTION_BUDGET_EXCEEDED,
                reason=f"You exceeded your monthly budget for '{context.categories.exceeded_budgets[0]}'.",
                severity="medium"
            ))
            score += self.DEDUCTION_BUDGET_EXCEEDED
            recommendations.append(f"Reduce spending in '{context.categories.exceeded_budgets[0]}' to fit your budget.")

        # 2. Weekend Overspending (-6)
        weekend_findings = [f for f in findings if f.rule_type == "weekend_spending"]
        if weekend_findings:
            negative_factors.append(ScoreFactor(
                name="Weekend Overspending",
                category="Spending",
                impact=self.DEDUCTION_WEEKEND_OVERSPENDING,
                reason="Your weekend average daily spending is significantly higher than weekdays.",
                severity="medium"
            ))
            score += self.DEDUCTION_WEEKEND_OVERSPENDING
            recommendations.append("Set a weekend spending limit.")

        # 3. Duplicate Transactions (-4 each)
        if duplicate_findings:
            deduct_amt = self.DEDUCTION_DUPLICATE_TRANSACTIONS * len(duplicate_findings)
            negative_factors.append(ScoreFactor(
                name="Duplicate Transactions",
                category="Spending",
                impact=deduct_amt,
                reason=f"We detected {len(duplicate_findings)} possible duplicate transaction charges.",
                severity="medium"
            ))
            score += deduct_amt
            recommendations.append("Review duplicate charges and contact merchants for refunds.")

        # 4. Spending Spike (-8)
        spike_findings = [f for f in findings if f.rule_type == "spending_spike"]
        if spike_findings:
            negative_factors.append(ScoreFactor(
                name="Spending Spike",
                category="Spending",
                impact=self.DEDUCTION_SPENDING_SPIKE,
                reason="You had a significant, sudden increase in category/merchant spending.",
                severity="medium"
            ))
            score += self.DEDUCTION_SPENDING_SPIKE
            recommendations.append("Investigate recent spending spikes to see if they are recurring.")

        # 5. High Subscription Cost (-6)
        if context.health.recurring_percentage > 15.0:
            negative_factors.append(ScoreFactor(
                name="High Subscription Cost",
                category="Spending",
                impact=self.DEDUCTION_HIGH_SUBSCRIPTION_COST,
                reason="Recurring subscriptions consume more than 15% of your monthly expenses.",
                severity="medium"
            ))
            score += self.DEDUCTION_HIGH_SUBSCRIPTION_COST
            recommendations.append("Review recurring subscriptions and cancel unused ones.")

        # 6. Subscription Price Increase (-3)
        price_inc_findings = [f for f in findings if f.rule_type == "subscription_price_increase"]
        if price_inc_findings:
            negative_factors.append(ScoreFactor(
                name="Subscription Price Increase",
                category="Spending",
                impact=self.DEDUCTION_SUBSCRIPTION_PRICE_INCREASE,
                reason="Some of your monthly subscriptions have increased in price.",
                severity="low"
            ))
            score += self.DEDUCTION_SUBSCRIPTION_PRICE_INCREASE
            recommendations.append("Review subscriptions that increased in price.")

        # 7. Merchant Concentration (-5)
        if concentration_findings:
            negative_factors.append(ScoreFactor(
                name="Merchant Concentration",
                category="Spending",
                impact=self.DEDUCTION_MERCHANT_CONCENTRATION,
                reason="A single merchant accounts for 25% or more of your total expenses.",
                severity="medium"
            ))
            score += self.DEDUCTION_MERCHANT_CONCENTRATION
            recommendations.append("Diversify spending across alternative merchants.")

        # 8. Category Concentration (-6)
        cat_concentration_findings = [f for f in findings if f.rule_type == "category_concentration"]
        if cat_concentration_findings:
            negative_factors.append(ScoreFactor(
                name="Category Concentration",
                category="Spending",
                impact=self.DEDUCTION_CATEGORY_CONCENTRATION,
                reason="A single category consumes a highly disproportionate share of your budget.",
                severity="medium"
            ))
            score += self.DEDUCTION_CATEGORY_CONCENTRATION
            recommendations.append("Optimize allocations to spread category spending evenly.")

        # 9. Large Statistical Outlier (-4)
        outlier_findings = [f for f in findings if f.rule_type == "large_transaction"]
        if outlier_findings:
            negative_factors.append(ScoreFactor(
                name="Large Statistical Outlier",
                category="Spending",
                impact=self.DEDUCTION_OUTLIER_TRANSACTION,
                reason="We flagged unusually large outlier transactions.",
                severity="medium"
            ))
            score += self.DEDUCTION_OUTLIER_TRANSACTION
            recommendations.append("Verify large transaction outliers are legitimate.")

        # 10. High Monthly Spending Growth (-5)
        if context.expenses.percentage_change >= 30.0:
            negative_factors.append(ScoreFactor(
                name="High Monthly Spending Growth",
                category="Spending",
                impact=self.DEDUCTION_HIGH_SPENDING_GROWTH,
                reason="Your monthly expenses grew by 30% or more compared to last month.",
                severity="medium"
            ))
            score += self.DEDUCTION_HIGH_SPENDING_GROWTH
            recommendations.append("Curb spending to manage monthly expense growth.")

        # 11. Impulse Shopping Concentration (-5)
        shopping_share = context.categories.category_percentages.get("Shopping", 0.0)
        ent_share = context.categories.category_percentages.get("Entertainment", 0.0)
        if (shopping_share + ent_share) >= 40.0:
            negative_factors.append(ScoreFactor(
                name="Impulse Shopping Concentration",
                category="Spending",
                impact=self.DEDUCTION_IMPULSE_SHOPPING,
                reason="Shopping and Entertainment consume 40% or more of your total spend.",
                severity="medium"
            ))
            score += self.DEDUCTION_IMPULSE_SHOPPING
            recommendations.append("Limit impulse shopping and entertainment purchases.")


        # --- NORMALIZATION & CLAMPING ---
        final_score = max(0, min(100, score))

        # --- DETERMINE GRADE, COLOR & RISK LEVEL ---
        if final_score >= 90:
            grade = "A"
            risk_level = "Low"
            score_color = "green"
            summary_text = "Excellent financial discipline. You consistently stay within budget and maintain healthy spending habits."
        elif final_score >= 80:
            grade = "B"
            risk_level = "Medium"
            score_color = "yellow"
            summary_text = "Your finances are generally healthy, but recurring subscriptions and shopping expenses are lowering your score."
        elif final_score >= 70:
            grade = "C"
            risk_level = "Medium"
            score_color = "orange"
            summary_text = "Your financial health is fair, but requires attention due to budget overruns and spending spikes."
        elif final_score >= 60:
            grade = "D"
            risk_level = "High"
            score_color = "orange"
            summary_text = "Your financial health is weak. Repeated overspending and concentration risks are putting you under stress."
        else:
            grade = "F"
            risk_level = "Critical"
            score_color = "red"
            summary_text = "Your finances require critical attention due to repeated overspending, duplicates, or increasing recurring expenses."

        # Re-verify recommendations are unique
        unique_recs = []
        for r in recommendations:
            if r not in unique_recs:
                unique_recs.append(r)
        
        # If perfect score and no recommendations:
        if final_score == 100 and not unique_recs:
            unique_recs.append("Keep maintaining your excellent financial discipline!")

        return HealthScore(
            score=final_score,
            grade=grade,
            summary=summary_text,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            recommendations=unique_recs,
            score_color=score_color,
            progress_percentage=final_score,
            risk_level=risk_level
        )
