"""
Custom exceptions and error handling.
"""

from fastapi import HTTPException, status


class TickerNotFoundError(HTTPException):
    """Raised when a ticker symbol is not found."""

    def __init__(self, symbol: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown symbol",
        )


class ExternalServiceError(HTTPException):
    """Raised when an external service (yfinance, OpenAI) fails."""

    def __init__(self, service: str, message: str | None = None):
        # Don't expose internal details to clients
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="External service unavailable",
        )


class ValidationError(HTTPException):
    """Raised for invalid request parameters."""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
