import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.services.ai.financial_context_builder import FinancialContextBuilder
from app.services.ai.health_score_service import HealthScoreService
from app.services.ai.savings_opportunity_service import SavingsOpportunityService
from app.services.ai.context_compressor import ContextCompressor
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.conversation_manager import ConversationManager

from app.schemas.prompt import PromptOutput, ChatMessage
from app.services.ai.prompt_templates import SYSTEM_PROMPT_TEMPLATE, DEVELOPER_INSTRUCTIONS_TEMPLATE

logger = logging.getLogger("ai_orchestrator")


class AIOrchestrator:
    """
    AIOrchestrator coordinates the pipeline from user questions and conversation
    histories to structured prompt payloads, invoking context extraction, health score
    evaluation, savings audits, context compression, and prompt assembly.
    Does NOT call any LLMs.
    """

    def __init__(self):
        self.context_builder = FinancialContextBuilder()
        self.health_service = HealthScoreService()
        self.savings_service = SavingsOpportunityService()
        self.compressor = ContextCompressor()
        self.prompt_builder = PromptBuilder()

    def orchestrate_prompt_generation(
        self,
        db: Session,
        user_id: UUID,
        current_question: str,
        chat_history: List[ChatMessage]
    ) -> PromptOutput:
        logger.info(f"Orchestrating prompt generation for user {user_id}")

        if not current_question.strip():
            raise ValueError("Current question cannot be empty.")

        # 1. Build full FinancialContext in memory
        context = self.context_builder.build_context(db, user_id)
        if not context:
            raise ValueError("Failed to compile user financial context.")

        # 2. Run Health Score Engine
        health_score_val = self.health_service.calculate_score(context)

        # 3. Run Savings Opportunity Engine
        savings_summary_val = self.savings_service.generate_opportunities(context)

        # 4. Invoke Context Compressor to compile markdown context and manage limits
        compression_res = self.compressor.compress_if_needed(
            context=context,
            health_score_val=health_score_val,
            savings_summary_val=savings_summary_val,
            history=chat_history,
            current_question=current_question,
            system_prompt=SYSTEM_PROMPT_TEMPLATE,
            developer_prompt=DEVELOPER_INSTRUCTIONS_TEMPLATE
        )

        # 5. Build final PromptOutput
        prompt_output = self.prompt_builder.build_prompt(
            compressed_context_text=compression_res["context_text"],
            history_text=compression_res["history_text"],
            current_question=current_question,
            token_count=compression_res["tokens"]
        )

        return prompt_output
