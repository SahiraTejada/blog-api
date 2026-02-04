import re
from typing import Literal, Optional
from urllib.parse import urlparse


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
        raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")

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
        raise ValueError(f"{field_name} must contain at least one special character (!@#$%^&*()_+-=[]{{}}|;:,.<>?)")

    return password


ImageFormat = Literal["jpg", "jpeg", "png", "gif", "webp", "svg", "ico", "bmp", "avif"]


def validate_image_url(
    url: str, allowed_formats: Optional[list[str]] = None, require_https: bool = False, max_length: int = 2048
) -> tuple[bool, Optional[str]]:
    """
    Validates image URLs with multiple criteria

    Args:
        url: The URL to validate
        allowed_formats: List of allowed formats (e.g., ['jpg', 'png'])
                        If None, allows all common formats
        require_https: If True, only accepts HTTPS URLs
        max_length: Maximum URL length

    Returns:
        (is_valid, error_message)

    Examples:
        >>> validate_image_url("https://example.com/image.jpg")
        (True, None)
        >>> validate_image_url("http://example.com/image.pdf")
        (False, "Invalid image format. Must end with: .jpg, .jpeg, .png...")
    """
    # Validation 1: URL is not empty
    if not url or not url.strip():
        return False, "Image URL cannot be empty"

    url = url.strip()

    # Validation 2: Maximum length
    if len(url) > max_length:
        return False, f"URL too long. Maximum {max_length} characters"

    try:
        # Validation 3: Parse URL
        parsed = urlparse(url)

        # Validation 4: Valid scheme
        if not parsed.scheme:
            return False, "URL must include http:// or https://"

        if parsed.scheme not in ["http", "https"]:
            return False, f"Invalid protocol: {parsed.scheme}. Must be http or https"

        # Validation 5: HTTPS required (optional)
        if require_https and parsed.scheme != "https":
            return False, "Only HTTPS URLs are allowed for security reasons"

        # Validation 6: Valid domain
        if not parsed.netloc:
            return False, "URL must include a valid domain"

        # Validation 7: Image format
        if allowed_formats is None:
            # Default formats
            allowed_formats = ["jpg", "jpeg", "png", "gif", "webp", "svg", "ico", "bmp", "avif"]

        # Get the extension (handles query params and fragments)
        path = parsed.path.lower()

        # Remove query strings and fragments to get the real extension
        if "?" in path:
            path = path.split("?")[0]
        if "#" in path:
            path = path.split("#")[0]

        # Verify extension
        valid_extensions = tuple(f".{fmt.lower()}" for fmt in allowed_formats)

        if not path.endswith(valid_extensions):
            formats_str = ", ".join(f".{fmt}" for fmt in allowed_formats)
            return False, f"Invalid image format. Must end with: {formats_str}"

        return True, None

    except ValueError as e:
        return False, f"Invalid URL format: {str(e)}"
