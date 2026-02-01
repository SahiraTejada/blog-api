from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category, Post, PostStatus
from app.repositories.base_repository import BaseRepository
from app.schemas.base import PaginatedResponse, PaginationParams


class PostRepository(BaseRepository[Post]):
    """
    Repository for Post model operations.

    Inherits common CRUD operations from BaseRepository and adds
    post-specific business logic.
    """

    def __init__(self, db: Session):
        """Initialize PostRepository with Post model."""
        super().__init__(Post, db)

    # ========================================================================
    # POST-SPECIFIC READ METHODS
    # ========================================================================

    def get_by_author_uuid(
        self,
        author_uuid: UUID,
        status: Optional[PostStatus] = PostStatus.PUBLISHED,
        include_deleted: bool = False,
        pagination: Optional[PaginationParams] = None,
    ) -> Union[List[Post], PaginatedResponse[Post]]:
        """
        Get all posts by an author UUID.

        Convenience method that uses get_posts() internally.

        Args:
            author_uuid: The UUID of the author
            status: Optional status filter (e.g., PostStatus.PUBLISHED)
            include_deleted: If True, includes soft-deleted posts
            pagination: Optional pagination parameters

        Returns:
            List of post instances or PaginatedResponse if pagination provided

        Example:
            # Get all posts by author
            posts = post_repo.get_by_author_uuid(user_uuid)

            # Get only published posts by author
            published = post_repo.get_by_author_uuid(
                user_uuid,
                status=PostStatus.PUBLISHED
            )

            # With pagination
            result = post_repo.get_by_author_uuid(
                user_uuid,
                pagination=PaginationParams(page=1, page_size=20)
            )
        """
        return self.get_posts(author_uuid=author_uuid, status=status, include_deleted=include_deleted, pagination=pagination)

    def get_by_title(
        self,
        title: str,
        include_deleted: bool = False,
    ) -> Optional[Post]:
        """
        Get a post by title (case-insensitive).

        Args:
            title: The post title to find
            include_deleted: If True, includes soft-deleted posts

        Returns:
            The post instance if found, None otherwise

        Example:
            post = post_repo.get_by_title("My First Post")
        """

        return self.get_by_text_field({"title": title}, include_deleted=include_deleted)

    # ========================================================================
    # SEARCH METHODS (use BaseRepository methods)
    # ========================================================================

    def get_posts(
        self,
        include_deleted: bool = False,
        pagination: Optional[PaginationParams] = None,
        status: Optional[PostStatus] = PostStatus.PUBLISHED,
        search_term: Optional[str] = None,
        category_uuid: Optional[UUID] = None,
        author_uuid: Optional[UUID] = None,
    ) -> Union[List[Post], PaginatedResponse[Post]]:
        """
        Get posts with flexible filtering options.

        This is the main method for retrieving posts with various filters.
        Supports status, search, category, and author filtering with optional pagination.

        Args:
            include_deleted: If True, includes soft-deleted posts
            pagination: Optional pagination parameters
            status: Filter by post status (default: PUBLISHED)
            search_term: Search in title and content
            category_uuid: Filter posts by category (many-to-many relation)
            author_uuid: Filter posts by author

        Returns:
            List of post instances or PaginatedResponse if pagination provided

        Examples:
            # Get all published posts
            posts = post_repo.get_posts()

            # Search published posts
            posts = post_repo.get_posts(search_term="python")

            # Get posts by category
            posts = post_repo.get_posts(category_uuid=category_id)

            # Get posts by author with pagination
            posts = post_repo.get_posts(
                author_uuid=user_id,
                pagination=PaginationParams(page=1, page_size=20)
            )

            # Complex query: published posts in category with search
            posts = post_repo.get_posts(
                status=PostStatus.PUBLISHED,
                category_uuid=tech_category_id,
                search_term="tutorial",
                pagination=pagination
            )
        """

        filters: Dict[str, Any] = {}
        if status:
            filters["status"] = status
        if author_uuid:
            filters["author_uuid"] = author_uuid

        search_fields = ["title", "content"] if search_term else None

        if category_uuid:
            base_query = self.db.query(self.model).join(self.model.categories).filter(Category.uuid == category_uuid)

        return self.get_multi(
            search_fields=search_fields,
            search_term=search_term,
            filters=filters if filters else None,
            pagination=pagination,
            include_deleted=include_deleted,
            base_query=base_query if category_uuid else None,
        )

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def title_exists(self, title: str, exclude_uuid: Optional[UUID] = None) -> bool:
        """
        Check if a post title already exists (case-insensitive).

        Args:
            title: The title to check
            exclude_uuid: Optional UUID to exclude from check (for updates)

        Returns:
            True if the title exists, False otherwise

        Example:
            if post_repo.title_exists("My Post"):
                raise HTTPException(409, "Title already taken")
        """
        query = self.db.query(self.model.uuid).filter(
            func.lower(self.model.title) == title.lower()
        )
        query = self._apply_soft_delete_filter(query)

        if exclude_uuid:
            query = query.filter(self.model.uuid != exclude_uuid)

        return query.first() is not None

    # ========================================================================
    # GET OR CREATE METHODS (use BaseRepository methods)
    # ========================================================================

    def get_or_create_by_title(self, title: str, defaults: Optional[dict] = None) -> Tuple[Post, bool]:
        """
        Get a post by title or create it if it doesn't exist.

        Uses get_or_create() from BaseRepository.

        Args:
            title: The post title
            defaults: Additional fields to set when creating (optional)

        Returns:
            Tuple of (post_instance, created)

        Example:
            post, created = post_repo.get_or_create_by_title(
                title="My First Post",
                defaults={
                    "author_uuid": user_uuid,
                    "content": "Post content here",
                    "status": PostStatus.DRAFT
                }
            )
        """
        return self.get_or_create(title=title, defaults=defaults)

    # ========================================================================
    # STATISTICS (use BaseRepository count method)
    # ========================================================================

    def count_by_status(self, status: PostStatus) -> int:
        """
        Count posts by status.

        Uses count() from BaseRepository.

        Args:
            status: The status to count (PostStatus enum)

        Returns:
            Number of posts with the specified status

        Example:
            draft_count = post_repo.count_by_status(PostStatus.DRAFT)
        """
        return self.count(filters={"status": status})

    def count_by_author(self, author_uuid: UUID) -> int:
        """
        Count posts by author.

        Uses count() from BaseRepository.

        Args:
            author_uuid: The UUID of the author

        Returns:
            Number of posts created by the author

        Example:
            post_count = post_repo.count_by_author(user_uuid)
        """
        return self.count(filters={"author_uuid": author_uuid})

    def count_published_posts(self) -> int:
        """
        Count all published posts.

        Uses count() from BaseRepository.

        Returns:
            Number of published posts

        Example:
            total_published = post_repo.count_published_posts()
        """
        return self.count(filters={"status": PostStatus.PUBLISHED})

    # ========================================================================
    # POST STATUS UPDATES
    # ========================================================================

    def publish_post(self, post_uuid: UUID) -> Optional[Post]:
        """
        Publish a draft post.

        Uses update() from BaseRepository.

        Args:
            post_uuid: UUID of the post to publish

        Returns:
            Updated post instance, or None if not found

        Example:
            published_post = post_repo.publish_post(post_uuid)
        """
        return self.update(post_uuid, {"status": PostStatus.PUBLISHED})

    def unpublish_post(self, post_uuid: UUID) -> Optional[Post]:
        """
        Unpublish a post (set back to draft).

        Uses update() from BaseRepository.

        Args:
            post_uuid: UUID of the post to unpublish

        Returns:
            Updated post instance, or None if not found

        Example:
            draft_post = post_repo.unpublish_post(post_uuid)
        """
        return self.update(post_uuid, {"status": PostStatus.DRAFT})
