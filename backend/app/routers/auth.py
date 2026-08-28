# =============================================================
#  app/routers/auth.py — Auth endpoints
#
#  POST /auth/signup  — register a new user
#  POST /auth/login   — verify credentials, return JWT
#  GET  /auth/me      — return current authenticated user
# =============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import create_user, authenticate_user
from app.core.security import create_access_token
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.dependencies.rate_limit import RateLimiter

router = APIRouter()

login_limiter = RateLimiter(30, 60)
signup_limiter = RateLimiter(30, 60)



@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    dependencies=[Depends(signup_limiter)],
)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account.

    - Validates email format
    - Rejects duplicate email addresses (400)
    - Hashes password with bcrypt
    - Returns the created user (no password exposed)
    """
    return create_user(db=db, user_in=user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive a JWT access token",
    dependencies=[Depends(login_limiter)],
)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with email and password.

    Returns a Bearer JWT token on success.
    Returns 401 if credentials are invalid.
    """
    user = authenticate_user(db=db, email=credentials.email, password=credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently logged-in user.

    Requires a valid Bearer token in the Authorization header.
    Returns 401 if the token is missing or invalid.
    """
    return current_user
