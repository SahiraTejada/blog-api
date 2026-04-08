# Code Review Guide - Blog API

## Purpose

This guide defines the **order and criteria** for reviewing the Blog API codebase. Follow this sequence bottom-to-top (infrastructure first, features last) to catch foundational issues before they cascade.

---

## Review Order

### Phase 1: Foundation (Config, DB, Security)

| # | File(s) | What to verify |
|---|---------|----------------|
| 1 | `app/core/config.py` | All env vars have sensible defaults. Secrets are never hardcoded. `DATABASE_URL` uses `postgresql+psycopg2://`. Token expiration times are reasonable. |
| 2 | `app/database/connection.py` | Engine uses `pool_pre_ping=True`. `Base` is a single shared instance. `init_db()` and `close_db()` are symmetric. |
| 3 | `app/database/session.py` | `get_db()` yields and always closes the session in `finally`. `autocommit=False`, `autoflush=False`. No global session leaks. |
| 4 | `app/core/security.py` | bcrypt rounds >= 12. Password verification uses constant-time comparison. No plaintext passwords anywhere. |
| 5 | `app/core/error_codes.py` | Every `ErrorCode` maps to a unique HTTP status. No overlapping codes. |
| 6 | `app/core/exceptions/base.py` | `AppException` carries `status_code`, `message`, and `code`. `to_dict()` never leaks stack traces. |
| 7 | `app/core/exceptions/*.py` | Each domain exception inherits `AppException`. Status codes match REST conventions (404 for not found, 409 for conflict, etc.). |

**Checklist:**
- [ ] No hardcoded secrets in source code
- [ ] DB session always closes (even on exception)
- [ ] All custom exceptions have correct HTTP status codes

---

### Phase 2: Models & Database Schema

| # | File(s) | What to verify |
|---|---------|----------------|
| 8 | `app/models/base.py` | `uuid` PK uses `UUID(as_uuid=True)` with `default=uuid4`. `created_at` uses timezone-aware datetime. `updated_at` auto-updates via `onupdate`. `deleted_at` is nullable. |
| 9 | `app/models/users.py` | `username` and `email` are unique + indexed. `hashed_password` is never exposed in relationships. `role` uses an Enum. Relationships match ER diagram. |
| 10 | `app/models/posts.py` | `author_uuid` FK is indexed. `status` Enum has DRAFT/PUBLISHED. `post_categories` junction table has composite PK. `likes_count`/`comments_count` properties filter by `deleted_at IS NULL`. |
| 11 | `app/models/comments.py` | Self-referential `parent_comment_uuid` is nullable. `remote_side` is set correctly for nested replies. |
| 12 | `app/models/likes.py` | Composite PK `(user_uuid, post_uuid)`. Does NOT inherit `BaseModel`. Has `deleted_at` for soft delete. |
| 13 | `app/models/follows.py` | Composite PK `(follower_uuid, followee_uuid)`. Does NOT inherit `BaseModel`. Has `deleted_at` for soft delete. |
| 14 | `app/models/tokens.py` | `token_type` distinguishes access/refresh. `revoked` bool defaults to False. `expires_at` is timezone-aware. |

**Checklist:**
- [ ] All FKs have matching `relationship()` on both sides (`back_populates`)
- [ ] All unique constraints match the ER diagram (`docs/er_diagram.png`)
- [ ] Composite PK models (Likes, Follows) don't inherit from BaseModel
- [ ] No circular import issues (use `TYPE_CHECKING` guard)

---

### Phase 3: Repository Layer

| # | File(s) | What to verify |
|---|---------|----------------|
| 15 | `app/repositories/base_repository.py` | `_apply_soft_delete_filter` always runs unless `include_deleted=True`. `get_multi` returns `PaginatedResponse` when pagination is provided. `delete()` defaults to soft delete. `create()` calls `db.flush()` + `db.refresh()`. |
| 16 | `app/repositories/user_repository.py` | `get_by_username` and `get_by_email` are case-insensitive. `username_exists`/`email_exists` check active records only. |
| 17 | `app/repositories/post_repository.py` | Filters by `status` and `category_uuid` work correctly. Search uses `ilike` for case-insensitive matching. |
| 18 | `app/repositories/comment_repository.py` | Queries filter by `post_uuid`. Nested comment queries handle `parent_comment_uuid`. |
| 19 | `app/repositories/likes_repository.py` | `like()` restores soft-deleted records (clears `deleted_at`). `unlike()` sets `deleted_at`. `has_liked()` checks `deleted_at IS NULL`. |
| 20 | `app/repositories/follows_repository.py` | Same soft-delete restore pattern as likes. `is_following()` checks active records only. |
| 21 | `app/repositories/token_repository.py` | `revoke_token()` sets `revoked=True`. Expired token queries check `expires_at`. |
| 22 | `app/repositories/category_repository.py` | `name` uniqueness is case-insensitive. |

**Checklist:**
- [ ] Every repository method that reads data filters out soft-deleted records by default
- [ ] No raw SQL - all queries use SQLAlchemy ORM
- [ ] `db.commit()` is NOT called inside repositories (session-per-request pattern)
- [ ] Pagination math is correct: `skip = (page - 1) * page_size`

---

### Phase 4: Service Layer (Business Logic)

| # | File(s) | What to verify |
|---|---------|----------------|
| 23 | `app/services/base_service.py` | `get_by_uuid` raises `NotFoundException` if repo returns `None`. Generic `_raise_not_found()` uses model name. |
| 24 | `app/services/auth_service.py` | `register` hashes password before storing. `login` verifies password with constant-time comparison. Token creation stores in DB. `refresh` validates refresh token type. `logout` revokes both tokens. |
| 25 | `app/services/user_service.py` | `create_user` checks username AND email uniqueness before insert. `update_user` validates uniqueness only for changed fields. `delete_user` is soft delete. |
| 26 | `app/services/post_service.py` | `create_post` validates category UUIDs exist. `update_post` checks ownership or admin role. `delete_post` checks ownership or admin role. |
| 27 | `app/services/comment_service.py` | `create_comment` validates post exists. Nested comments validate parent exists AND belongs to same post. `delete_comment` checks ownership or admin. |
| 28 | `app/services/likes_service.py` | `like_post` validates post exists, raises `AlreadyLikedException` on duplicate. `unlike_post` raises `LikeNotFoundException`. `toggle_like` validates post exists before toggling. |
| 29 | `app/services/follows_service.py` | `follow` prevents self-follow. Validates followee exists. Raises `AlreadyFollowingException` on duplicate. `unfollow` raises `FollowNotFoundException`. |
| 30 | `app/services/token_service.py` | Token creation includes `user_uuid`, `exp`, `token_type` in payload. Validation checks `revoked`, `expires_at`, and `deleted_at` on user. |

**Checklist:**
- [ ] Services never access `db` directly - always go through repository
- [ ] All user-facing error paths raise specific `AppException` subclasses (not generic 500s)
- [ ] Business rules from `docs/requirements.pdf` are enforced here (not in routes)
- [ ] No data transformation logic here - that belongs in schemas

---

### Phase 5: Schemas (Validation & Serialization)

| # | File(s) | What to verify |
|---|---------|----------------|
| 31 | `app/schemas/base.py` | `BaseSchema` has `from_attributes=True`. `PaginationParams` validates `page >= 1`, `page_size` between 1-100. `PaginatedResponse` is generic. |
| 32 | `app/schemas/user.py` | `UserCreate` validates email format. Password has minimum length. `UserPublicSchema` NEVER includes `email` or `hashed_password`. `UserResponse` excludes `hashed_password`. |
| 33 | `app/schemas/post.py` | `PostCreateSchema` validates title length (1-255). `PostResponse` includes `likes_count` and `comments_count`. `PostUpdateSchema` has all fields optional. |
| 34 | `app/schemas/comment.py` | `parent_comment_uuid` is optional. Content has minimum length. |
| 35 | `app/schemas/likes.py` | `LikeResponse` uses composite key fields (no uuid). `LikeToggleResponse` includes `liked` bool + `likes_count`. |
| 36 | `app/schemas/follows.py` | `FollowResponse` uses composite key fields. `FollowWithUserResponse` nests `UserPublicSchema`. |
| 37 | `app/schemas/auth.py` | `LoginRequest` has email + password. `TokenResponse` includes `access_token`, `refresh_token`, `token_type`. |

**Checklist:**
- [ ] No sensitive fields (`hashed_password`, `email` in public schemas) are exposed
- [ ] All `Create` schemas exclude auto-generated fields (`uuid`, `created_at`)
- [ ] All `Update` schemas have optional fields for partial updates
- [ ] `model_config` has `from_attributes = True` on all response schemas
- [ ] Examples in `json_schema_extra` are realistic and consistent

---

### Phase 6: API Layer (Routes, Auth, Middleware)

| # | File(s) | What to verify |
|---|---------|----------------|
| 38 | `app/api/dependencies.py` | `AuthContext` is frozen dataclass. `get_auth_context` validates JWT + checks token in DB + checks user is active. `RoleChecker` returns `AuthContext` (not just bool). Bearer scheme uses `auto_error=False`. |
| 39 | `app/api/middleware/error_handler.py` | All `AppException` subclasses are caught. `ValidationError` returns 422 with field details. `IntegrityError` returns 409. Generic exceptions return 500 without stack traces in production. |
| 40 | `app/api/v1/routes/__init__.py` | All routers are included. Prefixes don't conflict. Tags match module names. |
| 41 | `app/api/v1/routes/auth.py` | `POST /register` - no auth required. `POST /login` - no auth required. `POST /refresh` - no auth required (uses refresh token). `POST /logout` - auth required. |
| 42 | `app/api/v1/routes/users.py` | `GET /users` - public or admin. `GET /users/{uuid}` - public. `PATCH /users/{uuid}` - owner or admin. `DELETE /users/{uuid}` - owner or admin. |
| 43 | `app/api/v1/routes/posts.py` | `POST /posts` - auth required. `GET /posts` - public with pagination. `PATCH /posts/{uuid}` - author or admin. `DELETE /posts/{uuid}` - author or admin. |
| 44 | `app/api/v1/routes/comments.py` | `POST /comments` - auth required. `GET /comments` - public. `DELETE /comments/{uuid}` - author or admin. Nested comments validated. |
| 45 | `app/api/v1/routes/likes.py` | `POST /likes` - auth required. `DELETE /likes/{post_uuid}` - auth required. `POST /likes/toggle/{post_uuid}` - auth required. `GET` endpoints - public. |
| 46 | `app/api/v1/routes/follow.py` | `POST /follow` - auth required. `DELETE /follow/{uuid}` - auth required. `GET` endpoints - public. |
| 47 | `app/main.py` | Lifespan handles `init_db()` / `close_db()`. CORS configured. Exception handlers registered. API mounted at `/api/v1`. |

**Checklist:**
- [ ] All mutation endpoints (POST, PATCH, DELETE) require authentication
- [ ] Public read endpoints don't leak private data
- [ ] Response models match the actual return types
- [ ] HTTP status codes are correct (201 for create, 200 for update/delete, etc.)
- [ ] No business logic in routes - delegated to services
- [ ] Pagination uses `Depends()` for query params

---

### Phase 7: Utilities & Cross-Cutting

| # | File(s) | What to verify |
|---|---------|----------------|
| 48 | `app/utils/pagination.py` | `paginate()` calculates `total_pages` with ceiling division. `has_next`/`has_previous` are correct at boundaries. |
| 49 | `app/utils/validators.py` | Custom validators are reusable. No business logic here. |
| 50 | `app/utils/validator_utils.py` | Username validation rules match requirements. |

---

## Consistency Checks (Run Across All Files)

These checks apply globally. Run them after completing the per-file review.

### Naming Conventions
- [ ] Models: singular class name (`User`), plural table name (`users`)
- [ ] Schemas: `{Entity}CreateSchema`, `{Entity}UpdateSchema`, `{Entity}Response`
- [ ] Repositories: `{Entity}Repository` inherits `BaseRepository[Entity]`
- [ ] Services: `{Entity}Service` inherits `BaseService[Entity]`
- [ ] Routes: `router = APIRouter(prefix="/{entities}")`
- [ ] Exceptions: `{Entity}{Action}Exception` (e.g., `PostNotFoundException`)

### Import Hygiene
- [ ] No circular imports (`TYPE_CHECKING` used where needed)
- [ ] No unused imports
- [ ] Imports sorted (`isort --check-only`)

### Soft Delete Consistency
- [ ] Every query that reads data excludes `deleted_at IS NOT NULL`
- [ ] `delete()` sets `deleted_at` (not hard delete) unless explicitly requested
- [ ] Unique constraints consider soft-deleted records (can re-create after delete?)

### Error Handling Consistency
- [ ] Every service method that can fail raises a specific `AppException`
- [ ] No bare `except:` or `except Exception:` that silently swallows errors
- [ ] All exceptions are caught by `error_handler.py` middleware

### Type Safety
- [ ] All function signatures have type hints
- [ ] `mypy` passes with no errors: `python -m mypy app/ --ignore-missing-imports`
- [ ] No use of `Any` where a specific type is possible
- [ ] No use of `cast()` (project convention)

---

## Quick Commands

```bash
# Linting
python -m flake8 app/ --max-line-length 120

# Type checking
python -m mypy app/ --ignore-missing-imports

# Import sorting check
python -m isort app/ --check-only --profile black

# Code formatting check
python -m black app/ --check --line-length 127

# Security scan
python -m bandit -r app/ -c pyproject.toml

# Run all checks in sequence
python -m flake8 app/ --max-line-length 120 && \
python -m mypy app/ --ignore-missing-imports && \
python -m isort app/ --check-only --profile black && \
python -m black app/ --check --line-length 127
```

---

## Review Priority

If time is limited, focus on these high-impact areas first:

1. **Security** - Auth flow, password handling, token validation, no data leaks
2. **Data integrity** - Soft delete consistency, unique constraints, FK relationships
3. **Error handling** - All paths return proper status codes, no unhandled exceptions
4. **Business rules** - Requirements from `docs/requirements.pdf` are enforced in services
5. **API contract** - Response schemas match what clients expect, pagination works correctly
