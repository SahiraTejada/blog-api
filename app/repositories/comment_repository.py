from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, overload
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.comments import Comments
from app.repositories.base_repository import BaseRepository
from app.schemas.base import PaginationParams

if TYPE_CHECKING:
    from app.schemas.base import PaginatedResponse


class CommentRepository(BaseRepository[Comments]):
    """
    Repository for Comments model operations.

    Inherits common CRUD operations from BaseRepository and adds
    comment-specific business logic including nested comment tree building.
    """

    def __init__(self, db: Session):
        """Initialize CommentRepository with Comments model."""
        super().__init__(Comments, db)

    # ========================================================================
    # COMMENT-SPECIFIC READ METHODS
    # ========================================================================

    @overload
    def get_by_post_uuid(
        self, post_uuid: UUID, pagination: PaginationParams, include_deleted: bool = ...,
    ) -> PaginatedResponse[Comments]: ...

    @overload
    def get_by_post_uuid(
        self, post_uuid: UUID, pagination: None = ..., include_deleted: bool = ...,
    ) -> List[Comments]: ...

    def get_by_post_uuid(
        self,
        post_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
        include_deleted: bool = False,
    ) -> Union[List[Comments], PaginatedResponse[Comments]]:
        """
        Get top-level comments for a post (where parent_comment_uuid IS NULL).

        Args:
            post_uuid: The UUID of the post
            pagination: Optional pagination parameters
            include_deleted: If True, includes soft-deleted comments

        Returns:
            List of top-level comments or PaginatedResponse if pagination provided
        """
        return self.get_multi(
            filters={"post_uuid": post_uuid, "parent_comment_uuid": None},
            pagination=pagination,
            include_deleted=include_deleted,
            order_by="created_at",
            order_desc=False,
        )

    @overload
    def get_replies(
        self, parent_comment_uuid: UUID, pagination: PaginationParams, include_deleted: bool = ...,
    ) -> PaginatedResponse[Comments]: ...

    @overload
    def get_replies(
        self, parent_comment_uuid: UUID, pagination: None = ..., include_deleted: bool = ...,
    ) -> List[Comments]: ...

    def get_replies(
        self,
        parent_comment_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
        include_deleted: bool = False,
    ) -> Union[List[Comments], PaginatedResponse[Comments]]:
        """
        Get direct replies to a specific comment.

        Args:
            parent_comment_uuid: The UUID of the parent comment
            pagination: Optional pagination parameters
            include_deleted: If True, includes soft-deleted comments

        Returns:
            List of reply comments or PaginatedResponse if pagination provided
        """
        return self.get_multi(
            filters={"parent_comment_uuid": parent_comment_uuid},
            pagination=pagination,
            include_deleted=include_deleted,
            order_by="created_at",
            order_desc=False,
        )

    def get_comment_tree(
        self,
        post_uuid: UUID,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all comments for a post and build a nested tree structure.

        Fetches all comments in a single query, then assembles the tree
        in Python to avoid N+1 queries or recursive SQL.

        Args:
            post_uuid: The UUID of the post
            include_deleted: If True, includes soft-deleted comments

        Returns:
            List of top-level comment dicts, each with a nested 'replies' list.
            Each dict contains: 'comment' (Comments instance) and 'replies' (list).
        """
        # Fetch all comments for the post in one query
        all_comments: List[Comments] = self.get_multi(
            filters={"post_uuid": post_uuid},
            include_deleted=include_deleted,
            order_by="created_at",
            order_desc=False,
        )  # type: ignore[assignment]

        # Build lookup: uuid -> node dict
        nodes: Dict[UUID, Dict[str, Any]] = {}
        for comment in all_comments:
            nodes[comment.uuid] = {"comment": comment, "replies": []}

        # Assemble tree: attach children to their parents
        roots: List[Dict[str, Any]] = []
        for comment in all_comments:
            node = nodes[comment.uuid]
            if comment.parent_comment_uuid and comment.parent_comment_uuid in nodes:
                nodes[comment.parent_comment_uuid]["replies"].append(node)
            else:
                roots.append(node)

        return roots

    @overload
    def get_by_author_uuid(
        self, author_uuid: UUID, pagination: PaginationParams, include_deleted: bool = ...,
    ) -> PaginatedResponse[Comments]: ...

    @overload
    def get_by_author_uuid(
        self, author_uuid: UUID, pagination: None = ..., include_deleted: bool = ...,
    ) -> List[Comments]: ...

    def get_by_author_uuid(
        self,
        author_uuid: UUID,
        pagination: Optional[PaginationParams] = None,
        include_deleted: bool = False,
    ) -> Union[List[Comments], PaginatedResponse[Comments]]:
        """
        Get all comments by a specific user.

        Args:
            author_uuid: The UUID of the author
            pagination: Optional pagination parameters
            include_deleted: If True, includes soft-deleted comments

        Returns:
            List of comments or PaginatedResponse if pagination provided
        """
        return self.get_multi(
            filters={"author_uuid": author_uuid},
            pagination=pagination,
            include_deleted=include_deleted,
            order_by="created_at",
            order_desc=True,
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def count_by_post(self, post_uuid: UUID) -> int:
        """
        Count total comments for a post (all levels).

        Args:
            post_uuid: The UUID of the post

        Returns:
            Total number of comments on the post
        """
        return self.count(filters={"post_uuid": post_uuid})

    def count_by_post_batch(self, post_uuids: List[UUID]) -> Dict[UUID, int]:
        """
        Count total comments for multiple posts in a single query.

        Args:
            post_uuids: List of post UUIDs

        Returns:
            Dictionary mapping post_uuid to comment count
        """
        if not post_uuids:
            return {}

        from sqlalchemy import and_, func

        rows = self.db.query(
            Comments.post_uuid,
            func.count().label("cnt"),
        ).filter(
            and_(
                Comments.post_uuid.in_(post_uuids),
                Comments.deleted_at.is_(None),
            )
        ).group_by(Comments.post_uuid).all()

        counts = {row[0]: row[1] for row in rows}
        return {uuid: counts.get(uuid, 0) for uuid in post_uuids}

    def count_by_author(self, author_uuid: UUID) -> int:
        """
        Count total comments by a user.

        Args:
            author_uuid: The UUID of the author

        Returns:
            Total number of comments by the user
        """
        return self.count(filters={"author_uuid": author_uuid})

    def count_replies(self, parent_comment_uuid: UUID) -> int:
        """
        Count direct replies to a specific comment.

        Args:
            parent_comment_uuid: The UUID of the parent comment

        Returns:
            Number of direct replies
        """
        return self.count(filters={"parent_comment_uuid": parent_comment_uuid})

    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================

    def get_comment_depth(self, comment_uuid: UUID) -> int:
        """
        Calculate the nesting depth of a comment using a recursive CTE.

        Executes a single SQL query instead of O(N) queries.
        Depth 0 = top-level comment, depth 1 = reply to top-level, etc.

        Args:
            comment_uuid: The UUID of the comment

        Returns:
            The nesting depth (0-based)
        """
        from sqlalchemy import func, literal

        # Base case: the target comment at depth 0
        base = (
            self.db.query(
                Comments.uuid,
                Comments.parent_comment_uuid,
                literal(0).label("depth"),
            )
            .filter(Comments.uuid == comment_uuid)
            .cte(name="comment_chain", recursive=True)
        )

        # Recursive step: walk up to the parent
        recursive = (
            self.db.query(
                Comments.uuid,
                Comments.parent_comment_uuid,
                (base.c.depth + 1).label("depth"),
            )
            .join(base, Comments.uuid == base.c.parent_comment_uuid)
        )

        cte = base.union_all(recursive)
        result = self.db.query(func.max(cte.c.depth)).scalar()
        return result or 0

    def parent_exists(self, parent_comment_uuid: UUID) -> bool:
        """
        Verify a parent comment exists and is not deleted.

        Args:
            parent_comment_uuid: The UUID of the parent comment

        Returns:
            True if the parent comment exists and is active
        """
        return self.exists(parent_comment_uuid)

    def parent_belongs_to_post(self, parent_comment_uuid: UUID, post_uuid: UUID) -> bool:
        """
        Ensure a parent comment belongs to the specified post.

        Prevents cross-post nesting where a reply references a comment
        from a different post.

        Args:
            parent_comment_uuid: The UUID of the parent comment
            post_uuid: The UUID of the post

        Returns:
            True if the parent comment belongs to the post
        """
        parent = self.get_by_uuid(parent_comment_uuid)
        if not parent:
            return False
        return parent.post_uuid == post_uuid
