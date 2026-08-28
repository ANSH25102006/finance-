# =============================================================
#  app/services/auth_service.py — Authentication business logic
#  Keep all DB + auth logic here, out of the routers.
# =============================================================

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a user by email address. Returns None if not found."""
    return db.query(User).filter(User.email == email.lower().strip()).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Register a new user.

    Raises:
        HTTPException 400: if the email is already registered.
    """
    email = user_in.email.lower().strip()

    # Reject duplicate emails before hashing to save compute
    existing = get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    new_user = User(
        email=email,
        password_hash=hash_password(user_in.password),
    )
    db.add(new_user)
    db.flush()

    # Create default account for new user to avoid empty destination account state
    from app.models.account import Account
    default_account = Account(
        user_id=new_user.id,
        name="Primary Checking",
        balance=0.0,
        currency="INR",
        color="#3b82f6",
        icon="Building2"
    )
    db.add(default_account)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Verify email/password credentials.

    Returns the User on success, or None if credentials are invalid.
    Intentionally does NOT raise an exception so the router can return 401.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
