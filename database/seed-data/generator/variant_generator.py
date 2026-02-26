#!/usr/bin/env python
"""
Variant Generator for Dataset Scaling

Creates lightweight variants of seed posts by mutating metadata while keeping body identical.
200 variants per seed post = lightweight scaling without content bloat.

Variants differ in:
  - Title (add suffix: "(2026)", "(Beginner)", "(Advanced)")
  - Slug (append variant number)
  - Published date (spread over 5-10 years)
  - Author (rotate through users)
  - Tags/categories (recombine)
  - Status (70% published, 30% draft)
  - Metrics (random views, likes, bookmarks)

Body stays identical (or lightly mutated at 2% rate for larger scales).
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from faker import Faker

    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False
    Faker = None

logger = logging.getLogger(__name__)


class VariantGenerator:
    """Generate lightweight variants from seed posts."""

    # Title suffixes for variants
    TITLE_SUFFIXES = [
        "(2026)",
        "(2025)",
        "(2024)",
        "(2023)",
        "(Beginner)",
        "(Intermediate)",
        "(Advanced)",
        "(Quick Guide)",
        "(Deep Dive)",
        "(Cheat Sheet)",
        "(Best Practices)",
        "(Gotchas)",
        "(Performance)",
        "(Testing)",
        "(Debugging)",
        "(Integration)",
        "(Migration)",
        "(Refactor)",
        "(Case Study)",
        "(FAQ)",
        "(Tutorial)",
        "(Reference)",
    ]

    # Status distribution: 70% published, 30% draft
    STATUS_WEIGHTS = {"published": 0.7, "draft": 0.3}

    def __init__(self, seed_dir: Path, scale_params: dict[str, Any]):
        """
        Initialize variant generator.

        Args:
            seed_dir: Path to gold corpus with seed posts
            scale_params: dict with 'posts', 'users', 'comments', 'seed_posts', 'profile'
        """
        self.seed_dir = Path(seed_dir)
        self.scale_params = scale_params

        # Initialize Faker with fixed seed for reproducibility
        if HAS_FAKER:
            self.fake = Faker()
            Faker.seed(42)
        else:
            self.fake = None

        random.seed(42)

        # Statistics
        self.stats = {
            "posts_generated": 0,
            "users_generated": 0,
            "comments_generated": 0,
            "variants_per_seed": 0,
        }

    def discover_seed_posts(self) -> list[dict[str, Any]]:
        """
        Discover and load seed posts from gold corpus.

        For now, returns empty list if corpus doesn't exist.
        In production, would load actual 5K posts from markdown files.

        Returns:
            List of seed post dicts
        """
        seed_posts = []

        if self.seed_dir.exists():
            # In production, would load actual posts from corpus
            md_files = list(self.seed_dir.rglob("*.md"))
            for i, md_file in enumerate(md_files[: self.scale_params["seed_posts"]]):
                post = {
                    "id": str(uuid.uuid4()),
                    "title": md_file.stem.replace("-", " ").title(),
                    "body": f"Content from {md_file.name}",
                    "excerpt": f"Excerpt from {md_file.stem}...",
                    "original_slug": md_file.stem,
                }
                seed_posts.append(post)
        else:
            # Generate synthetic seed posts for testing
            logger.warning("Gold corpus not found, generating synthetic seed posts")
            for i in range(self.scale_params["seed_posts"]):
                post = {
                    "id": str(uuid.uuid4()),
                    "title": self.fake.sentence(nb_words=6),
                    "body": self.fake.paragraph(nb_sentences=10),
                    "excerpt": self.fake.sentence(nb_words=15),
                    "original_slug": f"post-{i:05d}",
                }
                seed_posts.append(post)

        logger.info(f"Discovered {len(seed_posts)} seed posts")
        return seed_posts

    def generate_users(self, count: int) -> list[dict[str, Any]]:
        """
        Generate users with Faker.

        Args:
            count: Number of users to generate

        Returns:
            List of user dicts
        """
        logger.info(f"Generating {count:,} users...")
        users = []
        used_usernames = set()

        for i in range(count):
            email = self.fake.unique.email()
            username = email.split("@")[0]

            # Ensure unique username
            if username in used_usernames:
                counter = 1
                while f"{username}{counter}" in used_usernames:
                    counter += 1
                username = f"{username}{counter}"

            used_usernames.add(username)
            name_parts = self.fake.name().split()

            user = {
                "pk_user": i + 1,
                "id": str(uuid.uuid4()),
                "email": email,
                "username": username,
                "first_name": name_parts[0] if name_parts else "User",
                "last_name": name_parts[-1] if len(name_parts) > 1 else str(i),
                "bio": self.fake.text(max_nb_chars=200)
                if random.random() > 0.3
                else None,
                "is_active": True,
                "created_at": datetime.now() - timedelta(days=random.randint(1, 730)),
                "updated_at": datetime.now(),
            }
            users.append(user)

        logger.info(f"  ✓ Generated {len(users):,} users")
        return users

    def mutate_title(self, original_title: str, variant_index: int) -> str:
        """
        Mutate post title with suffix.

        Args:
            original_title: Original post title
            variant_index: Index of this variant (0-199)

        Returns:
            Mutated title
        """
        # Pick a suffix based on variant index
        suffix_index = variant_index % len(self.TITLE_SUFFIXES)
        suffix = self.TITLE_SUFFIXES[suffix_index]

        return f"{original_title} {suffix}".strip()

    def spread_publish_date(self, seed_index: int, variant_index: int) -> datetime:
        """
        Spread publication dates across 5-10 years.

        Args:
            seed_index: Index of seed post
            variant_index: Index of variant (0-199)

        Returns:
            datetime for publication
        """
        # Use seed and variant to deterministically spread dates
        combined_index = (seed_index * 200) + variant_index
        days_back = (combined_index % 3650) + 365  # 1-10 years back
        return datetime.now() - timedelta(days=days_back)

    def assign_author(self, variant_index: int, num_users: int) -> int:
        """
        Assign author using round-robin.

        Args:
            variant_index: Index of variant
            num_users: Total number of users

        Returns:
            pk_user (1-indexed)
        """
        return 1 + (variant_index % num_users)

    def pick_status(self) -> str:
        """
        Pick status with weighted distribution (70% published, 30% draft).

        Returns:
            'published' or 'draft'
        """
        return random.choices(
            list(self.STATUS_WEIGHTS.keys()),
            weights=list(self.STATUS_WEIGHTS.values()),
            k=1,
        )[0]

    def generate_metrics(self) -> dict[str, Any]:
        """
        Generate realistic metrics for posts.

        Returns:
            dict with views, likes, bookmarks
        """
        return {
            "views": random.randint(0, 10000),
            "likes": random.randint(0, 1000),
            "bookmarks": random.randint(0, 500),
        }

    def generate_variants(
        self, seed_posts: list[dict[str, Any]], num_users: int
    ) -> list[dict[str, Any]]:
        """
        Generate all variants from seed posts.

        Args:
            seed_posts: List of seed post dicts
            num_users: Number of users for author assignment

        Returns:
            List of variant post dicts
        """
        variants = []
        variants_per_seed = self.scale_params["posts"] // len(seed_posts)

        logger.info(f"Generating {variants_per_seed} variants per seed post...")

        for seed_idx, seed_post in enumerate(seed_posts):
            for var_idx in range(variants_per_seed):
                variant = {
                    "pk_post": len(variants) + 1,  # Sequential ID
                    "id": str(uuid.uuid4()),
                    "title": self.mutate_title(seed_post["title"], var_idx),
                    "slug": f"{seed_post['original_slug']}-{var_idx}",
                    "content": seed_post["body"],
                    "excerpt": seed_post["excerpt"],
                    "fk_author": self.assign_author(var_idx, num_users),
                    "status": self.pick_status(),
                    "published_at": self.spread_publish_date(seed_idx, var_idx),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    **self.generate_metrics(),
                }
                variants.append(variant)

            if (seed_idx + 1) % 100 == 0:
                logger.info(
                    f"  Generated variants for {seed_idx + 1}/{len(seed_posts)} seed posts..."
                )

        self.stats["posts_generated"] = len(variants)
        self.stats["variants_per_seed"] = variants_per_seed
        logger.info(f"  ✓ Generated {len(variants):,} total variants")

        return variants

    def generate_comments(self, num_posts: int, num_users: int) -> list[dict[str, Any]]:
        """
        Generate comments for posts.

        Args:
            num_posts: Number of posts
            num_users: Number of users

        Returns:
            List of comment dicts
        """
        num_comments = self.scale_params["comments"]
        logger.info(f"Generating {num_comments:,} comments...")

        comments = []
        for i in range(num_comments):
            comment = {
                "pk_comment": i + 1,
                "id": str(uuid.uuid4()),
                "fk_post": random.randint(1, num_posts),
                "fk_author": random.randint(1, num_users),
                "content": self.fake.paragraph(nb_sentences=3),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 365)),
                "updated_at": datetime.now(),
            }
            comments.append(comment)

            if (i + 1) % 100000 == 0:
                logger.info(f"  Generated {i + 1:,}/{num_comments:,} comments...")

        self.stats["comments_generated"] = len(comments)
        logger.info(f"  ✓ Generated {len(comments):,} comments")

        return comments

    def generate(
        self, output_dir: Path, format: str = "both"
    ) -> tuple[bool, dict[str, Any]]:
        """
        Main generation workflow: discover seeds, generate variants, users, comments.

        Args:
            output_dir: Directory for output files
            format: Output format ('tsv', 'sql', 'both')

        Returns:
            (success: bool, stats: dict)
        """
        try:
            # Step 1: Discover seed posts
            seed_posts = self.discover_seed_posts()
            if not seed_posts:
                logger.error("No seed posts found")
                return (False, {})

            # Step 2: Generate users
            users = self.generate_users(self.scale_params["users"])
            self.stats["users_generated"] = len(users)

            # Step 3: Generate variants
            variants = self.generate_variants(seed_posts, len(users))

            # Step 4: Generate comments
            comments = self.generate_comments(len(variants), len(users))

            # Step 5: Output files
            self._write_output(output_dir, users, variants, comments, format)

            return (True, self.stats)

        except Exception as e:
            logger.error(f"Error during generation: {e}")
            import traceback

            traceback.print_exc()
            return (False, {})

    def _write_output(
        self,
        output_dir: Path,
        users: list[dict[str, Any]],
        posts: list[dict[str, Any]],
        comments: list[dict[str, Any]],
        format: str,
    ) -> None:
        """
        Write generated data to TSV/SQL files.

        Args:
            output_dir: Output directory
            users: List of user dicts
            posts: List of post dicts
            comments: List of comment dicts
            format: Output format ('tsv', 'sql', 'both')
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        if format in ["tsv", "both"]:
            self._write_tsv(output_dir, users, posts, comments)

        if format in ["sql", "both"]:
            self._write_sql(output_dir, users, posts, comments)

    def _write_tsv(
        self,
        output_dir: Path,
        users: list[dict[str, Any]],
        posts: list[dict[str, Any]],
        comments: list[dict[str, Any]],
    ) -> None:
        """Write TSV files for PostgreSQL COPY."""
        logger.info(f"Writing TSV files to {output_dir}...")

        # Users TSV
        users_file = output_dir / "blog_users.tsv"
        with open(users_file, "w", encoding="utf-8") as f:
            for user in users:
                row = [
                    str(user["pk_user"]),
                    user["id"],
                    user["email"],
                    user["username"],
                    user["first_name"],
                    user["last_name"],
                    user["bio"] if user["bio"] else "\\N",
                    "true" if user["is_active"] else "false",
                    user["created_at"].isoformat(),
                    user["updated_at"].isoformat(),
                ]
                f.write("\t".join([self._escape_tsv(str(v)) for v in row]) + "\n")
        logger.info(f"  ✓ {users_file}")

        # Posts TSV
        posts_file = output_dir / "blog_posts.tsv"
        with open(posts_file, "w", encoding="utf-8") as f:
            for post in posts:
                row = [
                    str(post["pk_post"]),
                    post["id"],
                    post["title"],
                    post["content"],
                    post["excerpt"] if post["excerpt"] else "\\N",
                    str(post["fk_author"]),
                    post["status"],
                    post["published_at"].isoformat(),
                    post["created_at"].isoformat(),
                    post["updated_at"].isoformat(),
                    str(post.get("views", 0)),
                    str(post.get("likes", 0)),
                    str(post.get("bookmarks", 0)),
                ]
                f.write("\t".join([self._escape_tsv(str(v)) for v in row]) + "\n")
        logger.info(f"  ✓ {posts_file}")

        # Comments TSV
        comments_file = output_dir / "blog_comments.tsv"
        with open(comments_file, "w", encoding="utf-8") as f:
            for comment in comments:
                row = [
                    str(comment["pk_comment"]),
                    comment["id"],
                    str(comment["fk_post"]),
                    str(comment["fk_author"]),
                    comment["content"],
                    comment["created_at"].isoformat(),
                    comment["updated_at"].isoformat(),
                ]
                f.write("\t".join([self._escape_tsv(str(v)) for v in row]) + "\n")
        logger.info(f"  ✓ {comments_file}")

    def _write_sql(
        self,
        output_dir: Path,
        users: list[dict[str, Any]],
        posts: list[dict[str, Any]],
        comments: list[dict[str, Any]],
    ) -> None:
        """Write SQL file for database loading."""
        logger.info(f"Writing SQL file to {output_dir}...")

        sql_file = output_dir / "data.sql"
        with open(sql_file, "w", encoding="utf-8") as f:
            f.write("-- Generated blog data\n\n")

            # Users
            f.write("INSERT INTO benchmark.tb_user VALUES\n")
            for i, user in enumerate(users):
                comma = "," if i < len(users) - 1 else ";"
                f.write(
                    f"  ({user['pk_user']}, '{user['id']}', '{user['email']}', "
                    f"'{user['username']}', '{user['first_name']}', '{user['last_name']}', "
                    f"'{user['bio'] or ''}', {str(user['is_active']).lower()}, "
                    f"'{user['created_at'].isoformat()}', '{user['updated_at'].isoformat()}'){comma}\n"
                )

            # Posts
            f.write("\nINSERT INTO benchmark.tb_post VALUES\n")
            for i, post in enumerate(posts):
                comma = "," if i < len(posts) - 1 else ";"
                # Simple SQL escaping (not production-grade)
                title = post["title"].replace("'", "''")
                content = post["content"].replace("'", "''")
                excerpt = (post["excerpt"] or "").replace("'", "''")
                f.write(
                    f"  ({post['pk_post']}, '{post['id']}', '{title}', "
                    f"'{content}', '{excerpt}', {post['fk_author']}, "
                    f"'{post['status']}', '{post['published_at'].isoformat()}', "
                    f"'{post['created_at'].isoformat()}', '{post['updated_at'].isoformat()}'){comma}\n"
                )

        logger.info(f"  ✓ {sql_file}")

    @staticmethod
    def _escape_tsv(value: str) -> str:
        """Escape special characters for PostgreSQL TSV COPY format."""
        value = value.replace("\\", "\\\\")
        value = value.replace("\t", "\\t")
        value = value.replace("\n", "\\n")
        value = value.replace("\r", "\\r")
        return value
