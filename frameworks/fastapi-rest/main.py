#!/usr/bin/env python3
"""FastAPI REST Comparative Benchmarking Implementation.

Async REST API with asyncpg connection pooling that matches GraphQL
operations using include parameters.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path as PathlibPath
from typing import Any
from uuid import UUID

import prometheus_client
from fastapi import FastAPI, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

sys.path.insert(0, str(PathlibPath(__file__).parent.parent))
from common.config import ConfigurationError, get_db_config  # noqa: E402
from common.errors import (  # noqa: E402
    AppError,
    InputValidationError,
    ResourceNotFoundError,
)
from common.health_check import HealthCheckManager  # noqa: E402
from common.logging_middleware import FastAPILoggingMiddleware  # noqa: E402
from common.validators import Validator  # noqa: E402

from common.async_db import AsyncDatabase  # noqa: E402

# Metrics
REQUEST_COUNT = prometheus_client.Counter(
    "fastapi_rest_requests_total", "Total requests", ["method", "endpoint"]
)
REQUEST_LATENCY = prometheus_client.Histogram(
    "fastapi_rest_request_duration_seconds", "Request latency", ["method", "endpoint"]
)


# Pydantic models for request/response
class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    bio: str | None = Field(None, max_length=1000)


class UserResponse(BaseModel):
    id: UUID
    username: str
    full_name: str | None
    bio: str | None
    posts: list[dict[str, Any]] | None = None


class PostResponse(BaseModel):
    id: UUID
    title: str
    content: str | None
    author: dict[str, Any] | None = None
    comments: list[dict[str, Any]] | None = None


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup - validate configuration first
    try:
        config = get_db_config()
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise

    db = AsyncDatabase()

    # Get pool configuration from environment or use defaults
    pool_min_size = int(os.getenv("DB_POOL_MIN_SIZE", "10"))
    pool_max_size = int(os.getenv("DB_POOL_MAX_SIZE", "50"))
    pool_statement_cache = int(os.getenv("DB_POOL_STATEMENT_CACHE_SIZE", "100"))

    await db.connect(
        host=config.host,
        port=config.port,
        database=config.name,
        user=config.user,
        password=config.password,
        min_size=pool_min_size,
        max_size=pool_max_size,
        statement_cache_size=pool_statement_cache,
    )
    app.state.db = db
    logger.info("Database pool initialized")

    # Initialize health check manager
    health_manager = HealthCheckManager(
        service_name="fastapi-rest",
        version="1.0.0",
        database=db,
        environment=os.getenv("ENVIRONMENT", "development"),
    )
    app.state.health = health_manager
    logger.info("Health check manager initialized")

    yield

    # Shutdown
    await app.state.db.close()
    logger.info("Database pool closed")


# FastAPI app with lifespan
app = FastAPI(title="FastAPI REST Comparative Benchmark", lifespan=lifespan)

# Add logging middleware
app.add_middleware(FastAPILoggingMiddleware)


# Exception handler for application errors
@app.exception_handler(AppError)
async def app_error_handler(_request, exc: AppError):
    """Handle application errors with proper status codes."""
    logger.error(
        f"Application error: {exc.message}",
        extra={"error_code": exc.error_code},
    )
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


def get_db() -> AsyncDatabase:
    """Get database from app state."""
    return app.state.db


def get_health() -> HealthCheckManager:
    """Get health check manager from app state."""
    return app.state.health


# Health check endpoints
@app.get("/health")
async def health():
    """Combined health check (defaults to readiness)"""
    health_manager = get_health()
    result = await health_manager.probe("readiness")
    return result.to_dict()


@app.get("/health/live")
async def health_live():
    """Liveness probe - Is the process alive?"""
    health_manager = get_health()
    result = await health_manager.probe("liveness")
    return result.to_dict()


@app.get("/health/ready")
async def health_ready():
    """Readiness probe - Can the service handle traffic?"""
    health_manager = get_health()
    result = await health_manager.probe("readiness")
    return result.to_dict()


@app.get("/health/startup")
async def health_startup():
    """Startup probe - Has initialization completed?"""
    health_manager = get_health()
    result = await health_manager.probe("startup")
    return result.to_dict()


@app.get("/ping")
async def ping():
    """Simple ping endpoint for throughput testing"""
    REQUEST_COUNT.labels(method="GET", endpoint="/ping").inc()
    return {"message": "pong"}


@app.get("/users")
async def list_users(
    limit: int = Query(10, ge=1, le=100),
    include: str | None = None,
    ids: str | None = Query(
        None, description="Comma-separated list of user IDs for batch fetch"
    ),
):
    """List users with optional includes or batch fetch by IDs"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users").inc()

    db = get_db()

    # Batch fetch by IDs if provided
    if ids:
        try:
            id_list = Validator.validate_uuid_list(ids, max_count=100)
        except InputValidationError:
            raise
        if not id_list:
            return {"users": []}

        users = await db.fetch(
            """
            SELECT id, username, full_name, bio, avatar_url
            FROM benchmark.tb_user
            WHERE id = ANY($1::uuid[])
        """,
            id_list,
        )
        return {"users": users}

    # Base query for listing
    query = """
        SELECT id, username, full_name, bio
        FROM benchmark.tb_user
        ORDER BY created_at DESC
        LIMIT $1
    """

    users = await db.fetch(query, limit)

    # Handle includes
    if include and "posts" in include:
        for user in users:
            posts = await db.fetch(
                """
                SELECT p.id, p.title, p.content
                FROM benchmark.tb_post p
                JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
                WHERE u.id = $1
                ORDER BY p.created_at DESC
                LIMIT 5
            """,
                user["id"],
            )
            user["posts"] = posts

    return {"users": users}


@app.get("/users/{user_id}")
async def get_user(user_id: str = Path(...), include: str | None = None):
    """Get user by ID with optional includes"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{id}").inc()

    db = get_db()

    # Validate user_id format
    try:
        Validator.validate_uuid(user_id, "user_id")
    except InputValidationError:
        raise

    # Base user query
    user = await db.fetchrow(
        """
        SELECT id, username, full_name, bio
        FROM benchmark.tb_user
        WHERE id = $1
    """,
        user_id,
    )

    if not user:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")

    user_data = dict(user)

    # Validate include parameter
    allowed_includes = {"posts", "posts.comments", "posts.comments.author"}
    if include:
        try:
            includes = Validator.validate_include_fields(include, allowed_includes)
        except InputValidationError:
            raise
    else:
        includes = []

    if "posts" in includes:
        posts = await db.fetch(
            """
            SELECT p.id, p.title, p.content
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE u.id = $1
            ORDER BY p.created_at DESC
            LIMIT 10
        """,
            user_id,
        )

        # Handle nested includes
        if "posts.comments" in includes or "posts.comments.author" in includes:
            for post in posts:
                comments = await db.fetch(
                    """
                    SELECT c.id, c.content, c.created_at,
                           u2.id as author_id, u2.username as author_username
                    FROM benchmark.tb_comment c
                    JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
                    JOIN benchmark.tb_user u2 ON c.fk_author = u2.pk_user
                    WHERE p.id = $1
                    ORDER BY c.created_at DESC
                    LIMIT 5
                """,
                    post["id"],
                )

                # Add author info to comments if requested
                if "posts.comments.author" in includes:
                    comments = [
                        {
                            **{
                                k: v
                                for k, v in comment.items()
                                if k not in ("author_id", "author_username")
                            },
                            "author": {
                                "id": comment["author_id"],
                                "username": comment["author_username"],
                            },
                        }
                        for comment in comments
                    ]

                post["comments"] = comments

        user_data["posts"] = posts

    return user_data


@app.put("/users/{user_id}")
async def update_user(
    user_id: str = Path(...),
    user_update: UserUpdate | None = None,
    include: str | None = None,
):
    """Update user and optionally return related data"""
    REQUEST_COUNT.labels(method="PUT", endpoint="/users/{id}").inc()

    db = get_db()

    # Update user
    update_fields = []
    params = [user_id]
    param_idx = 2

    if user_update:
        if user_update.full_name is not None:
            update_fields.append(f"full_name = ${param_idx}")
            params.append(user_update.full_name)
            param_idx += 1
        if user_update.bio is not None:
            update_fields.append(f"bio = ${param_idx}")
            params.append(user_update.bio)
            param_idx += 1

    if update_fields:
        await db.execute(
            f"""
            UPDATE benchmark.tb_user
            SET {", ".join(update_fields)}, updated_at = NOW()
            WHERE id = $1
        """,
            *params,
        )

    # Return updated user (unlike GraphQL cascade, this requires a separate query)
    return await get_user(user_id, include)


@app.get("/posts")
async def list_posts(limit: int = Query(10, ge=1, le=100), include: str | None = None):
    """List posts with optional includes"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts").inc()

    db = get_db()

    # Base query with author
    query = """
        SELECT p.id, p.title, p.content, p.created_at,
               u.id as author_id, u.username as author_username
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        ORDER BY p.created_at DESC
        LIMIT $1
    """

    posts = await db.fetch(query, limit)

    # Handle includes
    if include and "author" in include:
        for post in posts:
            post["author"] = {
                "id": post["author_id"],
                "username": post["author_username"],
            }
            del post["author_id"]
            del post["author_username"]

    if include and "comments" in include:
        for post in posts:
            comments = await db.fetch(
                """
                SELECT c.id, c.content, c.created_at,
                       u.id as author_id, u.username as author_username
                FROM benchmark.tb_comment c
                JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
                JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
                WHERE p.id = $1
                ORDER BY c.created_at DESC
                LIMIT 5
            """,
                post["id"],
            )

            if "comments.author" in include:
                for comment in comments:
                    comment["author"] = {
                        "id": comment["author_id"],
                        "username": comment["author_username"],
                    }
                    del comment["author_id"]
                    del comment["author_username"]

            post["comments"] = comments

    return {"posts": posts}


@app.get("/posts/{post_id}")
async def get_post(post_id: str = Path(...), include: str | None = None):
    """Get post by ID with optional includes"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}").inc()

    db = get_db()

    # Validate post_id format
    try:
        Validator.validate_uuid(post_id, "post_id")
    except InputValidationError:
        raise

    # Base post query with author
    post = await db.fetchrow(
        """
        SELECT p.id, p.title, p.content, p.created_at,
               u.id as author_id, u.username as author_username
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        WHERE p.id = $1
    """,
        post_id,
    )

    if not post:
        raise ResourceNotFoundError(f"Post with ID {post_id} not found")

    post_data = dict(post)

    # Handle includes
    if include and "author" in include:
        post_data["author"] = {
            "id": post_data["author_id"],
            "username": post_data["author_username"],
        }
        del post_data["author_id"]
        del post_data["author_username"]

    if include and "comments" in include:
        comments = await db.fetch(
            """
            SELECT c.id, c.content, c.created_at,
                   u.id as author_id, u.username as author_username
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            WHERE p.id = $1
            ORDER BY c.created_at DESC
        """,
            post_id,
        )

        if "comments.author" in include:
            for comment in comments:
                comment["author"] = {
                    "id": comment["author_id"],
                    "username": comment["author_username"],
                }
                del comment["author_id"]
                del comment["author_username"]

        post_data["comments"] = comments

    return post_data


@app.get("/posts/{post_id}/comments")
async def get_post_comments(
    post_id: str = Path(...),
    limit: int = Query(10, ge=1, le=100),
):
    """Get comments for a specific post"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}/comments").inc()

    db = get_db()

    comments = await db.fetch(
        """
        SELECT c.id, c.content, c.created_at, c.is_approved,
               u.id as author_id, u.username as author_username,
               u.avatar_url as author_avatar
        FROM benchmark.tb_comment c
        JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
        JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
        WHERE p.id = $1
        ORDER BY c.created_at DESC
        LIMIT $2
    """,
        post_id,
        limit,
    )

    return [dict(c) for c in comments]


@app.get("/metrics")
async def metrics():
    return prometheus_client.generate_latest()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003, workers=4)
