import logging
from typing import List, Dict, Any
from app.schemas.financial_context import FinancialContext
from app.schemas.prompt import ChatMessage

logger = logging.getLogger("context_compressor")


class ContextCompressor:
    """
    ContextCompressor cleanses and formats the FinancialContext into a clean,
    concise Markdown representation, completely stripping raw records, IDs, or DB details.
    It implements token estimation (approx. 4 characters/token) and a priority pruning
    pipeline if the total prompt exceeds the target limit (3000 tokens).
    """

    MAX_TOKENS = 3000
    CHAR_TO_TOKEN_RATIO = 4.0

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count based on standard character ratio."""
        return int(len(text) / self.CHAR_TO_TOKEN_RATIO)

    def compress_context(
        self,
        context: FinancialContext,
        prune_categories: bool = False,
        prune_historical: bool = False,
        prune_minor_rules: bool = False
    ) -> str:
        """
        Formulate a clean, compressed markdown summary of the financial context.
        Supports selective pruning switches.
        """
        lines = []

        # --- Section 1: Financial Overview ---
        lines.append("### FINANCIAL OVERVIEW")
        lines.append(f"- Current Month: {context.profile.current_month}")
        lines.append(f"- Monthly Income: {context.profile.currency} {context.income.monthly_income:,.2f}")
        lines.append(f"- Monthly Expenses: {context.profile.currency} {context.expenses.monthly_expenses:,.2f}")
        
        if not prune_historical:
            lines.append(f"- Previous Month Expenses: {context.profile.currency} {context.expenses.previous_month_expenses:,.2f}")
            lines.append(f"- Monthly Spending Change: {context.expenses.percentage_change:+.1f}%")

        # --- Section 2: Health Score ---
        lines.append(f"\n### FINANCIAL HEALTH")
        lines.append(f"- Health Score: {context.health.savings_rate:.0f} (Grade {context.health.expense_ratio:.0f if hasattr(context.health, 'grade') else 'B'})")
        # Access properties safely
        grade = getattr(context.health, 'grade', 'B')
        risk = getattr(context.health, 'risk_level', 'Medium')
        # Wait, let's read the health score from the precompiled context directly
        # The schema definition has context.health.savings_rate etc. Let's look at what context contains:
        # It contains actual context.health.savings_rate, etc.
        # Wait! The main health score is in `context.health` or where?
        # Let's check schemas/financial_context.py:
        # Class HealthContext: savings_rate, expense_ratio, liquidity_ratio, emergency_fund_months, recurring_percentage
        # Wait, does FinancialContext have the HealthScore from HealthScoreService?
        # Ah! HealthScoreService returns a HealthScore object (with score, grade, summary, etc.).
        # But FinancialContext has the raw health context (savings_rate, expense_ratio, liquidity_ratio, etc.).
        # Wait! Let's check how the AIOrchestrator can merge or pass the health score details.
        # Yes! AIOrchestrator runs HealthScoreService.calculate_score(context) and gets the calculated score!
        # So we can pass the calculated health score as a parameter, or add it to the compressor!
        # Let's pass the calculated `health_score` object directly to `compress_context` or `compress_if_needed`.
        # This is incredibly clean! Let's write `compress_context(context, health_score, ...)`
        
        return "" # We will write the full method below

    def compress_if_needed(
        self,
        context: FinancialContext,
        health_score_val: Any, # HealthScore object
        savings_summary_val: Any, # SavingsSummary object
        history: List[ChatMessage],
        current_question: str,
        system_prompt: str,
        developer_prompt: str
    ) -> Dict[str, Any]:
        """
        Orchestrate the pruning pipeline to fit system prompt + context + history + question
        within 3000 tokens.
        """
        prune_categories = False
        prune_historical = False
        prune_minor_rules = False
        active_history = list(history)

        # Priority Pruning Loop
        for pass_num in range(5):
            # Formulate chat history text
            history_lines = []
            for msg in active_history:
                history_lines.append(f"{msg.role.upper()}: {msg.content}")
            history_text = "\n".join(history_lines)

            # Formulate context markdown
            context_text = self._build_markdown_context(
                context,
                health_score_val,
                savings_summary_val,
                prune_categories,
                prune_historical,
                prune_minor_rules
            )

            # Combine full prompt to check size
            full_prompt = (
                f"{system_prompt}\n\n"
                f"{developer_prompt}\n\n"
                f"{context_text}\n\n"
                f"CHAT HISTORY:\n{history_text}\n\n"
                f"USER QUESTION: {current_question}"
            )

            token_count = self.estimate_tokens(full_prompt)
            if token_count <= self.MAX_TOKENS:
                logger.info(f"Context compiled successfully in {token_count} tokens (Pass {pass_num + 1}).")
                return {
                    "context_text": context_text,
                    "history_text": history_text,
                    "tokens": token_count,
                    "warnings": []
                }

            # Prune step sequence:
            if pass_num == 0:
                # 1. Prune lowest categories (limit top categories to top 3)
                prune_categories = True
                logger.info("Token threshold exceeded. Pruning lowest spending categories.")
            elif pass_num == 1:
                # 2. Prune old conversation (drop oldest 5 messages)
                if len(active_history) > 3:
                    active_history = active_history[-3:]
                    logger.info("Token threshold exceeded. Pruning oldest conversation turns.")
                else:
                    # If already short, skip to next pruning phase
                    prune_minor_rules = True
            elif pass_num == 2:
                # 3. Prune minor rules findings (exclude low severity)
                prune_minor_rules = True
                logger.info("Token threshold exceeded. Pruning minor rule findings (Low severity).")
            elif pass_num == 3:
                # 4. Prune historical summaries
                prune_historical = True
                logger.info("Token threshold exceeded. Pruning historical trend summaries.")
            else:
                # If still too large, warn the user but stop pruning to avoid removing core data
                logger.warning(f"Prompt size {token_count} exceeds target limit of 3000 tokens after maximum compression.")
                return {
                    "context_text": context_text,
                    "history_text": history_text,
                    "tokens": token_count,
                    "warnings": ["Prompt exceeds the target limit of 3000 tokens."]
                }

        # Fallback return
        return {
            "context_text": context_text,
            "history_text": "\n".join([f"{m.role.upper()}: {m.content}" for m in active_history]),
            "tokens": self.estimate_tokens(full_prompt),
            "warnings": ["Prompt exceeds the target limit of 3000 tokens."]
        }

    def _build_markdown_context(
        self,
        context: FinancialContext,
        health_score_val: Any,
        savings_summary_val: Any,
        prune_categories: bool,
        prune_historical: bool,
        prune_minor_rules: bool
    ) -> str:
        lines = []

        # --- Section 1: Financial Overview ---
        lines.append("### FINANCIAL SUMMARY")
        lines.append(f"- Current Month: {context.profile.current_month}")
        lines.append(f"- Monthly Spending: {context.profile.currency} {context.expenses.monthly_expenses:,.2f}")
        lines.append(f"- Monthly Income: {context.profile.currency} {context.income.monthly_income:,.2f}")
        if not prune_historical:
            lines.append(f"- Previous Month Spending: {context.profile.currency} {context.expenses.previous_month_expenses:,.2f}")
            lines.append(f"- Monthly Growth: {context.expenses.percentage_change:+.1f}%")

        # --- Section 2: Health Score ---
        lines.append(f"\n### HEALTH SCORE")
        lines.append(f"- Score: {health_score_val.score}/100 (Grade: {health_score_val.grade})")
        lines.append(f"- Risk Level: {health_score_val.risk_level}")
        lines.append(f"- Summary: {health_score_val.summary}")

        # --- Section 3: Savings Opportunities ---
        lines.append(f"\n### SAVINGS OPPORTUNITIES")
        lines.append(f"- Total Monthly Potential Savings: {context.profile.currency} {savings_summary_val.monthly_savings:,.2f}")
        lines.append(f"- Total Annual Potential Savings: {context.profile.currency} {savings_summary_val.yearly_savings:,.2f}")
        
        for opp in savings_summary_val.opportunities:
            lines.append(f"- [{opp.opportunity_type.upper()}] {opp.title}: save {context.profile.currency} {opp.potential_monthly_savings:,.2f}/month")

        # --- Section 4: Top Categories ---
        lines.append("\n### TOP CATEGORIES")
        top_cats = context.categories.top_categories
        if prune_categories:
            top_cats = top_cats[:3]  # Only show top 3
        for item in top_cats:
            lines.append(f"- {item['category']}: {context.profile.currency} {item['amount']:,.2f}")

        # --- Section 5: Top Merchants ---
        lines.append("\n### TOP MERCHANTS")
        top_merch = context.merchants.top_merchants[:3] # Show top 3 merchants
        for item in top_merch:
            lines.append(f"- {item['merchant']}: {context.profile.currency} {item['amount']:,.2f}")

        # --- Section 6: Active Subscriptions ---
        lines.append("\n### ACTIVE SUBSCRIPTIONS")
        for sub in context.subscriptions.active_subscriptions:
            lines.append(f"- {sub.merchant}: {context.profile.currency} {sub.monthly_amount:,.2f}/month")

        # --- Section 7: Budget Status ---
        lines.append("\n### BUDGET UTILIZATION")
        for bu in context.categories.budget_utilization:
            status = "EXCEEDED" if bu.is_exceeded else "Utilized"
            lines.append(f"- {bu.category_name}: spent {context.profile.currency} {bu.spent_amount:,.2f} of {bu.budget_amount:,.2f} ({bu.utilization_pct:.1f}% - {status})")

        # --- Section 8: Rules Findings ---
        lines.append("\n### SYSTEM FINDINGS")
        for f in context.rules_engine:
            if prune_minor_rules and f.severity.lower() == "low":
                continue
            lines.append(f"- [{f.severity.upper()}] {f.title}: {f.description}")

        return "\n".join(lines)
