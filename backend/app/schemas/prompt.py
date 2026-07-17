from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of message sender ('user' or 'assistant')")
    content: str = Field(..., description="Text content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time the message was sent")


class PromptOutput(BaseModel):
    system_prompt: str = Field(..., description="Section 1: AI Financial Auditor rules")
    developer_prompt: str = Field(..., description="Section 2: Developer reasoning requirements")
    financial_context: str = Field(..., description="Section 3: Compressed markdown financial summary")
    conversation: str = Field(..., description="Section 4: String representation of previous chat turns")
    user_message: str = Field(..., description="Section 5: Current user question")
    full_prompt: str = Field(..., description="Complete combined prompt text ready for LLM submission")
    estimated_tokens: int = Field(..., description="Estimated token count of the full prompt")

    model_config = ConfigDict(from_attributes=True)
