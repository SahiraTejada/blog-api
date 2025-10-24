"""
Error Handler Middleware

This module provides centralized error handling for the FastAPI application.
It catches all exceptions and returns consistent error responses using the
ErrorResponse schema.

Features:
- Consistent error response format
- Different handling for dev vs production
- Structured logging with context
- Specific handlers for common error types
- Security: No stack traces in production
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.core.error_codes import ErrorCode
from app.schemas.base import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def build_error_response(
    message: str,
    status_code: int,
    errors: Optional[List[Dict[str, Any]]] = None,
    error_code: Optional[str] = None,
) -> JSONResponse:
    """
    Build a consistent error response using ErrorResponse schema.

    Args:
        message: Main error message
        status_code: HTTP status code
        errors: List of error details (optional)
        error_code: Error code for frontend (optional)

    Returns:
        JSONResponse with ErrorResponse format
    """
    # Build error details list
    error_details = []
    if errors:
        error_details = errors
    elif error_code:
        # If no errors list but error_code provided, create one error detail
        error_details = [
            ErrorDetail(message=message, code=error_code).model_dump()
        ]

    # Create ErrorResponse
    error_response = ErrorResponse(
        success=False,
        message=message,
        errors=error_details if error_details else None,
        status_code=status_code,
    )

    return JSONResponse(
        status_code=status_code, content=error_response.model_dump()
    )


def log_error(
    request: Request,
    exc: Exception,
    level: str = "error",
    extra_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log error with structured context.

    Args:
        request: FastAPI request object
        exc: Exception that occurred
        level: Log level (error, warning, info)
        extra_context: Additional context to include in log
    """
    # Build log context
    context = {
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else "unknown",
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }

    # Add extra context if provided
    if extra_context:
        context.update(extra_context)

    # Add request ID if available
    if hasattr(request.state, "request_id"):
        context["request_id"] = request.state.request_id

    # Add user ID if available (from auth middleware)
    if hasattr(request.state, "user_id"):
        context["user_id"] = request.state.user_id

    # Log based on level
    log_message = (
        f"{context['error_type']} on {context['method']} {context['path']}: "
        f"{context['error_message']}"
    )

    if level == "error":
        logger.error(log_message, extra=context)
    elif level == "warning":
        logger.warning(log_message, extra=context)
    else:
        logger.info(log_message, extra=context)

    # Log stack trace in development
    if settings.DEBUG:
        logger.debug(f"Stack trace:\n{traceback.format_exc()}")


def is_production() -> bool:
    """Check if running in production mode."""
    return not settings.DEBUG


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


async def validation_exception_handler(
    request: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Returns 422 Unprocessable Entity with validation error details.
    """
    log_error(request, exc, level="warning")

    # Extract validation errors
    error_details = []
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            error_details.append(
                ErrorDetail(
                    field=field,
                    message=error["msg"],
                    code=ErrorCode.VALIDATION_ERROR,
                ).model_dump()
            )
    else:
        # Pydantic ValidationError
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            error_details.append(
                ErrorDetail(
                    field=field,
                    message=error["msg"],
                    code=ErrorCode.VALIDATION_ERROR,
                ).model_dump()
            )

    return build_error_response(
        message="Validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        errors=error_details,
    )


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """
    Handle FastAPI HTTPException.

    These are exceptions raised explicitly in endpoint code.
    """
    log_error(request, exc, level="warning")

    # Map status codes to error codes
    error_code_map = {
        401: ErrorCode.INVALID_TOKEN,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    return build_error_response(
        message=exc.detail,
        status_code=exc.status_code,
        error_code=error_code,
    )


async def integrity_exception_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """
    Handle SQLAlchemy IntegrityError (unique constraints, foreign keys, etc).

    Returns 409 Conflict for duplicate entries or constraint violations.
    """
    log_error(request, exc, level="error")

    # Extract meaningful message from IntegrityError
    error_message = str(exc.orig) if hasattr(exc, "orig") else str(exc)

    # Check if it's a duplicate key error
    if "unique constraint" in error_message.lower() or "duplicate" in error_message.lower():
        message = "A record with this information already exists"
        error_code = ErrorCode.DUPLICATE_ENTRY
    elif "foreign key" in error_message.lower():
        message = "Referenced resource does not exist"
        error_code = ErrorCode.INTEGRITY_ERROR
    else:
        message = "Database constraint violation"
        error_code = ErrorCode.INTEGRITY_ERROR

    # In production, don't expose database details
    if is_production():
        return build_error_response(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
        )
    else:
        # In development, include more details
        return build_error_response(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            errors=[
                ErrorDetail(
                    message=error_message[:200],  # Limit length
                    code=error_code,
                ).model_dump()
            ],
        )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle generic SQLAlchemy errors.

    Returns 500 Internal Server Error.
    """
    log_error(request, exc, level="error")

    # In production, return generic message
    if is_production():
        return build_error_response(
            message="A database error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.DATABASE_ERROR,
        )
    else:
        # In development, include error details
        error_message = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        return build_error_response(
            message="Database error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            errors=[
                ErrorDetail(
                    message=error_message[:200],
                    code=ErrorCode.DATABASE_ERROR,
                ).model_dump()
            ],
        )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for any unhandled exceptions.

    Returns 500 Internal Server Error.
    This is the last line of defense to ensure no exception goes unhandled.
    """
    log_error(request, exc, level="error")

    # In production, return generic message
    if is_production():
        return build_error_response(
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_ERROR,
        )
    else:
        # In development, include stack trace
        return build_error_response(
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            errors=[
                ErrorDetail(
                    message=f"{type(exc).__name__}: {str(exc)}",
                    code=ErrorCode.INTERNAL_ERROR,
                ).model_dump()
            ],
        )


# ============================================================================
# REGISTRATION FUNCTION
# ============================================================================


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Validation errors (Pydantic)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # HTTP exceptions (FastAPI)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Database errors (SQLAlchemy)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # Generic catch-all
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")
