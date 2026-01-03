"""
FastAPI application factory and configuration.

This is the main entry point for the TradeLens backend API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, health, market, outlook
from app.core.logging import get_logger

logger = get_logger(__name__)

# CORS origins - permissive for local development
CORS_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "*",  # OK for local dev
]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TradeLens API",
        description="Backend API for the TradeLens iOS day trading companion app.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(market.router, prefix="/ticker", tags=["Market"])
    app.include_router(outlook.router, tags=["Outlook"])
    app.include_router(ai.router, tags=["AI"])

    logger.info("TradeLens API initialized")

    return app


# Create app instance for uvicorn
app = create_app()
