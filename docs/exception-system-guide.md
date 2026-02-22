# Custom Exception System

## Objective

Create a centralized exception system that:
- Replaces direct usage of `HTTPException` in services
- Provides consistent error messages and codes
- Facilitates maintenance and internationalization
- Separates business logic from HTTP status codes
- Uses FastAPI Exception Handlers (recommended approach)

---

## Proposed Architecture

```
app/
├── core/
│   ├── exceptions/
│   │   ├── __init__.py          # Exports all exceptions
│   │   ├── base.py              # Base exception class
│   │   ├── auth.py              # Authentication exceptions
│   │   ├── user.py              # User exceptions
│   │   ├── token.py             # Token exceptions
│   │   └── common.py            # Common exceptions (404, 409, etc.)
│   └── error_codes.py           # Error codes (already exists)
├── api/
│   └── exception_handlers.py    # FastAPI exception handlers
└── main.py                      # Register exception handlers
```

---

## Why FastAPI Exception Handlers over Middleware?

| Aspect | Exception Middleware | FastAPI Exception Handlers |
|--------|---------------------|---------------------------|
| **Configuration** | Middleware stack | `@app.exception_handler` decorator |
| **Execution order** | Before routing | After routing |
| **Performance** | Slightly slower | Faster (only runs on exception) |
| **Recommended by FastAPI** | For logging/tracking | For business exceptions |
| **Separation of concerns** | Less clear | Cleaner |
| **Testing** | More complex | Easier |

**Recommendation:** Use FastAPI Exception Handlers for custom exceptions.

---

## Implementation Steps

### Step 1: Create Base Exception

**File:** `app/core/exceptions/base.py`

```python
"""
Base Exception Module

This module provides the base exception class for all custom
application exceptions. All other exceptions should inherit from AppException.
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """
    Base exception class for the application.

    All custom exceptions should inherit from this class.
    The exception handler will convert these to HTTP responses.

    Attributes:
        message: Human-readable error message
        code: Unique error code (e.g., "USER_NOT_FOUND")
        status_code: Suggested HTTP status code
        details: Additional error details (optional)

    Example:
        raise AppException(
            message="Something went wrong",
            code="CUSTOM_ERROR",
            details={"field": "value"}
        )
    """

    message: str = "An error occurred"
    code: str = "APP_ERROR"
    status_code: int = 500

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception.

        Args:
            message: Override default message
            code: Override default error code
            status_code: Override default HTTP status code
            details: Additional context information
        """
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for JSON response.

        Returns:
            Dictionary with error information
        """
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }
```

---

### Step 2: Create Common Exceptions

**File:** `app/core/exceptions/common.py`

```python
"""
Common Exceptions Module

This module provides common exceptions used across the application
such as not found, conflict, validation, and permission errors.
"""

from typing import Optional

from app.core.exceptions.base import AppException


class NotFoundException(AppException):
    """
    Resource not found exception (404).

    Use when a requested resource does not exist in the database.

    Example:
        raise NotFoundException(resource="User", identifier="123")
    """

    message = "Resource not found"
    code = "NOT_FOUND"
    status_code = 404

    def __init__(
        self,
        resource: str = "Resource",
        identifier: Optional[str] = None,
        message: Optional[str] = None
    ):
        """
        Initialize not found exception.

        Args:
            resource: Name of the resource (e.g., "User", "Post")
            identifier: Resource identifier (e.g., UUID)
            message: Custom message (overrides default)
        """
        if message is None:
            if identifier:
                message = f"{resource} with id '{identifier}' not found"
            else:
                message = f"{resource} not found"
        super().__init__(message=message)


class ConflictException(AppException):
    """
    Conflict exception (409).

    Use when a resource already exists or there's a constraint violation.

    Example:
        raise ConflictException(message="Email already registered")
    """

    message = "Resource already exists"
    code = "CONFLICT"
    status_code = 409


class ValidationException(AppException):
    """
    Validation error exception (422).

    Use when input validation fails beyond Pydantic's automatic validation.

    Example:
        raise ValidationException(
            message="Password too weak",
            details={"field": "password", "reason": "Must contain uppercase"}
        )
    """

    message = "Validation error"
    code = "VALIDATION_ERROR"
    status_code = 422


class ForbiddenException(AppException):
    """
    Forbidden access exception (403).

    Use when user is authenticated but lacks permission.

    Example:
        raise ForbiddenException(message="Only admins can perform this action")
    """

    message = "Access forbidden"
    code = "FORBIDDEN"
    status_code = 403


class BadRequestException(AppException):
    """
    Bad request exception (400).

    Use for malformed requests or invalid parameters.

    Example:
        raise BadRequestException(message="Invalid date format")
    """

    message = "Bad request"
    code = "BAD_REQUEST"
    status_code = 400
```

---

### Step 3: Create Authentication Exceptions

**File:** `app/core/exceptions/auth.py`

```python
"""
Authentication Exceptions Module

This module provides exceptions related to authentication and authorization.
All authentication exceptions return 401 Unauthorized by default.
"""

from app.core.exceptions.base import AppException


class AuthenticationException(AppException):
    """
    Base authentication exception (401).

    Parent class for all authentication-related exceptions.
    """

    message = "Authentication failed"
    code = "AUTH_ERROR"
    status_code = 401


class InvalidCredentialsException(AuthenticationException):
    """
    Invalid credentials exception.

    Use when email/password combination is incorrect.
    Message is intentionally generic to prevent user enumeration.

    Example:
        raise InvalidCredentialsException()
    """

    message = "Invalid email or password"
    code = "INVALID_CREDENTIALS"


class TokenExpiredException(AuthenticationException):
    """
    Token expired exception.

    Use when JWT token has passed its expiration time.

    Example:
        raise TokenExpiredException()
    """

    message = "Token has expired"
    code = "TOKEN_EXPIRED"


class TokenInvalidException(AuthenticationException):
    """
    Invalid token exception.

    Use when JWT token is malformed or signature is invalid.

    Example:
        raise TokenInvalidException()
    """

    message = "Invalid token"
    code = "TOKEN_INVALID"


class TokenRevokedException(AuthenticationException):
    """
    Token revoked exception.

    Use when token exists but has been revoked (logout).

    Example:
        raise TokenRevokedException()
    """

    message = "Token has been revoked"
    code = "TOKEN_REVOKED"


class TokenNotFoundException(AuthenticationException):
    """
    Token not found exception.

    Use when token does not exist in database.

    Example:
        raise TokenNotFoundException()
    """

    message = "Token not found"
    code = "TOKEN_NOT_FOUND"


class InvalidTokenTypeException(AuthenticationException):
    """
    Invalid token type exception.

    Use when token type doesn't match expected type.

    Example:
        raise InvalidTokenTypeException(expected="access", received="refresh")
    """

    message = "Invalid token type"
    code = "INVALID_TOKEN_TYPE"

    def __init__(self, expected: str = None, received: str = None):
        """
        Initialize with expected and received token types.

        Args:
            expected: Expected token type
            received: Received token type
        """
        if expected and received:
            message = f"Invalid token type. Expected '{expected}', got '{received}'"
        else:
            message = self.message
        super().__init__(message=message)
```

---

### Step 4: Create User Exceptions

**File:** `app/core/exceptions/user.py`

```python
"""
User Exceptions Module

This module provides exceptions specific to user operations
such as registration, profile updates, and user lookups.
"""

from typing import Optional

from app.core.exceptions.base import AppException
from app.core.exceptions.common import ConflictException, NotFoundException


class UserNotFoundException(NotFoundException):
    """
    User not found exception.

    Example:
        raise UserNotFoundException(identifier="123e4567-...")
    """

    code = "USER_NOT_FOUND"

    def __init__(self, identifier: Optional[str] = None):
        """
        Initialize user not found exception.

        Args:
            identifier: User UUID or identifier
        """
        super().__init__(resource="User", identifier=identifier)


class UsernameExistsException(ConflictException):
    """
    Username already exists exception.

    Use during registration when username is taken.

    Example:
        raise UsernameExistsException()
    """

    message = "Username already exists"
    code = "USERNAME_EXISTS"


class EmailExistsException(ConflictException):
    """
    Email already registered exception.

    Use during registration when email is already in use.

    Example:
        raise EmailExistsException()
    """

    message = "Email already registered"
    code = "EMAIL_EXISTS"


class PasswordIncorrectException(AppException):
    """
    Password incorrect exception.

    Use when current password verification fails (e.g., password change).

    Example:
        raise PasswordIncorrectException()
    """

    message = "Current password is incorrect"
    code = "PASSWORD_INCORRECT"
    status_code = 401


class UserInactiveException(AppException):
    """
    User inactive exception.

    Use when user account is deactivated or suspended.

    Example:
        raise UserInactiveException()
    """

    message = "User account is inactive"
    code = "USER_INACTIVE"
    status_code = 403
```

---

### Step 5: Create Export File

**File:** `app/core/exceptions/__init__.py`

```python
"""
Custom Application Exceptions

This module exports all custom exceptions for the application.
Import exceptions from here rather than individual modules.

Usage:
    from app.core.exceptions import (
        UserNotFoundException,
        InvalidCredentialsException,
        EmailExistsException,
    )
"""

from app.core.exceptions.base import AppException
from app.core.exceptions.common import (
    NotFoundException,
    ConflictException,
    ValidationException,
    ForbiddenException,
    BadRequestException,
)
from app.core.exceptions.auth import (
    AuthenticationException,
    InvalidCredentialsException,
    TokenExpiredException,
    TokenInvalidException,
    TokenRevokedException,
    TokenNotFoundException,
    InvalidTokenTypeException,
)
from app.core.exceptions.user import (
    UserNotFoundException,
    UsernameExistsException,
    EmailExistsException,
    PasswordIncorrectException,
    UserInactiveException,
)

__all__ = [
    # Base
    "AppException",
    # Common
    "NotFoundException",
    "ConflictException",
    "ValidationException",
    "ForbiddenException",
    "BadRequestException",
    # Auth
    "AuthenticationException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    "TokenInvalidException",
    "TokenRevokedException",
    "TokenNotFoundException",
    "InvalidTokenTypeException",
    # User
    "UserNotFoundException",
    "UsernameExistsException",
    "EmailExistsException",
    "PasswordIncorrectException",
    "UserInactiveException",
]
```

---

### Step 6: Create Exception Handlers

**File:** `app/api/exception_handlers.py`

```python
"""
FastAPI Exception Handlers

This module provides exception handlers that convert custom
exceptions to HTTP responses. Register these in main.py.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle all custom application exceptions.

    Converts AppException instances to standardized JSON responses
    with appropriate HTTP status codes.

    Args:
        request: FastAPI request object
        exc: The raised AppException

    Returns:
        JSONResponse with error details
    """
    headers = None

    # Add WWW-Authenticate header for 401 responses (OAuth2 spec)
    if exc.status_code == 401:
        headers = {"WWW-Authenticate": "Bearer"}

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=headers
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Catches any unhandled exception and returns a generic error response.
    In production, this prevents leaking internal error details.

    Args:
        request: FastAPI request object
        exc: The raised exception

    Returns:
        JSONResponse with generic error message
    """
    # Log the actual error for debugging (implement your logger)
    # logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        }
    )
```

---

### Step 7: Register Handlers in main.py

**File:** `app/main.py` (add to existing)

```python
from fastapi import FastAPI

from app.core.exceptions import AppException
from app.api.exception_handlers import (
    app_exception_handler,
    generic_exception_handler,
)

app = FastAPI()

# Register custom exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

---

### Step 8: Update Services

**Before (with HTTPException):**
```python
from fastapi import HTTPException, status

class AuthService:
    def create_user(self, ...):
        if self.user_repo.username_exists(username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )

        if self.user_repo.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
```

**After (with custom exceptions):**
```python
from app.core.exceptions import UsernameExistsException, EmailExistsException

class AuthService:
    def create_user(self, ...):
        if self.user_repo.username_exists(username):
            raise UsernameExistsException()

        if self.user_repo.email_exists(email):
            raise EmailExistsException()
```

---

## Error Response Format

All errors follow this consistent format:

```json
{
    "success": false,
    "error": {
        "code": "EMAIL_EXISTS",
        "message": "Email already registered",
        "details": {}
    }
}
```

### With Details

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Password validation failed",
        "details": {
            "field": "password",
            "requirements": ["uppercase", "number", "special_char"]
        }
    }
}
```

---

## Benefits

| Aspect | Before (HTTPException) | After (Custom Exceptions) |
|--------|----------------------|----------------------------|
| **Readability** | `HTTPException(409, "...")` | `UsernameExistsException()` |
| **Maintenance** | Duplicated strings | Centralized messages |
| **Testing** | Check status + message | `assertRaises(UsernameExistsException)` |
| **i18n** | Difficult | Easy (change in one place) |
| **Error codes** | Not standardized | `USER_NOT_FOUND`, `EMAIL_EXISTS` |
| **Frontend** | Parse strings | Use consistent codes |
| **Service layer** | Depends on FastAPI | Framework agnostic |

---

## Implementation Checklist

1. [ ] Create `app/core/exceptions/base.py`
2. [ ] Create `app/core/exceptions/common.py`
3. [ ] Create `app/core/exceptions/auth.py`
4. [ ] Create `app/core/exceptions/user.py`
5. [ ] Create `app/core/exceptions/__init__.py`
6. [ ] Create `app/api/exception_handlers.py`
7. [ ] Register handlers in `app/main.py`
8. [ ] Migrate `AuthService` to custom exceptions
9. [ ] Migrate `TokenService` to custom exceptions
10. [ ] Migrate `BaseService` to custom exceptions
11. [ ] Update tests

---

## Additional Notes

- Services no longer import `HTTPException` from FastAPI
- Services become easier to test (no FastAPI dependency)
- Exception handlers convert exceptions to HTTP responses
- Error codes (`USER_NOT_FOUND`) make frontend error handling easier
- All messages and comments are in English
