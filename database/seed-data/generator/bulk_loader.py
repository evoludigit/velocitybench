#!/usr/bin/env python
"""
Bulk Loader for Dataset Scaling

Loads generated TSV files to PostgreSQL using COPY (10-100x faster than INSERT).
"""

from pathlib import Path
from typing import Tuple, Optional
import logging

try:
    import psycopg
except ImportError:
    psycopg = None

logger = logging.getLogger(__name__)


class BulkLoader:
    """Load generated TSV files to PostgreSQL using COPY."""

    def __init__(self, output_dir: Path):
        """
        Initialize bulk loader.

        Args:
            output_dir: Directory with generated TSV files
        """
        self.output_dir = Path(output_dir)
        self.stats = {
            "users_loaded": 0,
            "posts_loaded": 0,
            "comments_loaded": 0,
        }

    def load_to_postgres(self, connection_string: str) -> tuple[bool, dict]:
        """
        Load TSV files to PostgreSQL using COPY.

        Args:
            connection_string: PostgreSQL connection string

        Returns:
            (success: bool, stats: dict)
        """
        if not psycopg:
            logger.error("psycopg not installed. Install with: pip install psycopg")
            return (False, self.stats)

        try:
            logger.info("Loading data to PostgreSQL...")

            with psycopg.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    # Load users
                    users_file = self.output_dir / "blog_users.tsv"
                    if users_file.exists():
                        logger.info(f"  Loading users from {users_file.name}...")
                        users_loaded = self._load_users(cur, users_file)
                        self.stats["users_loaded"] = users_loaded
                        logger.info(f"    ✓ Loaded {users_loaded:,} users")

                    # Load posts
                    posts_file = self.output_dir / "blog_posts.tsv"
                    if posts_file.exists():
                        logger.info(f"  Loading posts from {posts_file.name}...")
                        posts_loaded = self._load_posts(cur, posts_file)
                        self.stats["posts_loaded"] = posts_loaded
                        logger.info(f"    ✓ Loaded {posts_loaded:,} posts")

                    # Load comments
                    comments_file = self.output_dir / "blog_comments.tsv"
                    if comments_file.exists():
                        logger.info(f"  Loading comments from {comments_file.name}...")
                        comments_loaded = self._load_comments(cur, comments_file)
                        self.stats["comments_loaded"] = comments_loaded
                        logger.info(f"    ✓ Loaded {comments_loaded:,} comments")

                    conn.commit()

            logger.info("✓ Database loading complete")
            return (True, self.stats)

        except Exception as e:
            logger.error(f"Error loading to PostgreSQL: {e}")
            import traceback

            traceback.print_exc()
            return (False, self.stats)

    def _load_users(self, cur, users_file: Path) -> int:
        """
        Load users from TSV file.

        Args:
            cur: psycopg cursor
            users_file: Path to users TSV file

        Returns:
            Number of users loaded
        """
        with open(users_file, encoding="utf-8") as f:
            with cur.copy(
                "COPY benchmark.tb_user (pk_user, id, email, username, first_name, last_name, bio, is_active, created_at, updated_at) FROM STDIN"
            ) as copy:
                for line in f:
                    copy.write(line.encode("utf-8"))

        # Verify load
        cur.execute("SELECT COUNT(*) FROM benchmark.tb_user;")
        return cur.fetchone()[0]

    def _load_posts(self, cur, posts_file: Path) -> int:
        """
        Load posts from TSV file.

        Args:
            cur: psycopg cursor
            posts_file: Path to posts TSV file

        Returns:
            Number of posts loaded
        """
        with open(posts_file, encoding="utf-8") as f:
            with cur.copy(
                "COPY benchmark.tb_post (pk_post, id, title, content, excerpt, fk_author, status, published_at, created_at, updated_at, views, likes, bookmarks) FROM STDIN"
            ) as copy:
                for line in f:
                    copy.write(line.encode("utf-8"))

        # Verify load
        cur.execute("SELECT COUNT(*) FROM benchmark.tb_post;")
        return cur.fetchone()[0]

    def _load_comments(self, cur, comments_file: Path) -> int:
        """
        Load comments from TSV file.

        Args:
            cur: psycopg cursor
            comments_file: Path to comments TSV file

        Returns:
            Number of comments loaded
        """
        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS benchmark.tb_comment (
                pk_comment INTEGER PRIMARY KEY,
                id TEXT NOT NULL,
                fk_post INTEGER NOT NULL REFERENCES benchmark.tb_post(pk_post),
                fk_author INTEGER NOT NULL REFERENCES benchmark.tb_user(pk_user),
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            );
        """)

        with open(comments_file, encoding="utf-8") as f:
            with cur.copy(
                "COPY benchmark.tb_comment (pk_comment, id, fk_post, fk_author, content, created_at, updated_at) FROM STDIN"
            ) as copy:
                for line in f:
                    copy.write(line.encode("utf-8"))

        # Verify load
        cur.execute("SELECT COUNT(*) FROM benchmark.tb_comment;")
        return cur.fetchone()[0]
