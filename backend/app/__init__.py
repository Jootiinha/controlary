"""Application factory for FastAPI."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

import config
from app.database import init_db, create_all_tables, SessionLocal, Base
from app.database.optimize_schema import create_performance_indexes
from app.routes import auth, accounts, payments, cards, subscriptions, categories, analytics, audit
from app.middleware.csrf import setup_csrf_protection, CSRFConfig
from app.utils.rate_limit import configure_rate_limits

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up Controle Financeiro API...")
    try:
        from app import database
        init_db(config.DATABASE_URL, echo=config.SQLALCHEMY_ECHO)
        create_all_tables()
        logger.info("Database initialized successfully")

        # Create performance indexes
        logger.info("Creating performance indexes...")
        create_performance_indexes(database.engine)
        logger.info("Performance indexes created successfully")

        # Configure rate limiting
        logger.info("Configuring rate limits...")
        configure_rate_limits()
        logger.info("Rate limits configured successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Controle Financeiro API...")


def create_app(testing: bool = False) -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=config.API_TITLE,
        version=config.API_VERSION,
        description=config.API_DESCRIPTION,
        lifespan=lifespan if not testing else None,
    )

    # Add CSRF protection middleware (must be before other middleware)
    if not testing:
        logger.info("Setting up CSRF protection...")
        csrf_config = CSRFConfig()
        csrf_config.SECURE = config.ENVIRONMENT == "production"
        setup_csrf_protection(app, config.JWT_SECRET_KEY, csrf_config)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection in older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy - restrict resource loading
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )

        # HSTS - enforce HTTPS in production
        if config.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Prevent DNS prefetching
        response.headers["X-DNS-Prefetch-Control"] = "off"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": config.API_VERSION,
            "environment": config.ENVIRONMENT,
        }

    # Include routers
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
    app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
    app.include_router(cards.router, prefix="/api/cards", tags=["cards"])
    app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
    app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
    app.include_router(analytics.router)
    app.include_router(audit.router, tags=["audit"])

    return app
