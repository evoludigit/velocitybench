"""FraiseQL Schema Definition for VelocityBench

This schema defines the GraphQL types and queries/mutations for the VelocityBench
FraiseQL framework. It maps to the JSONB views created in the database (v_user,
v_post, v_comment) which implement the FraiseQL pattern of pre-shaped JSONB data.

Architecture:
- Types defined with @fraiseql.type decorators
- Queries reference JSONB views (v_user, v_post, v_comment)
- fraiseql-cli compiles schema.py -> schema.json -> schema.compiled.json
- fraiseql-server executes queries against compiled schema and database views

Usage:
    python schema.py              # Export schema.json
    fraiseql-cli compile schema.json
    fraiseql-server --schema schema.compiled.json --database-url postgresql://...
"""

import fraiseql


# ============================================================================
# Type Definitions
# ============================================================================


@fraiseql.type
class User:
    """User type representing a platform user."""

    id: str  # UUID
    email: str
    username: str
    firstName: str | None
    lastName: str | None
    bio: str | None
    avatarUrl: str | None
    isActive: bool
    createdAt: str  # ISO 8601 timestamp
    updatedAt: str  # ISO 8601 timestamp


@fraiseql.type
class Post:
    """Post type representing a blog post."""

    id: str  # UUID
    title: str
    content: str | None
    excerpt: str | None
    status: str  # 'draft', 'published', 'archived'
    author: User  # Nested relationship pre-computed in JSONB
    publishedAt: str | None  # ISO 8601 timestamp
    createdAt: str  # ISO 8601 timestamp
    updatedAt: str  # ISO 8601 timestamp


@fraiseql.type
class Comment:
    """Comment type representing a comment on a post."""

    id: str  # UUID
    content: str
    isApproved: bool
    author: User  # Nested relationship pre-computed in JSONB
    post: Post  # Nested relationship pre-computed in JSONB
    createdAt: str  # ISO 8601 timestamp
    updatedAt: str  # ISO 8601 timestamp


# ============================================================================
# Query Definitions
# ============================================================================


@fraiseql.query(
    sql_source="v_user",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def users(
    limit: int = 10,
    offset: int = 0,
    is_active: bool | None = None,
) -> list[User]:
    """Get list of users with pagination and filtering.

    Args:
        limit: Maximum number of users to return (default: 10)
        offset: Number of users to skip (default: 0)
        is_active: Filter by active status (optional)

    Returns:
        List of User objects
    """
    pass


@fraiseql.query(sql_source="v_user")
def user(id: str) -> User | None:
    """Get a single user by UUID.

    Args:
        id: User UUID

    Returns:
        User object or None if not found
    """
    pass


@fraiseql.query(
    sql_source="v_post",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def posts(
    limit: int = 10,
    offset: int = 0,
    status: str | None = None,
    author_id: str | None = None,
) -> list[Post]:
    """Get list of posts with filtering and pagination.

    Args:
        limit: Maximum number of posts to return (default: 10)
        offset: Number of posts to skip (default: 0)
        status: Filter by status ('draft', 'published', 'archived')
        author_id: Filter by author UUID

    Returns:
        List of Post objects
    """
    pass


@fraiseql.query(sql_source="v_post")
def post(id: str) -> Post | None:
    """Get a single post by UUID.

    Args:
        id: Post UUID

    Returns:
        Post object or None if not found
    """
    pass


@fraiseql.query(
    sql_source="v_comment",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def comments(
    limit: int = 10,
    offset: int = 0,
    post_id: str | None = None,
    author_id: str | None = None,
    is_approved: bool | None = None,
) -> list[Comment]:
    """Get list of comments with filtering and pagination.

    Args:
        limit: Maximum number of comments to return (default: 10)
        offset: Number of comments to skip (default: 0)
        post_id: Filter by post UUID
        author_id: Filter by author UUID
        is_approved: Filter by approval status

    Returns:
        List of Comment objects
    """
    pass


@fraiseql.query(sql_source="v_comment")
def comment(id: str) -> Comment | None:
    """Get a single comment by UUID.

    Args:
        id: Comment UUID

    Returns:
        Comment object or None if not found
    """
    pass


# ============================================================================
# Mutation Definitions (if needed)
# ============================================================================
# Note: FraiseQL mutations would reference database functions (fn_* pattern)
# For now, queries are sufficient for benchmarking read performance


if __name__ == "__main__":
    # Export schema to JSON
    # This creates schema.json that will be compiled by fraiseql-cli
    fraiseql.export_schema("schema.json")

    print("\n✅ FraiseQL schema exported successfully!")
    print("   Location: schema.json")
    print("\n   Next steps:")
    print("   1. Compile schema:   fraiseql-cli compile schema.json")
    print("   2. Start server:     fraiseql-server --schema schema.compiled.json")
    print("   3. Query GraphQL:    curl -X POST http://localhost:3000/graphql")
