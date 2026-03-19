"""FraiseQL v2 Schema Definition for VelocityBench

This schema defines the GraphQL types and queries for the VelocityBench
FraiseQL v2 framework. It maps to the JSONB views in the database
(v_user, v_post, v_comment).

FraiseQL v2 Architecture:
- Types defined with @fraiseql.type decorator
- Trinity pattern: every type exposes pk (int), id (ID), identifier (str)
- Queries use @fraiseql.query with sql_source parameter
- fraiseql-cli compiles schema.py -> schema.json -> schema.compiled.json
- fraiseql-server executes queries against compiled schema

Benchmark Variant A (this file):
- Views (v_*) compute JSONB on-the-fly at query time
- camelCase field names match GraphQL convention

Usage:
    python schema.py                        # Export schema.json
    fraiseql-cli compile fraiseql.toml      # Compile to schema.compiled.json
    fraiseql-server                         # Start (reads FRAISEQL_CONFIG)
"""

import fraiseql
from fraiseql.scalars import ID, DateTime

# ============================================================================
# Type Definitions — Trinity Pattern (pk / id / identifier)
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
# Query Definitions — sql_source maps to benchmark schema views
# ============================================================================


@fraiseql.query(
    sql_source="benchmark.v_user",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def users(
    limit: int = 10,
    offset: int = 0,
) -> list[User]:
    """Get list of users with pagination."""
    pass


@fraiseql.query(sql_source="benchmark.v_user")
def user(id: ID) -> User | None:
    """Get a single user by UUID."""
    pass


@fraiseql.query(
    sql_source="benchmark.v_post",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def posts(
    limit: int = 10,
    offset: int = 0,
    published: bool | None = None,
    authorId: ID | None = None,
) -> list[Post]:
    """Get list of posts with filtering and pagination."""
    pass


@fraiseql.query(sql_source="benchmark.v_post")
def post(id: ID) -> Post | None:
    """Get a single post by UUID."""
    pass


@fraiseql.query(
    sql_source="benchmark.v_comment",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def comments(
    limit: int = 10,
    offset: int = 0,
    postId: ID | None = None,
    authorId: ID | None = None,
) -> list[Comment]:
    """Get list of comments with filtering and pagination."""
    pass


@fraiseql.query(sql_source="benchmark.v_comment")
def comment(id: ID) -> Comment | None:
    """Get a single comment by UUID."""
    pass


# ============================================================================
# Mutation Definitions — write through tb_* CQRS command tables
# pg_tviews triggers auto-cascade writes to v_* views
# ============================================================================


@fraiseql.mutation(sql_source="benchmark.fn_update_user", operation="UPDATE")
def updateUser(id: ID, bio: str | None = None) -> User | None:
    """Update a user's bio. Returns the updated user."""
    pass


@fraiseql.mutation(sql_source="benchmark.fn_create_post", operation="CREATE")
def createPost(
    title: str,
    content: str,
    authorId: ID,
    published: bool = False,
) -> Post | None:
    """Create a new post. Returns the created post."""
    pass


# ============================================================================
# Schema Export
# ============================================================================

if __name__ == "__main__":
    fraiseql.export_schema("schema.json")

    print("\n✅ FraiseQL v2 schema exported successfully!")
    print("   Location: schema.json")
    print("\n   Next steps:")
    print("   1. Compile schema:  fraiseql-cli compile fraiseql.toml")
    print("   2. Start server:    fraiseql-server  (reads FRAISEQL_CONFIG env var)")
    print("   3. Query GraphQL:   curl -X POST http://localhost:8815/graphql")
