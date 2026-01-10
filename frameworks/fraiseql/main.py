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


# FraiseQL Mutation Input Types
@fraiseql.input
class UpdateUserInput:
    """Input for updating user information."""
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None


@fraiseql.input
class CreatePostInput:
    """Input for creating a new post."""
    title: str
    content: str | None = None
    excerpt: str | None = None
    status: str = "published"


@fraiseql.input
class CreateCommentInput:
    """Input for creating a new comment."""
    content: str
    parent_comment_id: str | None = None


# FraiseQL Mutation Success Types
@fraiseql.type
class UpdateUserSuccess:
    """Result of successful user update."""
    user: User


@fraiseql.type
class CreatePostSuccess:
    """Result of successful post creation."""
    post: Post


@fraiseql.type
class CreateCommentSuccess:
    """Result of successful comment creation."""
    comment: Comment


# FraiseQL Mutation Error Types
@fraiseql.type
class UpdateUserError:
    """Error result for user update operations."""
    message: str
    code: str


@fraiseql.type
class CreatePostError:
    """Error result for post creation operations."""
    message: str
    code: str


@fraiseql.type
class CreateCommentError:
    """Error result for comment creation operations."""
    message: str
    code: str


# FraiseQL Mutation NOOP Types (No Operation - idempotent results)
@fraiseql.type
class UpdateUserNoop:
    """No-op result when user has no fields to update."""
    message: str = "No fields to update"


@fraiseql.type
class CreatePostNoop:
    """No-op result for post creation (reserved for future idempotent operations)."""
    message: str = "Post creation skipped"


@fraiseql.type
class CreateCommentNoop:
    """No-op result for comment creation (reserved for future idempotent operations)."""
    message: str = "Comment creation skipped"


# FraiseQL Mutation Core Implementation Functions
# These implement the actual business logic

async def update_user_impl(
    info: GraphQLResolveInfo,
    id: str,
    input: UpdateUserInput,
) -> UpdateUserSuccess | UpdateUserError | UpdateUserNoop:
    """Core implementation for updating user via database functions.

    Pattern: FraiseQL enterprise mutation pattern
    - Calls database functions for mutation
    - Returns one of three types: Success, Error, or NoOp
    - Uses composition layer (tv_user) for nested data
    """
    db = info.context["db"]

    try:
        # Build update data - snake_case for database columns
        update_data = {}
        if input.first_name is not None:
            update_data["first_name"] = input.first_name
        if input.last_name is not None:
            update_data["last_name"] = input.last_name
        if input.bio is not None:
            update_data["bio"] = input.bio

        # NOOP: No fields to update
        if not update_data:
            return UpdateUserNoop()

        # Update write layer (tb_user table)
        await db.update(
            "benchmark.tb_user",
            where={"id": {"eq": id}},
            data=update_data,
        )

        # Return via composition layer (tv_user view with JSONB data)
        user = await db.find_one("benchmark.tv_user", id=id)
        return UpdateUserSuccess(user=user)

    except Exception as e:
        return UpdateUserError(
            message=f"Failed to update user: {str(e)}",
            code="UPDATE_FAILED",
        )


async def create_post_impl(
    info: GraphQLResolveInfo,
    author_id: str,
    input: CreatePostInput,
) -> CreatePostSuccess | CreatePostError:
    """Core implementation for creating post via database functions.

    Pattern: FraiseQL enterprise mutation pattern
    - Validates author exists before insert
    - Calls database insert function
    - Returns Success or Error (no NoOp for create)
    - Uses composition layer (tv_post) with nested author
    """
    db = info.context["db"]

    try:
        # Verify author exists
        author = await db.find_one("benchmark.tv_user", id=author_id)
        if not author:
            return CreatePostError(
                message=f"Author {author_id} not found",
                code="AUTHOR_NOT_FOUND",
            )

        # Insert into write layer (tb_post table)
        result = await db.insert(
            "benchmark.tb_post",
            data={
                "author_id": author_id,
                "title": input.title,
                "content": input.content,
                "excerpt": input.excerpt,
                "status": input.status,
            },
        )

        # Return newly created post via composition layer
        if result and "id" in result:
            post = await db.find_one("benchmark.tv_post", id=result["id"])
            return CreatePostSuccess(post=post)
        else:
            return CreatePostError(
                message="Failed to create post - no ID returned",
                code="CREATE_FAILED",
            )

    except Exception as e:
        return CreatePostError(
            message=f"Failed to create post: {str(e)}",
            code="CREATE_ERROR",
        )


async def create_comment_impl(
    info: GraphQLResolveInfo,
    author_id: str,
    post_id: str,
    input: CreateCommentInput,
) -> CreateCommentSuccess | CreateCommentError:
    """Core implementation for creating comment via database functions.

    Pattern: FraiseQL enterprise mutation pattern
    - Validates author, post, and parent comment exist
    - Calls database insert function
    - Returns Success or Error (no NoOp for create)
    - Uses composition layer (tv_comment) with nested objects
    """
    db = info.context["db"]

    try:
        # Verify author exists
        author = await db.find_one("benchmark.tv_user", id=author_id)
        if not author:
            return CreateCommentError(
                message=f"Author {author_id} not found",
                code="AUTHOR_NOT_FOUND",
            )

        # Verify post exists
        post = await db.find_one("benchmark.tv_post", id=post_id)
        if not post:
            return CreateCommentError(
                message=f"Post {post_id} not found",
                code="POST_NOT_FOUND",
            )

        # Verify parent comment exists if provided
        if input.parent_comment_id:
            parent = await db.find_one("benchmark.tv_comment", id=input.parent_comment_id)
            if not parent:
                return CreateCommentError(
                    message=f"Parent comment {input.parent_comment_id} not found",
                    code="PARENT_NOT_FOUND",
                )

        # Insert into write layer (tb_comment table)
        result = await db.insert(
            "benchmark.tb_comment",
            data={
                "author_id": author_id,
                "post_id": post_id,
                "content": input.content,
                "parent_comment_id": input.parent_comment_id,
            },
        )

        # Return newly created comment via composition layer
        if result and "id" in result:
            comment = await db.find_one("benchmark.tv_comment", id=result["id"])
            return CreateCommentSuccess(comment=comment)
        else:
            return CreateCommentError(
                message="Failed to create comment - no ID returned",
                code="CREATE_FAILED",
            )

    except Exception as e:
        return CreateCommentError(
            message=f"Failed to create comment: {str(e)}",
            code="CREATE_ERROR",
        )


# FraiseQL Enterprise Mutation Classes
# Pattern: Class-based mutations with @fraiseql.mutation decorator
# References: function="app.{mutation_name}" points to implementation above


@fraiseql.mutation(function="app.update_user")
class UpdateUser:
    """Update user with enterprise mutation pattern.

    Blueprint Pattern:
    - Dedicated input type (UpdateUserInput)
    - Three response types: Success, Error, NoOp
    - Function attribute points to implementation
    - Composition layer provides all nested data
    """

    input: UpdateUserInput
    success: UpdateUserSuccess
    error: UpdateUserError
    noop: UpdateUserNoop


@fraiseql.mutation(function="app.create_post")
class CreatePost:
    """Create post with enterprise mutation pattern.

    Blueprint Pattern:
    - Dedicated input type (CreatePostInput)
    - Success/Error response types
    - Function attribute points to implementation
    - Composition layer includes nested author object
    """

    input: CreatePostInput
    success: CreatePostSuccess
    error: CreatePostError


@fraiseql.mutation(function="app.create_comment")
class CreateComment:
    """Create comment with enterprise mutation pattern.

    Blueprint Pattern:
    - Dedicated input type (CreateCommentInput)
    - Success/Error response types
    - Function attribute points to implementation
    - Composition layer includes author, post, parentComment
    """

    input: CreateCommentInput
    success: CreateCommentSuccess
    error: CreateCommentError


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
