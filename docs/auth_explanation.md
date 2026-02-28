# Authentication Deep Dive: JWT, Sessions & Auth Middleware

## Table of Contents
1. [What is JWT?](#1-what-is-jwt)
2. [JWT vs Session-Based Authentication](#2-jwt-vs-session-based-authentication)
3. [Auth Middleware Explained](#3-auth-middleware-explained)
4. [Implementation Flow](#4-implementation-flow)

---

## 1. What is JWT?

### 1.1 Definition

**JWT (JSON Web Token)** is an open standard (RFC 7519) that defines a compact and self-contained way to securely transmit information between parties as a JSON object. This information can be verified and trusted because it is digitally signed.

### 1.2 JWT Structure

A JWT consists of three parts separated by dots (`.`):

```
xxxxx.yyyyy.zzzzz
  │      │      │
  │      │      └── Signature
  │      └── Payload
  └── Header
```

#### Part 1: Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```
- **alg**: The signing algorithm (e.g., HS256, RS256)
- **typ**: The type of token

#### Part 2: Payload (Claims)
```json
{
  "sub": "user-uuid-123",
  "email": "user@example.com",
  "role": "USER",
  "iat": 1704067200,
  "exp": 1704070800
}
```

**Standard Claims:**
| Claim | Name | Description |
|-------|------|-------------|
| `sub` | Subject | The user identifier (usually user ID or UUID) |
| `iat` | Issued At | Timestamp when the token was created |
| `exp` | Expiration | Timestamp when the token expires |
| `nbf` | Not Before | Token is not valid before this time |
| `iss` | Issuer | Who issued the token (your API) |
| `aud` | Audience | Who the token is intended for |

**Custom Claims:**
You can add any custom data relevant to your application:
- `role`: User role (USER, ADMIN)
- `email`: User email
- `permissions`: Array of permissions

#### Part 3: Signature
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret_key
)
```

The signature ensures:
1. The token hasn't been tampered with
2. The token was issued by a trusted source

### 1.3 How JWT Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            JWT AUTHENTICATION FLOW                          │
└─────────────────────────────────────────────────────────────────────────────┘

   CLIENT                                                     SERVER
     │                                                           │
     │  1. POST /login {email, password}                         │
     │ ─────────────────────────────────────────────────────────>│
     │                                                           │
     │                              2. Validate credentials      │
     │                              3. Generate JWT tokens       │
     │                                                           │
     │  4. Response: {access_token, refresh_token}               │
     │ <─────────────────────────────────────────────────────────│
     │                                                           │
     │  5. Store tokens (memory/localStorage)                    │
     │                                                           │
     │  6. GET /api/posts                                        │
     │     Header: Authorization: Bearer <access_token>          │
     │ ─────────────────────────────────────────────────────────>│
     │                                                           │
     │                              7. Verify JWT signature      │
     │                              8. Check expiration          │
     │                              9. Extract user from payload │
     │                                                           │
     │  10. Response: {posts data}                               │
     │ <─────────────────────────────────────────────────────────│
     │                                                           │
```

### 1.4 Token Types

#### Access Token
- **Purpose**: Authenticate API requests
- **Lifetime**: Short (15-30 minutes)
- **Storage**: Memory (preferred) or localStorage
- **Contains**: User ID, role, permissions

#### Refresh Token
- **Purpose**: Obtain new access tokens without re-login
- **Lifetime**: Long (7-30 days)
- **Storage**: HTTP-only cookie (most secure) or secure storage
- **Contains**: Minimal data (just user ID and token ID)

```
┌────────────────────────────────────────────────────────────────┐
│                    TOKEN REFRESH FLOW                          │
└────────────────────────────────────────────────────────────────┘

   CLIENT                                              SERVER
     │                                                    │
     │  Access token expired!                             │
     │                                                    │
     │  POST /auth/refresh                                │
     │  Body: {refresh_token}                             │
     │ ──────────────────────────────────────────────────>│
     │                                                    │
     │                         Validate refresh token     │
     │                         Check if revoked           │
     │                         Generate new access token  │
     │                                                    │
     │  Response: {new_access_token}                      │
     │ <──────────────────────────────────────────────────│
     │                                                    │
```

### 1.5 JWT Security Best Practices

| Practice | Description |
|----------|-------------|
| **Use HTTPS** | Always transmit tokens over encrypted connections |
| **Short expiration** | Access tokens should expire in 15-30 minutes |
| **Secure storage** | Never store tokens in localStorage for sensitive apps |
| **Token rotation** | Issue new refresh tokens on each refresh |
| **Revocation list** | Store revoked tokens in database for validation |
| **Strong secrets** | Use cryptographically secure random secrets (256+ bits) |
| **Validate all claims** | Check `exp`, `iat`, `iss`, `aud` on every request |

---

## 2. JWT vs Session-Based Authentication

### 2.1 Session-Based Authentication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SESSION-BASED AUTHENTICATION                         │
└─────────────────────────────────────────────────────────────────────────────┘

   CLIENT                           SERVER                      DATABASE
     │                                │                            │
     │  POST /login                   │                            │
     │ ──────────────────────────────>│                            │
     │                                │                            │
     │                                │  Create session            │
     │                                │ ──────────────────────────>│
     │                                │                            │
     │                                │  Store: session_id -> user │
     │                                │ <──────────────────────────│
     │                                │                            │
     │  Set-Cookie: session_id=abc123 │                            │
     │ <──────────────────────────────│                            │
     │                                │                            │
     │  GET /api/posts                │                            │
     │  Cookie: session_id=abc123     │                            │
     │ ──────────────────────────────>│                            │
     │                                │                            │
     │                                │  Lookup session            │
     │                                │ ──────────────────────────>│
     │                                │                            │
     │                                │  Return user data          │
     │                                │ <──────────────────────────│
     │                                │                            │
     │  Response: {posts}             │                            │
     │ <──────────────────────────────│                            │
```

**How it works:**
1. User logs in with credentials
2. Server creates a session and stores it (memory, Redis, database)
3. Server sends session ID as a cookie
4. Client sends cookie with every request
5. Server looks up session to identify user

### 2.2 Comparison Table

| Aspect | Session-Based | JWT-Based |
|--------|---------------|-----------|
| **State** | Stateful (server stores sessions) | Stateless (token contains all info) |
| **Storage** | Server-side (memory/Redis/DB) | Client-side (token) |
| **Scalability** | Harder (need shared session store) | Easier (no shared state) |
| **Database lookup** | Every request | Only on token refresh |
| **Revocation** | Easy (delete session) | Harder (need blocklist) |
| **Size** | Small cookie (~32 bytes) | Larger token (~500+ bytes) |
| **Mobile apps** | Complex (cookie handling) | Simple (token in header) |
| **Microservices** | Complex (session sharing) | Simple (token validation) |
| **CSRF protection** | Required | Not needed (if using headers) |
| **XSS vulnerability** | Less (HTTP-only cookies) | More (if stored in localStorage) |

### 2.3 When to Use Each

#### Use Session-Based When:
- Traditional web applications (server-rendered)
- Single server or easy session sharing
- Need simple, immediate revocation
- High security requirements
- Browser-only clients

#### Use JWT When:
- RESTful APIs
- Mobile applications
- Microservices architecture
- Need horizontal scaling
- Multiple client types (web, mobile, IoT)
- Third-party API access

### 2.4 Hybrid Approach (This Project)

This blog API uses a **hybrid approach**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      HYBRID APPROACH                            │
│                                                                 │
│   JWT for authentication + Database for token management        │
└─────────────────────────────────────────────────────────────────┘

Benefits:
├── Stateless verification (JWT signature)
├── Token revocation (database lookup)
├── Token tracking (audit trail)
├── Multiple device management
└── Security (revoke compromised tokens)

Token Table:
┌──────────────────────────────────────────────────────────────┐
│ uuid │ user_uuid │ token │ type │ expires_at │ revoked │ ip │
├──────────────────────────────────────────────────────────────┤
│ ...  │ ...       │ ...   │ ...  │ ...        │ false   │ ...│
└──────────────────────────────────────────────────────────────┘
```

**Flow:**
1. Generate JWT with user claims
2. Store token metadata in database (for revocation)
3. On each request: verify JWT signature first (fast)
4. If sensitive operation: check database for revocation (secure)

---

## 3. Auth Middleware Explained

### 3.1 What is Middleware?

Middleware is code that runs **between** receiving a request and executing the route handler. It can:
- Inspect/modify requests
- Inspect/modify responses
- Terminate requests early
- Pass control to the next handler

```
┌─────────────────────────────────────────────────────────────────┐
│                      REQUEST LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────┘

  HTTP Request
       │
       ▼
┌─────────────────┐
│   Middleware 1  │  (Logging)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Middleware 2  │  (CORS)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Middleware 3  │  (Auth) ◄── Can reject request here
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Middleware 4  │  (Rate Limiting)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Route Handler  │  (Your endpoint code)
└────────┬────────┘
         │
         ▼
  HTTP Response
```

### 3.2 Auth Middleware Purpose

The Auth Middleware is responsible for:

1. **Extracting** the token from the request
2. **Validating** the token (signature, expiration)
3. **Identifying** the user from the token
4. **Attaching** user info to the request
5. **Rejecting** unauthorized requests

### 3.3 Auth Middleware Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTH MIDDLEWARE FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │ Incoming Request│
                              └────────┬────────┘
                                       │
                                       ▼
                         ┌─────────────────────────┐
                         │ Extract Authorization   │
                         │ Header                  │
                         └────────────┬────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                          ▼                       ▼
                    ┌──────────┐           ┌──────────────┐
                    │ Missing  │           │ Header Found │
                    └────┬─────┘           └──────┬───────┘
                         │                        │
                         ▼                        ▼
              ┌─────────────────────┐   ┌─────────────────────┐
              │ Is route public?    │   │ Validate "Bearer"   │
              └──────────┬──────────┘   │ prefix              │
                         │              └──────────┬──────────┘
               ┌─────────┴─────────┐               │
               │                   │               ▼
               ▼                   ▼     ┌─────────────────────┐
         ┌──────────┐        ┌──────────┐│ Extract token       │
         │   Yes    │        │    No    ││ (remove "Bearer ")  │
         └────┬─────┘        └────┬─────┘└──────────┬──────────┘
              │                   │                 │
              ▼                   ▼                 ▼
        ┌───────────┐      ┌───────────┐  ┌─────────────────────┐
        │ Continue  │      │ Return    │  │ Decode JWT          │
        │ to route  │      │ 401 Error │  │ (verify signature)  │
        └───────────┘      └───────────┘  └──────────┬──────────┘
                                                     │
                                          ┌──────────┴──────────┐
                                          │                     │
                                          ▼                     ▼
                                    ┌──────────┐          ┌──────────┐
                                    │ Invalid  │          │  Valid   │
                                    └────┬─────┘          └────┬─────┘
                                         │                     │
                                         ▼                     ▼
                                  ┌───────────┐       ┌─────────────────┐
                                  │ Return    │       │ Check expiration│
                                  │ 401 Error │       └────────┬────────┘
                                  └───────────┘                │
                                                    ┌──────────┴──────────┐
                                                    │                     │
                                                    ▼                     ▼
                                              ┌──────────┐          ┌──────────┐
                                              │ Expired  │          │  Valid   │
                                              └────┬─────┘          └────┬─────┘
                                                   │                     │
                                                   ▼                     ▼
                                            ┌───────────┐       ┌─────────────────┐
                                            │ Return    │       │ Check revocation│
                                            │ 401 Error │       │ (database)      │
                                            └───────────┘       └────────┬────────┘
                                                                         │
                                                              ┌──────────┴──────────┐
                                                              │                     │
                                                              ▼                     ▼
                                                        ┌──────────┐          ┌──────────┐
                                                        │ Revoked  │          │  Valid   │
                                                        └────┬─────┘          └────┬─────┘
                                                             │                     │
                                                             ▼                     ▼
                                                      ┌───────────┐       ┌─────────────────┐
                                                      │ Return    │       │ Attach user to  │
                                                      │ 401 Error │       │ request.state   │
                                                      └───────────┘       └────────┬────────┘
                                                                                   │
                                                                                   ▼
                                                                          ┌─────────────────┐
                                                                          │ Continue to     │
                                                                          │ route handler   │
                                                                          └─────────────────┘
```

### 3.4 Implementation Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTH MIDDLEWARE COMPONENTS                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      AuthMiddleware Class                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Dependencies:                                                  │
│  ├── TokenService (for token validation)                        │
│  └── Settings (for configuration)                               │
│                                                                 │
│  Properties:                                                    │
│  ├── public_paths: List[str]  (routes that don't need auth)     │
│  └── exempt_methods: List[str] (e.g., OPTIONS for CORS)         │
│                                                                 │
│  Methods:                                                       │
│  ├── __call__(request, call_next)  (main middleware function)   │
│  ├── _extract_token(request) -> str | None                      │
│  ├── _is_public_path(path) -> bool                              │
│  └── _get_current_user(token) -> User                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 Public vs Protected Routes

```python
# Public paths (no authentication required)
PUBLIC_PATHS = [
    "/",
    "/health",
    "/health/ping",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/docs",
    "/redoc",
    "/openapi.json",
]

# Protected paths (authentication required)
# Everything else requires a valid JWT token
```

### 3.6 Error Responses

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `MISSING_TOKEN` | No Authorization header provided |
| 401 | `INVALID_TOKEN_FORMAT` | Header doesn't start with "Bearer " |
| 401 | `INVALID_TOKEN` | JWT signature verification failed |
| 401 | `EXPIRED_TOKEN` | Token has expired |
| 401 | `REVOKED_TOKEN` | Token has been revoked |
| 403 | `PERMISSION_DENIED` | User lacks required permissions |

### 3.7 FastAPI Dependency Alternative

Instead of middleware, FastAPI also supports **dependency injection** for auth:

```
┌─────────────────────────────────────────────────────────────────┐
│              MIDDLEWARE vs DEPENDENCY INJECTION                 │
└─────────────────────────────────────────────────────────────────┘

MIDDLEWARE APPROACH:
────────────────────
- Runs on EVERY request
- Global authentication
- Good for: APIs where most routes are protected

DEPENDENCY APPROACH:
────────────────────
- Runs only on specific routes
- Granular control
- Good for: Mixed public/private APIs

Example:
┌────────────────────────────────────────────────────────────────┐
│  @router.get("/posts")                                         │
│  def get_posts(                                                │
│      current_user: User = Depends(get_current_user)  # Auth    │
│  ):                                                            │
│      return posts                                              │
│                                                                │
│  @router.get("/public/posts")                                  │
│  def get_public_posts():  # No auth dependency                 │
│      return public_posts                                       │
└────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation Flow

### 4.1 Implementation Order

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION ORDER                         │
└─────────────────────────────────────────────────────────────────┘

Step 1: Token Service
─────────────────────
├── create_access_token(user_data) -> str
├── create_refresh_token(user_data) -> str
├── decode_token(token) -> dict
├── verify_token(token) -> bool
└── revoke_token(token_uuid) -> bool

                    │
                    ▼

Step 2: Auth Service
────────────────────
├── register(user_data) -> User
├── login(email, password) -> TokenPair
├── refresh_tokens(refresh_token) -> TokenPair
├── logout(token) -> bool
└── get_current_user(token) -> User

                    │
                    ▼

Step 3: Auth Middleware
───────────────────────
├── Extract token from header
├── Validate token (using TokenService)
├── Attach user to request
└── Handle errors

                    │
                    ▼

Step 4: Auth Routes
───────────────────
├── POST /auth/register
├── POST /auth/login
├── POST /auth/refresh
├── POST /auth/logout
└── GET  /auth/me
```

### 4.2 Dependencies Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPENDENCY GRAPH                             │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   Auth Routes   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
     │Auth Service │ │Auth Middle- │ │ Rate Limiter    │
     │             │ │   ware      │ │   Middleware    │
     └──────┬──────┘ └──────┬──────┘ └─────────────────┘
            │               │
            │    ┌──────────┘
            │    │
            ▼    ▼
     ┌─────────────────┐
     │  Token Service  │
     └────────┬────────┘
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
┌──────────┐    ┌─────────────┐
│  User    │    │   Token     │
│Repository│    │ Repository  │
└────┬─────┘    └──────┬──────┘
     │                 │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │    Database     │
     └─────────────────┘
```

### 4.3 Request Flow Example

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE REQUEST FLOW EXAMPLE                            │
│                    GET /api/v1/posts (Protected Route)                      │
└─────────────────────────────────────────────────────────────────────────────┘

  Client                                                              Server
    │                                                                    │
    │  GET /api/v1/posts                                                 │
    │  Authorization: Bearer eyJhbGciOiJIUzI1NiIs...                     │
    │ ──────────────────────────────────────────────────────────────────>│
    │                                                                    │
    │                                         ┌──────────────────────────┤
    │                                         │ 1. CORS Middleware       │
    │                                         │    - Check origin        │
    │                                         │    - Add CORS headers    │
    │                                         └──────────────────────────┤
    │                                                                    │
    │                                         ┌──────────────────────────┤
    │                                         │ 2. Auth Middleware       │
    │                                         │    - Extract token       │
    │                                         │    - Verify signature    │
    │                                         │    - Check expiration    │
    │                                         │    - Load user           │
    │                                         │    - Attach to request   │
    │                                         └──────────────────────────┤
    │                                                                    │
    │                                         ┌──────────────────────────┤
    │                                         │ 3. Rate Limit Middleware │
    │                                         │    - Check request count │
    │                                         │    - Update counter      │
    │                                         └──────────────────────────┤
    │                                                                    │
    │                                         ┌──────────────────────────┤
    │                                         │ 4. Route Handler         │
    │                                         │    - posts_router.get()  │
    │                                         │    - Call PostService    │
    │                                         │    - Return posts        │
    │                                         └──────────────────────────┤
    │                                                                    │
    │  200 OK                                                            │
    │  {                                                                 │
    │    "data": [...posts...],                                          │
    │    "pagination": {...}                                             │
    │  }                                                                 │
    │ <──────────────────────────────────────────────────────────────────│
    │                                                                    │
```

---

## Summary

| Component | Purpose | Depends On |
|-----------|---------|------------|
| **JWT** | Encode user identity in a signed token | Secret key |
| **Token Service** | Create, validate, revoke tokens | Token Repository |
| **Auth Service** | Handle login, register, refresh | User Repository, Token Service |
| **Auth Middleware** | Protect routes, extract user | Token Service |

**Key Takeaways:**
1. JWT provides stateless authentication but this project uses a hybrid approach with database storage for revocation
2. Auth Middleware runs before every request to protected routes
3. Implementation order: Token Service -> Auth Service -> Auth Middleware
4. Always validate tokens on the server, never trust client-side validation
