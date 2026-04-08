# Code Audit Findings - Blog API

> Audit date: 2026-03-29
> Reviewer perspective: Senior Backend Engineer
> Goal: Security, stability, maintainability, clean code

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 6 | Must fix before any deploy |
| HIGH | 12 | Fix in current sprint |
| MEDIUM | 18 | Plan for next sprint |
| LOW | 10 | Address during refactors |

---

## CRITICAL - Must Fix Immediately

### C-1. Missing Authorization in Post Update/Delete

**Files:** `app/api/v1/routes/posts.py:170-229`

The docstrings say "Only the post author or an admin can update/delete a post" but **no ownership check exists**. Any authenticated user can modify or delete any post.

```python
# CURRENT (posts.py:187-194) - No ownership check
async def update_post(
    post_uuid: UUID,
    update_data: PostUpdateSchema,
    auth: AuthContext = Depends(require_user),  # auth is captured but never used
    db: Session = Depends(get_db),
) -> PostResponse:
    post_service = PostService(db)
    updated_post = post_service.update_post(
        post_uuid=post_uuid,
        update_data=update_data.model_dump(exclude_unset=True),
    )
    # auth.user.uuid is never checked against post.author_uuid
```

**Fix:** Pass `auth.user` to the service and verify ownership there. Same for `delete_post()`.

---

### C-2. Missing Authorization in Comment Update/Delete

**Files:** `app/api/v1/routes/comments.py:267-321`

Same issue as C-1. Any authenticated user can update or delete any comment.

---

### C-3. CORS Wildcard + Credentials

**File:** `app/main.py:54-59`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Default: ["*"]
    allow_credentials=True,                   # DANGEROUS with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_credentials=True` with `allow_origins=["*"]` violates the CORS spec and allows any website to make authenticated requests to the API. Browsers may block this, but it signals misconfiguration.

**Fix:** Either remove `allow_credentials=True` or set explicit allowed origins (never `"*"` with credentials).

---

### C-4. TrustedHostMiddleware Uses CORS Origins

**File:** `app/main.py:62-64`

```python
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_ORIGINS  # Wrong setting - CORS origins != host headers
)
```

`ALLOWED_ORIGINS` contains CORS origins (e.g., `["http://localhost:3000"]`) but `TrustedHostMiddleware` expects bare hostnames (e.g., `["localhost"]`). This likely blocks all requests or allows none correctly.

**Fix:** Create a separate `ALLOWED_HOSTS` setting.

---

### C-5. No Rate Limiting on Auth Endpoints

**File:** `app/api/middleware/rate_limiter.py` is **empty** (0 bytes).

No brute-force protection on:
- `POST /auth/login` - unlimited password guessing
- `POST /auth/register` - unlimited account creation
- `POST /auth/refresh` - unlimited token refresh

**Fix:** Implement rate limiting (e.g., `slowapi`) or add at reverse proxy level.

---

### C-6. No Input Sanitization on Content Fields (XSS)

**Files:** `app/schemas/post.py:58-62`, `app/schemas/comment.py:27-31`

Post and comment `content` fields accept arbitrary strings with no HTML/script sanitization. If content is rendered in a frontend without escaping, stored XSS is possible.

**Fix:** Sanitize HTML at the service layer (e.g., `bleach.clean()`) or document that frontends MUST escape output.

---

## HIGH - Fix This Sprint

### H-1. N+1 Query in `Post.likes_count` and `Post.comments_count`

**File:** `app/models/posts.py:82-90`

```python
@property
def likes_count(self) -> int:
    return sum(1 for like in self.likes if like.deleted_at is None)
```

This loads ALL likes into memory just to count them. For a post with 10,000 likes, this fetches 10,000 rows. And if `likes` wasn't eager-loaded, it triggers a lazy-load query per post in a list.

**Fix:** Use a SQL-level `COUNT()` via `column_property` or `hybrid_property`, or use `selectinload` + `func.count()` in the repository query.

---

### H-2. N+1 Query in `CommentRepository.get_comment_depth()`

**File:** `app/repositories/comment_repository.py:194-216`

```python
while current_uuid:
    comment = self.get_by_uuid(current_uuid)  # 1 query per level
    if not comment or not comment.parent_comment_uuid:
        break
    depth += 1
    current_uuid = comment.parent_comment_uuid
```

Each nesting level triggers a separate DB query.

**Fix:** Use a recursive CTE or fetch the full comment chain in one query.

---

### H-3. Missing Soft-Delete Filter in `PostRepository.get_posts()` with Category Join

**File:** `app/repositories/post_repository.py:159-160`

```python
if category_uuid:
    base_query = self.db.query(self.model).join(self.model.categories).filter(
        Category.uuid == category_uuid
    )
    # soft-delete filter NOT applied to this custom base_query
```

When filtering by category, the custom `base_query` bypasses `_apply_soft_delete_filter()`, potentially returning deleted posts.

**Fix:** Apply soft-delete filter to `base_query` explicitly.

---

### H-4. No Error Handling in Likes/Follows Repositories

**Files:** `app/repositories/likes_repository.py:58-96`, `app/repositories/follows_repository.py:58-99`

These repositories don't inherit `BaseRepository` and lack try-catch blocks around `db.flush()`:

```python
like.deleted_at = None
self.db.flush()       # Can throw - no catch, no rollback
self.db.refresh(like) # Can throw - no catch
```

Compare with `BaseRepository` which wraps all DB operations in try-except with rollback.

**Fix:** Add try-except with `db.rollback()` around DB operations.

---

### H-5. Missing User Existence Validation in `LikesService.like_post()`

**File:** `app/services/likes_service.py:67-91`

```python
def like_post(self, user_uuid: UUID, post_uuid: UUID) -> Likes:
    post = self.post_repo.get_by_uuid(post_uuid)  # validates post
    if not post:
        raise PostNotFoundException(...)

    # user_uuid is NOT validated - could create orphan likes
    return self.likes_repo.like(user_uuid, post_uuid)
```

**Fix:** Add user existence check before creating the like.

---

### H-6. Self-Referential Relationship Uses `backref` Instead of `back_populates`

**File:** `app/models/comments.py:60-65`

```python
replies: Mapped[List["Comments"]] = relationship(
    "Comments",
    backref="parent",           # Old-style, creates untyped attribute
    remote_side="Comments.uuid",
    foreign_keys=[parent_comment_uuid]
)
```

SQLAlchemy 2.0 with `Mapped[T]` should use `back_populates` for type safety. The `parent` attribute exists at runtime but has no type annotation, breaking mypy.

**Fix:** Declare both sides explicitly with `back_populates`.

---

### H-7. `assert` Statements in Production Code

**Files:** `posts.py:117`, `comments.py:121`, `likes.py:217`, `follow.py:175`

```python
assert isinstance(result, PaginatedResponse)  # Disabled with python -O
```

`assert` is stripped when Python runs with `-O` flag. This would cause `result` to be used without type verification.

**Fix:** Replace with `if not isinstance(...): raise TypeError(...)` or trust the type system.

---

### H-8. Email Case Normalization Only in Service, Not Schema

**File:** `app/services/user_service.py:264-267`

Email is normalized to lowercase in `update_user()` but not in `UserUpdateSchema`. If email is used for lookups before reaching the service, case mismatch causes duplicates.

**Fix:** Add `@field_validator('email')` in `UserUpdateSchema` to normalize to lowercase.

---

### H-9. Mutable Default Argument in `AppException`

**File:** `app/core/exceptions/base.py:41`

```python
class AppException(Exception):
    details: Dict[str, Any] = {}  # Shared across ALL instances
```

All exception instances share the same `details` dict. Modifying one modifies all.

**Fix:** Use `field(default_factory=dict)` or set in `__init__`.

---

### H-10. `print()` in Production Entry Point

**File:** `app/main.py:18-29, 34-37`

```python
print(f"Database connection: {'OK' if db else 'FAILED'}")
print("Starting Blog Application...")
```

`print()` bypasses structured logging, doesn't show in log aggregators, and can't be filtered by level.

**Fix:** Use `logging.getLogger(__name__).info(...)`.

---

### H-11. `datetime.utcnow()` Deprecated

**File:** `app/api/v1/routes/health.py:19`

`datetime.utcnow()` is deprecated in Python 3.12+. Returns naive datetime without timezone info.

**Fix:** Use `datetime.now(timezone.utc)`.

---

### H-12. Inconsistent Services Don't Validate Foreign Keys on Create

**Files:** `app/services/post_service.py:100-105`, `app/services/comment_service.py:108-115`

`author_uuid` is accepted without verifying the user exists. The FK constraint will catch it at DB level, but the error becomes a generic 500 instead of a clear 404.

**Fix:** Validate user existence before creating posts/comments.

---

## MEDIUM - Plan for Next Sprint

### M-1. Missing Individual Indexes on Composite PK Tables

**Files:** `app/models/likes.py:49-51`, `app/models/follows.py` (similar)

```python
__table_args__ = (
    PrimaryKeyConstraint('user_uuid', 'post_uuid'),
)
```

Queries that filter by `post_uuid` alone (e.g., `get_post_likes()`) can't use the composite PK index efficiently because `user_uuid` comes first.

**Fix:** Add `Index('ix_likes_post_uuid', 'post_uuid')`.

---

### M-2. Soft-Deleted Records Visible Through Relationships

**Files:** All models with relationships

```python
# comments.py - replies includes soft-deleted comments
replies: Mapped[List["Comments"]] = relationship("Comments", ...)

# posts.py - likes/comments relationships include soft-deleted records
likes: Mapped[List["Likes"]] = relationship("Likes", back_populates="post")
```

Accessing `post.likes` returns ALL likes including soft-deleted ones. The `likes_count` property filters in Python, but any code accessing the relationship directly gets stale data.

**Fix:** Add `primaryjoin` with soft-delete filter, or always use repository methods instead of direct relationship access.

---

### M-3. Business Logic in Repository: `created_at` Reset on Restore

**Files:** `app/repositories/likes_repository.py:83`, `app/repositories/follows_repository.py:86`

```python
existing.created_at = datetime.now(timezone.utc)  # Resets original creation time
```

Resetting `created_at` when restoring a soft-deleted like is a business decision that should live in the service layer, not the repository.

---

### M-4. Token Filtering in Python Instead of SQL

**File:** `app/repositories/token_repository.py:89-134`

```python
tokens = self.filter_by(...)  # Fetch ALL tokens
for token in tokens:           # Filter in Python
    if not include_revoked and token.is_revoked:
        continue
```

Should filter `revoked` and `expires_at` in the SQL query.

---

### M-5. `PostRepository.get_posts()` Hardcodes Default Status

**File:** `app/repositories/post_repository.py:105`

```python
def get_posts(
    self,
    status: Optional[PostStatus] = PostStatus.PUBLISHED,  # Surprising default
```

A caller passing `status=None` means "all statuses", but the default is PUBLISHED. This is a hidden filter that should be explicit.

---

### M-6. Race Condition in `BaseRepository.get_or_create()`

**File:** `app/repositories/base_repository.py:794-854`

Classic TOCTOU (time-of-check-time-of-use) between `filter_by()` and `create()`. Under concurrent requests, two threads could both pass the existence check and both try to create.

The code handles this with an `IntegrityError` catch + retry, which is correct, but the retry `filter_by` could also fail if the other transaction hasn't committed yet.

---

### M-7. Inconsistent Error Return Patterns

| Service | On failure... | Returns |
|---------|--------------|---------|
| `LikesService.unlike_post()` | Like not found | Raises `LikeNotFoundException` |
| `TokenService.revoke_token()` | Token not found | Returns `False` |
| `BaseService.delete()` | Not found | Raises `NotFoundException` |
| `FollowService.unfollow()` | Not found | Raises `FollowNotFoundException` |

Some services raise exceptions, others return booleans. Routes must handle both patterns differently.

**Fix:** Standardize: all services raise exceptions on failure, never return `False`.

---

### M-8. Middleware Ordering

**File:** `app/main.py:54-71`

Current order:
1. CORS middleware (line 54)
2. TrustedHost middleware (line 62)
3. Exception handlers (line 68)
4. Router (line 71)

Exception handlers should be registered before middleware to catch errors from middleware itself.

---

### M-9. `get_db()` Session Commit Ordering

**File:** `app/database/session.py:56-63`

```python
try:
    yield db
    db.commit()    # Runs AFTER the route handler completes
except Exception:
    db.rollback()  # Good
    raise
finally:
    db.close()     # Good
```

This is correct but fragile. If a route returns a response that triggers serialization errors AFTER the yield, the commit still happens because FastAPI processes the response after the generator yields.

---

### M-10. Inconsistent Method Naming

| Pattern | Examples |
|---------|----------|
| `get_by_X` | `get_by_uuid()`, `get_by_username()`, `get_by_email()` |
| `get_X` | `get_posts()`, `get_comment_tree()`, `get_post_likes()` |
| `count_X` | `count_post_likes()`, `count_followers()` |
| `X_exists` | `username_exists()`, `email_exists()` |
| `has_X` | `has_liked()`, `is_following()` |

The `has_liked()` vs `is_following()` inconsistency is notable - both check boolean existence but use different prefixes.

---

### M-11. Silent Category Ignore on Post Create

**File:** `app/services/post_service.py:374-395`

```python
for uuid in category_uuids:
    category = self.category_repo.get_by_uuid(uuid)
    if category:           # Silently ignores invalid UUIDs
        post.categories.append(category)
```

If a user sends 3 category UUIDs and 1 is invalid, the post is created with only 2 categories. No error, no warning.

**Fix:** Raise `CategoryNotFoundException` listing the invalid UUIDs.

---

### M-12. No Pagination Bounds Check

**File:** `app/schemas/base.py:110-120`

Requesting `page=999999` on a 10-item dataset triggers a full query with `OFFSET 19999980`. The DB scans all rows to calculate the offset. Returns empty data but wastes resources.

---

### M-13. `X-Forwarded-For` Trusted Without Validation

**File:** `app/api/middleware/auth.py:31-33`

The IP address is extracted from `X-Forwarded-For` blindly. Any client can set this header to spoof their IP for logging/rate-limiting.

---

### M-14. No Request ID Tracking

**File:** `app/api/middleware/error_handler.py:110`

Code references `request.state.request_id` but nothing sets it. Error logs have no correlation ID for tracing.

---

### M-15. Inconsistent Pydantic Config Style

Some schemas use `model_config = ConfigDict(...)` (Pydantic v2 style), others use inner `class Config:` (Pydantic v1 style). Example: `base.py:150-158` uses `class Config` while `base.py:23-27` uses `model_config`.

---

### M-16. Duplicate Import in `token_repository.py`

**File:** `app/repositories/token_repository.py:1, 342`

```python
from datetime import datetime, timedelta, timezone  # Line 1
# ...
from datetime import timedelta                       # Line 342 (duplicate)
```

---

### M-17. Authorization Not Enforced in Service Layer

All authorization lives in routes. If a new route or internal caller uses a service directly, there's no safety net. Services should optionally accept `current_user_uuid` and verify ownership for mutation methods.

---

### M-18. No SECRET_KEY Strength Validation

**File:** `app/core/config.py:13`

`SECRET_KEY` has no minimum length or complexity check. A weak key like `"secret"` would be accepted.

---

## LOW - Address During Refactors

### L-1. `CategoryRepository.get_category_post_count()` Doesn't Filter Deleted Categories

**File:** `app/repositories/category_repository.py:300-310`

Filters deleted posts but not deleted categories. If a category is soft-deleted, count still works.

### L-2. Unused `Tuple` Import

**File:** `app/repositories/post_repository.py:6` - `Tuple` imported but not used.

### L-3. Empty Utility Files

**Files:** `app/utils/validators.py` (0 bytes), `app/utils/decorators.py` (0 bytes). Should be deleted or implemented.

### L-4. IP Address Field Not Validated

**File:** `app/models/tokens.py:69-73` - `String(45)` accepts any string, not just valid IPs.

### L-5. `parent_belongs_to_post()` Method Exists But Never Called

**File:** `app/repositories/comment_repository.py:230-247` - Validation method exists but isn't used anywhere.

### L-6. No Logging Configuration

Loggers created everywhere with `getLogger(__name__)` but no handlers configured. All logs go to default stderr.

### L-7. Missing `__all__` in Most `__init__.py` Files

Modules don't define `__all__`, making it unclear what the public API is.

### L-8. Comment Model Named `Comments` (Plural) While Others Are Singular

`User`, `Post`, `Category`, `Follow` vs `Comments`, `Likes` - inconsistent singular/plural naming on model classes.

### L-9. `typing.List` vs `list` Builtin

Files use `from typing import List` (Python < 3.9 style). Since the project targets 3.9+, lowercase `list` is preferred.

### L-10. Docstring Says "raises HTTPException" But Code Raises Custom Exception

**File:** `app/services/token_service.py:435-438` - Documentation mismatch.

---

## Recommended Fix Order

```
Week 1 (CRITICAL):
  C-1  Add ownership checks to post update/delete
  C-2  Add ownership checks to comment update/delete
  C-3  Fix CORS configuration
  C-4  Separate ALLOWED_HOSTS from ALLOWED_ORIGINS
  C-5  Implement rate limiting on auth endpoints
  C-6  Add content sanitization

Week 2 (HIGH):
  H-1  Fix N+1 in likes_count/comments_count (use SQL COUNT)
  H-2  Fix N+1 in get_comment_depth (recursive CTE)
  H-3  Fix soft-delete filter in category join query
  H-4  Add error handling to likes/follows repos
  H-5  Validate user exists in like_post()
  H-6  Fix backref -> back_populates in Comments
  H-7  Replace assert with proper checks
  H-8  Normalize email in schema validator
  H-9  Fix mutable default in AppException
  H-10 Replace print() with logging
  H-11 Fix deprecated utcnow()
  H-12 Validate FK existence on create

Week 3-4 (MEDIUM):
  M-1  Add individual indexes on composite PK tables
  M-2  Add soft-delete filters to relationships
  M-5  Remove hardcoded default status
  M-7  Standardize error return patterns (always raise)
  M-8  Fix middleware ordering
  M-10 Standardize method naming
  M-11 Raise on invalid category UUIDs
  M-17 Add optional auth to service methods
  M-18 Validate SECRET_KEY strength
  (remaining M items as time allows)

Ongoing:
  L-*  Address during related refactors
```
