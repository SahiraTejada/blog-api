from typing import List, Optional, Tuple
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
        include_deleted: bool = False
    ) -> List[Post]:
        """
        Get all posts by an author UUID.

        Args:
            author_uuid: The UUID of the author
            status: Optional status filter (e.g., PostStatus.PUBLISHED)
            include_deleted: If True, includes soft-deleted posts

        Returns:
            List of post instances created by the author, empty list if none found

        Example:
            # Get all posts by author
            posts = post_repo.get_by_author_uuid(user_uuid)

            # Get only published posts by author
            published = post_repo.get_by_author_uuid(
                user_uuid, 
                status=PostStatus.PUBLISHED
            )
        """
        filters = {"author_uuid": author_uuid}
        if status:
            filters["status"] = status

        return self.filter_by(include_deleted=include_deleted, **filters)

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
        filters = {"title": title.lower()}

        return self.filter_by(include_deleted=include_deleted, **filters)

    # ========================================================================
    # SEARCH METHODS (use BaseRepository methods)
    # ========================================================================

    def search_posts(
        self,
        search_term: str,
        include_deleted: bool = False
    ) -> List[Post]:
        """
        Search posts by title or content.

        Uses search() from BaseRepository.

        Args:
            search_term: Text to search for
            include_deleted: If True, includes soft-deleted posts

        Returns:
            List of all matching post instances

        Example:
            posts = post_repo.search_posts("python")
        """
        return self.search(
            search_fields=["title", "content"],
            search_term=search_term,
            include_deleted=include_deleted
        )

    def search_posts_paginated(
        self,
        search_term: str,
        pagination: PaginationParams,
        include_deleted: bool = False
    ) -> PaginatedResponse[Post]:
        """
        Search posts with pagination.

        Uses search_paginated() from BaseRepository.

        Args:
            search_term: Text to search for
            pagination: PaginationParams with page and page_size
            include_deleted: If True, includes soft-deleted posts

        Returns:
            PaginatedResponse with matching posts and pagination metadata

        Example:
            pagination = PaginationParams(page=1, page_size=20)
            result = post_repo.search_posts_paginated("python", pagination)
        """
        return self.search_paginated(
            search_fields=["title", "content"],
            search_term=search_term,
            pagination=pagination,
            include_deleted=include_deleted
        )

    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================

    def title_exists(
        self,
        title: str,
        exclude_uuid: Optional[UUID] = None
    ) -> bool:
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
        ).filter(self.model.deleted_at.is_(None))

        if exclude_uuid:
            query = query.filter(self.model.uuid != exclude_uuid)

        return query.first() is not None

    # ========================================================================
    # GET OR CREATE METHODS (use BaseRepository methods)
    # ========================================================================

    def get_or_create_by_title(
        self,
        title: str,
        defaults: Optional[dict] = None
    ) -> Tuple[Post, bool]:
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
        return self.get_or_create(
            title=title,
            defaults=defaults
        )

    # ========================================================================
    # POST-SPECIFIC METHODS (use BaseRepository methods where possible)
    # ========================================================================

    def get_posts_by_status(
        self,
        status: PostStatus,
        include_deleted: bool = False
    ) -> List[Post]:
        """
        Get all posts with a specific status.

        Uses filter_by() from BaseRepository.

        Args:
            status: The status to filter by (PostStatus enum)
            include_deleted: If True, includes soft-deleted posts

        Returns:
            List of posts with the specified status

        Example:
            published_posts = post_repo.get_posts_by_status(PostStatus.PUBLISHED)
        """
        return self.filter_by(
            status=status,
            include_deleted=include_deleted
        )

    def get_posts_by_status_paginated(
        self,
        status: PostStatus,
        pagination: PaginationParams,
        include_deleted: bool = False
    ) -> PaginatedResponse[Post]:
        """
        Get posts by status with pagination.

        Uses get_multi_paginated() from BaseRepository.

        Args:
            status: The status to filter by (PostStatus enum)
            pagination: PaginationParams with page and page_size
            include_deleted: If True, includes soft-deleted posts

        Returns:
            PaginatedResponse with posts and pagination metadata

        Example:
            pagination = PaginationParams(page=1, page_size=20)
            result = post_repo.get_posts_by_status_paginated(
                PostStatus.PUBLISHED, 
                pagination
            )
        """
        return self.get_multi_paginated(
            pagination=pagination,
            filters={"status": status},
            include_deleted=include_deleted,
            order_by="created_at",
            order_desc=True
        )

    def get_posts_by_category(
        self,
        category_uuid: UUID,
        include_deleted: bool = False
    ) -> List[Post]:
        """
        Get all posts in a specific category.

        Args:
            category_uuid: The UUID of the category
            include_deleted: If True, includes soft-deleted posts

        Returns:
            List of posts in the specified category

        Example:
            posts = post_repo.get_posts_by_category(category_uuid)
        """
        query = self.db.query(self.model).join(
            self.model.categories
        ).filter(
            Category.uuid == category_uuid
        )

        if not include_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        return query.all()

    def get_published_posts(
        self,
        pagination: Optional[PaginationParams] = None,
        include_deleted: bool = False
    ) -> List[Post] | PaginatedResponse[Post]:
        """
        Get all published posts, optionally paginated.

        Uses filter_by() or get_multi_paginated() from BaseRepository.

        Args:
            pagination: Optional pagination parameters
            include_deleted: If True, includes soft-deleted posts

        Returns:
            List of published posts or PaginatedResponse if pagination provided

        Example:
            # Get all published posts
            posts = post_repo.get_published_posts()

            # Get paginated published posts
            pagination = PaginationParams(page=1, page_size=20)
            result = post_repo.get_published_posts(pagination)
        """
        if pagination:
            return self.get_multi_paginated(
                pagination=pagination,
                filters={"status": PostStatus.PUBLISHED},
                include_deleted=include_deleted,
                order_by="created_at",
                order_desc=True
            )

        return self.filter_by(
            status=PostStatus.PUBLISHED,
            include_deleted=include_deleted
        )

    def get_draft_posts(
        self,
        pagination: Optional[PaginationParams] = None,
        include_deleted: bool = False
    ) -> List[Post] | PaginatedResponse[Post]:
        """
        Get all draft posts, optionally paginated.

        Uses filter_by() or get_multi_paginated() from BaseRepository.

        Args:
            pagination: Optional pagination parameters
            include_deleted: If True, includes soft-deleted posts

        Returns:
            List of draft posts or PaginatedResponse if pagination provided

        Example:
            drafts = post_repo.get_draft_posts()
        """
        if pagination:
            return self.get_multi_paginated(
                pagination=pagination,
                filters={"status": PostStatus.DRAFT},
                include_deleted=include_deleted,
                order_by="updated_at",
                order_desc=True
            )

        return self.filter_by(
            status=PostStatus.DRAFT,
            include_deleted=include_deleted
        )

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
