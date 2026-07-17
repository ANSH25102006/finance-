import logging
import time
from typing import List, Dict, Any
from app.schemas.prompt import PromptOutput, ChatMessage
from app.services.ai.prompt_templates import SYSTEM_PROMPT_TEMPLATE, DEVELOPER_INSTRUCTIONS_TEMPLATE
from app.services.ai.context_compressor import ContextCompressor

logger = logging.getLogger("prompt_builder")


class PromptBuilder:
    """
    PromptBuilder compiles the final structured prompt ready for submission
    to an LLM. It divides the prompt into five sections:
    1. System Prompt
    2. Developer Instructions
    3. Financial Context (Compressed Markdown Summary)
    4. Conversation History (Pruned/Trimmed)
    5. Current user question
    """

    def __init__(self):
        self.compressor = ContextCompressor()

    def build_prompt(
        self,
        compressed_context_text: str,
        history_text: str,
        current_question: str,
        token_count: int
    ) -> PromptOutput:
        start_time = time.time()
        logger.info("Starting prompt compilation.")

        # Structure the 5 clearly separated sections in full_prompt
        full_prompt = (
            f"=== 1. SYSTEM PROMPT ===\n"
            f"{SYSTEM_PROMPT_TEMPLATE}\n\n"
            f"=== 2. DEVELOPER INSTRUCTIONS ===\n"
            f"{DEVELOPER_INSTRUCTIONS_TEMPLATE}\n\n"
            f"=== 3. FINANCIAL CONTEXT ===\n"
            f"{compressed_context_text}\n\n"
            f"=== 4. CONVERSATION HISTORY ===\n"
            f"{history_text if history_text else 'No previous conversation history.'}\n\n"
            f"=== 5. CURRENT QUESTION ===\n"
            f"{current_question}"
        )

        duration_ms = (time.time() - start_time) * 1000.0
        logger.info(f"Prompt compiled in {duration_ms:.1f}ms. Estimated tokens: {token_count}")

        # Warn if prompt exceeds threshold
        if token_count > 3000:
            logger.warning(f"Full prompt exceeds 3000 token limit target: {token_count} estimated tokens.")

        return PromptOutput(
            system_prompt=SYSTEM_PROMPT_TEMPLATE,
            developer_prompt=DEVELOPER_INSTRUCTIONS_TEMPLATE,
            financial_context=compressed_context_text,
            conversation=history_text,
            user_message=current_question,
            full_prompt=full_prompt,
            estimated_tokens=token_count
        )
