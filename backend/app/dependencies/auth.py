import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# Use HTTPBearer so Swagger UI shows the "Authorize" button
_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that extracts and validates the Bearer JWT.

    Usage:
        @router.get("/protected")
        def protected(current_user: User = Depends(get_current_user)):
            ...

    Raises:
        401: if the token is missing, malformed, expired, or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise credentials_exception

    try:
        user_id = uuid.UUID(str(user_id_raw)) if not isinstance(user_id_raw, uuid.UUID) else user_id_raw
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user
