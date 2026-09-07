# ============================================================
#  main.py — FastAPI application entry point
#
#  Run with:
#    uvicorn app.main:app --reload
#
#  Swagger UI:  http://localhost:8000/docs
#  ReDoc:       http://localhost:8000/redoc
# ============================================================

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

from app.config import get_settings
from app.database import get_db
from app.routers import auth as auth_router

settings = get_settings()

logger = logging.getLogger("main")

from contextlib import asynccontextmanager
from app.database import engine, Base
import app.models  # Register all ORM models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup if they don't exist yet
    Base.metadata.create_all(bind=engine)
    yield

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
    lifespan=lifespan,
)

# Exception handlers to prevent leaking stack traces or internal DB details
@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database exception encountered at {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred. Please try again later."}
    )

@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception encountered at {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

# Security headers middleware
#
# Content-Security-Policy notes
# ──────────────────────────────
# Development (DEBUG=True):
#   CSP is intentionally omitted so that Swagger UI and ReDoc can load their
#   assets from cdn.jsdelivr.net and fastapi.tiangolo.com without being blocked.
#   All other hardening headers remain active.
#
# Production (DEBUG=False):
#   A strict CSP is applied. Swagger UI / ReDoc will be blocked by this policy,
#   which is acceptable — API docs should not be publicly exposed in production.
#   If docs are required in production, set DEBUG=True only on a private network
#   or configure an allowlist that covers the specific CDN origins.
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if not settings.debug:
        # Production: strict CSP — blocks inline scripts and external origins.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'"
        )

    return response

# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ---------------------------------------------------------------------------
# CORS middleware
# Allow the Vite dev server to communicate with the API during development.
# Tighten allowed origins in production.
# ---------------------------------------------------------------------------
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

configured_origins = []
for origin in settings.cors_origins.split(","):
    clean_origin = origin.strip().rstrip("/")
    if clean_origin:
        configured_origins.append(clean_origin)
        configured_origins.append(f"{clean_origin}/")

allowed_origins = list(set(default_origins + configured_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
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
from app.routers import intelligence as intelligence_router
from app.routers import timeline as timeline_router
from app.routers import predictions as predictions_router
from app.routers import simulator as simulator_router

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
app.include_router(intelligence_router.router, prefix="/api", tags=["Financial Intelligence"])
app.include_router(timeline_router.router, tags=["Financial Timeline"])
app.include_router(predictions_router.router, tags=["Predictive Intelligence"])
app.include_router(simulator_router.router, tags=["Savings Simulator"])

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


@app.get("/ready", tags=["Health"])
def readiness_check(db: Session = Depends(get_db)):
    """Readiness check endpoint — checks database availability."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )
