import uuid
import logging
from typing import List, Dict, Any
from app.schemas.financial_context import FinancialContext
from app.schemas.savings import SavingsSummary, SavingsOpportunity, SavingsRecommendation

logger = logging.getLogger("savings_opportunity_service")


class SavingsOpportunityService:
    """
    SavingsOpportunityService evaluates a user's FinancialContext in-memory
    to discover actionable savings recommendations and compiles them into
    a structured SavingsSummary (no LLMs).
    """

    def generate_opportunities(self, context: FinancialContext) -> SavingsSummary:
        logger.info("Generating savings opportunities from financial context")

        opportunities: List[SavingsOpportunity] = []
        findings = context.rules_engine

        # 1. Evaluate Forgotten Subscriptions
        if context.subscriptions.monthly_subscription_cost > 0:
            sub_tx_ids = []
            for f in findings:
                if f.rule_type == "forgotten_subscription":
                    sub_tx_ids.extend(f.affected_transactions)

            opp_id = str(uuid.uuid4())
            opportunities.append(SavingsOpportunity(
                id=opp_id,
                opportunity_type="subscriptions",
                title="Cancel Forgotten Subscriptions",
                description=f"You have {len(context.subscriptions.active_subscriptions)} recurring subscriptions costing {context.subscriptions.monthly_subscription_cost:.2f} monthly.",
                potential_monthly_savings=context.subscriptions.monthly_subscription_cost,
                potential_yearly_savings=context.subscriptions.annual_subscription_cost,
                confidence_score=95,
                affected_transactions=sub_tx_ids,
                recommendation=SavingsRecommendation(
                    title="Review Recurring Subscriptions",
                    description="Cancel subscription services that have not been actively utilized.",
                    action_steps=[
                        "Review your active subscriptions list.",
                        "Cancel subscriptions you haven't used in the past 30 days.",
                        "Check for duplicate services (e.g. multiple music or video streaming platforms)."
                    ]
                ),
                metadata={
                    "count": len(context.subscriptions.active_subscriptions),
                    "merchants": [s.merchant for s in context.subscriptions.active_subscriptions]
                }
            ))

        # 2. Evaluate Duplicate Charges
        if context.savings.duplicate_charges_total > 0:
            dup_tx_ids = []
            for f in findings:
                if f.rule_type == "duplicate_charge":
                    dup_tx_ids.extend(f.affected_transactions)

            opp_id = str(uuid.uuid4())
            opportunities.append(SavingsOpportunity(
                id=opp_id,
                opportunity_type="duplicates",
                title="Dispute Duplicate Charges",
                description=f"We identified duplicate charges totaling {context.savings.duplicate_charges_total:.2f} likely due to merchant billing errors.",
                potential_monthly_savings=context.savings.duplicate_charges_total,
                potential_yearly_savings=context.savings.duplicate_charges_total,
                confidence_score=90,
                affected_transactions=dup_tx_ids,
                recommendation=SavingsRecommendation(
                    title="Request Duplicate Reimbursements",
                    description="Reach out to merchant support teams to reverse duplicate billing transactions.",
                    action_steps=[
                        "Locate the transaction items on your official bank accounts statement.",
                        "Contact the merchant's support desk to verify double-billing and request a refund.",
                        "If the merchant refuses, dispute the payment through your card provider."
                    ]
                ),
                metadata={
                    "total_duplicates": context.savings.duplicate_charges_total
                }
            ))

        # 3. Evaluate Weekend Spending Reduction
        if context.savings.weekend_spend_reduction > 0:
            weekend_tx_ids = []
            for f in findings:
                if f.rule_type == "weekend_spending":
                    weekend_tx_ids.extend(f.affected_transactions)

            opp_id = str(uuid.uuid4())
            opportunities.append(SavingsOpportunity(
                id=opp_id,
                opportunity_type="weekend_spend",
                title="Optimize Weekend Spending",
                description=f"Your average daily spending on weekends exceeds weekday averages. Adjusting weekend spending could save you {context.savings.weekend_spend_reduction:.2f} monthly.",
                potential_monthly_savings=context.savings.weekend_spend_reduction,
                potential_yearly_savings=context.savings.weekend_spend_reduction * 12.0,
                confidence_score=85,
                affected_transactions=weekend_tx_ids,
                recommendation=SavingsRecommendation(
                    title="Establish Weekend Spending Limits",
                    description="Implement targets to keep leisure and dining expenditures balanced.",
                    action_steps=[
                        "Create a specific budget limit for weekend purchases.",
                        "Plan weekend meals or activities in advance to avoid impulse dining/entertainment spend.",
                        "Monitor weekend outflows relative to your weekday averages."
                    ]
                ),
                metadata={
                    "weekend_savings": context.savings.weekend_spend_reduction
                }
            ))

        # 4. Evaluate Budget Overruns
        if context.savings.budget_overrun_total > 0:
            overrun_tx_ids = []
            for f in findings:
                if f.rule_type == "category_concentration" and f.severity in ["medium", "high"] and "Budget" in f.title:
                    overrun_tx_ids.extend(f.affected_transactions)

            opp_id = str(uuid.uuid4())
            opportunities.append(SavingsOpportunity(
                id=opp_id,
                opportunity_type="budget_overruns",
                title="Eliminate Category Budget Overruns",
                description=f"You exceeded budgets in categories like {', '.join(context.categories.exceeded_budgets)} by a total of {context.savings.budget_overrun_total:.2f}.",
                potential_monthly_savings=context.savings.budget_overrun_total,
                potential_yearly_savings=context.savings.budget_overrun_total * 12.0,
                confidence_score=95,
                affected_transactions=overrun_tx_ids,
                recommendation=SavingsRecommendation(
                    title="Control Budget Overrun Expenditures",
                    description="Review category allocations and cap spending in over-budget sectors.",
                    action_steps=[
                        "Review categories that exceeded their budget limits (e.g. food, shopping).",
                        "Pause discretionary spending in these categories immediately.",
                        "Set budget alerts in your account settings to get notified at 80% consumption."
                    ]
                ),
                metadata={
                    "overrun_total": context.savings.budget_overrun_total,
                    "exceeded_categories": context.categories.exceeded_budgets
                }
            ))

        # 5. Evaluate Merchant Concentration Optimizations
        for f in findings:
            if f.rule_type == "merchant_concentration":
                meta = f.metadata
                merchant = meta["merchant"]
                spend = float(meta["merchant_spend"])
                
                # Check for substantial spend
                if spend >= 1000.0:
                    potential_m_savings = spend * 0.10  # Suggest 10% optimization target
                    
                    opp_id = str(uuid.uuid4())
                    opportunities.append(SavingsOpportunity(
                        id=opp_id,
                        opportunity_type="merchant_concentration",
                        title=f"Optimize Spending at {merchant}",
                        description=f"Spending at '{merchant}' consumes {meta['percentage']:.1f}% of your total expenses. A 10% optimization target saves {potential_m_savings:.2f} monthly.",
                        potential_monthly_savings=potential_m_savings,
                        potential_yearly_savings=potential_m_savings * 12.0,
                        confidence_score=80,
                        affected_transactions=f.affected_transactions,
                        recommendation=SavingsRecommendation(
                            title=f"Review Single-Merchant Concentration",
                            description="Optimize shopping behavior at high concentration vendors.",
                            action_steps=[
                                f"Review purchases at '{merchant}' to check for bulk buying opportunities.",
                                "Negotiate recurring discounts or look for cheaper vendor alternatives.",
                                "Diversify your purchases to avoid single-vendor lock-in."
                            ]
                        ),
                        metadata={
                            "merchant": merchant,
                            "spend": spend,
                            "percentage": meta["percentage"]
                        }
                    ))

        # Calculate summaries and aggregates
        tot_m_savings = sum(opp.potential_monthly_savings for opp in opportunities)
        tot_y_savings = sum(opp.potential_yearly_savings for opp in opportunities)

        # Weighted confidence calculation
        if tot_m_savings > 0:
            weighted_conf_sum = sum(opp.confidence_score * opp.potential_monthly_savings for opp in opportunities)
            avg_confidence = int(weighted_conf_sum / tot_m_savings)
        else:
            avg_confidence = 90

        return SavingsSummary(
            monthly_savings=round(tot_m_savings, 2),
            yearly_savings=round(tot_y_savings, 2),
            confidence=avg_confidence,
            opportunities=opportunities
        )
