#!/usr/bin/env python3
"""
Async GraphQL Benchmarking Server for Strawberry with SQLAlchemy ORM
Uses SQLAlchemy async ORM with DataLoader for N+1 prevention.
"""

import os
from datetime import datetime
from typing import Optional

import strawberry
from fastapi import FastAPI
from sqlalchemy import UUID, Column, DateTime, Text, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from strawberry.dataloader import DataLoader
from strawberry.fastapi import BaseContext, GraphQLRouter

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
    """SQLAlchemy model for benchmark.tv_user"""

    __tablename__ = "tv_user"
    __table_args__ = {"schema": "benchmark"}

    pk_user = Column(UUID, primary_key=True)
    id = Column(Text, unique=True, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    username = Column(Text, unique=True, nullable=False)
    full_name = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(
        Text, nullable=False, default=True
    )  # Note: schema shows BOOLEAN but we're using Text for compatibility
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to PostModel
    posts = relationship("PostModel", back_populates="author", foreign_keys=[PostModel.fk_author])


class PostModel(Base):
    """SQLAlchemy model for benchmark.tb_post"""

    __tablename__ = "tb_post"
    __table_args__ = {"schema": "benchmark"}

    pk_post = Column(UUID, primary_key=True)
    id = Column(Text, unique=True, nullable=False)
    fk_author = Column(UUID, nullable=False)  # Foreign key to tb_user.pk_user
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="published")
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to UserModel
    author = relationship("UserModel", back_populates="posts", foreign_keys=[fk_author])


class CommentModel(Base):
    """SQLAlchemy model for benchmark.tb_comment"""

    __tablename__ = "tb_comment"
    __table_args__ = {"schema": "benchmark"}

    pk_comment = Column(UUID, primary_key=True)
    id = Column(Text, unique=False)
    fk_post = Column(UUID, nullable=False)  # Foreign key to tb_post.pk_post
    fk_author = Column(UUID, nullable=False)  # Foreign key to tb_user.pk_user
    parent_id = Column(UUID, nullable=True)  # For nested comments
    content = Column(Text, nullable=False)
    is_approved = Column(
        Text, nullable=False, default="true"
    )  # Note: schema shows BOOLEAN but using Text for compatibility
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================================================
# DataLoader Functions
# ============================================================================


async def load_users_batch(keys: list[str], session_maker) -> list[dict | None]:
    """Batch load users by IDs using SQLAlchemy."""
    async with session_maker() as session:
        stmt = select(UserModel).where(UserModel.id.in_(keys))
        result = await session.execute(stmt)
        users = result.scalars().all()

        # Create map for O(1) lookup - convert to dict format expected by GraphQL
        user_map = {}
        for user in users:
            user_map[str(user.id)] = {
                "id": str(user.id),
                "username": user.username,
                "fullName": user.first_name,  # Note: keeping JSONB naming for compatibility
                "bio": user.bio,
            }
        return [user_map.get(key) for key in keys]


async def load_posts_batch(keys: list[str], session_maker) -> list[dict | None]:
    """Batch load posts by IDs using SQLAlchemy."""
    async with session_maker() as session:
        stmt = select(PostModel).where(PostModel.id.in_(keys))
        result = await session.execute(stmt)
        posts = result.scalars().all()

        # Create map for O(1) lookup - convert to dict format expected by GraphQL
        post_map = {}
        for post in posts:
            post_map[str(post.id)] = {
                "id": str(post.id),
                "title": post.title,
                "content": post.content,
                "author": {"id": str(post.fk_author)},  # Note: fk_author points to pk_user
            }
        return [post_map.get(key) for key in keys]


async def load_posts_by_author_batch(keys: list[str], session_maker) -> list[list[dict]]:
    """Batch load posts by author IDs using SQLAlchemy."""
    async with session_maker() as session:
        # Query posts where fk_author (which points to pk_user) corresponds to user IDs
        # First, get the pk_user values for the given user IDs
        user_stmt = select(UserModel.pk_user).where(UserModel.id.in_(keys))
        user_result = await session.execute(user_stmt)
        pk_users = [row[0] for row in user_result.all()]

        if not pk_users:
            return [[] for _ in keys]

        # Now query posts by pk_user values
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
                posts_by_author[str(user_id)].append(
                    {
                        "id": str(post.id),
                        "title": post.title,
                        "content": post.content,
                        "author": {"id": str(user_id)},
                    }
                )

        return [posts_by_author[key] for key in keys]


async def load_comments_by_post_batch(keys: list[str], session_maker) -> list[list[dict]]:
    """Batch load comments by post IDs using SQLAlchemy."""
    async with session_maker() as session:
        # Query comments where post.id is in the keys (JSONB query)
        stmt = (
            select(CommentModel)
            .where(func.jsonb_extract_path_text(CommentModel.data, "post", "id").in_(keys))
            .order_by(func.jsonb_extract_path_text(CommentModel.data, "createdAt").desc())
        )
        result = await session.execute(stmt)
        comments = result.scalars().all()

        # Group by post_id
        comments_by_post = {key: [] for key in keys}
        for comment in comments:
            post_id = comment.data.get("post", {}).get("id")
            if post_id in comments_by_post:
                comments_by_post[post_id].append(comment.data)

        return [comments_by_post[key][:50] for key in keys]  # Limit 50 per post


# ============================================================================
# GraphQL Types
# ============================================================================


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
                username=user_data.get("username"),
                first_name=user_data.get("fullName"),  # Note: JSONB has fullName
                last_name=None,
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
                author_id=post_data.get("author", {}).get("id"),
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
                username=user_data.get("username"),
                first_name=user_data.get("fullName"),
                last_name=None,
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
                author_id=comment.get("author", {}).get("id"),
                post_id=comment.get("post", {}).get("id"),
            )
            for comment in comments_data[:limit]
        ]


@strawberry.type
class User:
    id: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None

    @strawberry.field
    async def posts(self, info, limit: int = 50) -> list[Post]:
        posts_data = await info.context.posts_by_author_loader.load(self.id)
        return [
            Post(
                id=post["id"],
                title=post["title"],
                content=post.get("content"),
                author_id=post.get("author", {}).get("id"),
            )
            for post in posts_data[:limit]
        ]


# ============================================================================
# GraphQL Queries and Mutations
# ============================================================================


@strawberry.type
class Query:
    @strawberry.field
    async def ping(self) -> str:
        return "pong"

    @strawberry.field
    async def user(self, info, id: str) -> User | None:
        session_maker = info.context.session_maker
        async with session_maker() as session:
            stmt = select(UserModel).where(UserModel.id == id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()

            if user_model:
                data = user_model.data
                return User(
                    id=data["id"],
                    username=data.get("username"),
                    first_name=data.get("fullName"),
                    last_name=None,
                    bio=data.get("bio"),
                )
            return None

    @strawberry.field
    async def users(self, info, limit: int = 10) -> list[User]:
        session_maker = info.context.session_maker
        async with session_maker() as session:
            stmt = select(UserModel).limit(limit)
            result = await session.execute(stmt)
            users = result.scalars().all()

            return [
                User(
                    id=data["id"],
                    username=data.get("username"),
                    first_name=data.get("fullName"),
                    last_name=None,
                    bio=data.get("bio"),
                )
                for user in users
                if (data := user.data)
            ]

    @strawberry.field
    async def post(self, info, id: str) -> Post | None:
        session_maker = info.context.session_maker
        async with session_maker() as session:
            stmt = select(PostModel).where(PostModel.id == id)
            result = await session.execute(stmt)
            post_model = result.scalar_one_or_none()

            if post_model:
                data = post_model.data
                return Post(
                    id=data["id"],
                    title=data["title"],
                    content=data.get("content"),
                    author_id=data.get("author", {}).get("id"),
                )
            return None

    @strawberry.field
    async def posts(self, info, limit: int = 10) -> list[Post]:
        session_maker = info.context.session_maker
        async with session_maker() as session:
            stmt = select(PostModel).limit(limit)
            result = await session.execute(stmt)
            posts = result.scalars().all()

            return [
                Post(
                    id=data["id"],
                    title=data["title"],
                    content=data.get("content"),
                    author_id=data.get("author", {}).get("id"),
                )
                for post in posts
                if (data := post.data)
            ]

    @strawberry.field
    async def comment(self, info, id: str) -> Comment | None:
        session_maker = info.context.session_maker
        async with session_maker() as session:
            stmt = select(CommentModel).where(CommentModel.id == id)
            result = await session.execute(stmt)
            comment_model = result.scalar_one_or_none()

            if comment_model:
                data = comment_model.data
                return Comment(
                    id=data["id"],
                    content=data["content"],
                    author_id=data.get("author", {}).get("id"),
                    post_id=data.get("post", {}).get("id"),
                )
            return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def update_user(
        self,
        info,
        id: str,
        bio: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User | None:
        session_maker = info.context.session_maker
        async with session_maker() as session:
            # Load user
            stmt = select(UserModel).where(UserModel.id == id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()

            if not user_model:
                return None

            # Update JSONB data
            data = user_model.data.copy()
            if bio is not None:
                data["bio"] = bio
            if first_name is not None:
                data["fullName"] = first_name

            user_model.data = data
            user_model.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(user_model)

            # Return updated user
            return User(
                id=data["id"],
                username=data.get("username"),
                first_name=data.get("fullName"),
                last_name=None,
                bio=data.get("bio"),
            )


schema = strawberry.Schema(query=Query, mutation=Mutation)


# ============================================================================
# Context and Application Setup
# ============================================================================


class Context(BaseContext):
    def __init__(self, session_maker):
        super().__init__()
        self.session_maker = session_maker
        # Create DataLoaders for batching
        self.user_loader = DataLoader(load_fn=lambda keys: load_users_batch(keys, session_maker))
        self.post_loader = DataLoader(load_fn=lambda keys: load_posts_batch(keys, session_maker))
        self.posts_by_author_loader = DataLoader(
            load_fn=lambda keys: load_posts_by_author_batch(keys, session_maker)
        )
        self.comments_by_post_loader = DataLoader(
            load_fn=lambda keys: load_comments_by_post_batch(keys, session_maker)
        )


async def get_context() -> Context:
    """Context factory for each request."""
    return Context(session_maker=app.state.session_maker)


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


graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "framework": "strawberry-sqlalchemy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
