import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.ai_chat import AIChatRequest, AIChatResponse
from app.services.ai.ai_chat_service import AIChatService

logger = logging.getLogger("ai_router")
router = APIRouter(prefix="/ai", tags=["AI Auditor"])

# Inject reusable chat service instance
chat_service = AIChatService()


@router.post("/chat", response_model=AIChatResponse)
@router.post("/chat/", response_model=AIChatResponse, include_in_schema=False)
def post_ai_chat(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits a financial query to the AI Auditor.
    Retrieves the user's conversation history, builds the context in-memory,
    evaluates score metrics, and queries the LLM provider.
    """
    try:
        response = chat_service.process_chat_message(
            db=db,
            user_id=current_user.id,
            message=payload.message
        )
        return response
    except ValueError as e:
        logger.warning(f"Validation failure in AI chat route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Secure endpoint from internal leakages
        logger.error(f"Uncaught exception in AI chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing your audit query."
        )
