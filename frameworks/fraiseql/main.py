#!/usr/bin/env python3
"""
FraiseQL Comparative Benchmarking Implementation v1.8.1
Optimized GraphQL server using FraiseQL with Rust pipeline for performance testing against other frameworks.

Architecture: Three-layer view system
1. tb_* (write layer): Tables with pk_*, id (UUID), fk_* (internal FKs)
2. v_* (projection layer): Scalar extraction from tb_* tables
3. tv_* (composition layer): JSONB denormalized objects for FraiseQL GraphQL

FraiseQL queries tv_* views which provide JSONB 'data' field with:
- All scalar fields in camelCase (id, username, firstName, lastName, bio, etc.)
- Nested objects (author, post, parentComment) as pre-composed JSONB
- No need for N+1 queries - all composition done at database layer
"""

import logging
import os
from typing import Any

# FraiseQL v1.8.1 imports
import fraiseql
import prometheus_client
import uvicorn
from fastapi import Request
from fraiseql.fastapi import FraiseQLConfig, create_fraiseql_app
from fraiseql.fastapi.config import IntrospectionPolicy
from fraiseql.types import UUID
from graphql import GraphQLResolveInfo


# FraiseQL Configuration
def create_fraiseql_config() -> FraiseQLConfig:
    """Create FraiseQL configuration for benchmarking."""
    return FraiseQLConfig(
        database_url=f"postgresql://{os.getenv('DB_USER', 'benchmark')}:{os.getenv('DB_PASSWORD', 'benchmark123')}@{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'fraiseql_benchmark')}",
        environment="development",
        introspection_policy=IntrospectionPolicy.PUBLIC,
        enable_playground=True,
        default_query_schema="benchmark",  # Query from benchmark schema where views live
        default_mutation_schema="benchmark",  # Mutations update tb_* tables in benchmark schema
        auto_camel_case=True,  # Convert snake_case from DB to camelCase in GraphQL
        cors_enabled=True,
        complexity_enabled=False,  # Disable for benchmarking
        database_pool_size=20,
        database_max_overflow=10,
        max_query_depth=10,
    )


# FraiseQL GraphQL Types
# These map to tv_* views which provide JSONB 'data' field with composed objects

@fraiseql.type(sql_source="benchmark.tv_user")
class User:
    """User type - queries tv_user view returning JSONB-composed user objects."""
    id: UUID
    username: str
    email: str
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    created_at: str
    updated_at: str


@fraiseql.type(sql_source="benchmark.tv_post")
class Post:
    """Post type - queries tv_post view returning JSONB-composed posts with author."""
    id: UUID
    title: str
    content: str | None = None
    excerpt: str | None = None
    status: str = "published"
    published_at: str | None = None
    created_at: str
    updated_at: str
    # author field is pre-composed in tv_post JSONB, FraiseQL will deserialize it
    author: User


@fraiseql.type(sql_source="benchmark.tv_comment")
class Comment:
    """Comment type - queries tv_comment view returning JSONB-composed comments with author, post, parent."""
    id: UUID
    content: str
    is_approved: bool = True
    created_at: str
    updated_at: str
    # Nested objects are pre-composed in tv_comment JSONB
    author: User
    post: Post
    parent_comment: "Comment | None" = None


# FraiseQL Query Resolvers
@fraiseql.query
async def ping(info: GraphQLResolveInfo) -> str:
    """Simple ping query for throughput testing."""
    return "pong"


@fraiseql.query
async def user(info: GraphQLResolveInfo, id: str) -> User | None:
    """Get user by UUID id."""
    db = info.context["db"]
    return await db.find_one("benchmark.tv_user", id=id)


@fraiseql.query
async def users(info: GraphQLResolveInfo, limit: int = 10) -> list[User]:
    """Get users list with pagination."""
    db = info.context["db"]
    return await db.find("benchmark.tv_user", limit=limit, order_by=[{"created_at": "DESC"}])


@fraiseql.query
async def posts(info: GraphQLResolveInfo, limit: int = 10) -> list[Post]:
    """Get posts list - with pre-composed author objects."""
    db = info.context["db"]
    # tv_post view includes author as nested JSONB object
    return await db.find("benchmark.tv_post", limit=limit, order_by=[{"created_at": "DESC"}])


@fraiseql.query
async def comments(info: GraphQLResolveInfo, limit: int = 10) -> list[Comment]:
    """Get comments list - with pre-composed author, post, and parent comment objects."""
    db = info.context["db"]
    # tv_comment view includes author, post, and parentComment as nested JSONB objects
    return await db.find("benchmark.tv_comment", limit=limit, order_by=[{"created_at": "DESC"}])


@fraiseql.query
async def post(info: GraphQLResolveInfo, id: str) -> Post | None:
    """Get post by UUID id - includes pre-composed author object."""
    db = info.context["db"]
    return await db.find_one("benchmark.tv_post", id=id)


@fraiseql.query
async def comment(info: GraphQLResolveInfo, id: str) -> Comment | None:
    """Get comment by UUID id - includes pre-composed author, post, and parent comment objects."""
    db = info.context["db"]
    return await db.find_one("benchmark.tv_comment", id=id)


# FraiseQL Mutation Resolvers
@fraiseql.mutation
async def update_user(
    info: GraphQLResolveInfo,
    id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    bio: str | None = None,
) -> User | None:
    """Update user by UUID id.

    Updates tb_user table (write layer) and returns via tv_user (composition layer).
    """
    db = info.context["db"]

    # Build update data - snake_case for database columns
    update_data = {}
    if first_name is not None:
        update_data["first_name"] = first_name
    if last_name is not None:
        update_data["last_name"] = last_name
    if bio is not None:
        update_data["bio"] = bio

    if update_data:
        update_data["updated_at"] = "NOW()"  # SQL function

        # Update write layer (tb_user table)
        await db.update("benchmark.tb_user", where={"id": {"eq": id}}, data=update_data)

    # Return via composition layer (tv_user view with JSONB data)
    return await db.find_one("benchmark.tv_user", id=id)


@fraiseql.mutation
async def create_post(
    info: GraphQLResolveInfo,
    author_id: str,
    title: str,
    content: str | None = None,
    excerpt: str | None = None,
    status: str = "published",
) -> Post | None:
    """Create post mutation.

    Inserts into tb_post table (write layer) and returns via tv_post (composition layer).
    Note: author_id is the UUID id, FraiseQL will convert to internal pk_author via view join.
    """
    db = info.context["db"]

    # Insert into write layer (tb_post table)
    # The view will join with author using fk_author -> pk_user mapping
    insert_data = {
        "author_id": author_id,
        "title": title,
        "content": content,
        "excerpt": excerpt,
        "status": status,
    }

    result = await db.insert("benchmark.tb_post", data=insert_data)

    # Return newly created post via composition layer
    if result:
        return await db.find_one("benchmark.tv_post", id=result["id"])
    return None


@fraiseql.mutation
async def create_comment(
    info: GraphQLResolveInfo,
    author_id: str,
    post_id: str,
    content: str,
    parent_comment_id: str | None = None,
) -> Comment | None:
    """Create comment mutation.

    Inserts into tb_comment table (write layer) and returns via tv_comment (composition layer).
    """
    db = info.context["db"]

    insert_data = {
        "author_id": author_id,
        "post_id": post_id,
        "content": content,
        "parent_comment_id": parent_comment_id,
    }

    result = await db.insert("benchmark.tb_comment", data=insert_data)

    # Return newly created comment via composition layer
    if result:
        return await db.find_one("benchmark.tv_comment", id=result["id"])
    return None


# Context getter for FraiseQL
async def get_context(request: Request) -> dict[str, Any]:
    """Context creation for FraiseQL requests."""
    # Return empty context - FraiseQL will inject database automatically
    return {}


# Create FraiseQL app
app = create_fraiseql_app(
    config=create_fraiseql_config(),
    context_getter=get_context,
    title="FraiseQL Comparative Benchmark v1.8.1",
    description="FraiseQL GraphQL server using Rust pipeline for performance testing",
    production=False,
)


# Add additional routes for health and metrics
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "framework": "fraiseql", "version": "1.8.1"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import Response

    return Response(
        media_type="text/plain", content=prometheus_client.generate_latest()
    )


def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=4000, log_level="info")


if __name__ == "__main__":
    main()
