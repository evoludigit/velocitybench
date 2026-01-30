"""In-memory test factory for Hasura integration tests."""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class TestUser:
    id: str
    pk_user: int
    username: str
    full_name: str
    bio: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class TestPost:
    id: str
    pk_post: int
    fk_author: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    author: TestUser | None = None


@dataclass
class TestComment:
    id: str
    pk_comment: int
    fk_post: int
    fk_author: int
    content: str
    created_at: datetime
    author: TestUser | None = None
    post: TestPost | None = None


class TestFactory:
    """In-memory test factory for isolated tests."""

    def __init__(self):
        self.users: dict[str, TestUser] = {}
        self.posts: dict[str, TestPost] = {}
        self.comments: dict[str, TestComment] = {}
        self._user_counter = 0
        self._post_counter = 0
        self._comment_counter = 0

    def create_user(
        self,
        username: str,
        email: str,
        full_name: str,
        bio: Optional[str] = None
    ) -> TestUser:
        self._user_counter += 1
        user = TestUser(
            id=str(uuid.uuid4()),
            pk_user=self._user_counter,
            username=username,
            full_name=full_name,
            bio=bio,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.users[user.id] = user
        return user

    def create_post(
        self,
        author_id: str,
        title: str,
        content: str = "Default content"
    ) -> TestPost:
        author = self.users.get(author_id)
        if not author:
            raise ValueError(f"Author not found: {author_id}")

        self._post_counter += 1
        post = TestPost(
            id=str(uuid.uuid4()),
            pk_post=self._post_counter,
            fk_author=author.pk_user,
            title=title,
            content=content,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            author=author,
        )
        self.posts[post.id] = post
        return post

    def create_comment(
        self,
        author_id: str,
        post_id: str,
        content: str
    ) -> TestComment:
        author = self.users.get(author_id)
        post = self.posts.get(post_id)

        if not author:
            raise ValueError("Author not found")
        if not post:
            raise ValueError("Post not found")

        self._comment_counter += 1
        comment = TestComment(
            id=str(uuid.uuid4()),
            pk_comment=self._comment_counter,
            fk_post=post.pk_post,
            fk_author=author.pk_user,
            content=content,
            created_at=datetime.now(timezone.utc),
            author=author,
            post=post,
        )
        self.comments[comment.id] = comment
        return comment

    def get_user(self, id: str) -> Optional[TestUser]:
        return self.users.get(id)

    def get_post(self, id: str) -> Optional[TestPost]:
        return self.posts.get(id)

    def get_comment(self, id: str) -> Optional[TestComment]:
        return self.comments.get(id)

    def get_all_users(self) -> list[TestUser]:
        return list(self.users.values())

    def get_posts_by_author(self, author_pk: int) -> list[TestPost]:
        return [p for p in self.posts.values() if p.fk_author == author_pk]

    def get_comments_by_post(self, post_pk: int) -> list[TestComment]:
        return [c for c in self.comments.values() if c.fk_post == post_pk]

    def reset(self):
        self.users.clear()
        self.posts.clear()
        self.comments.clear()
        self._user_counter = 0
        self._post_counter = 0
        self._comment_counter = 0


class ValidationHelper:
    UUID_REGEX = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

    @staticmethod
    def is_valid_uuid(value: str) -> bool:
        import re
        return bool(re.match(ValidationHelper.UUID_REGEX, value.lower()))


class DataGenerator:
    @staticmethod
    def generate_long_string(length: int) -> str:
        return "x" * length

    @staticmethod
    def generate_random_username() -> str:
        return f"user_{uuid.uuid4().hex[:8]}"
