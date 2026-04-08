"""
Base Exception Module

This module provides the base exception class for all custom
application exceptions. All other exceptions should inherit from AppException.

The exception system separates business logic from HTTP concerns:
- Services raise domain exceptions (e.g., UserNotFoundException)
- Exception handlers convert them to HTTP responses
"""

from typing import Any, Dict, Optional

from app.core.error_codes import ErrorCode


class AppException(Exception):
    """
    Base exception class for the application.

    All custom exceptions should inherit from this class.
    The exception handler will convert these to HTTP responses.

    Attributes:
        message: Human-readable error message
        code: Error code from ErrorCode enum
        status_code: Suggested HTTP status code
        details: Additional error details (optional)

    Example:
        raise AppException(
            message="Something went wrong",
            code=ErrorCode.INTERNAL_ERROR,
            details={"field": "value"}
        )
    """

    message: str = "An error occurred"
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    status_code: int = 500

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[ErrorCode] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the exception.

        Args:
            message: Override default message
            code: Override default error code
            status_code: Override default HTTP status code
            details: Additional context information
        """
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details if details is not None else {}

        # Pass message to Exception base class for pickle/copy compatibility
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for JSON response.

        Returns:
            Dictionary with standardized error format
        """
        return {
            "success": False,
            "error": {
                "code": self.code.value if isinstance(self.code, ErrorCode) else self.code,
                "message": self.message,
                "details": self.details,
            },
        }

    def __repr__(self) -> str:
        """Return string representation of the exception."""
        return f"{self.__class__.__name__}(code={self.code}, message={self.message})"
