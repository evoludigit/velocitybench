#!/usr/bin/env python3
"""
Async GraphQL Benchmarking Server for Graphene with SQLAlchemy ORM
Uses SQLAlchemy async ORM with aiodataloader for N+1 prevention.
"""

import asyncio
import json
import os
from datetime import datetime

import asyncpg
import graphene
from aiodataloader import DataLoader
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from graphene import ID, Field, Int, ObjectType, String
from graphene import List as GrapheneList
from sqlalchemy import UUID, Column, DateTime, Integer, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Database configuration
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.getenv('DB_USER', 'benchmark')}:"
    f"{os.getenv('DB_PASSWORD', 'benchmark123')}@"
    f"{os.getenv('DB_HOST', 'postgres')}:"
    f"{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'fraiseql_benchmark')}"
)

Base = declarative_base()


# ============================================================================
# SQLAlchemy Models
# ============================================================================


class UserModel(Base):
    """SQLAlchemy model for benchmark.tb_user"""

    __tablename__ = "tb_user"
    __table_args__ = {"schema": "benchmark"}

    pk_user = Column(Integer, primary_key=True)
    id = Column(UUID, unique=True, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    username = Column(Text, unique=True, nullable=False)
    full_name = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Text, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PostModel(Base):
    """SQLAlchemy model for benchmark.tb_post"""

    __tablename__ = "tb_post"
    __table_args__ = {"schema": "benchmark"}

    pk_post = Column(Integer, primary_key=True)
    id = Column(UUID, unique=True, nullable=False)
    fk_author = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="published")
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CommentModel(Base):
    """SQLAlchemy model for benchmark.tb_comment"""

    __tablename__ = "tb_comment"
    __table_args__ = {"schema": "benchmark"}

    pk_comment = Column(Integer, primary_key=True)
    id = Column(UUID, unique=True, nullable=False)
    fk_post = Column(Integer, nullable=False)
    fk_author = Column(Integer, nullable=False)
    parent_id = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    is_approved = Column(Text, nullable=False, default="true")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================================================
# DataLoader Classes
# ============================================================================


class UserLoader(DataLoader):
    def __init__(self, session_maker):
        super().__init__()
        self.session_maker = session_maker

    async def batch_load_fn(self, keys: list[str]) -> list[dict | None]:
        async with self.session_maker() as session:
            stmt = select(UserModel).where(UserModel.id.in_(keys))
            result = await session.execute(stmt)
            users = result.scalars().all()
            user_map = {str(user.id): {
                "id": str(user.id),
                "username": user.username,
                "fullName": user.full_name,
                "bio": user.bio,
            } for user in users}
            return [user_map.get(key) for key in keys]


class PostLoader(DataLoader):
    def __init__(self, session_maker):
        super().__init__()
        self.session_maker = session_maker

    async def batch_load_fn(self, keys: list[str]) -> list[dict | None]:
        async with self.session_maker() as session:
            stmt = select(PostModel).where(PostModel.id.in_(keys))
            result = await session.execute(stmt)
            posts = result.scalars().all()
            post_map = {str(post.id): {
                "id": str(post.id),
                "title": post.title,
                "content": post.content,
                "author": {"id": str(post.fk_author)},
            } for post in posts}
            return [post_map.get(key) for key in keys]


class PostsByAuthorLoader(DataLoader):
    def __init__(self, session_maker):
        super().__init__()
        self.session_maker = session_maker

    async def batch_load_fn(self, keys: list[str]) -> list[list[dict]]:
        async with self.session_maker() as session:
            # Get pk_user values for the given user IDs
            user_stmt = select(UserModel.pk_user).where(UserModel.id.in_(keys))
            user_result = await session.execute(user_stmt)
            pk_users = [row[0] for row in user_result.all()]

            if not pk_users:
                return [[] for _ in keys]

            # Query posts by pk_user values
            stmt = (
                select(PostModel)
                .where(PostModel.fk_author.in_(pk_users))
                .order_by(PostModel.created_at.desc())
            )
            result = await session.execute(stmt)
            posts = result.scalars().all()

            # Group by author_id (user.id)
            posts_by_author = {key: [] for key in keys}
            for post in posts:
                # Find the user ID for this post's fk_author
                user_stmt = select(UserModel.id).where(UserModel.pk_user == post.fk_author)
                user_result = await session.execute(user_stmt)
                user_id = user_result.scalar_one_or_none()

                if user_id and str(user_id) in posts_by_author:
                    posts_by_author[str(user_id)].append({
                        "id": str(post.id),
                        "title": post.title,
                        "content": post.content,
                        "author": {"id": str(user_id)},
                    })

            return [posts_by_author[key] for key in keys]


class CommentsByPostLoader(DataLoader):
    def __init__(self, session_maker):
        super().__init__()
        self.session_maker = session_maker

    async def batch_load_fn(self, keys: list[str]) -> list[list[dict]]:
        async with self.session_maker() as session:
            # Get pk_post values for the given post IDs
            post_stmt = select(PostModel.pk_post).where(PostModel.id.in_(keys))
            post_result = await session.execute(post_stmt)
            pk_posts = [row[0] for row in post_result.all()]

            if not pk_posts:
                return [[] for _ in keys]

            # Query comments by pk_post values
            stmt = (
                select(CommentModel)
                .where(CommentModel.fk_post.in_(pk_posts))
                .order_by(CommentModel.created_at.desc())
            )
            result = await session.execute(stmt)
            comments = result.scalars().all()

            # Group by post_id
            comments_by_post = {key: [] for key in keys}
            for comment in comments:
                # Find the post ID for this comment's fk_post
                post_stmt = select(PostModel.id).where(PostModel.pk_post == comment.fk_post)
                post_result = await session.execute(post_stmt)
                post_id = post_result.scalar_one_or_none()

                if post_id and str(post_id) in comments_by_post:
                    comments_by_post[str(post_id)].append({
                        "id": str(comment.id),
                        "content": comment.content,
                        "author": {"id": str(comment.fk_author)},
                        "post": {"id": str(post_id)},
                    })

            return [comments_by_post[key][:50] for key in keys]


# ============================================================================
# GraphQL Types
# ============================================================================


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
                username=user_data.get("username"),
                first_name=user_data.get("fullName"),
                last_name=None,
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
                author_id=post_data.get("author", {}).get("id"),
            )
        return None


class Post(ObjectType):
    id = ID()
    title = String()
    content = String()
    author = Field(lambda: User)
    comments = GrapheneList(lambda: Comment)

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
                username=user_data.get("username"),
                first_name=user_data.get("fullName"),
                last_name=None,
                bio=user_data.get("bio"),
            )
        return None

    async def resolve_comments(self, info):
        comments_data = await info.context["comments_by_post_loader"].load(self.id)
        return [
            Comment(
                id=comment["id"],
                content=comment["content"],
                author_id=comment.get("author", {}).get("id"),
                post_id=comment.get("post", {}).get("id"),
            )
            for comment in comments_data
        ]


class User(ObjectType):
    id = ID()
    username = String()
    first_name = String()
    last_name = String()
    bio = String()
    posts = GrapheneList(lambda: Post)

    async def resolve_posts(self, info):
        posts_data = await info.context["posts_by_author_loader"].load(self.id)
        return [
            Post(
                id=post["id"],
                title=post["title"],
                content=post.get("content"),
                author_id=post.get("author", {}).get("id"),
            )
            for post in posts_data[:10]
        ]


# ============================================================================
# GraphQL Queries and Mutations
# ============================================================================


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
        session_maker = info.context["session_maker"]
        async with session_maker() as session:
            stmt = select(UserModel).where(UserModel.id == id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()

            if not user_model:
                return None

            return User(
                id=str(user_model.id),
                username=user_model.username,
                first_name=user_model.full_name,
                last_name=None,
                bio=user_model.bio,
            )

    async def resolve_users(self, info, limit):
        session_maker = info.context["session_maker"]
        async with session_maker() as session:
            stmt = select(UserModel).limit(limit)
            result = await session.execute(stmt)
            users = result.scalars().all()

            return [
                User(
                    id=str(user.id),
                    username=user.username,
                    first_name=user.full_name,
                    last_name=None,
                    bio=user.bio,
                )
                for user in users
            ]

    async def resolve_post(self, info, id):
        session_maker = info.context["session_maker"]
        async with session_maker() as session:
            stmt = select(PostModel).where(PostModel.id == id)
            result = await session.execute(stmt)
            post_model = result.scalar_one_or_none()

            if post_model:
                return Post(
                    id=str(post_model.id),
                    title=post_model.title,
                    content=post_model.content,
                    author_id=str(post_model.fk_author),
                )
            return None

    async def resolve_posts(self, info, limit):
        session_maker = info.context["session_maker"]
        async with session_maker() as session:
            stmt = select(PostModel).limit(limit)
            result = await session.execute(stmt)
            posts = result.scalars().all()

            return [
                Post(
                    id=str(post.id),
                    title=post.title,
                    content=post.content,
                    author_id=str(post.fk_author),
                )
                for post in posts
            ]

    async def resolve_comment(self, info, id):
        session_maker = info.context["session_maker"]
        async with session_maker() as session:
            stmt = select(CommentModel).where(CommentModel.id == id)
            result = await session.execute(stmt)
            comment_model = result.scalar_one_or_none()

            if comment_model:
                return Comment(
                    id=str(comment_model.id),
                    content=comment_model.content,
                    author_id=str(comment_model.fk_author),
                    post_id=str(comment_model.fk_post),
                )
            return None


class UpdateUser(graphene.Mutation):
    class Arguments:
        id = ID(required=True)
        bio = String()
        first_name = String()
        last_name = String()

    user = Field(lambda: User)

    async def mutate(self, info, id, bio=None, first_name=None, last_name=None):
        session_maker = info.context["session_maker"]
        async with session_maker() as session:
            # Load user
            stmt = select(UserModel).where(UserModel.id == id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()

            if not user_model:
                return UpdateUser(user=None)

            # Update user fields
            if bio is not None:
                user_model.bio = bio
            if first_name is not None:
                user_model.full_name = first_name

            user_model.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(user_model)

            return UpdateUser(
                user=User(
                    id=str(user_model.id),
                    username=user_model.username,
                    first_name=user_model.full_name,
                    last_name=None,
                    bio=user_model.bio,
                )
            )


class Mutation(ObjectType):
    update_user = UpdateUser.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize SQLAlchemy engine on startup."""
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        echo=False,
    )
    app.state.session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )


@app.post("/graphql")
async def graphql_endpoint(request: Request):
    try:
        # Parse JSON request
        body = await request.json()
        query = body.get("query")
        variables = body.get("variables") or {}

        # Create context with session maker and dataloaders
        session_maker = app.state.session_maker
        context = {
            "session_maker": session_maker,
            "user_loader": UserLoader(session_maker),
            "post_loader": PostLoader(session_maker),
            "posts_by_author_loader": PostsByAuthorLoader(session_maker),
            "comments_by_post_loader": CommentsByPostLoader(session_maker),
        }

        # Execute GraphQL query
        result = await schema.execute_async(query, context_value=context, variable_values=variables)

        response_data = {"data": result.data}
        if result.errors:
            response_data["errors"] = [{"message": str(e)} for e in result.errors]

        return JSONResponse(content=response_data)
    except (asyncpg.PostgresError, json.JSONDecodeError, ValueError, ConnectionError, OSError) as e:
        return JSONResponse(status_code=400, content={"errors": [{"message": str(e)}]})


@app.get("/health")
async def health_check():
    return {"status": "healthy", "framework": "graphene-sqlalchemy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
