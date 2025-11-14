"""
Validator utility functions for Pydantic schemas.

This module provides reusable validator functions that can be used across
multiple schemas to ensure consistent validation logic throughout the application.
"""
import re
from typing import Optional

from pydantic import ValidationError


def validate_username(username: Optional[str], allow_none: bool = False) -> Optional[str]:
    """
    Validate username format.

    Rules:
    - Must start with a letter or number
    - Can contain letters, numbers, underscores, and hyphens
    - Must end with a letter or number
    - No consecutive special characters (__, --, _-, -_)

    Args:
        username: The username to validate
        allow_none: If True, None values are allowed (for optional fields)

    Returns:
        The validated username

    Raises:
        ValueError: If username format is invalid

    Example:
        >>> validate_username("johndoe")
        'johndoe'
        >>> validate_username("john_doe")
        'john_doe'
        >>> validate_username("john-doe-123")
        'john-doe-123'
        >>> validate_username("_johndoe")  # Invalid
        ValueError: Username must start with a letter or number
    """
    if username is None:
        if allow_none:
            return None
        raise ValueError("Username cannot be None")

    # Strip whitespace
    username = username.strip()

    # Check if empty after stripping
    if not username:
        raise ValueError("Username cannot be empty or only whitespace")

    # Must start with letter or number
    if not re.match(r"^[a-zA-Z0-9]", username):
        raise ValueError("Username must start with a letter or number")

    # Must end with letter or number
    if not re.match(r".*[a-zA-Z0-9]$", username):
        raise ValueError("Username must end with a letter or number")

    # Can only contain letters, numbers, underscores, and hyphens
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        raise ValueError(
            "Username can only contain letters, numbers, underscores, and hyphens"
        )

    # No consecutive special characters
    if re.search(r"[-_]{2,}", username):
        raise ValueError("Username cannot contain consecutive underscores or hyphens")

    return username


def validate_password(password: str, field_name: str = "Password") -> str:
    """
    Validate password strength.

    Rules:
    - Must contain at least one uppercase letter
    - Must contain at least one lowercase letter
    - Must contain at least one digit
    - Must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    - No whitespace allowed

    Args:
        password: The password to validate
        field_name: Name of the field (for error messages)

    Returns:
        The validated password

    Raises:
        ValueError: If password doesn't meet strength requirements

    Example:
        >>> validate_password("SecurePass123!")
        'SecurePass123!'
        >>> validate_password("weak")  # Invalid
        ValueError: Password must contain at least one uppercase letter
    """
    if not password:
        raise ValueError(f"{field_name} cannot be empty")

    # Check for whitespace
    if re.search(r"\s", password):
        raise ValueError(f"{field_name} cannot contain whitespace")

    # Check for at least one uppercase letter
    if not re.search(r"[A-Z]", password):
        raise ValueError(f"{field_name} must contain at least one uppercase letter")

    # Check for at least one lowercase letter
    if not re.search(r"[a-z]", password):
        raise ValueError(f"{field_name} must contain at least one lowercase letter")

    # Check for at least one digit
    if not re.search(r"\d", password):
        raise ValueError(f"{field_name} must contain at least one digit")

    # Check for at least one special character
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
        raise ValueError(
            f"{field_name} must contain at least one special character (!@#$%^&*()_+-=[]{{}}|;:,.<>?)"
        )

    return password
