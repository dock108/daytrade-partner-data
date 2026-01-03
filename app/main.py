"""
FastAPI application factory and configuration.

This is the main entry point for the TradeLens backend API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, market, outlook, ai
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# CORS origins for iOS development
# iOS Simulator uses localhost, physical devices need local network IP
CORS_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:3000",
    # iOS Simulator WebView origins
    "capacitor://localhost",
    "ionic://localhost",
    # TODO: Add production origin when deployed
    # "https://api.tradelens.app",
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

    # CORS configuration
    # Use settings origins if explicitly configured, otherwise use defaults
    origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else CORS_ORIGINS
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(market.router, prefix="/market", tags=["Market"])
    app.include_router(outlook.router, tags=["Outlook"])
    app.include_router(ai.router, tags=["AI"])

    logger.info("TradeLens API initialized")

    return app


# Create app instance for uvicorn
app = create_app()

