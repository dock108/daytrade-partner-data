"""
Consistency safeguards for data providers.

Ensures all data access goes through canonical providers.
In development mode, raises exceptions for direct API access.
"""

import functools
from collections.abc import Callable

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DirectAPIAccessError(Exception):
    """Raised when code bypasses canonical providers to access APIs directly."""

    def __init__(self, api_name: str, caller: str):
        self.api_name = api_name
        self.caller = caller
        super().__init__(
            f"Direct access to {api_name} from {caller} is prohibited. "
            f"Use canonical providers from app.providers instead."
        )


def _get_caller_info() -> str:
    """Get the caller's module and function name."""
    import inspect

    # Walk up the stack to find the caller outside this module
    for frame_info in inspect.stack()[2:]:
        module = frame_info.frame.f_globals.get("__name__", "unknown")
        if not module.startswith("app.providers"):
            return f"{module}:{frame_info.function}"
    return "unknown"


def guard_direct_access(api_name: str) -> Callable:
    """
    Decorator to guard against direct API access outside providers.

    Usage:
        @guard_direct_access("yfinance")
        def some_function():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            caller = _get_caller_info()

            # Allow access from providers
            if caller.startswith("app.providers"):
                return func(*args, **kwargs)

            # In debug mode, raise exception
            if settings.DEBUG:
                raise DirectAPIAccessError(api_name, caller)

            # In production, log warning but allow
            logger.warning(
                f"Direct {api_name} access from {caller}. "
                f"This should use canonical providers."
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_response_has_timestamp(response: dict, field: str = "timestamp") -> bool:
    """Validate that a response includes a timestamp field."""
    if field not in response:
        logger.warning(f"Response missing required field: {field}")
        return False
    return True


def validate_response_has_source(response: dict, field: str = "source") -> bool:
    """Validate that a response includes a source field."""
    if field not in response:
        logger.warning(f"Response missing required field: {field}")
        return False
    return True


def validate_provider_response(response: dict) -> bool:
    """Validate that a provider response has all required metadata."""
    return (
        validate_response_has_timestamp(response) and validate_response_has_source(response)
    )

