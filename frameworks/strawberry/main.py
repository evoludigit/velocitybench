#!/usr/bin/env python3
"""
Async GraphQL Benchmarking Server for Strawberry with DataLoader
Uses asyncpg connection pooling and DataLoader to prevent N+1 queries.
"""

import os
import sys
from typing import Optional

import strawberry
from fastapi import FastAPI
from strawberry.dataloader import DataLoader
from strawberry.fastapi import BaseContext, GraphQLRouter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.async_db import AsyncDatabase


# DataLoader functions for batching
async def load_users_batch(keys: list[str], db: AsyncDatabase) -> list[dict | None]:
    """Batch load users by IDs."""
    result = await db.fetch(
        "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = ANY($1)",
        keys
    )
    # Create a map for O(1) lookup
    user_map = {user["id"]: user for user in result}
    # Return in the same order as keys
    return [user_map.get(key) for key in keys]


async def load_posts_batch(keys: list[str], db: AsyncDatabase) -> list[dict | None]:
    """Batch load posts by IDs."""
    result = await db.fetch(
        """
        SELECT p.id, p.title, p.content, u.id as author_id
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        WHERE p.id = ANY($1)
        """,
        keys
    )
    post_map = {post["id"]: post for post in result}
    return [post_map.get(key) for key in keys]


async def load_posts_by_author_batch(keys: list[str], db: AsyncDatabase) -> list[list[dict]]:
    """Batch load posts by author IDs."""
    result = await db.fetch(
        """
        SELECT p.id, p.title, p.content, u.id as author_id
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        WHERE u.id = ANY($1)
        ORDER BY u.id, p.created_at DESC
        """,
        keys
    )

    # Group by author_id
    posts_by_author = {key: [] for key in keys}
    for post in result:
        posts_by_author[post["author_id"]].append(post)

    return [posts_by_author[key] for key in keys]


async def load_comments_by_post_batch(keys: list[str], db: AsyncDatabase) -> list[list[dict]]:
    """Batch load comments by post IDs."""
    result = await db.fetch(
        """
        SELECT c.id, c.content, p.id as post_id, u.id as author_id
        FROM benchmark.tb_comment c
        JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
        JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
        WHERE p.id = ANY($1)
        ORDER BY p.id, c.created_at DESC
        """,
        keys
    )

    # Group by post_id
    comments_by_post = {key: [] for key in keys}
    for comment in result:
        comments_by_post[comment["post_id"]].append(comment)

    return [comments_by_post[key][:50] for key in keys]  # Limit 50 per post


@strawberry.type
class Comment:
    id: str
    content: str
    author_id: str | None = strawberry.field(default=None)
    post_id: str | None = strawberry.field(default=None)

    @strawberry.field
    async def author(self, info) -> Optional["User"]:
        if not self.author_id:
            return None
        user_data = await info.context.user_loader.load(self.author_id)
        if user_data:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                full_name=user_data.get("full_name"),
                bio=user_data.get("bio"),
            )
        return None

    @strawberry.field
    async def post(self, info) -> Optional["Post"]:
        if not self.post_id:
            return None
        post_data = await info.context.post_loader.load(self.post_id)
        if post_data:
            return Post(
                id=post_data["id"],
                title=post_data["title"],
                content=post_data.get("content"),
                author_id=post_data.get("author_id"),
            )
        return None


@strawberry.type
class Post:
    id: str
    title: str
    content: str | None = None
    author_id: str | None = strawberry.field(default=None)

    @strawberry.field
    async def author(self, info) -> Optional["User"]:
        if not self.author_id:
            return None
        user_data = await info.context.user_loader.load(self.author_id)
        if user_data:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                full_name=user_data.get("full_name"),
                bio=user_data.get("bio"),
            )
        return None

    @strawberry.field
    async def comments(self, info, limit: int = 50) -> list["Comment"]:
        comments_data = await info.context.comments_by_post_loader.load(self.id)
        return [
            Comment(
                id=comment["id"],
                content=comment["content"],
                author_id=comment.get("author_id"),
                post_id=comment.get("post_id"),
            )
            for comment in comments_data[:limit]
        ]


@strawberry.type
class User:
    id: str
    username: str
    full_name: str | None = None
    bio: str | None = None

    @strawberry.field
    def follower_count(self) -> int:
        """Return follower count (placeholder - no follows table in db)."""
        return 0

    @strawberry.field
    async def posts(self, info, limit: int = 50) -> list[Post]:
        posts_data = await info.context.posts_by_author_loader.load(self.id)
        return [
            Post(
                id=post["id"],
                title=post["title"],
                content=post.get("content"),
                author_id=post.get("author_id"),
            )
            for post in posts_data[:limit]
        ]


@strawberry.type
class Query:
    @strawberry.field
    async def ping(self) -> str:
        return "pong"

    @strawberry.field
    async def user(self, info, id: strawberry.ID) -> User | None:
        db = info.context.db
        result = await db.fetchrow(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1",
            id
        )
        if result:
            return User(
                id=result["id"],
                username=result["username"],
                full_name=result.get("full_name"),
                bio=result.get("bio"),
            )
        return None

    @strawberry.field
    async def users(self, info, limit: int = 10) -> list[User]:
        db = info.context.db
        result = await db.fetch(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user LIMIT $1",
            limit
        )
        return [
            User(
                id=row["id"],
                username=row["username"],
                full_name=row.get("full_name"),
                bio=row.get("bio"),
            )
            for row in result
        ]

    @strawberry.field
    async def post(self, info, id: strawberry.ID) -> Post | None:
        db = info.context.db
        result = await db.fetchrow(
            """
            SELECT p.id, p.title, p.content, u.id as author_id
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE p.id = $1
            """,
            id
        )
        if result:
            return Post(
                id=result["id"],
                title=result["title"],
                content=result.get("content"),
                author_id=result.get("author_id"),
            )
        return None

    @strawberry.field
    async def posts(self, info, limit: int = 10) -> list[Post]:
        db = info.context.db
        result = await db.fetch(
            """
            SELECT p.id, p.title, p.content, u.id as author_id
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            ORDER BY p.created_at DESC
            LIMIT $1
            """,
            limit
        )
        return [
            Post(
                id=row["id"],
                title=row["title"],
                content=row.get("content"),
                author_id=row.get("author_id"),
            )
            for row in result
        ]

    @strawberry.field
    async def comment(self, info, id: strawberry.ID) -> Comment | None:
        db = info.context.db
        result = await db.fetchrow(
            """
            SELECT c.id, c.content, u.id as author_id, p.id as post_id
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            WHERE c.id = $1
            """,
            id
        )
        if result:
            return Comment(
                id=result["id"],
                content=result["content"],
                author_id=result.get("author_id"),
                post_id=result.get("post_id"),
            )
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def update_user(
        self,
        info,
        id: strawberry.ID,
        bio: str | None = None,
        full_name: str | None = None,
    ) -> User | None:
        db = info.context.db

        # Update user
        update_fields = []
        params = [id]
        param_idx = 2

        if bio is not None:
            update_fields.append(f"bio = ${param_idx}")
            params.append(bio)
            param_idx += 1
        if full_name is not None:
            update_fields.append(f"full_name = ${param_idx}")
            params.append(full_name)
            param_idx += 1

        if update_fields:
            await db.execute(
                f"UPDATE benchmark.tb_user SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = $1",
                *params
            )

        # Return updated user
        result = await db.fetchrow(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1",
            id
        )
        if result:
            return User(
                id=result["id"],
                username=result["username"],
                full_name=result.get("full_name"),
                bio=result.get("bio"),
            )
        return None


schema = strawberry.Schema(query=Query, mutation=Mutation)


class Context(BaseContext):
    def __init__(self, db: AsyncDatabase):
        super().__init__()
        self.db = db
        # Create DataLoaders for batching
        self.user_loader = DataLoader(load_fn=lambda keys: load_users_batch(keys, db))
        self.post_loader = DataLoader(load_fn=lambda keys: load_posts_batch(keys, db))
        self.posts_by_author_loader = DataLoader(load_fn=lambda keys: load_posts_by_author_batch(keys, db))
        self.comments_by_post_loader = DataLoader(load_fn=lambda keys: load_comments_by_post_batch(keys, db))


async def get_context() -> Context:
    """Context factory for each request."""
    return Context(db=app.state.db)


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize database pool on startup."""
    db = AsyncDatabase()
    await db.connect(
        min_size=10,
        max_size=50,
        statement_cache_size=100
    )
    app.state.db = db


@app.on_event("shutdown")
async def shutdown_event():
    """Close database pool on shutdown."""
    await app.state.db.close()


graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "framework": "strawberry"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
