"""
Post Service Module

This module provides post management business logic including
post creation, retrieval, updates, deletion, and statistics.

Architecture Flow:
    Route → PostService → PostRepository → Database

The PostService handles:
    - Post creation with author assignment and category linking
    - Post retrieval by UUID or title
    - Post listing with search, filtering, and pagination
    - Post updates with title uniqueness validation
    - Post deletion (soft delete)
    - Post statistics (counts by status, author)
    - Post status transitions (publish/unpublish)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, overload
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions.common import ForbiddenException
from app.core.exceptions.post import PostNameExistsException, PostNotFoundException
from app.models.posts import Post, PostStatus
from app.models.users import User, UserRole
from app.repositories.post_repository import PostRepository
from app.schemas.base import PaginationParams
from app.services.base_service import BaseService

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class PostService(BaseService[Post]):
    """
    Service for post management operations.

    This service handles post creation, retrieval, updates, and deletion.

    Attributes:
        post_repo: PostRepository instance for database operations

    Example:
        post_service = PostService(db)
        post = post_service.create_post(
            title="My First Post",
            content="Hello world",
            author_uuid=user_uuid,
        )
    """

    def __init__(self, db: Session):
        """
        Initialize PostService with database session.

        Args:
            db: SQLAlchemy database session from FastAPI dependency

        Example:
            post_service = PostService(db)
        """
        self.post_repo = PostRepository(db)

        super().__init__(self.post_repo)

    # ========================================================================
    # POST CREATION
    # ========================================================================

    def create_post(
        self,
        title: str,
        content: str,
        author_uuid: UUID,
        status: PostStatus = PostStatus.DRAFT,
        category_uuids: Optional[List[UUID]] = None,
    ) -> Post:
        """
        Create a new post.

        Args:
            title: Unique post title
            content: Post content
            author_uuid: UUID of the post author
            status: Post status (default: DRAFT)
            category_uuids: Optional list of category UUIDs to assign

        Returns:
            Post: The created post model instance

        Raises:
            PostNameExistsException: If post title already exists
        """
        if self.post_repo.title_exists(title):
            raise PostNameExistsException()

        post_data: Dict[str, Any] = {
            "title": title,
            "content": content,
            "author_uuid": author_uuid,
            "status": status,
        }

        post = self.create(post_data)

        if category_uuids:
            self._assign_categories(post, category_uuids)

        return post

    # ========================================================================
    # POST RETRIEVAL
    # ========================================================================

    def get_by_post_uuid(self, post_uuid: UUID) -> Post:
        """
        Get post by UUID.

        Args:
            post_uuid: UUID of the post to retrieve

        Returns:
            Post: The post model instance

        Raises:
            PostNotFoundException: If post with given UUID does not exist
        """
        post = self.post_repo.get_by_uuid(post_uuid)

        if not post:
            raise PostNotFoundException()

        return post

    def get_by_title(self, title: str) -> Post:
        """
        Get post by title.

        Args:
            title: The title of the post to retrieve

        Returns:
            Post: The post model instance

        Raises:
            PostNotFoundException: If post with given title does not exist
        """
        post = self.post_repo.get_by_title(title)

        if not post:
            raise PostNotFoundException()

        return post

    def get_all_posts(
        self,
        pagination: PaginationParams,
        status: Optional[PostStatus] = PostStatus.PUBLISHED,
        search_term: Optional[str] = None,
        category_uuid: Optional[UUID] = None,
        author_uuid: Optional[UUID] = None,
    ) -> PaginatedResponse[Post]:
        """
        Get posts with flexible filtering options and pagination.

        Args:
            pagination: Pagination parameters (page, page_size)
            status: Filter by post status (default: PUBLISHED)
            search_term: Search in post title and content
            category_uuid: Filter posts by category
            author_uuid: Filter posts by author

        Returns:
            PaginatedResponse with posts and pagination metadata
        """
        return self.post_repo.get_posts(
            pagination=pagination,
            status=status,
            search_term=search_term,
            category_uuid=category_uuid,
            author_uuid=author_uuid,
        )

    @overload
    def get_posts_by_author(
        self, author_uuid: UUID, status: Optional[PostStatus] = ..., pagination: PaginationParams = ...,
    ) -> PaginatedResponse[Post]: ...

    @overload
    def get_posts_by_author(
        self, author_uuid: UUID, status: Optional[PostStatus] = ..., pagination: None = ...,
    ) -> List[Post]: ...

    def get_posts_by_author(
        self,
        author_uuid: UUID,
        status: Optional[PostStatus] = PostStatus.PUBLISHED,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Post], PaginatedResponse[Post]]:
        """
        Get all posts by a specific author.

        Args:
            author_uuid: UUID of the author
            status: Filter by post status (default: PUBLISHED)
            pagination: Optional pagination parameters

        Returns:
            List of posts or PaginatedResponse if pagination provided
        """
        return self.post_repo.get_by_author_uuid(
            author_uuid=author_uuid,
            status=status,
            pagination=pagination,
        )

    # ========================================================================
    # POST STATISTICS
    # ========================================================================

    def count_by_status(self, status: PostStatus) -> int:
        """
        Get the number of posts with a specific status.

        Args:
            status: The post status to count

        Returns:
            Number of posts with the given status
        """
        return self.post_repo.count_by_status(status)

    def count_by_author(self, author_uuid: UUID) -> int:
        """
        Get the number of posts by a specific author.

        Args:
            author_uuid: UUID of the author

        Returns:
            Number of posts by the author
        """
        return self.post_repo.count_by_author(author_uuid)

    def count_published_posts(self) -> int:
        """
        Get the total number of published posts.

        Returns:
            Number of published posts
        """
        return self.post_repo.count_published_posts()

    # ========================================================================
    # GET OR CREATE
    # ========================================================================

    def get_or_create_by_title(
        self, title: str, defaults: Optional[Dict[str, Any]] = None
    ) -> Tuple[Post, bool]:
        """
        Get a post by title or create it if it doesn't exist.

        Args:
            title: The post title
            defaults: Additional fields to set when creating (e.g., author_uuid, content)

        Returns:
            Tuple of (post, created) where created is True if new
        """
        return self.post_repo.get_or_create_by_title(title, defaults=defaults)

    # ========================================================================
    # POST UPDATE
    # ========================================================================

    def update_post(
        self,
        post_uuid: UUID,
        update_data: Dict[str, Any],
        current_user: User,
    ) -> Post:
        """
        Update post information.

        Args:
            post_uuid: UUID of the post to update
            update_data: Dictionary of fields to update (e.g., title, content, status)
            current_user: The authenticated user performing the action

        Returns:
            Post: The updated post model instance

        Raises:
            PostNotFoundException: If post with given UUID does not exist
            PostNameExistsException: If new title already exists
            ForbiddenException: If user is not the author or admin
        """
        post = self.post_repo.get_by_uuid(post_uuid)

        if not post:
            raise PostNotFoundException()

        if post.author_uuid != current_user.uuid and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(message="Only the post author or an admin can update this post")

        new_title = update_data.get("title")
        if new_title and new_title != post.title:
            if self.post_repo.title_exists(new_title, exclude_uuid=post_uuid):
                raise PostNameExistsException()

        category_uuids = update_data.pop("category_uuids", None)

        updated_post = self.post_repo.update(post_uuid, update_data)

        if not updated_post:
            raise PostNotFoundException()

        if category_uuids is not None:
            self._assign_categories(updated_post, category_uuids)

        return updated_post

    # ========================================================================
    # POST STATUS TRANSITIONS
    # ========================================================================

    def publish_post(self, post_uuid: UUID) -> Post:
        """
        Publish a draft post.

        Args:
            post_uuid: UUID of the post to publish

        Returns:
            Post: The published post

        Raises:
            PostNotFoundException: If post does not exist
        """
        post = self.post_repo.publish_post(post_uuid)

        if not post:
            raise PostNotFoundException()

        return post

    def unpublish_post(self, post_uuid: UUID) -> Post:
        """
        Unpublish a post (set back to draft).

        Args:
            post_uuid: UUID of the post to unpublish

        Returns:
            Post: The unpublished post

        Raises:
            PostNotFoundException: If post does not exist
        """
        post = self.post_repo.unpublish_post(post_uuid)

        if not post:
            raise PostNotFoundException()

        return post

    # ========================================================================
    # POST DELETION
    # ========================================================================

    def delete_post(
        self,
        post_uuid: UUID,
        current_user: User,
    ) -> None:
        """
        Soft-delete a post.

        Args:
            post_uuid: UUID of the post to delete
            current_user: The authenticated user performing the action

        Raises:
            PostNotFoundException: If post with given UUID does not exist
            ForbiddenException: If user is not the author or admin
        """
        post = self.post_repo.get_by_uuid(post_uuid)

        if not post:
            raise PostNotFoundException()

        if post.author_uuid != current_user.uuid and current_user.role != UserRole.ADMIN:
            raise ForbiddenException(message="Only the post author or an admin can delete this post")

        deleted = self.post_repo.delete(post_uuid)

        if not deleted:
            raise PostNotFoundException()

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    def _assign_categories(self, post: Post, category_uuids: List[UUID]) -> None:
        """
        Assign categories to a post via the many-to-many relationship.

        Replaces all existing category associations with the new list.

        Args:
            post: The post model instance
            category_uuids: List of category UUIDs to assign
        """
        from app.repositories.category_repository import CategoryRepository

        category_repo = CategoryRepository(self.post_repo.db)
        categories = []

        for cat_uuid in category_uuids:
            category = category_repo.get_by_uuid(cat_uuid)
            if category:
                categories.append(category)

        post.categories = categories
        self.post_repo.db.flush()
