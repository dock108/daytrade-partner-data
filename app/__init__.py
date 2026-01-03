"""
App factory and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, ticker, outlook, explain
from app.core.config import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TradeLens API",
        description="Backend API for the TradeLens iOS day trading companion app.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(ticker.router, prefix="/ticker", tags=["Ticker"])
    app.include_router(outlook.router, tags=["Outlook"])
    app.include_router(explain.router, tags=["Explain"])

    return app

