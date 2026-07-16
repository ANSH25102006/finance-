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
        "http://127.0.0.1:5173",   # IPv4 alternative dev port
        "http://localhost:5174",   # Vite fallback dev port
        "http://localhost",        # Just localhost
        "http://localhost:3000",   # Alternative dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from app.routers import accounts as accounts_router
from app.routers import transactions as transactions_router
from app.routers import categories as categories_router
from app.routers import budgets as budgets_router
from app.routers import goals as goals_router
from app.routers import dashboard as dashboard_router
from app.routers import analytics as analytics_router
from app.routers import audit as audit_router
from app.routers import imports as imports_router

app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(accounts_router.router, prefix="/api", tags=["Accounts"])
app.include_router(transactions_router.router, prefix="/api", tags=["Transactions"])
app.include_router(categories_router.router, prefix="/api", tags=["Categories"])
app.include_router(budgets_router.router, prefix="/api", tags=["Budgets"])
app.include_router(goals_router.router, prefix="/api", tags=["Goals"])
app.include_router(dashboard_router.router, prefix="/api", tags=["Dashboard"])
app.include_router(analytics_router.router, prefix="/api", tags=["Analytics"])
app.include_router(audit_router.router, prefix="/api", tags=["Audit"])
app.include_router(imports_router.router, prefix="/api", tags=["CSV Import"])

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
