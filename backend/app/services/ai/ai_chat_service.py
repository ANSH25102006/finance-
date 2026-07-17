import logging
import re
from datetime import datetime
from uuid import UUID
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.services.ai.ai_orchestrator import AIOrchestrator
from app.services.ai.conversation_manager import ConversationManager
from app.services.ai.provider_factory import ProviderFactory
from app.config import get_settings as get_ai_settings
from app.schemas.ai_chat import AIChatResponse

logger = logging.getLogger("ai_chat_service")


class AIChatService:
    """
    AIChatService acts as the primary controller for user AI chat execution,
    coordinating history retrieval, context compilation, prompt formatting,
    LLM queries, injection defenses, and response validation.
    """

    # In-memory session store for conversation managers to support history across requests.
    _conversation_managers: Dict[str, ConversationManager] = {}

    def __init__(self):
        self.orchestrator = AIOrchestrator()
        self.settings = get_ai_settings()

    def get_conversation_manager(self, user_id: UUID) -> ConversationManager:
        uid_str = str(user_id)
        if uid_str not in self._conversation_managers:
            self._conversation_managers[uid_str] = ConversationManager(uid_str)
        return self._conversation_managers[uid_str]

    def process_chat_message(self, db: Session, user_id: UUID, message: str) -> AIChatResponse:
        logger.info(f"Processing chat message for user: {user_id}")

        clean_message = message.strip()
        if not clean_message:
            raise ValueError("Message content cannot be empty.")

        # 1. Prompt Injection Defense
        injection_triggers = [
            "ignore previous instructions",
            "show your system prompt",
            "reveal your prompt",
            "print hidden context",
            "show system prompt",
            "reveal prompt"
        ]
        msg_lower = clean_message.lower()
        if any(trigger in msg_lower for trigger in injection_triggers):
            logger.warning(f"Prompt injection attempt blocked for user {user_id}: '{clean_message}'")
            # Returns a polite refusal directly without LLM invocation
            refusal_ans = "I am sorry, but I cannot reveal my system prompts or ignore my internal auditing instructions. How can I assist you with your financial questions?"
            return AIChatResponse(
                answer=refusal_ans,
                health_score=100,
                grade="A",
                monthly_savings=0.0,
                yearly_savings=0.0,
                sources=["security_filter"],
                provider="security",
                model="local-rule",
                generated_at=datetime.utcnow().isoformat(),
                conversation_id=str(user_id)
            )

        # 2. Retrieve Conversation History
        manager = self.get_conversation_manager(user_id)
        history = manager.get_history()

        # 3. Call AIOrchestrator to run all engines (Context, Health, Savings) and build prompt
        prompt_output = self.orchestrator.orchestrate_prompt_generation(
            db=db,
            user_id=user_id,
            current_question=clean_message,
            chat_history=history
        )

        # 4. Resolve LLM Provider
        provider = ProviderFactory.get_provider(self.settings)

        # 5. Submit Query
        start_time = datetime.utcnow()
        answer = provider.generate(prompt_output.full_prompt)
        latency = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"LLM generation completed in {latency:.2f}s using provider {provider.provider_name()}")

        # 6. Validate Response (Anti-Hallucination & Security Leakage)
        self._validate_response(answer, prompt_output.financial_context)

        # 7. Update Conversation History
        manager.add_message(role="user", content=clean_message)
        manager.add_message(role="assistant", content=answer)

        # 8. Re-evaluate Context for direct response metadata mappings (no duplicates queries)
        # We can extract values from context to return as metadata
        context = self.orchestrator.context_builder.build_context(db, user_id)
        health_score_val = self.orchestrator.health_service.calculate_score(context)
        savings_summary_val = self.orchestrator.savings_service.generate_opportunities(context)

        sources = ["financial_context", "rules_engine", "analytics", "health_score", "savings_engine", "spending_patterns", "subscriptions"]

        from app.schemas.ai_chat import AIRecommendation
        recommendations_mapped = [
            AIRecommendation(**rec) for rec in (context.recommendations_list or [])
        ]

        evidence_list = [
            {"metric": "savings_rate", "value": context.health.savings_rate},
            {"metric": "monthly_expenses", "value": context.expenses.monthly_expenses},
            {"metric": "monthly_income", "value": context.income.monthly_income},
            {"metric": "potential_savings_subscriptions", "value": context.savings.potential_savings_subscriptions},
            {"metric": "weekend_spend_reduction", "value": context.savings.weekend_spend_reduction}
        ]

        follow_up_qs = self._generate_follow_up_questions(clean_message, context)

        return AIChatResponse(
            answer=answer,
            health_score=health_score_val.score,
            grade=health_score_val.grade,
            monthly_savings=savings_summary_val.monthly_savings,
            yearly_savings=savings_summary_val.yearly_savings,
            recommendations=recommendations_mapped,
            evidence=evidence_list,
            follow_up_questions=follow_up_qs,
            sources=sources,
            provider=provider.provider_name(),
            model=provider.model_name(),
            generated_at=datetime.utcnow().isoformat(),
            conversation_id=str(user_id)
        )

    def _validate_response(self, answer: str, context_text: str) -> None:
        """Reject responses containing exposures or hallucinated numbers."""
        if not answer.strip():
            logger.error("Response validation failed: Empty response.")
            raise ValueError("Auditor returned an empty response.")

        # Check prompt leaks
        forbidden_keywords = [
            "system prompt",
            "developer instructions",
            "ignore previous instructions",
            "api_key",
            "secret_key"
        ]
        for kw in forbidden_keywords:
            if kw in answer.lower():
                logger.error(f"Response validation failed: Found leaked keyword '{kw}'.")
                raise ValueError("Response contains forbidden system prompt contents.")

        # Check stack traces
        if "traceback (most recent call last)" in answer.lower():
            logger.error("Response validation failed: Stack trace detected.")
            raise ValueError("Response contains an internal traceback error.")

        # Check for hallucinated financial figures (> 100) not present in context
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', answer)
        for num_str in numbers:
            val = float(num_str)
            if val > 100.0:
                # Allow standard dates, year indices, and common units
                if val in [2026.0, 2025.0, 365.0, 30.0, 12.0, 7.0, 100.0]:
                    continue
                # Check direct inclusion in context text
                if num_str not in context_text:
                    logger.error(f"Response validation failed: Hallucinated currency value {num_str} not in context.")
                    raise ValueError(
                        f"Response contains unauthorized financial values not present in deterministic calculations: {num_str}"
                    )

    def _generate_follow_up_questions(self, message: str, context: Any) -> List[str]:
        msg_lower = message.lower()
        
        if "health" in msg_lower or "score" in msg_lower:
            return [
                "Where do I spend the most?",
                "Show my subscriptions",
                "Give me a savings plan"
            ]
        elif "subscription" in msg_lower or "cancel" in msg_lower or "netflix" in msg_lower:
            return [
                "Show my spending trends",
                "Where can I save money?",
                "Explain my health score"
            ]
        elif "save" in msg_lower or "savings" in msg_lower or "budget" in msg_lower:
            return [
                "Compare this month with last month",
                "Show my recurring expenses",
                "What is my largest purchase?"
            ]
        else:
            return [
                "Explain my health score",
                "Show subscriptions",
                "Where can I save money?"
            ]
