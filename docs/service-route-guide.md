# Guide: Repository → Service → Route

This document describes how to implement the three layers above the model in this project. Every new feature follows the same path: **Repository** handles data access, **Service** owns business logic, and **Route** exposes the HTTP endpoint.

---

## Architecture at a Glance

```
HTTP Request
     │
     ▼
┌──────────────┐   validates input with Pydantic schemas
│   Route      │   injects db session via Depends(get_db)
│  (app/api/)  │   calls exactly one Service method
└──────┬───────┘
       │
       ▼
┌──────────────┐   validates business rules (ownership, uniqueness, etc.)
│   Service    │   orchestrates one or more Repository calls
│ (app/services/) │   raises HTTPException on errors
└──────┬───────┘
       │
       ▼
┌──────────────┐   inherits CRUD from BaseRepository[ModelType]
│  Repository  │   adds model-specific queries
│(app/repositories/)│   no business logic here
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Database   │   PostgreSQL via SQLAlchemy 2.0
└──────────────┘
```

**Rules that every layer must follow:**

| Layer | Knows about | Does NOT know about |
|---|---|---|
| Route | Schemas, Service, `get_db` | Repository, Models |
| Service | Repository, Models | Route, Schemas, HTTP status codes |
| Repository | Model, BaseRepository, Session | Service, Route, Schemas |

> **Schemas are a Route-only concern.** The Route receives a schema from FastAPI (input validation), converts it to a plain `dict` with `model_dump(exclude_unset=True)`, and passes that dict to the Service. On the way back, the Service returns a SQLAlchemy model instance and the Route serializes it via `response_model`. The Service never imports or references a schema.

---

## Layer 1 — Repository

**Location:** `app/repositories/<entity>_repository.py`

The repository is the only layer allowed to touch the database session. It inherits all generic CRUD from `BaseRepository[ModelType]` and only adds methods that are specific to the model.

### What BaseRepository already gives you for free

```python
# app/repositories/base_repository.py

get_by_uuid(uuid)                          # single record by PK
get_by_text_field(filters)                 # single record, case-insensitive
get_multi(filters, search_fields, ...)     # list with filtering + pagination
get_all()                                  # all records (use carefully)
count(filters)                             # count matching records
exists(uuid)                               # bool existence check
filter_by(**kwargs)                        # list by exact field match

create(obj_in: dict)                       # insert one
create_multi(objs_in: list[dict])          # insert many (single transaction)

update(uuid, obj_in: dict)                 # update one
update_multi(filters, obj_in)              # bulk update

delete(uuid, hard_delete=False)            # soft delete by default
delete_multi(filters, hard_delete=False)   # bulk soft/hard delete
restore(uuid)                              # undo soft delete

get_or_create(defaults, **kwargs)          # atomic get-or-create
```

### How to write a concrete repository

Look at `app/repositories/user_repository.py` as the reference implementation:

```python
# app/repositories/user_repository.py

from sqlalchemy.orm import Session
from app.models import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)       # pass model class + session

    # --- Model-specific reads ---

    def get_by_username(self, username: str) -> Optional[User]:
        # Delegate to inherited get_by_text_field (case-insensitive)
        return self.get_by_text_field({"username": username})

    def get_by_email(self, email: str) -> Optional[User]:
        return self.get_by_text_field({"email": email})

    # --- Validation helpers ---

    def username_exists(self, username: str) -> bool:
        return self.get_by_username(username) is not None

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    # --- Filtered listing (uses inherited get_multi) ---

    def get_all_users(
        self,
        order_by: str = "created_at",
        role: Optional[str] = None,
        search_term: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[User], PaginatedResponse[User]]:
        filters = {"role": role} if role else None
        search_fields = ["username", "email", "first_name", "last_name"] if search_term else None

        return self.get_multi(
            filters=filters,
            search_fields=search_fields,
            search_term=search_term,
            order_by=order_by,
            pagination=pagination,
        )
```

`PostRepository` (`app/repositories/post_repository.py`) shows how to handle a JOIN when filtering by a many-to-many relation (category):

```python
def get_posts(self, category_uuid=None, status=PostStatus.PUBLISHED, ...):
    filters = {}
    if status:
        filters["status"] = status

    # Build a custom base_query only when a JOIN is needed
    base_query = None
    if category_uuid:
        base_query = (
            self.db.query(self.model)
            .join(self.model.categories)
            .filter(Category.uuid == category_uuid)
        )

    return self.get_multi(
        filters=filters if filters else None,
        base_query=base_query,
        ...
    )
```

### Repository checklist

- [ ] Class inherits `BaseRepository[YourModel]`
- [ ] `__init__` calls `super().__init__(Model, db)`
- [ ] Only adds methods that are **model-specific**
- [ ] Reuses inherited methods (`get_multi`, `create`, `update`, `delete`, etc.) — never duplicate their logic
- [ ] No `HTTPException`, no business rules — only data access

---

## Layer 2 — Service

**Location:** `app/services/<entity>_service.py`

The service owns all business logic. It instantiates the repository it needs and orchestrates calls to it. This is where you validate rules like "a user can only edit their own posts" or "username must be unique before creating."

### Structure

```python
# app/services/post_service.py

from uuid import UUID
from typing import Optional, Union, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Post, PostStatus
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository
from app.schemas.base import PaginationParams
from app.schemas.base import PaginatedResponse


class PostService:
    def __init__(self, db: Session):
        # Instantiate only the repositories this service needs
        self.post_repo = PostRepository(db)
        self.user_repo = UserRepository(db)

    # --- CREATE ---

    def create_post(self, author_uuid: UUID, title: str, content: str, status: PostStatus = PostStatus.DRAFT) -> Post:
        # 1. Business validation
        if self.post_repo.title_exists(title):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A post with this title already exists"
            )

        # 2. Delegate to repository
        return self.post_repo.create({
            "author_uuid": author_uuid,
            "title": title,
            "content": content,
            "status": status,
        })

    # --- READ ---

    def get_post(self, post_uuid: UUID) -> Post:
        post = self.post_repo.get_by_uuid(post_uuid)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        return post

    def list_posts(
        self,
        pagination: PaginationParams,
        category_uuid: Optional[UUID] = None,
        author_uuid: Optional[UUID] = None,
        search_term: Optional[str] = None,
    ) -> PaginatedResponse[Post]:
        return self.post_repo.get_posts(
            pagination=pagination,
            category_uuid=category_uuid,
            author_uuid=author_uuid,
            search_term=search_term,
        )

    # --- UPDATE ---

    def update_post(self, post_uuid: UUID, current_user_uuid: UUID, data: dict) -> Post:
        post = self.get_post(post_uuid)  # raises 404 if missing

        # Ownership check — business rule
        if post.author_uuid != current_user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own posts"
            )

        # Uniqueness check on title if it is being changed
        new_title = data.get("title")
        if new_title and self.post_repo.title_exists(new_title, exclude_uuid=post_uuid):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A post with this title already exists"
            )

        updated = self.post_repo.update(post_uuid, data)
        return updated  # type: ignore[return-value]

    # --- DELETE ---

    def delete_post(self, post_uuid: UUID, current_user_uuid: UUID) -> None:
        post = self.get_post(post_uuid)

        if post.author_uuid != current_user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own posts"
            )

        self.post_repo.delete(post_uuid)  # soft delete
```

### Service checklist

- [ ] Receives `db: Session` in `__init__` and creates repository instances
- [ ] Contains **all** business rules: ownership, uniqueness, state transitions
- [ ] Raises `HTTPException` when a rule is violated
- [ ] Calls repository methods — never uses `db` directly
- [ ] Each public method maps to one user action (create, get, list, update, delete)

---

## Layer 3 — Route

**Location:** `app/api/v1/routes/<entity>.py`

The route is thin. It validates input (via Pydantic schemas), injects dependencies, calls one service method, and returns the response. No business logic lives here.

### Structure

```python
# app/api/v1/routes/posts.py

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.base import PaginationParams
from app.schemas.post import PostCreateSchema, PostUpdateSchema, PostResponseSchema
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", status_code=status.HTTP_200_OK)
def list_posts(
    pagination: PaginationParams = Depends(),
    category_uuid: Optional[UUID] = None,
    author_uuid: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    service = PostService(db)
    return service.list_posts(
        pagination=pagination,
        category_uuid=category_uuid,
        author_uuid=author_uuid,
        search_term=search,
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponseSchema)
def create_post(
    post_data: PostCreateSchema,
    # current_user: User = Depends(get_current_user),  # auth middleware
    db: Session = Depends(get_db),
):
    service = PostService(db)
    return service.create_post(
        author_uuid=current_user.uuid,
        title=post_data.title,
        content=post_data.content,
    )


@router.get("/{post_uuid}", status_code=status.HTTP_200_OK, response_model=PostResponseSchema)
def get_post(
    post_uuid: UUID,
    db: Session = Depends(get_db),
):
    service = PostService(db)
    return service.get_post(post_uuid)


@router.put("/{post_uuid}", status_code=status.HTTP_200_OK, response_model=PostResponseSchema)
def update_post(
    post_uuid: UUID,
    post_data: PostUpdateSchema,
    # current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PostService(db)
    return service.update_post(
        post_uuid=post_uuid,
        current_user_uuid=current_user.uuid,
        data=post_data.model_dump(exclude_unset=True),
    )


@router.delete("/{post_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_uuid: UUID,
    # current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PostService(db)
    service.delete_post(post_uuid, current_user_uuid=current_user.uuid)
```

### Registering the router

Once the route file is ready, uncomment the corresponding line in `app/api/v1/routes/__init__.py`:

```python
# app/api/v1/routes/__init__.py

from app.api.v1.routes import health, posts  # add import

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(posts.router, tags=["Posts"])   # uncomment / add
```

### Route checklist

- [ ] `router = APIRouter(prefix="/...", tags=["..."])`
- [ ] Each handler has an explicit `status_code` and `response_model`
- [ ] `db: Session = Depends(get_db)` on every handler that needs the database
- [ ] Auth via `Depends(get_current_user)` where required (see `app/api/middleware/auth.py`)
- [ ] Instantiates the service inside the handler: `service = MyService(db)`
- [ ] Calls exactly **one** service method per handler — no logic beyond that
- [ ] Uses `model_dump(exclude_unset=True)` for update schemas so only provided fields are sent to the service

---

## Full Walkthrough — Categories

This section shows every file you touch to wire up a new entity from scratch, using Categories as the example. All the pieces already exist in the codebase; the repositories and schemas just need to be filled in.

### 1. Schema (`app/schemas/category.py`)

```python
from typing import Optional
from pydantic import Field
from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema


class CategoryCreateSchema(CreateSchema):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)


class CategoryUpdateSchema(UpdateSchema):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)


class CategoryResponseSchema(ResponseSchema):
    name: str
    description: Optional[str] = None
```

### 2. Repository (`app/repositories/category_repository.py`)

Already implemented — see `app/repositories/category_repository.py`. Key methods:
- `get_by_name(name)` — single lookup
- `name_exists(name)` — uniqueness check
- `get_all_categories(search_term, pagination)` — filtered listing

### 3. Service (`app/services/category_service.py`)

```python
from uuid import UUID
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.base import PaginationParams
from app.schemas.base import PaginatedResponse


class CategoryService:
    def __init__(self, db: Session):
        self.category_repo = CategoryRepository(db)

    def create_category(self, name: str, description: Optional[str] = None) -> Category:
        if self.category_repo.name_exists(name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")
        return self.category_repo.create({"name": name, "description": description})

    def get_category(self, category_uuid: UUID) -> Category:
        category = self.category_repo.get_by_uuid(category_uuid)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    def list_categories(
        self,
        pagination: PaginationParams,
        search_term: Optional[str] = None,
    ) -> PaginatedResponse[Category]:
        return self.category_repo.get_all_categories(  # type: ignore[return-value]
            search_term=search_term,
            pagination=pagination,
        )

    def update_category(self, category_uuid: UUID, data: dict) -> Category:
        self.get_category(category_uuid)  # raises 404

        new_name = data.get("name")
        if new_name and self.category_repo.name_exists(new_name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")

        updated = self.category_repo.update(category_uuid, data)
        return updated  # type: ignore[return-value]

    def delete_category(self, category_uuid: UUID) -> None:
        self.get_category(category_uuid)  # raises 404
        self.category_repo.delete(category_uuid)
```

### 4. Route (`app/api/v1/routes/categories.py`)

```python
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.base import PaginationParams
from app.schemas.category import CategoryCreateSchema, CategoryUpdateSchema, CategoryResponseSchema
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", status_code=status.HTTP_200_OK)
def list_categories(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    return service.list_categories(pagination=pagination, search_term=search)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CategoryResponseSchema)
def create_category(
    data: CategoryCreateSchema,
    # current_user: User = Depends(get_current_user),  # admin check here
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    return service.create_category(name=data.name, description=data.description)


@router.get("/{category_uuid}", status_code=status.HTTP_200_OK, response_model=CategoryResponseSchema)
def get_category(
    category_uuid: UUID,
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    return service.get_category(category_uuid)


@router.put("/{category_uuid}", status_code=status.HTTP_200_OK, response_model=CategoryResponseSchema)
def update_category(
    category_uuid: UUID,
    data: CategoryUpdateSchema,
    # current_user: User = Depends(get_current_user),  # admin check here
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    return service.update_category(category_uuid, data.model_dump(exclude_unset=True))


@router.delete("/{category_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_uuid: UUID,
    # current_user: User = Depends(get_current_user),  # admin check here
    db: Session = Depends(get_db),
):
    service = CategoryService(db)
    service.delete_category(category_uuid)
```

### 5. Register the router

```python
# app/api/v1/routes/__init__.py
from app.api.v1.routes import health, categories

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(categories.router, tags=["Categories"])
```

---

## Summary — What goes where

| Decision | Where it lives |
|---|---|
| "Does this record exist?" | Repository (`exists`, `get_by_uuid`) |
| "Is this username already taken?" | Repository (`username_exists`) |
| "A user cannot edit someone else's post" | Service (ownership check → `HTTPException`) |
| "Return 404 if not found" | Service (`get_post` raises `HTTPException`) |
| "Return 409 if duplicate" | Service (calls repo check → raises `HTTPException`) |
| HTTP status codes on success | Route (`status_code=...`) |
| Request/response shape | Route (`response_model=...`, schema as parameter type) |
| Pagination query params | Route (`PaginationParams = Depends()`) |
| Database session lifecycle | Route (`Depends(get_db)`) |
| Auth / current user | Route (`Depends(get_current_user)`) |
