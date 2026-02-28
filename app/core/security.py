"""
Security module for password hashing and verification.

This module provides secure password handling using bcrypt algorithm.
Bcrypt is specifically designed for password hashing and includes
built-in protection against timing attacks and rainbow table attacks.

Why bcrypt?
-----------
1. Adaptive: The cost factor can be increased as hardware improves
2. Salted: Automatically generates and stores a unique salt per password
3. Slow by design: Makes brute-force attacks computationally expensive

Usage:
------
    from app.core.security import hash_password, verify_password

    # When registering a new user
    hashed = hash_password("user_plain_password")

    # When authenticating a user
    is_valid = verify_password("user_input", stored_hash)
"""

import bcrypt

# =============================================================================
# PASSWORD HASHING CONFIGURATION
# =============================================================================

# Cost factor for bcrypt (2^12 = 4096 iterations)
# Increase this value as hardware becomes faster
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt algorithm.

    This function takes a plain text password and returns a secure hash
    that can be safely stored in the database. The hash includes:
    - Algorithm identifier ($2b$ for bcrypt)
    - Cost factor (default 12 rounds = 2^12 iterations)
    - 22-character salt (randomly generated)
    - 31-character hash

    Example hash format:
        $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.d3HHSlGy
        ├──┤├┤├──────────────────────┤├─────────────────────────────┤
        algo cost      salt                    hash

    Args:
        password: The plain text password to hash.
                  Should already be validated for strength requirements.

    Returns:
        str: A bcrypt hash string (60 characters) safe for database storage.

    Example:
        >>> hashed = hash_password("SecurePass123!")
        >>> print(hashed)
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.d3HHSlGy'

    Security Notes:
        - Never log or print the plain password
        - The hash is one-way; the original password cannot be recovered
        - Each call generates a different hash due to random salt
        - bcrypt truncates passwords longer than 72 bytes
    """
    # Encode password to bytes
    password_bytes = password.encode("utf-8")

    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return as string for database storage
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a stored bcrypt hash.

    This function securely compares a user-provided password with a stored
    hash. It uses constant-time comparison to prevent timing attacks.

    How it works:
    1. Extracts the salt from the stored hash
    2. Hashes the plain password with the same salt
    3. Compares the two hashes in constant time

    Args:
        plain_password: The password provided by the user during login.
        hashed_password: The bcrypt hash stored in the database.

    Returns:
        bool: True if the password matches the hash, False otherwise.

    Example:
        >>> stored_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCO..."
        >>> verify_password("SecurePass123!", stored_hash)
        True
        >>> verify_password("WrongPassword", stored_hash)
        False

    Security Notes:
        - Always use this function instead of comparing hashes directly
        - Constant-time comparison prevents timing attacks
        - Returns False for malformed hashes (doesn't raise exceptions)
    """
    try:
        # Encode both to bytes
        password_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")

        # Verify using bcrypt's constant-time comparison
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, TypeError):
        # Return False for malformed hashes
        return False
