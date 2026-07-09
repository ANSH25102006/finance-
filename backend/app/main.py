# ============================================================
#  main.py — FastAPI application entry point
#
#  Run with:
#    uvicorn app.main:app --reload
#
#  Swagger UI:  http://localhost:8000/docs
#  ReDoc:       http://localhost:8000/redoc
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth as auth_router

settings = get_settings()

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "API for the Personal Finance Spend Auditor. "
        "Upload transaction files, categorize spending, and audit your finances."
    ),
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS middleware
# Allow the Vite dev server to communicate with the API during development.
# Tighten allowed origins in production.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite default dev port
        "http://localhost:3000",   # Alternative dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])

# ---------------------------------------------------------------------------
# Root endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    """Application root — confirms the API is running."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint — used by monitoring tools and load balancers."""
    return {"status": "ok"}
