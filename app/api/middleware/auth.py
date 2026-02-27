"""
Authentication Middleware Helpers

This module provides low-level authentication utilities:
- Token extraction from request headers
- Client IP extraction for security auditing
- Request state population for logging context

These helpers are used by the API dependencies in app/api/dependencies.py
and by route handlers that need direct access to request metadata.
"""

from typing import Optional

from fastapi import Request


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP address from request.

    Checks X-Forwarded-For header for proxied requests,
    falls back to direct client host.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address string, or None if unavailable
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def set_request_context(request: Request, user_uuid: str) -> None:
    """
    Set user context on request state for error logging.

    The error_handler middleware reads request.state.user_id
    to include user info in structured error logs.

    Args:
        request: FastAPI Request object
        user_uuid: UUID string of the authenticated user
    """
    request.state.user_id = user_uuid
