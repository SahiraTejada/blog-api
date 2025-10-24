# Complete Authentication Guide: JWT, Sessions, and OAuth

A comprehensive guide to understanding and implementing authentication in modern web applications.

---

## Table of Contents

1. [What is JWT?](#what-is-jwt)
2. [What is Session-Based Authentication?](#what-is-session-based-authentication)
3. [How to Implement JWT](#how-to-implement-jwt)
4. [How to Implement Session-Based Auth](#how-to-implement-session-based-auth)
5. [When to Use JWT vs Sessions](#when-to-use-jwt-vs-sessions)
6. [Auth Middleware Implementation](#auth-middleware-implementation)
7. [Using JWT and Sessions Together](#using-jwt-and-sessions-together)
8. [Benefits of Each Approach](#benefits-of-each-approach)
9. [User Creation and Login Flow](#user-creation-and-login-flow)
10. [Token Repository and User Repository](#token-repository-and-user-repository)
11. [What is OAuth?](#what-is-oauth)
12. [How to Implement OAuth](#how-to-implement-oauth)
13. [Security Best Practices](#security-best-practices)
14. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

---

## 1. What is JWT?

### Definition

**JWT (JSON Web Token)** is a compact, URL-safe means of representing claims to be transferred between two parties. It's a self-contained token that carries information about the user.

### Structure

A JWT consists of three parts separated by dots (`.`):

```
header.payload.signature
```

**Example JWT:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### Parts Explained

#### 1. Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```
- `alg`: Algorithm used for signing (e.g., HS256, RS256)
- `typ`: Type of token (always JWT)

#### 2. Payload
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "email": "john@example.com",
  "iat": 1516239022,
  "exp": 1516242622
}
```
- Contains **claims** (user data)
- Standard claims: `sub` (subject/user ID), `iat` (issued at), `exp` (expiration)
- Custom claims: Any data you want to include

#### 3. Signature
```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret
)
```
- Ensures token hasn't been tampered with
- Created using the header, payload, and a secret key

### Key Characteristics

✅ **Stateless**: Server doesn't store tokens
✅ **Self-contained**: Token contains all user information
✅ **Portable**: Can be used across different domains
✅ **Scalable**: No server-side storage needed
❌ **Cannot be invalidated**: Once issued, valid until expiration
❌ **Size**: Larger than session IDs

---

## 2. What is Session-Based Authentication?

### Definition

**Session-based authentication** stores user state on the server. The client receives a session ID (cookie) that references the server-side session data.

### How It Works

```
1. User logs in
2. Server creates session and stores it
3. Server sends session ID to client (as cookie)
4. Client sends session ID with each request
5. Server looks up session to authenticate user
```

### Session Storage

Sessions are typically stored in:
- **Memory** (fast but not scalable)
- **Database** (persistent, scalable)
- **Redis/Memcached** (fast and scalable)

### Example Session Data

**Server-side (Redis):**
```json
{
  "session_id": "abc123xyz",
  "user_id": "user-uuid-here",
  "email": "john@example.com",
  "created_at": "2025-01-15T10:00:00Z",
  "expires_at": "2025-01-15T22:00:00Z",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

**Client-side (Cookie):**
```
session_id=abc123xyz; HttpOnly; Secure; SameSite=Strict
```

### Key Characteristics

✅ **Stateful**: Server stores session data
✅ **Revocable**: Can invalidate sessions immediately
✅ **Small cookies**: Only session ID sent to client
✅ **Secure**: Session data never exposed to client
❌ **Not scalable**: Requires shared session storage
❌ **Server load**: Must query storage for each request

---

## 3. How to Implement JWT

### Step 1: Install Dependencies

```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

### Step 2: Configuration

```python
# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-here"  # CHANGE IN PRODUCTION
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 3: JWT Utilities

```python
# app/core/jwt.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiration."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from token."""
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None
```

### Step 4: Password Hashing

```python
# app/core/security.py

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

### Step 5: Authentication Endpoints

```python
# app/api/v1/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token, create_refresh_token, verify_token
from app.core.security import verify_password, hash_password
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user_repo = UserRepository(db)

    # Check if user exists
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    user_dict = user_data.model_dump()
    user_dict["password"] = hashed_password
    new_user = user_repo.create(user_dict)

    # Create tokens
    access_token = create_access_token(data={"sub": str(new_user.uuid)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.uuid)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens."""
    user_repo = UserRepository(db)

    # Get user by email
    user = user_repo.get_by_email(form_data.username)  # username = email

    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.uuid)})
    refresh_token = create_refresh_token(data={"sub": str(user.uuid)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
async def refresh_access_token(refresh_token: str):
    """Refresh access token using refresh token."""
    payload = verify_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    access_token = create_access_token(data={"sub": user_id})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
```

### Step 6: Get Current User Dependency

```python
# app/api/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.jwt import verify_token
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    This dependency can be used in any endpoint that requires authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise credentials_exception

    # Extract user ID
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    user_repo = UserRepository(db)
    user = user_repo.get_by_uuid(user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active (not disabled)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user
```

### Step 7: Protected Endpoint Example

```python
# app/api/v1/routes/users.py

from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_active_user
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile (protected route)."""
    return {
        "uuid": current_user.uuid,
        "email": current_user.email,
        "name": current_user.name,
        "created_at": current_user.created_at
    }


@router.put("/me")
async def update_current_user(
    update_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    user_repo = UserRepository(db)
    updated_user = user_repo.update(current_user.uuid, update_data)
    return updated_user
```

---

## 4. How to Implement Session-Based Auth

### Step 1: Install Dependencies

```bash
pip install redis aioredis
```

### Step 2: Session Configuration

```python
# app/core/config.py

class Settings(BaseSettings):
    # Session Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    SESSION_EXPIRE_SECONDS: int = 43200  # 12 hours
    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_COOKIE_SECURE: bool = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"

settings = Settings()
```

### Step 3: Redis Connection

```python
# app/core/redis.py

import redis
from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)


def get_redis():
    """Get Redis client."""
    return redis_client
```

### Step 4: Session Manager

```python
# app/core/session.py

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.core.redis import redis_client
from app.core.config import settings


class SessionManager:
    """Manage user sessions in Redis."""

    def __init__(self):
        self.redis = redis_client
        self.expire_seconds = settings.SESSION_EXPIRE_SECONDS

    def create_session(self, user_id: UUID, user_data: dict) -> str:
        """
        Create a new session.

        Args:
            user_id: User's UUID
            user_data: Additional user data to store in session

        Returns:
            Session ID
        """
        # Generate secure random session ID
        session_id = secrets.token_urlsafe(32)

        # Prepare session data
        session_data = {
            "user_id": str(user_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (
                datetime.now(timezone.utc) +
                timedelta(seconds=self.expire_seconds)
            ).isoformat(),
            **user_data
        }

        # Store in Redis with expiration
        key = f"session:{session_id}"
        self.redis.setex(
            key,
            self.expire_seconds,
            json.dumps(session_data)
        )

        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data.

        Args:
            session_id: Session ID

        Returns:
            Session data dictionary or None if not found
        """
        key = f"session:{session_id}"
        data = self.redis.get(key)

        if data:
            return json.loads(data)
        return None

    def update_session(self, session_id: str, data: dict) -> bool:
        """
        Update session data.

        Args:
            session_id: Session ID
            data: Data to update

        Returns:
            True if successful, False if session not found
        """
        key = f"session:{session_id}"
        current_data = self.get_session(session_id)

        if not current_data:
            return False

        # Merge new data
        current_data.update(data)

        # Update in Redis (reset TTL)
        self.redis.setex(
            key,
            self.expire_seconds,
            json.dumps(current_data)
        )

        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session (logout).

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        key = f"session:{session_id}"
        deleted = self.redis.delete(key)
        return deleted > 0

    def refresh_session(self, session_id: str) -> bool:
        """
        Refresh session expiration time.

        Args:
            session_id: Session ID

        Returns:
            True if refreshed, False if not found
        """
        key = f"session:{session_id}"

        if not self.redis.exists(key):
            return False

        # Reset expiration
        self.redis.expire(key, self.expire_seconds)
        return True

    def get_all_user_sessions(self, user_id: UUID) -> list:
        """Get all active sessions for a user."""
        pattern = "session:*"
        sessions = []

        for key in self.redis.scan_iter(match=pattern):
            data = self.redis.get(key)
            if data:
                session_data = json.loads(data)
                if session_data.get("user_id") == str(user_id):
                    sessions.append({
                        "session_id": key.replace("session:", ""),
                        **session_data
                    })

        return sessions

    def delete_all_user_sessions(self, user_id: UUID) -> int:
        """Delete all sessions for a user (logout from all devices)."""
        sessions = self.get_all_user_sessions(user_id)
        count = 0

        for session in sessions:
            if self.delete_session(session["session_id"]):
                count += 1

        return count


session_manager = SessionManager()
```

### Step 5: Session Authentication Endpoints

```python
# app/api/v1/routes/auth_session.py

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import verify_password, hash_password
from app.core.session import session_manager
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate, UserLogin

router = APIRouter(prefix="/auth/session", tags=["Session Authentication"])


@router.post("/register")
async def register_with_session(
    user_data: UserCreate,
    response: Response,
    db: Session = Depends(get_db)
):
    """Register a new user and create session."""
    user_repo = UserRepository(db)

    # Check if user exists
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    user_dict = user_data.model_dump()
    user_dict["password"] = hashed_password
    new_user = user_repo.create(user_dict)

    # Create session
    session_id = session_manager.create_session(
        new_user.uuid,
        {
            "email": new_user.email,
            "name": new_user.name
        }
    )

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="lax",
        max_age=43200  # 12 hours
    )

    return {
        "message": "User registered successfully",
        "user": {
            "uuid": new_user.uuid,
            "email": new_user.email,
            "name": new_user.name
        }
    }


@router.post("/login")
async def login_with_session(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login user and create session."""
    user_repo = UserRepository(db)

    # Get user
    user = user_repo.get_by_email(credentials.email)

    # Verify credentials
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create session
    session_id = session_manager.create_session(
        user.uuid,
        {
            "email": user.email,
            "name": user.name
        }
    )

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=43200
    )

    return {
        "message": "Login successful",
        "user": {
            "uuid": user.uuid,
            "email": user.email,
            "name": user.name
        }
    }


@router.post("/logout")
async def logout(response: Response, session_id: str = Cookie(None)):
    """Logout user (delete session)."""
    if session_id:
        session_manager.delete_session(session_id)

    # Clear cookie
    response.delete_cookie(key="session_id")

    return {"message": "Logout successful"}


@router.post("/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user_session),
    response: Response
):
    """Logout from all devices."""
    count = session_manager.delete_all_user_sessions(current_user.uuid)

    # Clear current cookie
    response.delete_cookie(key="session_id")

    return {
        "message": f"Logged out from {count} devices"
    }
```

### Step 6: Session Dependency

```python
# app/api/dependencies.py

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.session import session_manager
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.models import User


async def get_current_user_session(
    session_id: str = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from session.

    This dependency can be used in any endpoint that requires authentication.
    """
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get session data
    session_data = session_manager.get_session(session_id)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    # Get user from database
    user_id = session_data.get("user_id")
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)

    if not user:
        # Session exists but user doesn't - clean up
        session_manager.delete_session(session_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Refresh session expiration
    session_manager.refresh_session(session_id)

    return user
```

### Step 7: Protected Endpoint with Session

```python
@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user_session)
):
    """Get current user profile (session-based auth)."""
    return {
        "uuid": current_user.uuid,
        "email": current_user.email,
        "name": current_user.name
    }
```

---

## 5. When to Use JWT vs Sessions

### Use JWT When:

✅ **Microservices Architecture**
- JWT is stateless, no shared session storage needed
- Each service can verify tokens independently

✅ **Mobile Apps**
- Easier to store and send JWT in Authorization header
- No cookie management needed

✅ **Cross-Domain / CORS**
- JWT can be sent to different domains easily
- No cookie CORS issues

✅ **Scalability is Priority**
- No server-side storage required
- Horizontal scaling is easier

✅ **API-Only Backend**
- No need for cookie management
- RESTful stateless design

**Example Use Cases:**
- Mobile app backend
- Public API
- Microservices
- Third-party integrations
- Single Sign-On (SSO)

---

### Use Sessions When:

✅ **Traditional Web Applications**
- Server-rendered pages with cookies
- Better browser security (HttpOnly cookies)

✅ **Need to Revoke Access Immediately**
- Can invalidate sessions server-side
- Important for security-critical apps

✅ **Simpler Implementation**
- Less complexity than JWT
- Framework support built-in

✅ **Sensitive Applications**
- Banking, healthcare, admin panels
- Need fine-grained control over sessions

✅ **Small to Medium Scale**
- Single server or few servers
- Shared Redis is acceptable

**Example Use Cases:**
- Admin dashboards
- Banking applications
- Enterprise internal tools
- E-commerce checkout
- Social media platforms

---

### Comparison Table

| Feature | JWT | Session |
|---------|-----|---------|
| **Storage** | Client-side (localStorage/cookie) | Server-side (Redis/DB) |
| **State** | Stateless | Stateful |
| **Scalability** | Excellent | Good (with Redis) |
| **Revocation** | Difficult (blacklist needed) | Easy (delete session) |
| **Size** | Large (~1KB) | Small (session ID only) |
| **Expiration** | Fixed (in token) | Flexible (server-controlled) |
| **CSRF Protection** | Not needed (if in header) | Needed (if in cookie) |
| **XSS Risk** | High (if in localStorage) | Low (HttpOnly cookie) |
| **Cross-Domain** | Easy | Complex (CORS) |
| **Mobile Apps** | Perfect | Complicated |
| **Server Load** | Low | Medium (Redis lookup) |
| **Implementation** | Complex | Simple |

---

## 6. Auth Middleware Implementation

### JWT Middleware

```python
# app/api/middleware/jwt_auth.py

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.jwt import verify_token
from app.repositories.user_repository import UserRepository
from app.database import SessionLocal


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically authenticate requests using JWT.

    Extracts token from Authorization header and validates it.
    Adds user to request.state if authenticated.
    """

    # Routes that don't require authentication
    PUBLIC_ROUTES = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/health"
    ]

    async def dispatch(self, request: Request, call_next):
        """Process request and add user to state if authenticated."""

        # Check if route is public
        if any(request.url.path.startswith(route) for route in self.PUBLIC_ROUTES):
            return await call_next(request)

        # Extract token from Authorization header
        token = self.extract_token(request)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Verify token
        payload = verify_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Get user from database
        user_id = payload.get("sub")
        db = SessionLocal()

        try:
            user_repo = UserRepository(db)
            user = user_repo.get(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            # Add user to request state
            request.state.user = user
            request.state.user_id = str(user.uuid)

        finally:
            db.close()

        # Continue processing request
        response = await call_next(request)
        return response

    def extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        # Expected format: "Bearer <token>"
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]
```

### Session Middleware

```python
# app/api/middleware/session_auth.py

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.session import session_manager
from app.repositories.user_repository import UserRepository
from app.database import SessionLocal


class SessionAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically authenticate requests using sessions.

    Extracts session ID from cookie and validates it.
    Adds user to request.state if authenticated.
    """

    # Routes that don't require authentication
    PUBLIC_ROUTES = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/session/login",
        "/api/v1/auth/session/register",
        "/api/v1/health"
    ]

    async def dispatch(self, request: Request, call_next):
        """Process request and add user to state if authenticated."""

        # Check if route is public
        if any(request.url.path.startswith(route) for route in self.PUBLIC_ROUTES):
            return await call_next(request)

        # Extract session ID from cookie
        session_id = request.cookies.get("session_id")

        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing session cookie"
            )

        # Get session data
        session_data = session_manager.get_session(session_id)

        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )

        # Get user from database
        user_id = session_data.get("user_id")
        db = SessionLocal()

        try:
            user_repo = UserRepository(db)
            user = user_repo.get(user_id)

            if not user:
                # Clean up invalid session
                session_manager.delete_session(session_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            # Add user to request state
            request.state.user = user
            request.state.user_id = str(user.uuid)
            request.state.session_id = session_id

            # Refresh session
            session_manager.refresh_session(session_id)

        finally:
            db.close()

        # Continue processing request
        response = await call_next(request)
        return response
```

### Register Middleware in Main App

```python
# app/main.py

from app.api.middleware.jwt_auth import JWTAuthMiddleware
from app.api.middleware.session_auth import SessionAuthMiddleware

# Choose ONE authentication method

# Option 1: JWT Authentication
app.add_middleware(JWTAuthMiddleware)

# Option 2: Session Authentication
# app.add_middleware(SessionAuthMiddleware)
```

---

## 7. Using JWT and Sessions Together

### Can You Use Both?

**Yes!** You can use JWT and sessions together in the same application. This is called **hybrid authentication**.

### Why Use Both?

1. **Different Clients**: JWT for mobile apps, sessions for web
2. **Flexibility**: Let users choose authentication method
3. **Migration**: Transition from sessions to JWT gradually
4. **Security Layers**: Sessions for sensitive operations, JWT for regular API calls

### Implementation Strategy

```python
# app/api/middleware/hybrid_auth.py

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.jwt import verify_token
from app.core.session import session_manager
from app.repositories.user_repository import UserRepository
from app.database import SessionLocal


class HybridAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware supporting both JWT and session authentication.

    Tries JWT first (Authorization header), falls back to session (cookie).
    """

    PUBLIC_ROUTES = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth",  # All auth endpoints
        "/api/v1/health"
    ]

    async def dispatch(self, request: Request, call_next):
        """Authenticate using JWT or session."""

        # Check if route is public
        if any(request.url.path.startswith(route) for route in self.PUBLIC_ROUTES):
            return await call_next(request)

        user = None
        auth_method = None

        # Try JWT authentication first
        token = self.extract_token(request)
        if token:
            user, auth_method = await self.authenticate_jwt(token)

        # If JWT failed, try session
        if not user:
            session_id = request.cookies.get("session_id")
            if session_id:
                user, auth_method = await self.authenticate_session(session_id)

        # If both failed, reject request
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Add user and auth method to request state
        request.state.user = user
        request.state.user_id = str(user.uuid)
        request.state.auth_method = auth_method

        # Continue processing
        response = await call_next(request)
        return response

    def extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    async def authenticate_jwt(self, token: str) -> tuple:
        """Authenticate using JWT."""
        payload = verify_token(token)

        if not payload:
            return None, None

        user_id = payload.get("sub")
        db = SessionLocal()

        try:
            user_repo = UserRepository(db)
            user = user_repo.get(user_id)
            return user, "jwt"
        finally:
            db.close()

    async def authenticate_session(self, session_id: str) -> tuple:
        """Authenticate using session."""
        session_data = session_manager.get_session(session_id)

        if not session_data:
            return None, None

        user_id = session_data.get("user_id")
        db = SessionLocal()

        try:
            user_repo = UserRepository(db)
            user = user_repo.get(user_id)

            if user:
                # Refresh session
                session_manager.refresh_session(session_id)

            return user, "session"
        finally:
            db.close()
```

### Usage in Endpoints

```python
@router.get("/profile")
async def get_profile(request: Request):
    """
    Get profile - works with both JWT and session auth.

    Middleware automatically handles authentication.
    """
    user = request.state.user
    auth_method = request.state.auth_method

    return {
        "user": {
            "uuid": user.uuid,
            "email": user.email,
            "name": user.name
        },
        "authenticated_via": auth_method  # "jwt" or "session"
    }
```

---

## 8. Benefits of Each Approach

### JWT Benefits

#### ✅ Stateless
- No server-side storage needed
- Each request is self-contained
- Easy to scale horizontally

#### ✅ Portable
- Works across different domains
- Can be sent to third-party services
- Mobile-friendly

#### ✅ Performance
- No database lookup per request
- Faster authentication
- Reduced server load

#### ✅ Decentralized
- Microservices can verify independently
- No single point of failure
- Service-to-service auth

#### ✅ Standards-Based
- Industry standard (RFC 7519)
- Wide library support
- Well-documented

#### ✅ Custom Claims
- Store any data in token
- User roles, permissions, preferences
- Reduce database queries

### JWT Drawbacks

#### ❌ Cannot Revoke
- Token valid until expiration
- Need blacklist for revocation
- Security risk if compromised

#### ❌ Size
- ~1KB per token
- Sent with every request
- Bandwidth overhead

#### ❌ Complexity
- Harder to implement correctly
- Key management
- Token refresh logic

#### ❌ XSS Vulnerability
- If stored in localStorage
- Can be stolen by malicious scripts
- Need careful implementation

---

### Session Benefits

#### ✅ Revocable
- Can invalidate immediately
- Server has full control
- Better security

#### ✅ Smaller Payload
- Only session ID in cookie
- Reduces bandwidth
- Faster transmission

#### ✅ Flexible
- Can update session data anytime
- No need to re-issue token
- Dynamic permissions

#### ✅ Secure by Default
- HttpOnly cookies
- Protection against XSS
- CSRF tokens available

#### ✅ Simpler
- Easier to understand
- Framework support
- Less code to maintain

#### ✅ Better UX
- Automatic cookie management
- "Remember me" functionality
- Session persistence

### Session Drawbacks

#### ❌ Stateful
- Requires server-side storage
- Redis/database dependency
- Single point of failure

#### ❌ Scalability
- Need shared session store
- More complex infrastructure
- Higher server load

#### ❌ Cross-Domain Issues
- Cookies don't work across domains
- CORS complications
- Subdomain configuration needed

#### ❌ Mobile Apps
- Cookies harder to manage
- Platform-specific handling
- Less flexible

---

## 9. User Creation and Login Flow

### JWT Flow

#### Registration Flow

```
1. User submits registration form
   ↓
2. Server validates data
   ↓
3. Server hashes password
   ↓
4. Server creates user in database
   ↓
5. Server generates access + refresh tokens
   ↓
6. Server returns tokens to client
   ↓
7. Client stores tokens (localStorage/secure storage)
   ↓
8. Client includes token in future requests
```

**Code Example:**

```python
# Registration endpoint
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 1. Validate data (Pydantic does this automatically)

    # 2. Check if user exists
    user_repo = UserRepository(db)
    if user_repo.get_by_email(user_data.email):
        raise HTTPException(409, "Email already registered")

    # 3. Hash password
    hashed_password = hash_password(user_data.password)

    # 4. Create user
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password
    }
    new_user = user_repo.create(user_dict)

    # 5. Generate tokens
    access_token = create_access_token({"sub": str(new_user.uuid)})
    refresh_token = create_refresh_token({"sub": str(new_user.uuid)})

    # 6. Return tokens
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "uuid": new_user.uuid,
            "email": new_user.email,
            "name": new_user.name
        }
    }
```

**Client-side (JavaScript):**

```javascript
// Registration
async function register(email, name, password) {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, name, password })
  });

  const data = await response.json();

  // Store tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  return data.user;
}

// Making authenticated requests
async function getProfile() {
  const token = localStorage.getItem('access_token');

  const response = await fetch('/api/v1/users/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  return await response.json();
}

// Handle token refresh
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
}
```

#### Login Flow

```
1. User submits credentials
   ↓
2. Server validates email and password
   ↓
3. Server generates tokens
   ↓
4. Server returns tokens
   ↓
5. Client stores tokens
```

**Code Example:**

```python
@router.post("/login")
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 1. Get user
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(credentials.username)

    # 2. Verify password
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(401, "Invalid credentials")

    # 3. Generate tokens
    access_token = create_access_token({"sub": str(user.uuid)})
    refresh_token = create_refresh_token({"sub": str(user.uuid)})

    # 4. Return tokens
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
```

---

### Session Flow

#### Registration Flow

```
1. User submits registration form
   ↓
2. Server validates data
   ↓
3. Server hashes password
   ↓
4. Server creates user in database
   ↓
5. Server creates session in Redis
   ↓
6. Server sets session cookie
   ↓
7. Browser automatically sends cookie with future requests
```

**Code Example:**

```python
@router.post("/register")
async def register(
    user_data: UserCreate,
    response: Response,
    db: Session = Depends(get_db)
):
    # 1-4. Same as JWT (create user)
    user_repo = UserRepository(db)
    if user_repo.get_by_email(user_data.email):
        raise HTTPException(409, "Email already registered")

    hashed_password = hash_password(user_data.password)
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password
    }
    new_user = user_repo.create(user_dict)

    # 5. Create session
    session_id = session_manager.create_session(
        new_user.uuid,
        {"email": new_user.email, "name": new_user.name}
    )

    # 6. Set cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,  # Cannot be accessed by JavaScript
        secure=True,    # HTTPS only
        samesite="lax", # CSRF protection
        max_age=43200   # 12 hours
    )

    return {
        "message": "Registration successful",
        "user": {
            "uuid": new_user.uuid,
            "email": new_user.email,
            "name": new_user.name
        }
    }
```

**Client-side (JavaScript):**

```javascript
// Registration - much simpler!
async function register(email, name, password) {
  const response = await fetch('/api/v1/auth/session/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',  // Important: send cookies
    body: JSON.stringify({ email, name, password })
  });

  return await response.json();
  // Cookie is automatically stored by browser
}

// Making authenticated requests
async function getProfile() {
  const response = await fetch('/api/v1/users/me', {
    credentials: 'include'  // Send cookies automatically
  });

  return await response.json();
}

// Logout
async function logout() {
  await fetch('/api/v1/auth/session/logout', {
    method: 'POST',
    credentials: 'include'
  });
  // Cookie is automatically cleared by server
}
```

#### Login Flow

```
1. User submits credentials
   ↓
2. Server validates email and password
   ↓
3. Server creates session in Redis
   ↓
4. Server sets session cookie
```

**Code Example:**

```python
@router.post("/login")
async def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    # 1. Get user
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(credentials.email)

    # 2. Verify password
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(401, "Invalid credentials")

    # 3. Create session
    session_id = session_manager.create_session(
        user.uuid,
        {"email": user.email, "name": user.name}
    )

    # 4. Set cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=43200
    )

    return {"message": "Login successful"}
```

---

## 10. Token Repository and User Repository

### User Repository

```python
# app/repositories/user_repository.py

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations.

    Extends BaseRepository with user-specific queries.
    """

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            User instance or None if not found
        """
        return self.db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        ).first()

    def get_by_uuid(self, uuid: str) -> Optional[User]:
        """Get user by UUID (as string)."""
        try:
            user_uuid = UUID(uuid)
            return self.get(user_uuid)
        except (ValueError, AttributeError):
            return None

    def email_exists(self, email: str, exclude_user_id: Optional[UUID] = None) -> bool:
        """
        Check if email is already registered.

        Args:
            email: Email to check
            exclude_user_id: Exclude this user ID from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        query = self.db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        )

        if exclude_user_id:
            query = query.filter(User.uuid != exclude_user_id)

        return query.first() is not None

    def get_active_users(self) -> list[User]:
        """Get all active (non-deleted, is_active=True) users."""
        return self.db.query(User).filter(
            User.deleted_at.is_(None),
            User.is_active == True
        ).all()

    def update_last_login(self, user_id: UUID) -> Optional[User]:
        """Update user's last login timestamp."""
        from datetime import datetime, timezone

        return self.update(
            user_id,
            {"last_login": datetime.now(timezone.utc)}
        )

    def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """Deactivate a user (soft disable)."""
        return self.update(user_id, {"is_active": False})

    def activate_user(self, user_id: UUID) -> Optional[User]:
        """Activate a user."""
        return self.update(user_id, {"is_active": True})
```

### Token Repository (for JWT Blacklist)

```python
# app/repositories/token_repository.py

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models import TokenBlacklist
from app.repositories.base_repository import BaseRepository


class TokenRepository(BaseRepository[TokenBlacklist]):
    """
    Repository for managing JWT token blacklist.

    Used to revoke JWT tokens before their expiration.
    """

    def __init__(self, db: Session):
        super().__init__(TokenBlacklist, db)

    def blacklist_token(
        self,
        token: str,
        user_id: UUID,
        expires_at: datetime,
        reason: str = "logout"
    ) -> TokenBlacklist:
        """
        Add token to blacklist.

        Args:
            token: JWT token string
            user_id: User who owns the token
            expires_at: When the token would naturally expire
            reason: Reason for blacklisting

        Returns:
            TokenBlacklist instance
        """
        blacklist_entry = self.create({
            "token": token,
            "user_id": user_id,
            "expires_at": expires_at,
            "reason": reason,
            "blacklisted_at": datetime.now(timezone.utc)
        })

        return blacklist_entry

    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted.

        Args:
            token: JWT token to check

        Returns:
            True if blacklisted, False otherwise
        """
        blacklisted = self.db.query(TokenBlacklist).filter(
            TokenBlacklist.token == token,
            TokenBlacklist.expires_at > datetime.now(timezone.utc)
        ).first()

        return blacklisted is not None

    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from blacklist.

        Returns:
            Number of tokens removed
        """
        count = self.db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at <= datetime.now(timezone.utc)
        ).delete()

        self.db.commit()
        return count

    def blacklist_all_user_tokens(self, user_id: UUID) -> int:
        """
        Blacklist all active tokens for a user.

        This is used when user changes password or logs out from all devices.
        Note: This only works if you track all issued tokens.

        Args:
            user_id: User UUID

        Returns:
            Number of tokens blacklisted
        """
        # Get all active tokens for user from database
        # (Assumes you store issued tokens - see RefreshToken model)
        from app.models import RefreshToken

        active_tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at > datetime.now(timezone.utc),
            RefreshToken.revoked == False
        ).all()

        count = 0
        for token_record in active_tokens:
            self.blacklist_token(
                token=token_record.token,
                user_id=user_id,
                expires_at=token_record.expires_at,
                reason="logout_all_devices"
            )
            count += 1

        return count
```

### TokenBlacklist Model

```python
# app/models/token_blacklist.py

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import BaseModel


class TokenBlacklist(BaseModel):
    """
    Model for blacklisted JWT tokens.

    Used to revoke tokens before their natural expiration.
    """

    __tablename__ = "token_blacklist"

    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    blacklisted_at = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String, nullable=True)  # "logout", "password_change", etc.
```

### RefreshToken Model (Optional - for tracking)

```python
# app/models/refresh_token.py

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class RefreshToken(BaseModel):
    """
    Model for tracking issued refresh tokens.

    Allows revoking specific tokens or all user tokens.
    """

    __tablename__ = "refresh_tokens"

    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
```

---

## 11. What is OAuth?

### Definition

**OAuth 2.0** is an authorization framework that enables third-party applications to obtain limited access to user accounts on an HTTP service (like Google, GitHub, Facebook).

### Key Concept

OAuth is about **authorization**, not authentication:
- **Authentication**: "Who are you?" (Login)
- **Authorization**: "What can you access?" (Permissions)

### How OAuth Works

```
1. User clicks "Login with Google"
   ↓
2. Redirect to Google's login page
   ↓
3. User logs in and grants permissions
   ↓
4. Google redirects back with authorization code
   ↓
5. Your server exchanges code for access token
   ↓
6. Use access token to get user info from Google
   ↓
7. Create/login user in your database
```

### OAuth Roles

1. **Resource Owner**: The user
2. **Client**: Your application
3. **Authorization Server**: Google/GitHub/etc (handles login)
4. **Resource Server**: Google/GitHub/etc (provides user data)

### OAuth Flow Diagram

```
┌──────────┐                                       ┌────────────────┐
│          │  1. Click "Login with Google"         │                │
│  User    │───────────────────────────────────────>│  Your App      │
│          │                                       │  (Client)      │
└──────────┘                                       └────────────────┘
     │                                                     │
     │ 2. Redirect to Google                              │
     │<───────────────────────────────────────────────────┘
     │
     v
┌────────────────┐
│   Google       │  3. User logs in
│   (OAuth       │     and grants permissions
│   Provider)    │
└────────────────┘
     │
     │ 4. Redirect back with code
     │
     v
┌────────────────┐
│  Your App      │  5. Exchange code for token
│                │────────────────────────────────>┌────────────────┐
│                │<────────────────────────────────│   Google       │
│                │  6. Access token                │   API          │
│                │                                 └────────────────┘
│                │  7. Get user info
│                │────────────────────────────────>┌────────────────┐
│                │<────────────────────────────────│   Google       │
└────────────────┘  8. User data                   │   User Info    │
                                                   └────────────────┘
```

---

## 12. How to Implement OAuth

### Step 1: Register Your Application

**With Google:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs

You'll get:
- **Client ID**: `123456789.apps.googleusercontent.com`
- **Client Secret**: `secret-key-here`

### Step 2: Install Dependencies

```bash
pip install authlib httpx
```

### Step 3: Configuration

```python
# app/core/config.py

class Settings(BaseSettings):
    # OAuth Configuration
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/github/callback"

settings = Settings()
```

### Step 4: OAuth Client Setup

```python
# app/core/oauth.py

from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

oauth = OAuth()

# Google OAuth
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# GitHub OAuth
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)
```

### Step 5: OAuth Endpoints

```python
# app/api/v1/routes/oauth.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.oauth import oauth
from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import hash_password
from app.database import get_db
from app.repositories.user_repository import UserRepository
import secrets

router = APIRouter(prefix="/auth", tags=["OAuth"])


@router.get("/google/login")
async def google_login(request: Request):
    """
    Initiate Google OAuth login.

    Redirects user to Google's login page.
    """
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.

    Exchange authorization code for access token and get user info.
    """
    # Get access token
    token = await oauth.google.authorize_access_token(request)

    # Get user info from Google
    user_info = token.get('userinfo')

    if not user_info:
        # Fallback: fetch user info manually
        resp = await oauth.google.get('userinfo', token=token)
        user_info = resp.json()

    # Extract user data
    email = user_info.get('email')
    name = user_info.get('name')
    google_id = user_info.get('sub')  # Google's user ID
    picture = user_info.get('picture')

    # Get or create user
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(email)

    if not user:
        # Create new user
        random_password = hash_password(secrets.token_urlsafe(32))
        user_data = {
            "email": email,
            "name": name,
            "password": random_password,  # Random password (OAuth users don't need it)
            "google_id": google_id,
            "avatar_url": picture,
            "email_verified": True  # Google verified it
        }
        user = user_repo.create(user_data)
    else:
        # Update existing user with Google info
        update_data = {}
        if not user.google_id:
            update_data["google_id"] = google_id
        if not user.avatar_url and picture:
            update_data["avatar_url"] = picture

        if update_data:
            user = user_repo.update(user.uuid, update_data)

    # Create JWT tokens
    access_token = create_access_token({"sub": str(user.uuid)})
    refresh_token = create_refresh_token({"sub": str(user.uuid)})

    # Redirect to frontend with tokens
    # In production, redirect to your frontend app
    frontend_url = f"http://localhost:3000/auth/callback?access_token={access_token}&refresh_token={refresh_token}"

    return RedirectResponse(url=frontend_url)


@router.get("/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth login."""
    redirect_uri = request.url_for('github_callback')
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback."""
    # Get access token
    token = await oauth.github.authorize_access_token(request)

    # Get user info from GitHub
    resp = await oauth.github.get('user', token=token)
    user_info = resp.json()

    # Get user emails (GitHub may not return email in user endpoint)
    resp_emails = await oauth.github.get('user/emails', token=token)
    emails = resp_emails.json()

    # Find primary email
    primary_email = next(
        (email['email'] for email in emails if email['primary']),
        emails[0]['email'] if emails else None
    )

    if not primary_email:
        raise HTTPException(400, "No email found in GitHub account")

    # Extract data
    github_id = user_info.get('id')
    name = user_info.get('name') or user_info.get('login')
    avatar = user_info.get('avatar_url')

    # Get or create user (same logic as Google)
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(primary_email)

    if not user:
        random_password = hash_password(secrets.token_urlsafe(32))
        user_data = {
            "email": primary_email,
            "name": name,
            "password": random_password,
            "github_id": str(github_id),
            "avatar_url": avatar,
            "email_verified": True
        }
        user = user_repo.create(user_data)
    else:
        update_data = {}
        if not user.github_id:
            update_data["github_id"] = str(github_id)
        if not user.avatar_url and avatar:
            update_data["avatar_url"] = avatar

        if update_data:
            user = user_repo.update(user.uuid, update_data)

    # Create tokens
    access_token = create_access_token({"sub": str(user.uuid)})
    refresh_token = create_refresh_token({"sub": str(user.uuid)})

    # Redirect to frontend
    frontend_url = f"http://localhost:3000/auth/callback?access_token={access_token}&refresh_token={refresh_token}"

    return RedirectResponse(url=frontend_url)
```

### Step 6: User Model Updates

```python
# Add to User model

class User(BaseModel):
    __tablename__ = "users"

    # ... existing fields ...

    # OAuth fields
    google_id = Column(String, unique=True, nullable=True, index=True)
    github_id = Column(String, unique=True, nullable=True, index=True)
    facebook_id = Column(String, unique=True, nullable=True, index=True)
    avatar_url = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False)
```

### Step 7: Frontend Integration

```javascript
// React/Vue/Angular example

function LoginPage() {
  const handleGoogleLogin = () => {
    // Redirect to backend OAuth endpoint
    window.location.href = '/api/v1/auth/google/login';
  };

  const handleGitHubLogin = () => {
    window.location.href = '/api/v1/auth/github/login';
  };

  return (
    <div>
      <button onClick={handleGoogleLogin}>
        Login with Google
      </button>
      <button onClick={handleGitHubLogin}>
        Login with GitHub
      </button>
    </div>
  );
}

// Callback page to receive tokens
function AuthCallback() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    if (accessToken) {
      // Store tokens
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);

      // Redirect to dashboard
      window.location.href = '/dashboard';
    }
  }, []);

  return <div>Logging in...</div>;
}
```

---

## 13. Security Best Practices

### General Security

#### ✅ Always Use HTTPS
```python
# Force HTTPS in production
if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)
```

#### ✅ Use Strong Secrets
```python
# Generate secure secret key
import secrets
SECRET_KEY = secrets.token_urlsafe(32)
```

#### ✅ Rate Limiting
```python
# Prevent brute force attacks
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # Max 5 attempts per minute
async def login(...):
    ...
```

### JWT Security

#### ✅ Short Expiration Times
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days
```

#### ✅ Use Strong Algorithms
```python
ALGORITHM = "RS256"  # RSA, more secure than HS256
# or
ALGORITHM = "HS256"  # HMAC, simpler but needs strong secret
```

#### ✅ Validate All Claims
```python
def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,  # Check expiration
                "verify_nbf": True,  # Check not before
                "verify_iat": True,  # Check issued at
                "verify_aud": True,  # Check audience
            }
        )
        return payload
    except JWTError:
        return None
```

#### ❌ Don't Store Sensitive Data
```python
# ❌ BAD
payload = {
    "sub": user_id,
    "password": user.password,  # NEVER!
    "ssn": user.ssn              # NEVER!
}

# ✅ GOOD
payload = {
    "sub": user_id,
    "email": user.email,
    "role": user.role
}
```

#### ✅ Implement Token Refresh
```python
# Use refresh tokens to get new access tokens
# Access token: short-lived (15 min)
# Refresh token: long-lived (7 days)
```

### Session Security

#### ✅ HttpOnly Cookies
```python
response.set_cookie(
    key="session_id",
    value=session_id,
    httponly=True,  # Prevents JavaScript access (XSS protection)
    secure=True,    # HTTPS only
    samesite="lax"  # CSRF protection
)
```

#### ✅ Regenerate Session ID
```python
# After login, create new session ID
# After privilege escalation, create new session ID

def elevate_privileges(user_id: UUID):
    old_session_id = current_session_id

    # Create new session with elevated privileges
    new_session_id = session_manager.create_session(user_id, {
        "elevated": True
    })

    # Delete old session
    session_manager.delete_session(old_session_id)

    return new_session_id
```

#### ✅ Store IP and User Agent
```python
# Detect session hijacking
session_data = {
    "user_id": user_id,
    "ip_address": request.client.host,
    "user_agent": request.headers.get("user-agent"),
    "created_at": datetime.now()
}

# On each request, verify IP hasn't changed drastically
current_ip = request.client.host
session_ip = session_data.get("ip_address")

if current_ip != session_ip:
    # Potentially hijacked - require re-authentication
    logger.warning(f"IP mismatch: {session_ip} -> {current_ip}")
```

### Password Security

#### ✅ Strong Hashing
```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost factor (higher = slower but more secure)
)
```

#### ✅ Password Requirements
```python
from pydantic import Field, validator

class UserCreate(BaseModel):
    password: str = Field(min_length=8, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in '!@#$%^&*()_+-=' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v
```

#### ✅ Password Change Flow
```python
@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify old password
    if not verify_password(old_password, current_user.password):
        raise HTTPException(400, "Incorrect old password")

    # Hash new password
    hashed = hash_password(new_password)

    # Update user
    user_repo = UserRepository(db)
    user_repo.update(current_user.uuid, {"password": hashed})

    # Invalidate all existing sessions/tokens
    # Option 1: Blacklist all tokens (JWT)
    token_repo = TokenRepository(db)
    token_repo.blacklist_all_user_tokens(current_user.uuid)

    # Option 2: Delete all sessions (Session-based)
    session_manager.delete_all_user_sessions(current_user.uuid)

    return {"message": "Password changed successfully"}
```

### OAuth Security

#### ✅ Validate State Parameter
```python
import secrets

# Generate state before redirect
state = secrets.token_urlsafe(32)
session['oauth_state'] = state

# Verify state in callback
if request.args.get('state') != session.get('oauth_state'):
    raise HTTPException(400, "Invalid state parameter")
```

#### ✅ Use PKCE (for mobile apps)
```python
# Proof Key for Code Exchange
# Protects against authorization code interception

import hashlib
import base64

# Generate code verifier
code_verifier = secrets.token_urlsafe(32)

# Generate code challenge
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip('=')

# Send code_challenge with authorization request
# Send code_verifier with token exchange request
```

---

## 14. Common Pitfalls and Solutions

### Pitfall 1: Storing JWT in localStorage

**Problem:**
```javascript
// ❌ Vulnerable to XSS attacks
localStorage.setItem('token', jwt);
```

**Solution:**
```javascript
// ✅ Store in HttpOnly cookie (set by server)
// OR
// ✅ Store in memory (lost on refresh, use refresh token)

// In-memory storage
let accessToken = null;

function setToken(token) {
  accessToken = token;
}

function getToken() {
  return accessToken;
}

// Use refresh token (in HttpOnly cookie) to get new access token on page load
```

---

### Pitfall 2: No Token Expiration

**Problem:**
```python
# ❌ Token never expires
token = create_token({"sub": user_id})  # No exp claim
```

**Solution:**
```python
# ✅ Always set expiration
token = create_access_token(
    {"sub": user_id},
    expires_delta=timedelta(minutes=15)
)
```

---

### Pitfall 3: Not Validating Token on Every Request

**Problem:**
```python
# ❌ Trusting token without validation
payload = jwt.decode(token, verify=False)  # DANGEROUS!
```

**Solution:**
```python
# ✅ Always verify signature and claims
try:
    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"verify_signature": True, "verify_exp": True}
    )
except JWTError:
    raise HTTPException(401, "Invalid token")
```

---

### Pitfall 4: Weak Passwords

**Problem:**
```python
# ❌ Accepting weak passwords
password = "123456"  # Accepted!
```

**Solution:**
```python
# ✅ Enforce strong password policy
class UserCreate(BaseModel):
    password: str = Field(min_length=8)

    @validator('password')
    def validate_password_strength(cls, v):
        # Check for uppercase, lowercase, digit, special char
        # Use libraries like `password-validator`
        return v
```

---

### Pitfall 5: Session Fixation

**Problem:**
```python
# ❌ Reusing session ID after login
# Attacker sets session ID before login
# After login, same session ID has elevated privileges
```

**Solution:**
```python
# ✅ Regenerate session ID on login
def login(user_id):
    # Delete old session
    old_session = request.cookies.get('session_id')
    if old_session:
        session_manager.delete_session(old_session)

    # Create new session
    new_session_id = session_manager.create_session(user_id, {})

    # Set new cookie
    response.set_cookie('session_id', new_session_id)
```

---

### Pitfall 6: Not Handling Concurrent Logins

**Problem:**
```python
# ❌ User can't login on multiple devices
# OR
# ❌ Old sessions never expire
```

**Solution:**
```python
# ✅ Option 1: Allow multiple sessions (track all)
def login(user_id):
    # Create new session (don't delete old ones)
    session_id = session_manager.create_session(user_id, {
        "device": "Chrome on Windows"
    })

# ✅ Option 2: Single session only (logout other devices)
def login(user_id):
    # Delete all existing sessions
    session_manager.delete_all_user_sessions(user_id)

    # Create new session
    session_id = session_manager.create_session(user_id, {})

# ✅ Option 3: Limit number of sessions
MAX_SESSIONS = 5

def login(user_id):
    sessions = session_manager.get_all_user_sessions(user_id)

    if len(sessions) >= MAX_SESSIONS:
        # Delete oldest session
        oldest = min(sessions, key=lambda s: s['created_at'])
        session_manager.delete_session(oldest['session_id'])

    # Create new session
    session_id = session_manager.create_session(user_id, {})
```

---

### Pitfall 7: Exposing Sensitive Info in JWT

**Problem:**
```python
# ❌ Including sensitive data in JWT
token = create_token({
    "sub": user_id,
    "email": user.email,
    "credit_card": user.credit_card,  # NEVER!
    "password": user.password          # NEVER!
})
```

**Solution:**
```python
# ✅ Only include minimal, non-sensitive data
token = create_token({
    "sub": str(user_id),
    "email": user.email,
    "role": user.role,
    "type": "access"
})

# ✅ Fetch sensitive data from database when needed
user = get_user_from_database(user_id)
```

---

### Pitfall 8: CORS Misconfiguration

**Problem:**
```python
# ❌ Allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DANGEROUS!
    allow_credentials=True
)
```

**Solution:**
```python
# ✅ Whitelist specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myapp.com",
        "https://www.myapp.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)
```

---

## Conclusion

This guide covered:

✅ **JWT**: Stateless, portable, scalable authentication
✅ **Sessions**: Stateful, revocable, secure authentication
✅ **OAuth**: Third-party authentication (Google, GitHub, etc.)
✅ **Implementation**: Complete code examples for all approaches
✅ **Security**: Best practices and common pitfalls
✅ **Repositories**: User and token management patterns

### Quick Decision Guide

**Choose JWT if:**
- Building a mobile app
- Need microservices
- Want stateless authentication
- API-only backend

**Choose Sessions if:**
- Traditional web app
- Need immediate revocation
- Simpler implementation preferred
- Security-critical application

**Use OAuth if:**
- Want social login
- Reduce registration friction
- Leverage existing user accounts
- Need delegated authorization

**Use Hybrid if:**
- Support multiple clients
- Want flexibility
- Gradual migration
- Different security levels

---

### Additional Resources

- [JWT.io](https://jwt.io/) - JWT debugger and documentation
- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749) - Official OAuth spec
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)

Happy coding! 🚀
