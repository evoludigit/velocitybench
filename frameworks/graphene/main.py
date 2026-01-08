#!/usr/bin/env python3
"""
Async GraphQL Benchmarking Server for Graphene with DataLoader
Uses asyncpg connection pooling and aiodataloader to prevent N+1 queries.
"""

import os
import sys

import graphene
from aiodataloader import DataLoader
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from graphene import ID, Field, Int, ObjectType, String
from graphene import List as GrapheneList

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.async_db import AsyncDatabase


# DataLoader classes for batching
class UserLoader(DataLoader):
    def __init__(self, db: AsyncDatabase):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, keys: list[str]) -> list[dict | None]:
        result = await self.db.fetch(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = ANY($1)", keys
        )
        user_map = {user["id"]: user for user in result}
        return [user_map.get(key) for key in keys]


class PostLoader(DataLoader):
    def __init__(self, db: AsyncDatabase):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, keys: list[str]) -> list[dict | None]:
        result = await self.db.fetch(
            """
            SELECT p.id, p.title, p.content, u.id as author_id
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE p.id = ANY($1)
            """,
            keys,
        )
        post_map = {post["id"]: post for post in result}
        return [post_map.get(key) for key in keys]


class PostsByAuthorLoader(DataLoader):
    def __init__(self, db: AsyncDatabase):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, keys: list[str]) -> list[list[dict]]:
        result = await self.db.fetch(
            """
            SELECT p.id, p.title, p.content, u.id as author_id
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE u.id = ANY($1)
            ORDER BY u.id, p.created_at DESC
            """,
            keys,
        )
        posts_by_author = {key: [] for key in keys}
        for post in result:
            posts_by_author[post["author_id"]].append(post)
        return [posts_by_author[key] for key in keys]


class CommentsByPostLoader(DataLoader):
    def __init__(self, db: AsyncDatabase):
        super().__init__()
        self.db = db

    async def batch_load_fn(self, keys: list[str]) -> list[list[dict]]:
        result = await self.db.fetch(
            """
            SELECT c.id, c.content, p.id as post_id, u.id as author_id
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            WHERE p.id = ANY($1)
            ORDER BY p.id, c.created_at DESC
            """,
            keys,
        )
        comments_by_post = {key: [] for key in keys}
        for comment in result:
            comments_by_post[comment["post_id"]].append(comment)
        return [comments_by_post[key][:5] for key in keys]  # Limit 5 per post


class Comment(ObjectType):
    id = ID()
    content = String()
    author = Field(lambda: User)
    post = Field(lambda: Post)

    def __init__(self, *args, **kwargs):
        self.author_id = kwargs.pop("author_id", None)
        self.post_id = kwargs.pop("post_id", None)
        super().__init__(*args, **kwargs)

    async def resolve_author(self, info):
        if not self.author_id:
            return None
        user_data = await info.context["user_loader"].load(self.author_id)
        if user_data:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                full_name=user_data.get("full_name"),
                bio=user_data.get("bio"),
            )
        return None

    async def resolve_post(self, info):
        if not self.post_id:
            return None
        post_data = await info.context["post_loader"].load(self.post_id)
        if post_data:
            return Post(
                id=post_data["id"],
                title=post_data["title"],
                content=post_data.get("content"),
                author_id=post_data.get("author_id"),
            )
        return None


class Post(ObjectType):
    id = ID()
    title = String()
    content = String()
    author = Field(lambda: User)
    comments = GrapheneList(lambda: Comment, limit=Int(default_value=10))

    def __init__(self, *args, **kwargs):
        self.author_id = kwargs.pop("author_id", None)
        super().__init__(*args, **kwargs)

    async def resolve_author(self, info):
        if not self.author_id:
            return None
        user_data = await info.context["user_loader"].load(self.author_id)
        if user_data:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                full_name=user_data.get("full_name"),
                bio=user_data.get("bio"),
            )
        return None

    async def resolve_comments(self, info, limit=10):
        comments_data = await info.context["comments_by_post_loader"].load(self.id)
        return [
            Comment(
                id=comment["id"],
                content=comment["content"],
                author_id=comment.get("author_id"),
                post_id=comment.get("post_id"),
            )
            for comment in comments_data[:limit]
        ]


class User(ObjectType):
    id = ID()
    username = String()
    full_name = String()
    bio = String()
    follower_count = Int()
    posts = GrapheneList(lambda: Post, limit=Int(default_value=10))

    def resolve_follower_count(self, info):
        """Return follower count (placeholder - no follows table in db)."""
        return 0

    async def resolve_posts(self, info, limit=10):
        posts_data = await info.context["posts_by_author_loader"].load(self.id)
        return [
            Post(
                id=post["id"],
                title=post["title"],
                content=post.get("content"),
                author_id=post.get("author_id"),
            )
            for post in posts_data[:limit]
        ]


class Query(ObjectType):
    ping = String(description="Simple ping query")
    user = Field(User, id=ID(required=True))
    users = GrapheneList(User, limit=Int(default_value=10))
    post = Field(Post, id=ID(required=True))
    posts = GrapheneList(Post, limit=Int(default_value=10))
    comment = Field(Comment, id=ID(required=True))

    async def resolve_ping(self, info):
        return "pong"

    async def resolve_user(self, info, id):
        db = info.context["db"]
        result = await db.fetchrow(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1", id
        )
        if not result:
            return None

        return User(
            id=result["id"],
            username=result["username"],
            full_name=result.get("full_name"),
            bio=result.get("bio"),
        )

    async def resolve_users(self, info, limit):
        db = info.context["db"]
        result = await db.fetch(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user LIMIT $1", limit
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

    async def resolve_post(self, info, id):
        db = info.context["db"]
        result = await db.fetchrow(
            """
            SELECT p.id, p.title, p.content, u.id as author_id
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE p.id = $1
            """,
            id,
        )
        if result:
            return Post(
                id=result["id"],
                title=result["title"],
                content=result.get("content"),
                author_id=result.get("author_id"),
            )
        return None

    async def resolve_posts(self, info, limit):
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

    async def resolve_comment(self, info, id):
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
        )
        if result:
            return Comment(
                id=result["id"],
                content=result["content"],
                author_id=result.get("author_id"),
                post_id=result.get("post_id"),
            )
        return None


class UpdateUser(graphene.Mutation):
    class Arguments:
        id = ID(required=True)
        bio = String()
        full_name = String()

    user = Field(lambda: User)

    async def mutate(self, info, id, bio=None, full_name=None):
        # Basic input validation
        if bio is not None and (not isinstance(bio, str) or len(bio) > 1000):
            raise ValueError("Bio must be a string with maximum length 1000")
        if full_name is not None and (not isinstance(full_name, str) or len(full_name) > 255):
            raise ValueError("Full name must be a string with maximum length 255")

        db = info.context["db"]

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
                *params,
            )

        # Return updated user
        result = await db.fetchrow(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1", id
        )
        if result:
            return UpdateUser(
                user=User(
                    id=result["id"],
                    username=result["username"],
                    full_name=result.get("full_name"),
                    bio=result.get("bio"),
                )
            )
        return UpdateUser(user=None)


class Mutation(ObjectType):
    update_user = UpdateUser.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize database pool on startup."""
    db = AsyncDatabase()
    await db.connect(min_size=10, max_size=50, statement_cache_size=100)
    app.state.db = db


@app.on_event("shutdown")
async def shutdown_event():
    """Close database pool on shutdown."""
    await app.state.db.close()


@app.post("/graphql")
async def graphql_endpoint(request: Request):
    try:
        # Parse JSON request
        body = await request.json()
        query = body.get("query")
        variables = body.get("variables") or {}

        # Create context with db and dataloaders
        db = app.state.db
        context = {
            "db": db,
            "user_loader": UserLoader(db),
            "post_loader": PostLoader(db),
            "posts_by_author_loader": PostsByAuthorLoader(db),
            "comments_by_post_loader": CommentsByPostLoader(db),
        }

        # Execute GraphQL query
        result = await schema.execute_async(query, context_value=context, variable_values=variables)

        response_data = {"data": result.data}
        if result.errors:
            response_data["errors"] = [{"message": str(e)} for e in result.errors]

        return JSONResponse(content=response_data)
    except Exception as e:
        return JSONResponse(status_code=400, content={"errors": [{"message": str(e)}]})


@app.get("/health")
async def health_check():
    return {"status": "healthy", "framework": "graphene"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
