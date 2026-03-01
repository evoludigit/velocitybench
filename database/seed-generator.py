#!/usr/bin/env python3
"""
Configurable benchmark data generator for FraiseQL performance assessment.
Generates realistic social media data at scale with reproducible seeding.

Usage:
    python seed-generator.py --preset large --db postgresql://user:pass@localhost/dbname
"""

import argparse
import random
import sys
import uuid
from datetime import datetime, timedelta

try:
    import psycopg
    from faker import Faker
except ImportError:
    print("Error: Required packages not installed")
    print("Install with: pip install faker psycopg[binary]")
    sys.exit(1)

# Configuration presets
PRESETS = {
    "small": {
        "users": 100,
        "posts": 500,
        "comments": 2000,
        "follows": 200,
        "likes": 1000,
        "description": "Small dataset for development (100 users, 500 posts)",
    },
    "medium": {
        "users": 1000,
        "posts": 5000,
        "comments": 20000,
        "follows": 5000,
        "likes": 10000,
        "description": "Medium dataset (1K users, 5K posts)",
    },
    "large": {
        "users": 10000,
        "posts": 100000,
        "comments": 500000,
        "follows": 50000,
        "likes": 200000,
        "description": "Large dataset (10K users, 100K posts)",
    },
    "xlarge": {
        "users": 50000,
        "posts": 500000,
        "comments": 2000000,
        "follows": 200000,
        "likes": 1000000,
        "description": "Extra large dataset (50K users, 500K posts)",
    },
}


class DataGenerator:
    """Generate realistic benchmark data for FraiseQL performance testing."""

    def __init__(self, conn_string: str, seed: int = 42):
        """Initialize database connection and random seed."""
        self.conn = psycopg.connect(conn_string)
        self.seed = seed

        # Initialize Faker with reproducible seed
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

        self.user_ids: list[uuid.UUID] = []
        self.post_ids: list[uuid.UUID] = []

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def generate_users(self, count: int, batch_size: int = 1000):
        """Generate users with varied profile data."""
        print(f"Generating {count} users...")

        with self.conn.cursor() as cur:
            for batch_start in range(0, count, batch_size):
                batch_end = min(batch_start + batch_size, count)

                # Build batch insert with COPY
                users_data = []

                for i in range(batch_start, batch_end):
                    # First 100 users get predictable UUIDs for testing
                    if i < 100:
                        user_id = uuid.UUID(f"{i + 1:08d}-1111-1111-1111-111111111111")
                        identifier = f"user_{i + 1:05d}"
                    else:
                        user_id = uuid.uuid4()
                        identifier = f"user_{self.fake.user_name()[:20]}"

                    self.user_ids.append(user_id)

                    users_data.append(
                        {
                            "id": user_id,
                            "identifier": identifier,
                            "email": self.fake.unique.email(),
                            "username": f"user_{i}"
                            if i < 100
                            else self.fake.unique.user_name(),
                            "full_name": self.fake.name(),
                            "bio": self.fake.text(max_nb_chars=500)
                            if random.random() > 0.3
                            else None,
                        }
                    )

                # Use COPY for better performance
                with cur.copy(
                    "COPY benchmark.tb_user (id, identifier, email, username, full_name, bio) FROM STDIN"
                ) as copy:
                    for user in users_data:
                        copy.write_row(
                            (
                                user["id"],
                                user["identifier"],
                                user["email"],
                                user["username"],
                                user["full_name"],
                                user["bio"],
                            )
                        )

                self.conn.commit()
                print(f"  Users: {batch_end}/{count}")

    def generate_posts(self, count: int, batch_size: int = 1000):
        """Generate posts with realistic content."""
        print(f"Generating {count} posts...")

        statuses = ["published"] * 80 + ["draft"] * 15 + ["archived"] * 5

        with self.conn.cursor() as cur:
            for batch_start in range(0, count, batch_size):
                batch_end = min(batch_start + batch_size, count)

                posts_data = []

                for i in range(batch_start, batch_end):
                    # First 100 posts get predictable UUIDs
                    if i < 100:
                        post_id = uuid.UUID(f"{i + 1:08d}-2222-2222-2222-222222222222")
                        identifier = f"post_{i + 1:05d}"
                    else:
                        post_id = uuid.uuid4()
                        identifier = f"post_{self.fake.slug()[:30]}"

                    self.post_ids.append(post_id)

                    status = random.choice(statuses)
                    created_at = datetime.now() - timedelta(days=random.randint(0, 365))
                    published = status == "published"

                    posts_data.append(
                        {
                            "id": post_id,
                            "identifier": identifier,
                            "title": self.fake.sentence(nb_words=random.randint(4, 12)),
                            "content": self.fake.text(
                                max_nb_chars=random.randint(200, 5000)
                            ),
                            "fk_author": (i % len(self.user_ids)) + 1,  # pk_user from 1
                            "published": published,
                            "created_at": created_at,
                        }
                    )

                # Use COPY for posts
                with cur.copy(
                    "COPY benchmark.tb_post (id, identifier, title, content, fk_author, published, created_at) FROM STDIN"
                ) as copy:
                    for post in posts_data:
                        copy.write_row(
                            (
                                post["id"],
                                post["identifier"],
                                post["title"],
                                post["content"],
                                post["fk_author"],
                                post["published"],
                                post["created_at"],
                            )
                        )

                self.conn.commit()
                print(f"  Posts: {batch_end}/{count}")

    def generate_comments(self, count: int, batch_size: int = 5000):
        """Generate comments with threading."""
        print(f"Generating {count} comments...")

        comment_ids = []

        with self.conn.cursor() as cur:
            for batch_start in range(0, count, batch_size):
                batch_end = min(batch_start + batch_size, count)

                comments_data = []

                for i in range(batch_start, batch_end):
                    # First 100 comments get predictable UUIDs
                    if i < 100:
                        comment_id = uuid.UUID(
                            f"{i + 1:08d}-3333-3333-3333-333333333333"
                        )
                        identifier = f"comment_{i + 1:05d}"
                    else:
                        comment_id = uuid.uuid4()
                        identifier = None

                    comments_data.append(
                        {
                            "id": comment_id,
                            "identifier": identifier,
                            "content": self.fake.text(
                                max_nb_chars=random.randint(50, 1000)
                            ),
                            "fk_post": (i % len(self.post_ids)) + 1,  # pk_post from 1
                            "fk_author": random.randint(1, len(self.user_ids)),
                            "created_at": datetime.now()
                            - timedelta(days=random.randint(0, 180)),
                        }
                    )

                    comment_ids.append(comment_id)

                # Use COPY for comments
                with cur.copy(
                    "COPY benchmark.tb_comment (id, identifier, content, fk_post, fk_author, created_at) FROM STDIN"
                ) as copy:
                    for comment in comments_data:
                        copy.write_row(
                            (
                                comment["id"],
                                comment["identifier"],
                                comment["content"],
                                comment["fk_post"],
                                comment["fk_author"],
                                comment["created_at"],
                            )
                        )

                self.conn.commit()
                print(f"  Comments: {batch_end}/{count}")

    def generate_follows(self, count: int, batch_size: int = 5000):
        """Generate follow relationships (social graph)."""
        print(f"Generating {count} follow relationships...")

        # Generate unique follow pairs
        follows = set()
        attempts = 0
        max_attempts = count * 3

        while len(follows) < count and attempts < max_attempts:
            follower_pk = random.randint(1, len(self.user_ids))
            following_pk = random.randint(1, len(self.user_ids))

            if follower_pk != following_pk:
                follows.add((follower_pk, following_pk))

            attempts += 1

        follows_list = list(follows)

        with self.conn.cursor() as cur:
            for batch_start in range(0, len(follows_list), batch_size):
                batch = follows_list[batch_start : batch_start + batch_size]

                with cur.copy(
                    "COPY benchmark.tb_user_follows (fk_follower, fk_following) FROM STDIN"
                ) as copy:
                    for follower_pk, following_pk in batch:
                        copy.write_row((follower_pk, following_pk))

                self.conn.commit()
                print(
                    f"  Follows: {min(batch_start + batch_size, len(follows_list))}/{len(follows_list)}"
                )

    def generate_likes(self, count: int, batch_size: int = 5000):
        """Generate post likes/reactions."""
        print(f"Generating {count} post likes...")

        likes = set()
        reaction_types = ["like"] * 70 + ["love"] * 20 + ["laugh"] * 8 + ["angry"] * 2

        while len(likes) < count:
            user_pk = random.randint(1, len(self.user_ids))
            post_pk = random.randint(1, len(self.post_ids))

            if (user_pk, post_pk) not in likes:
                likes.add((user_pk, post_pk))

        likes_list = [(u, p, random.choice(reaction_types)) for u, p in likes]

        with self.conn.cursor() as cur:
            for batch_start in range(0, len(likes_list), batch_size):
                batch = likes_list[batch_start : batch_start + batch_size]

                with cur.copy(
                    "COPY benchmark.tb_post_like (fk_user, fk_post, reaction_type) FROM STDIN"
                ) as copy:
                    for user_pk, post_pk, reaction_type in batch:
                        copy.write_row((user_pk, post_pk, reaction_type))

                self.conn.commit()
                print(
                    f"  Likes: {min(batch_start + batch_size, len(likes_list))}/{len(likes_list)}"
                )

    def sync_tv_tables(self):
        """Sync all data to query side (tv_* tables)."""
        print("Syncing to query-side tables (tv_*)...")

        with self.conn.cursor() as cur:
            # Sync all users
            cur.execute("SELECT COUNT(*) FROM benchmark.tb_user")
            user_count = cur.fetchone()[0]
            print(f"  Syncing {user_count} users to tv_user...")

            cur.execute("""
                SELECT benchmark.fn_sync_tv_user(id)
                FROM benchmark.tb_user
            """)
            self.conn.commit()

            # Sync all posts
            cur.execute("SELECT COUNT(*) FROM benchmark.tb_post")
            post_count = cur.fetchone()[0]
            print(f"  Syncing {post_count} posts to tv_post...")

            cur.execute("""
                SELECT benchmark.fn_sync_tv_post(id)
                FROM benchmark.tb_post
            """)
            self.conn.commit()

            # Sync all comments
            cur.execute("SELECT COUNT(*) FROM benchmark.tb_comment")
            comment_count = cur.fetchone()[0]
            print(f"  Syncing {comment_count} comments to tv_comment...")

            cur.execute("""
                SELECT benchmark.fn_sync_tv_comment(id)
                FROM benchmark.tb_comment
            """)
            self.conn.commit()

    def analyze_tables(self):
        """Analyze tables for query planner."""
        print("Analyzing tables for query planner...")

        with self.conn.cursor() as cur:
            cur.execute("ANALYZE benchmark.tb_user")
            cur.execute("ANALYZE benchmark.tb_post")
            cur.execute("ANALYZE benchmark.tb_comment")
            cur.execute("ANALYZE benchmark.tv_user")
            cur.execute("ANALYZE benchmark.tv_post")
            cur.execute("ANALYZE benchmark.tv_comment")
            self.conn.commit()

        print("  Analysis complete")

    def run(self, config: dict[str, int]):
        """Run full data generation."""
        print(f"\n{'=' * 60}")
        print("Starting data generation")
        print(f"{'=' * 60}")
        print(f"Seed: {self.seed}")
        print(f"Config: {config}\n")

        try:
            self.generate_users(config["users"])
            self.generate_posts(config["posts"])
            self.generate_comments(config["comments"])
            self.generate_follows(config["follows"])
            self.generate_likes(config["likes"])

            self.sync_tv_tables()
            self.analyze_tables()

            print(f"\n{'=' * 60}")
            print("Data generation complete!")
            print(f"{'=' * 60}\n")

        except Exception as e:
            print(f"\nError during data generation: {e}")
            self.conn.rollback()
            raise
        finally:
            self.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generate benchmark data for FraiseQL performance testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seed-generator.py --preset large
  python seed-generator.py --preset large --db postgresql://user:pass@localhost:5432/velocitybench_benchmark
  python seed-generator.py --preset xlarge --seed 12345
        """,
    )

    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        default="small",
        help="Data volume preset (default: small)",
    )

    parser.add_argument(
        "--db",
        default=None,
        help="Database connection string (required if DB_PASSWORD env var not set)",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible data (default: 42)",
    )

    parser.add_argument("--users", type=int, help="Override number of users")

    parser.add_argument("--posts", type=int, help="Override number of posts")

    parser.add_argument("--comments", type=int, help="Override number of comments")

    args = parser.parse_args()

    # Validate database connection string
    if not args.db:
        raise ValueError(
            "Database connection string is required. "
            "Use --db 'postgresql://user:password@host:port/db' "
            "or set DB_PASSWORD environment variable."
        )

    # Get base config from preset
    config = PRESETS[args.preset].copy()

    # Remove description and apply overrides
    config.pop("description", None)
    if args.users:
        config["users"] = args.users
    if args.posts:
        config["posts"] = args.posts
    if args.comments:
        config["comments"] = args.comments

    # Generate data
    generator = DataGenerator(args.db, seed=args.seed)
    generator.run(config)


if __name__ == "__main__":
    main()
