# Claude Code Instructions for Blog API Project

## Project Context

This is a FastAPI-based Blog API project following a layered architecture pattern. When working on this project, always consider the complete context including code AND documentation.

## Required Documentation Review

Before making any changes or providing recommendations, **ALWAYS review these key documentation files**:

1. **`docs/design_system.pdf`** - Contains the complete system design, architecture decisions, and design patterns used in the project
2. **`docs/requirements.pdf`** - Contains all functional and non-functional requirements, business rules, and project specifications
3. **`docs/er_diagram.png`** - Entity-Relationship diagram showing the complete database schema, relationships, and data model

## Architecture Layers

The project follows a strict layered architecture (bottom to top):

1. **Models** (`app/models/`) - SQLAlchemy 2.0 models with `Mapped[T]` syntax
2. **Schemas** (`app/schemas/`) - Pydantic schemas for validation
3. **Repositories** (`app/repositories/`) - Data access layer using Repository Pattern
4. **Services** (`app/services/`) - Business logic layer
5. **Routes** (`app/api/`) - API endpoints and request handling

## Key Implementation Guidelines

### 1. Always Check Documentation First
- Before implementing a new feature, review the requirements in `docs/requirements.pdf`
- Verify the database relationships in `docs/er_diagram.png`
- Follow design patterns from `docs/design_system.pdf`

### 2. SQLAlchemy 2.0 Standards
- All models use `Mapped[T]` with `mapped_column()`
- Use `TYPE_CHECKING` to avoid circular imports
- All relationships are typed: `Mapped["Model"]` or `Mapped[List["Model"]]`
- No use of `cast()` - proper typing should eliminate the need

### 3. Repository Pattern
- All repositories inherit from `BaseRepository[ModelType]`
- Utilize inherited CRUD methods instead of duplicating code
- Add model-specific methods for business logic queries
- No direct database access outside repositories

### 4. Code Quality
- All code must pass `mypy` type checking
- All code must pass `flake8` linting (max line length: 120)
- Follow existing naming conventions and patterns
- Add proper docstrings and type hints




## Important Notes

- **Soft Delete**: All models inherit from `BaseModel` which includes soft delete support via `deleted_at` field
- **UUID Primary Keys**: All entities use UUID instead of auto-increment integers
- **Token Management**: JWT tokens are stored in database for revocation and security auditing
- **Model Naming**: Class names are singular (User, Post, Category), table names are plural (users, posts, categories)
- **Error Handling**: Use proper HTTP status codes and error middleware from `app/middleware/`

## When Implementing New Features

1. Read the relevant sections in `docs/requirements.pdf`
2. Check the data model in `docs/er_diagram.png` for relationships
3. Review design patterns in `docs/design_system.pdf`
4. Ensure all changes align with existing architecture patterns
5. Run tests and type checking before completing

## File References



- Design System: `docs/design_system.pdf`
- Requirements: `docs/requirements.pdf`
- ER Diagram: `docs/er_diagram.png`

## Questions to Ask Before Coding

1. Is this feature documented in the requirements?
2. Does the database schema support this feature (check ER diagram)?
3. Does this follow the design patterns established in the design system?
4. Which layer(s) need to be modified?
5. Are there existing similar implementations to follow as examples?

---

**Remember**: The documentation files are not just reference material - they are the source of truth for this project. Always validate your implementation against them.
