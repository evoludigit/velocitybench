#!/usr/bin/env python3
"""
ASGI GraphQL Server for VelocityBench

Generic ASGI GraphQL implementation using graphql-core directly with Starlette.
This demonstrates using the reference GraphQL implementation without a framework.

Features:
- Direct graphql-core usage (the Python reference implementation)
- DataLoader for N+1 prevention
- asyncpg connection pooling
- Starlette ASGI integration
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

from graphql import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString,
    GraphQLInt,
    GraphQLID,
    GraphQLList,
    GraphQLNonNull,
    GraphQLArgument,
    graphql,
)
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.async_db import AsyncDatabase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ============================================================================
# DataLoader Implementation
# ============================================================================

class DataLoader:
    """Simple DataLoader implementation for batching database queries."""

    def __init__(self, batch_fn):
        self.batch_fn = batch_fn
        self._queue = {}
        self._cache = {}
        self._scheduled = False

    async def load(self, key: str) -> Any:
        """Load a single key, batching with other pending loads."""
        if key in self._cache:
            return self._cache[key]

        if key not in self._queue:
            self._queue[key] = asyncio.get_event_loop().create_future()

        if not self._scheduled:
            self._scheduled = True
            asyncio.get_event_loop().call_soon(
                lambda: asyncio.create_task(self._dispatch())
            )

        return await self._queue[key]

    async def _dispatch(self):
        """Execute batch load for all queued keys."""
        self._scheduled = False
        if not self._queue:
            return

        keys = list(self._queue.keys())
        futures = [self._queue[k] for k in keys]
        self._queue.clear()

        try:
            results = await self.batch_fn(keys)
            for key, future, result in zip(keys, futures, results):
                self._cache[key] = result
                if not future.done():
                    future.set_result(result)
        except Exception as e:
            for future in futures:
                if not future.done():
                    future.set_exception(e)


# ============================================================================
# Database Batch Loaders
# ============================================================================

async def load_users_batch(keys: list[str], db: AsyncDatabase) -> list[dict | None]:
    """Batch load users by IDs."""
    try:
        result = await db.fetch(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = ANY($1)",
            keys,
            timeout=5.0
        )
        user_map = {str(user["id"]): user for user in result}
        return [user_map.get(key) for key in keys]
    except Exception as e:
        logger.exception(f"Error loading users batch: {e}")
        return [None] * len(keys)


async def load_posts_batch(keys: list[str], db: AsyncDatabase) -> list[dict | None]:
    """Batch load posts by IDs."""
    try:
        result = await db.fetch(
            """
            SELECT p.id, p.title, p.content, u.id as author_id
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE p.id = ANY($1)
            """,
            keys,
            timeout=5.0
        )
        post_map = {str(post["id"]): post for post in result}
        return [post_map.get(key) for key in keys]
    except Exception as e:
        logger.exception(f"Error loading posts batch: {e}")
        return [None] * len(keys)


async def load_posts_by_author_batch(keys: list[str], db: AsyncDatabase) -> list[list[dict]]:
    """Batch load posts by author IDs."""
    try:
        result = await db.fetch(
            """
            SELECT p.id, p.title, p.content, u.id as author_id
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE u.id = ANY($1)
            ORDER BY u.id, p.created_at DESC
            """,
            keys,
            timeout=5.0
        )
        posts_by_author = {key: [] for key in keys}
        for post in result:
            author_id = str(post["author_id"])
            if author_id in posts_by_author:
                posts_by_author[author_id].append(post)
        return [posts_by_author[key] for key in keys]
    except Exception as e:
        logger.exception(f"Error loading posts by author: {e}")
        return [[] for _ in keys]


async def load_comments_by_post_batch(keys: list[str], db: AsyncDatabase) -> list[list[dict]]:
    """Batch load comments by post IDs."""
    try:
        result = await db.fetch(
            """
            SELECT c.id, c.content, p.id as post_id, u.id as author_id
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            WHERE p.id = ANY($1)
            ORDER BY p.id, c.created_at DESC
            """,
            keys,
            timeout=5.0
        )
        comments_by_post = {key: [] for key in keys}
        for comment in result:
            post_id = str(comment["post_id"])
            if post_id in comments_by_post:
                comments_by_post[post_id].append(comment)
        return [comments_by_post[key] for key in keys]
    except Exception as e:
        logger.exception(f"Error loading comments by post: {e}")
        return [[] for _ in keys]


# ============================================================================
# UUID Validation
# ============================================================================

def validate_uuid(value: str) -> bool:
    """Validate that value is a valid UUID."""
    try:
        UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


# ============================================================================
# GraphQL Type Definitions (using graphql-core directly)
# ============================================================================

# Forward references for circular type resolution
user_type = None
post_type = None
comment_type = None


def get_user_type():
    global user_type
    if user_type is None:
        user_type = GraphQLObjectType(
            "User",
            lambda: {
                "id": GraphQLField(GraphQLNonNull(GraphQLID)),
                "username": GraphQLField(GraphQLNonNull(GraphQLString)),
                "fullName": GraphQLField(GraphQLString),
                "bio": GraphQLField(GraphQLString),
                "followerCount": GraphQLField(
                    GraphQLNonNull(GraphQLInt),
                    resolve=lambda obj, info: 0
                ),
                "posts": GraphQLField(
                    GraphQLNonNull(GraphQLList(GraphQLNonNull(get_post_type()))),
                    args={"limit": GraphQLArgument(GraphQLInt, default_value=50)},
                    resolve=resolve_user_posts,
                ),
            },
        )
    return user_type


def get_post_type():
    global post_type
    if post_type is None:
        post_type = GraphQLObjectType(
            "Post",
            lambda: {
                "id": GraphQLField(GraphQLNonNull(GraphQLID)),
                "title": GraphQLField(GraphQLNonNull(GraphQLString)),
                "content": GraphQLField(GraphQLString),
                "author": GraphQLField(get_user_type(), resolve=resolve_post_author),
                "comments": GraphQLField(
                    GraphQLNonNull(GraphQLList(GraphQLNonNull(get_comment_type()))),
                    args={"limit": GraphQLArgument(GraphQLInt, default_value=50)},
                    resolve=resolve_post_comments,
                ),
            },
        )
    return post_type


def get_comment_type():
    global comment_type
    if comment_type is None:
        comment_type = GraphQLObjectType(
            "Comment",
            lambda: {
                "id": GraphQLField(GraphQLNonNull(GraphQLID)),
                "content": GraphQLField(GraphQLNonNull(GraphQLString)),
                "author": GraphQLField(get_user_type(), resolve=resolve_comment_author),
                "post": GraphQLField(get_post_type(), resolve=resolve_comment_post),
            },
        )
    return comment_type


# ============================================================================
# Resolvers
# ============================================================================

async def resolve_ping(root, info):
    return "pong"


async def resolve_user(root, info, id):
    if not validate_uuid(id):
        raise ValueError(f"Invalid user ID format: {id}")

    db = info.context["db"]
    result = await db.fetchrow(
        "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1",
        id,
        timeout=5.0
    )
    if result:
        return {
            "id": str(result["id"]),
            "username": result["username"],
            "fullName": result.get("full_name"),
            "bio": result.get("bio"),
        }
    return None


async def resolve_users(root, info, limit=10):
    limit = min(max(limit, 1), 100)
    db = info.context["db"]
    result = await db.fetch(
        "SELECT id, username, full_name, bio FROM benchmark.tb_user LIMIT $1",
        limit,
        timeout=5.0
    )
    return [
        {
            "id": str(row["id"]),
            "username": row["username"],
            "fullName": row.get("full_name"),
            "bio": row.get("bio"),
        }
        for row in result
    ]


async def resolve_post(root, info, id):
    if not validate_uuid(id):
        raise ValueError(f"Invalid post ID format: {id}")

    db = info.context["db"]
    result = await db.fetchrow(
        """
        SELECT p.id, p.title, p.content, u.id as author_id
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        WHERE p.id = $1
        """,
        id,
        timeout=5.0
    )
    if result:
        return {
            "id": str(result["id"]),
            "title": result["title"],
            "content": result.get("content"),
            "author_id": str(result["author_id"]) if result.get("author_id") else None,
        }
    return None


async def resolve_posts(root, info, limit=10):
    limit = min(max(limit, 1), 100)
    db = info.context["db"]
    result = await db.fetch(
        """
        SELECT p.id, p.title, p.content, u.id as author_id
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        ORDER BY p.created_at DESC
        LIMIT $1
        """,
        limit,
        timeout=5.0
    )
    return [
        {
            "id": str(row["id"]),
            "title": row["title"],
            "content": row.get("content"),
            "author_id": str(row["author_id"]) if row.get("author_id") else None,
        }
        for row in result
    ]


async def resolve_comment(root, info, id):
    if not validate_uuid(id):
        raise ValueError(f"Invalid comment ID format: {id}")

    db = info.context["db"]
    result = await db.fetchrow(
        """
        SELECT c.id, c.content, u.id as author_id, p.id as post_id
        FROM benchmark.tb_comment c
        JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
        JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
        WHERE c.id = $1
        """,
        id,
        timeout=5.0
    )
    if result:
        return {
            "id": str(result["id"]),
            "content": result["content"],
            "author_id": str(result["author_id"]) if result.get("author_id") else None,
            "post_id": str(result["post_id"]) if result.get("post_id") else None,
        }
    return None


async def resolve_user_posts(obj, info, limit=50):
    limit = min(limit, 50)
    posts_data = await info.context["posts_by_author_loader"].load(obj["id"])
    return [
        {
            "id": str(post["id"]),
            "title": post["title"],
            "content": post.get("content"),
            "author_id": str(post["author_id"]) if post.get("author_id") else None,
        }
        for post in posts_data[:limit]
    ]


async def resolve_post_author(obj, info):
    author_id = obj.get("author_id")
    if not author_id:
        return None
    user_data = await info.context["user_loader"].load(author_id)
    if user_data:
        return {
            "id": str(user_data["id"]),
            "username": user_data["username"],
            "fullName": user_data.get("full_name"),
            "bio": user_data.get("bio"),
        }
    return None


async def resolve_post_comments(obj, info, limit=50):
    limit = min(limit, 50)
    comments_data = await info.context["comments_by_post_loader"].load(obj["id"])
    return [
        {
            "id": str(comment["id"]),
            "content": comment["content"],
            "author_id": str(comment["author_id"]) if comment.get("author_id") else None,
            "post_id": str(comment["post_id"]) if comment.get("post_id") else None,
        }
        for comment in comments_data[:limit]
    ]


async def resolve_comment_author(obj, info):
    author_id = obj.get("author_id")
    if not author_id:
        return None
    user_data = await info.context["user_loader"].load(author_id)
    if user_data:
        return {
            "id": str(user_data["id"]),
            "username": user_data["username"],
            "fullName": user_data.get("full_name"),
            "bio": user_data.get("bio"),
        }
    return None


async def resolve_comment_post(obj, info):
    post_id = obj.get("post_id")
    if not post_id:
        return None
    post_data = await info.context["post_loader"].load(post_id)
    if post_data:
        return {
            "id": str(post_data["id"]),
            "title": post_data["title"],
            "content": post_data.get("content"),
            "author_id": str(post_data["author_id"]) if post_data.get("author_id") else None,
        }
    return None


async def resolve_update_user(root, info, id, bio=None, fullName=None):
    if not validate_uuid(id):
        raise ValueError(f"Invalid user ID format: {id}")

    if bio is None and fullName is None:
        raise ValueError("At least one of bio or fullName must be provided")

    db = info.context["db"]

    update_fields = []
    params = [id]
    param_idx = 2

    if bio is not None:
        update_fields.append(f"bio = ${param_idx}")
        params.append(bio)
        param_idx += 1
    if fullName is not None:
        update_fields.append(f"full_name = ${param_idx}")
        params.append(fullName)
        param_idx += 1

    if update_fields:
        await db.execute(
            f"UPDATE benchmark.tb_user SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = $1",
            *params,
            timeout=5.0
        )

    result = await db.fetchrow(
        "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1",
        id,
        timeout=5.0
    )
    if result:
        return {
            "id": str(result["id"]),
            "username": result["username"],
            "fullName": result.get("full_name"),
            "bio": result.get("bio"),
        }
    return None


# ============================================================================
# Schema Definition
# ============================================================================

query_type = GraphQLObjectType(
    "Query",
    {
        "ping": GraphQLField(GraphQLNonNull(GraphQLString), resolve=resolve_ping),
        "user": GraphQLField(
            get_user_type(),
            args={"id": GraphQLArgument(GraphQLNonNull(GraphQLID))},
            resolve=resolve_user,
        ),
        "users": GraphQLField(
            GraphQLNonNull(GraphQLList(GraphQLNonNull(get_user_type()))),
            args={"limit": GraphQLArgument(GraphQLInt, default_value=10)},
            resolve=resolve_users,
        ),
        "post": GraphQLField(
            get_post_type(),
            args={"id": GraphQLArgument(GraphQLNonNull(GraphQLID))},
            resolve=resolve_post,
        ),
        "posts": GraphQLField(
            GraphQLNonNull(GraphQLList(GraphQLNonNull(get_post_type()))),
            args={"limit": GraphQLArgument(GraphQLInt, default_value=10)},
            resolve=resolve_posts,
        ),
        "comment": GraphQLField(
            get_comment_type(),
            args={"id": GraphQLArgument(GraphQLNonNull(GraphQLID))},
            resolve=resolve_comment,
        ),
    },
)

mutation_type = GraphQLObjectType(
    "Mutation",
    {
        "updateUser": GraphQLField(
            get_user_type(),
            args={
                "id": GraphQLArgument(GraphQLNonNull(GraphQLID)),
                "bio": GraphQLArgument(GraphQLString),
                "fullName": GraphQLArgument(GraphQLString),
            },
            resolve=resolve_update_user,
        ),
    },
)

schema = GraphQLSchema(query=query_type, mutation=mutation_type)


# ============================================================================
# Application Setup
# ============================================================================

db = AsyncDatabase()


async def graphql_endpoint(request: Request):
    """Handle GraphQL requests."""
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({"errors": [{"message": "Invalid JSON"}]}, status_code=400)

    query = body.get("query")
    variables = body.get("variables", {})
    operation_name = body.get("operationName")

    if not query:
        return JSONResponse({"errors": [{"message": "No query provided"}]}, status_code=400)

    # Create context with DataLoaders (fresh per request)
    context = {
        "db": db,
        "user_loader": DataLoader(lambda keys: load_users_batch(keys, db)),
        "post_loader": DataLoader(lambda keys: load_posts_batch(keys, db)),
        "posts_by_author_loader": DataLoader(lambda keys: load_posts_by_author_batch(keys, db)),
        "comments_by_post_loader": DataLoader(lambda keys: load_comments_by_post_batch(keys, db)),
    }

    result = await graphql(
        schema,
        query,
        variable_values=variables,
        operation_name=operation_name,
        context_value=context,
    )

    response_data = {}
    if result.data:
        response_data["data"] = result.data
    if result.errors:
        response_data["errors"] = [
            {"message": str(error), "locations": error.locations, "path": error.path}
            for error in result.errors
        ]

    return JSONResponse(response_data)


async def health_check(request):
    return JSONResponse({"status": "healthy", "framework": "asgi-graphql"})


async def startup():
    await db.connect(min_size=10, max_size=50, statement_cache_size=100)
    logger.info("ASGI-GraphQL server started on port 4000")


async def shutdown():
    await db.close()
    logger.info("ASGI-GraphQL server stopped")


app = Starlette(
    debug=False,
    routes=[
        Route("/health", health_check),
        Route("/graphql", graphql_endpoint, methods=["POST"]),
    ],
    on_startup=[startup],
    on_shutdown=[shutdown],
)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "4000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
