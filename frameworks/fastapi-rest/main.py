#!/usr/bin/env python3
"""
FastAPI REST Comparative Benchmarking Implementation
Async REST API with asyncpg connection pooling that matches GraphQL operations using include parameters.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Any

import prometheus_client
from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.async_db import AsyncDatabase

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
    id: str
    username: str
    full_name: str | None
    bio: str | None
    posts: list[dict[str, Any]] | None = None


class PostResponse(BaseModel):
    id: str
    title: str
    content: str | None
    author: dict[str, Any] | None = None
    comments: list[dict[str, Any]] | None = None


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    db = AsyncDatabase()
    await db.connect(min_size=10, max_size=50, statement_cache_size=100)
    app.state.db = db
    print("Database pool initialized")

    yield

    # Shutdown
    await app.state.db.close()
    print("Database pool closed")


# FastAPI app with lifespan
app = FastAPI(title="FastAPI REST Comparative Benchmark", lifespan=lifespan)


def get_db() -> AsyncDatabase:
    """Get database from app state."""
    return app.state.db


@app.get("/ping")
async def ping():
    """Simple ping endpoint for throughput testing"""
    REQUEST_COUNT.labels(method="GET", endpoint="/ping").inc()
    return {"message": "pong"}


@app.get("/users")
async def list_users(limit: int = Query(10, ge=1, le=100), include: str | None = None):
    """List users with optional includes"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users").inc()

    db = get_db()

    # Base query
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
        raise HTTPException(status_code=404, detail="User not found")

    user_data = dict(user)

    # Handle includes
    if include:
        includes = include.split(",")

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
                        for comment in comments:
                            comment["author"] = {
                                "id": comment["author_id"],
                                "username": comment["author_username"],
                            }
                            del comment["author_id"]
                            del comment["author_username"]

                    post["comments"] = comments

            user_data["posts"] = posts

        # Note: tb_user_follows table doesn't exist, skip followers/following
        # if "followers" in includes:
        #     user_data["followers"] = []
        # if "following" in includes:
        #     user_data["following"] = []

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
        raise HTTPException(status_code=404, detail="Post not found")

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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "framework": "fastapi-rest"}


@app.get("/metrics")
async def metrics():
    return prometheus_client.generate_latest()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
