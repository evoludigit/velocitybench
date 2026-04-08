"""FraiseQL v2 Schema Definition for VelocityBench (TV Tables — Audit Variant)

Identical to schema_tv.py except mutations point to the _full SQL functions,
which add: before/after snapshots, log_mutation_event() audit logging,
cascade invalidation data, and structured error details.

Benchmark Variant C: measures the overhead of production-grade mutation logging
vs the lean variant (schema_tv.py). Read queries are identical.

Usage:
    python schema_tv_audit.py                       # Export schema_tv_audit.json
    fraiseql-cli compile fraiseql-build-tv-audit.toml
    fraiseql-server  (FRAISEQL_CONFIG=fraiseql-tv-audit.toml)
"""

import fraiseql
from fraiseql.scalars import ID, DateTime


@fraiseql.type
class User:
    """User type representing a platform user."""

    id: ID
    identifier: str

    email: str
    username: str
    full_name: str
    bio: str | None
    created_at: DateTime
    updated_at: DateTime


@fraiseql.type
class Post:
    """Post type representing a blog post."""

    id: ID
    identifier: str

    title: str
    content: str
    published: bool
    author: User
    created_at: DateTime
    updated_at: DateTime


@fraiseql.type
class Comment:
    """Comment type representing a comment on a post."""

    id: ID
    identifier: str | None

    content: str
    author: User
    post: Post
    created_at: DateTime
    updated_at: DateTime


@fraiseql.query(
    sql_source="tv_user",
    auto_params={"limit": True, "offset": True, "where": True, "order_by": True},
)
def users(
    limit: int = 10,
    offset: int = 0,
) -> list[User]:
    """Get list of users with pagination."""
    pass


@fraiseql.query(sql_source="tv_user")
def user(id: ID) -> User | None:
    """Get a single user by UUID."""
    pass


@fraiseql.query(
    sql_source="tv_post",
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


@fraiseql.query(sql_source="tv_post")
def post(id: ID) -> Post | None:
    """Get a single post by UUID."""
    pass


@fraiseql.query(
    sql_source="tv_comment",
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


@fraiseql.query(sql_source="tv_comment")
def comment(id: ID) -> Comment | None:
    """Get a single comment by UUID."""
    pass


# Mutations point to the _full variants: snapshot + audit log + cascade data
@fraiseql.mutation(sql_source="fn_update_user_full", operation="UPDATE")
def updateUser(id: ID, bio: str | None = None) -> User | None:
    """Update a user's bio. Logs before/after snapshot to tb_mutation_log."""
    pass


@fraiseql.mutation(sql_source="fn_create_post_full", operation="CREATE")
def createPost(
    title: str,
    content: str,
    author_id: ID,
    published: bool = False,
) -> Post | None:
    """Create a new post. Logs snapshot to tb_mutation_log and returns cascade data."""
    pass


if __name__ == "__main__":
    fraiseql.export_schema("schema_tv_audit.json")

    print("\n✅ FraiseQL v2 schema (TV tables, audit variant) exported!")
    print("   Location: schema_tv_audit.json")
    print("\n   Next steps:")
    print("   1. Compile: fraiseql-cli compile fraiseql-build-tv-audit.toml")
    print("   2. Start:   fraiseql-server  (FRAISEQL_CONFIG=fraiseql-tv-audit.toml)")
