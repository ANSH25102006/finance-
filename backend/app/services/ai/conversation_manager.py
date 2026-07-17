import logging
from datetime import datetime
from typing import List
from app.schemas.prompt import ChatMessage

logger = logging.getLogger("conversation_manager")


class ConversationManager:
    """
    ConversationManager stores and manages the chat history for a user.
    Maintains a maximum history of 10 messages, discarding older messages.
    Designed to easily adapt to DB/Redis persistence in the future.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        # Simple in-memory cache for chat history (stored per class instance or global mock cache)
        # In a real persistence layer, we would fetch from Postgres here.
        self._history: List[ChatMessage] = []

    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a new message to the chat history and trim if necessary."""
        if role not in ["user", "assistant"]:
            raise ValueError("Role must be 'user' or 'assistant'")
        
        msg = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        self._history.append(msg)
        self.trim_history()
        logger.info(f"Added message to chat history for user {self.user_id}. History size: {len(self._history)}")
        return msg

    def get_history(self) -> List[ChatMessage]:
        """Retrieve all active messages in history (up to 10 messages)."""
        return self._history

    def clear_history(self) -> None:
        """Clear all chat history for the user."""
        self._history.clear()
        logger.info(f"Cleared chat history for user {self.user_id}")

    def trim_history(self) -> None:
        """Keep only the last 10 messages, automatically discarding older ones."""
        if len(self._history) > 10:
            logger.info(f"Trimming chat history for user {self.user_id}. Discarding {len(self._history) - 10} old messages.")
            self._history = self._history[-10:]
