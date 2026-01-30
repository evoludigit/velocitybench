#!/usr/bin/env python3
"""
Async GraphQL Benchmarking Server for Strawberry with DataLoader
Uses connection pooling and DataLoader to prevent N+1 queries.

Best practices implemented:
- Error handling with proper GraphQL error responses
- Input validation for all resolver parameters
- Timeout protection for all database queries
- Request context with metadata (request_id, timing)
- Proper use of strawberry.ID scalar type
- DataLoader with error handling
- Field descriptions for GraphQL introspection
"""

import asyncio
import logging
import os
import sys
import time
from typing import Optional
from uuid import uuid4

import strawberry
from fastapi import FastAPI, Request
from strawberry.dataloader import DataLoader
from strawberry.fastapi import BaseContext, GraphQLRouter
from strawberry.types import ExecutionResult

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.async_db import AsyncDatabase
from common.health_check import HealthCheckManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Input validation helpers
def validate_uuid(value: str) -> bool:
    """Validate that value is a valid UUID."""
    try:
        from uuid import UUID
        UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


# DataLoader functions with error handling
async def load_users_batch(keys: list[str], db: AsyncDatabase) -> list[dict | None]:
    """Batch load users by IDs with error handling."""
    try:
        result = await db.fetch(
            "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = ANY($1)",
            keys,
            timeout=5.0
        )
        # Create a map for O(1) lookup
        user_map = {user["id"]: user for user in result}
        # Return in the same order as keys
        return [user_map.get(key) for key in keys]
    except asyncio.TimeoutError:
        logger.error(f"Timeout loading users: {keys}")
        return [None] * len(keys)
    except Exception as e:
        logger.exception(f"Error loading users batch: {e}")
        return [None] * len(keys)


async def load_posts_batch(keys: list[str], db: AsyncDatabase) -> list[dict | None]:
    """Batch load posts by IDs with error handling."""
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
        post_map = {post["id"]: post for post in result}
        return [post_map.get(key) for key in keys]
    except asyncio.TimeoutError:
        logger.error(f"Timeout loading posts: {keys}")
        return [None] * len(keys)
    except Exception as e:
        logger.exception(f"Error loading posts batch: {e}")
        return [None] * len(keys)


async def load_posts_by_author_batch(keys: list[str], db: AsyncDatabase) -> list[list[dict]]:
    """Batch load posts by author IDs with error handling."""
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
        # Group by author_id
        posts_by_author = {key: [] for key in keys}
        for post in result:
            posts_by_author[post["author_id"]].append(post)
        return [posts_by_author[key] for key in keys]
    except asyncio.TimeoutError:
        logger.error(f"Timeout loading posts by author: {keys}")
        return [[] for _ in keys]
    except Exception as e:
        logger.exception(f"Error loading posts by author: {e}")
        return [[] for _ in keys]


async def load_comments_by_post_batch(keys: list[str], db: AsyncDatabase) -> list[list[dict]]:
    """Batch load comments by post IDs with error handling."""
    try:
        result = await db.fetch(
            """
            SELECT c.id, c.content, p.id as post_id, u.id as author_id
            FROM benchmark.tb_comment c
            JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
            JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
            WHERE p.id = ANY($1)
            ORDER BY p.id, c.created_at DESC
            LIMIT 50
            """,
            keys,
            timeout=5.0
        )
        # Group by post_id
        comments_by_post = {key: [] for key in keys}
        for comment in result:
            comments_by_post[comment["post_id"]].append(comment)
        return [comments_by_post[key] for key in keys]
    except asyncio.TimeoutError:
        logger.error(f"Timeout loading comments by post: {keys}")
        return [[] for _ in keys]
    except Exception as e:
        logger.exception(f"Error loading comments by post: {e}")
        return [[] for _ in keys]


@strawberry.type
class Comment:
    """A comment on a post."""
    id: strawberry.ID = strawberry.field(description="Unique comment identifier")
    content: str = strawberry.field(description="Comment text content")
    author_id: strawberry.ID | None = strawberry.field(
        default=None,
        description="UUID of the comment author"
    )
    post_id: strawberry.ID | None = strawberry.field(
        default=None,
        description="UUID of the post this comment belongs to"
    )

    @strawberry.field(description="Author who wrote this comment")
    async def author(self, info) -> Optional["User"]:
        if not self.author_id:
            return None
        try:
            user_data = await info.context.user_loader.load(str(self.author_id))
            if user_data:
                return User(
                    id=strawberry.ID(user_data["id"]),
                    username=user_data["username"],
                    full_name=user_data.get("full_name"),
                    bio=user_data.get("bio"),
                )
        except Exception as e:
            logger.exception(f"Error loading author for comment {self.id}: {e}")
        return None

    @strawberry.field(description="Post this comment belongs to")
    async def post(self, info) -> Optional["Post"]:
        if not self.post_id:
            return None
        try:
            post_data = await info.context.post_loader.load(str(self.post_id))
            if post_data:
                return Post(
                    id=strawberry.ID(post_data["id"]),
                    title=post_data["title"],
                    content=post_data.get("content"),
                    author_id=strawberry.ID(post_data.get("author_id")) if post_data.get("author_id") else None,
                )
        except Exception as e:
            logger.exception(f"Error loading post for comment {self.id}: {e}")
        return None


@strawberry.type
class Post:
    """A published post."""
    id: strawberry.ID = strawberry.field(description="Unique post identifier")
    title: str = strawberry.field(description="Post title")
    content: str | None = strawberry.field(
        default=None,
        description="Post content (markdown format)"
    )
    author_id: strawberry.ID | None = strawberry.field(
        default=None,
        description="UUID of the post author"
    )

    @strawberry.field(description="Author who wrote this post")
    async def author(self, info) -> Optional["User"]:
        if not self.author_id:
            return None
        try:
            user_data = await info.context.user_loader.load(str(self.author_id))
            if user_data:
                return User(
                    id=strawberry.ID(user_data["id"]),
                    username=user_data["username"],
                    full_name=user_data.get("full_name"),
                    bio=user_data.get("bio"),
                )
        except Exception as e:
            logger.exception(f"Error loading author for post {self.id}: {e}")
        return None

    @strawberry.field(description="Comments on this post (limited to 50)")
    async def comments(self, info, limit: int = strawberry.field(default=50, description="Max 50 comments")) -> list["Comment"]:
        if limit > 50:
            limit = 50  # Server-side limit
        try:
            comments_data = await info.context.comments_by_post_loader.load(str(self.id))
            return [
                Comment(
                    id=strawberry.ID(comment["id"]),
                    content=comment["content"],
                    author_id=strawberry.ID(comment.get("author_id")) if comment.get("author_id") else None,
                    post_id=strawberry.ID(comment.get("post_id")) if comment.get("post_id") else None,
                )
                for comment in comments_data[:limit]
            ]
        except Exception as e:
            logger.exception(f"Error loading comments for post {self.id}: {e}")
            return []


@strawberry.type
class User:
    """A user in the system."""
    id: strawberry.ID = strawberry.field(description="Unique user identifier")
    username: str = strawberry.field(description="User's login username")
    full_name: str | None = strawberry.field(
        default=None,
        description="User's full name"
    )
    bio: str | None = strawberry.field(
        default=None,
        description="User's biography"
    )

    @strawberry.field(description="Number of followers (placeholder)")
    def follower_count(self) -> int:
        """Return follower count (placeholder - no follows table in db)."""
        return 0

    @strawberry.field(description="Posts authored by this user")
    async def posts(self, info, limit: int = strawberry.field(default=50, description="Max 50 posts")) -> list[Post]:
        if limit > 50:
            limit = 50  # Server-side limit
        try:
            posts_data = await info.context.posts_by_author_loader.load(str(self.id))
            return [
                Post(
                    id=strawberry.ID(post["id"]),
                    title=post["title"],
                    content=post.get("content"),
                    author_id=strawberry.ID(post.get("author_id")) if post.get("author_id") else None,
                )
                for post in posts_data[:limit]
            ]
        except Exception as e:
            logger.exception(f"Error loading posts for user {self.id}: {e}")
            return []


@strawberry.type
class Query:
    """Root query type."""

    @strawberry.field(description="Health check endpoint")
    async def ping(self) -> str:
        """Returns 'pong' to verify server is responding."""
        return "pong"

    @strawberry.field(description="Fetch a single user by ID")
    async def user(self, info, id: strawberry.ID = strawberry.field(description="User ID (UUID)")) -> User | None:
        """Fetch a user by their UUID."""
        try:
            # Validate UUID format
            if not validate_uuid(str(id)):
                logger.warning(f"Invalid user ID format: {id}")
                raise ValueError(f"Invalid user ID format: {id}")

            db = info.context.db
            result = await db.fetchrow(
                "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1",
                id,
                timeout=5.0
            )
            if result:
                return User(
                    id=strawberry.ID(result["id"]),
                    username=result["username"],
                    full_name=result.get("full_name"),
                    bio=result.get("bio"),
                )
            return None
        except ValueError as e:
            logger.warning(f"Invalid input for user query: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching user {id}")
            raise
        except Exception as e:
            logger.exception(f"Error fetching user {id}: {e}")
            raise

    @strawberry.field(description="Fetch multiple users")
    async def users(self, info, limit: int = strawberry.field(default=10, description="Max 100 users")) -> list[User]:
        """Fetch a list of users with pagination."""
        try:
            if limit > 100:
                limit = 100  # Server-side limit
            if limit < 1:
                limit = 1

            db = info.context.db
            result = await db.fetch(
                "SELECT id, username, full_name, bio FROM benchmark.tb_user LIMIT $1",
                limit,
                timeout=5.0
            )
            return [
                User(
                    id=strawberry.ID(row["id"]),
                    username=row["username"],
                    full_name=row.get("full_name"),
                    bio=row.get("bio"),
                )
                for row in result
            ]
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching users with limit {limit}")
            raise
        except Exception as e:
            logger.exception(f"Error fetching users: {e}")
            raise

    @strawberry.field(description="Fetch a single post by ID")
    async def post(self, info, id: strawberry.ID = strawberry.field(description="Post ID (UUID)")) -> Post | None:
        """Fetch a post by its UUID."""
        try:
            if not validate_uuid(str(id)):
                logger.warning(f"Invalid post ID format: {id}")
                raise ValueError(f"Invalid post ID format: {id}")

            db = info.context.db
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
                return Post(
                    id=strawberry.ID(result["id"]),
                    title=result["title"],
                    content=result.get("content"),
                    author_id=strawberry.ID(result.get("author_id")) if result.get("author_id") else None,
                )
            return None
        except ValueError as e:
            logger.warning(f"Invalid input for post query: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching post {id}")
            raise
        except Exception as e:
            logger.exception(f"Error fetching post {id}: {e}")
            raise

    @strawberry.field(description="Fetch multiple posts")
    async def posts(self, info, limit: int = strawberry.field(default=10, description="Max 100 posts")) -> list[Post]:
        """Fetch a list of posts ordered by creation date (newest first)."""
        try:
            if limit > 100:
                limit = 100  # Server-side limit
            if limit < 1:
                limit = 1

            db = info.context.db
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
                Post(
                    id=strawberry.ID(row["id"]),
                    title=row["title"],
                    content=row.get("content"),
                    author_id=strawberry.ID(row.get("author_id")) if row.get("author_id") else None,
                )
                for row in result
            ]
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching posts with limit {limit}")
            raise
        except Exception as e:
            logger.exception(f"Error fetching posts: {e}")
            raise

    @strawberry.field(description="Fetch a single comment by ID")
    async def comment(self, info, id: strawberry.ID = strawberry.field(description="Comment ID (UUID)")) -> Comment | None:
        """Fetch a comment by its UUID."""
        try:
            if not validate_uuid(str(id)):
                logger.warning(f"Invalid comment ID format: {id}")
                raise ValueError(f"Invalid comment ID format: {id}")

            db = info.context.db
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
                return Comment(
                    id=strawberry.ID(result["id"]),
                    content=result["content"],
                    author_id=strawberry.ID(result.get("author_id")) if result.get("author_id") else None,
                    post_id=strawberry.ID(result.get("post_id")) if result.get("post_id") else None,
                )
            return None
        except ValueError as e:
            logger.warning(f"Invalid input for comment query: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching comment {id}")
            raise
        except Exception as e:
            logger.exception(f"Error fetching comment {id}: {e}")
            raise


@strawberry.type
class Mutation:
    """Root mutation type."""

    @strawberry.mutation(description="Update a user's profile")
    async def update_user(
        self,
        info,
        id: strawberry.ID = strawberry.field(description="User ID to update"),
        bio: str | None = strawberry.field(default=None, description="Updated biography"),
        full_name: str | None = strawberry.field(default=None, description="Updated full name"),
    ) -> User | None:
        """Update user profile information (bio and/or full_name)."""
        try:
            # Validate UUID format
            if not validate_uuid(str(id)):
                logger.warning(f"Invalid user ID format for update: {id}")
                raise ValueError(f"Invalid user ID format: {id}")

            # Validate at least one field is being updated
            if bio is None and full_name is None:
                raise ValueError("At least one of bio or full_name must be provided")

            db = info.context.db

            # Build dynamic update query
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
                    timeout=5.0
                )

            # Return updated user
            result = await db.fetchrow(
                "SELECT id, username, full_name, bio FROM benchmark.tb_user WHERE id = $1",
                id,
                timeout=5.0
            )
            if result:
                return User(
                    id=strawberry.ID(result["id"]),
                    username=result["username"],
                    full_name=result.get("full_name"),
                    bio=result.get("bio"),
                )
            return None
        except ValueError as e:
            logger.warning(f"Invalid input for update_user mutation: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Timeout updating user {id}")
            raise
        except Exception as e:
            logger.exception(f"Error updating user {id}: {e}")
            raise


# Create schema with automatic camelCase conversion for snake_case fields
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    config=strawberry.SchemaConfig(
        name_converter=strawberry.utils.str_converters.to_camel_case
    )
)


class Context(BaseContext):
    """GraphQL request context with database access and DataLoaders."""

    def __init__(
        self,
        db: AsyncDatabase,
        request: Request | None = None,
        request_id: str | None = None,
    ):
        super().__init__()
        self.db = db
        self.request = request
        self.request_id = request_id or str(uuid4())
        self.start_time = time.time()

        # Create DataLoaders for batching (proper function references instead of lambdas)
        self.user_loader: DataLoader[str, dict | None] = DataLoader(
            load_fn=lambda keys: load_users_batch(keys, db)
        )
        self.post_loader: DataLoader[str, dict | None] = DataLoader(
            load_fn=lambda keys: load_posts_batch(keys, db)
        )
        self.posts_by_author_loader: DataLoader[str, list[dict]] = DataLoader(
            load_fn=lambda keys: load_posts_by_author_batch(keys, db)
        )
        self.comments_by_post_loader: DataLoader[str, list[dict]] = DataLoader(
            load_fn=lambda keys: load_comments_by_post_batch(keys, db)
        )

    def log_request(self, query_name: str, duration: float):
        """Log request execution time."""
        logger.info(
            f"[{self.request_id}] {query_name} completed in {duration:.3f}s"
        )


async def get_context(request: Request) -> Context:
    """Context factory for each request with request metadata."""
    request_id = request.headers.get("x-request-id", str(uuid4()))
    return Context(
        db=app.state.db,
        request=request,
        request_id=request_id,
    )


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

    # Initialize health check manager
    health_manager = HealthCheckManager(
        service_name="strawberry-graphql",
        version="1.0.0",
        database=db,
        environment=os.getenv("ENVIRONMENT", "development"),
    )
    app.state.health = health_manager


@app.on_event("shutdown")
async def shutdown_event():
    """Close database pool on shutdown."""
    await app.state.db.close()


graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")


# Health check endpoints
@app.get("/health")
async def health():
    """Combined health check (defaults to readiness)"""
    result = await app.state.health.probe("readiness")
    return result.to_dict()


@app.get("/health/live")
async def health_live():
    """Liveness probe - Is the process alive?"""
    result = await app.state.health.probe("liveness")
    return result.to_dict()


@app.get("/health/ready")
async def health_ready():
    """Readiness probe - Can the service handle traffic?"""
    result = await app.state.health.probe("readiness")
    return result.to_dict()


@app.get("/health/startup")
async def health_startup():
    """Startup probe - Has initialization completed?"""
    result = await app.state.health.probe("startup")
    return result.to_dict()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
