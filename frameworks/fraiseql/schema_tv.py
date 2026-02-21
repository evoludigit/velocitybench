"""FraiseQL v2 Schema Definition for VelocityBench (TV Tables — pre-computed JSONB)

This schema defines the GraphQL types and queries for the VelocityBench
FraiseQL v2 framework using pre-computed JSONB tables (tv_*).

Benchmark Variant B (this file):
- Pre-computed JSONB tables (tv_*): JSONB baked in at INSERT time, not query time
- camelCase field names align with GraphQL convention and the stored JSONB keys
- Avoids join overhead at query time (data is denormalized at write time)

Trinity pattern: every type exposes id (ID), identifier (str)

Usage:
    python schema_tv.py                          # Export schema_tv.json
    fraiseql-cli compile schema_tv.json          # Compile to schema_tv.compiled.json
    fraiseql-server                              # Start with appropriate config
"""

import fraiseql
from fraiseql.scalars import ID, DateTime

# ============================================================================
# Type Definitions — Trinity Pattern, camelCase keys (match tv_* JSONB)
# ============================================================================


@fraiseql.type
class User:
    """User type representing a platform user."""

    id: ID  # Public UUID (GraphQL ID scalar)
    identifier: str  # Human-readable identifier (username)

    email: str
    username: str
    fullName: str
    bio: str | None
    createdAt: DateTime
    updatedAt: DateTime


@fraiseql.type
class Post:
    """Post type representing a blog post."""

    id: ID  # Public UUID
    identifier: str  # Human-readable identifier (slug)

    title: str
    content: str
    published: bool
    author: User  # Nested relationship pre-computed in JSONB
    createdAt: DateTime
    updatedAt: DateTime


@fraiseql.type
class Comment:
    """Comment type representing a comment on a post."""

    id: ID  # Public UUID
    identifier: str | None  # Optional human-readable identifier

    content: str
    author: User  # Nested relationship pre-computed in JSONB
    post: Post  # Nested relationship pre-computed in JSONB
    createdAt: DateTime
    updatedAt: DateTime


# ============================================================================
# Query Definitions — sql_source maps to benchmark.tv_* pre-computed tables
# ============================================================================


@fraiseql.query(
    sql_source="benchmark.tv_user",
    jsonb_column="data",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def users(
    limit: int = 10,
    offset: int = 0,
) -> list[User]:
    """Get list of users with pagination."""
    pass


@fraiseql.query(sql_source="benchmark.tv_user", jsonb_column="data")
def user(id: ID) -> User | None:
    """Get a single user by UUID."""
    pass


@fraiseql.query(
    sql_source="benchmark.tv_post",
    jsonb_column="data",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def posts(
    limit: int = 10,
    offset: int = 0,
    published: bool | None = None,
    author_id: ID | None = None,
) -> list[Post]:
    """Get list of posts with filtering and pagination."""
    pass


@fraiseql.query(sql_source="benchmark.tv_post", jsonb_column="data")
def post(id: ID) -> Post | None:
    """Get a single post by UUID."""
    pass


@fraiseql.query(
    sql_source="benchmark.tv_comment",
    jsonb_column="data",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def comments(
    limit: int = 10,
    offset: int = 0,
    post_id: ID | None = None,
    author_id: ID | None = None,
) -> list[Comment]:
    """Get list of comments with filtering and pagination."""
    pass


@fraiseql.query(sql_source="benchmark.tv_comment", jsonb_column="data")
def comment(id: ID) -> Comment | None:
    """Get a single comment by UUID."""
    pass


# ============================================================================
# Schema Export
# ============================================================================

if __name__ == "__main__":
    fraiseql.export_schema("schema_tv.json")

    print("\n✅ FraiseQL v2 schema (TV tables) exported!")
    print("   Location: schema_tv.json")
    print("\n   Next steps:")
    print("   1. Compile: fraiseql-cli compile schema_tv.json")
    print(
        "   2. Start:   fraiseql-server  (point FRAISEQL_CONFIG at tv variant config)"
    )
