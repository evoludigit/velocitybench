#!/usr/bin/env python3
"""
Incremental database generator for FraiseQL benchmark suite.
Generates progressively larger datasets: XXS → XS → Small → Medium → Large → XLarge → XXLarge

Each size is generated independently with realistic vLLM content.
XXLarge is the concatenation of all previous datasets.

Dataset Sizes:
- XXS:    100 users,    1K posts,   5K comments (~5 min) - Proof of concept
- XS:     500 users,    5K posts,  25K comments (~15 min)
- Small:    1K users,   10K posts,  50K comments (~30 min)
- Medium:   5K users,   50K posts, 250K comments (~1.5 hours)
- Large:   10K users,  100K posts, 500K comments (~2 hours)
- XLarge:  50K users,  500K posts, 2.5M comments (~5 hours)
- XXLarge: 100K users, 1M+ posts, 5M+ comments (sum of all above)

Usage:
    python database/incremental-generator.py [vllm_endpoint]
"""

import random
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    from faker import Faker
except ImportError:
    print("Error: Faker not installed")
    print("Install with: pip install faker")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI client not installed")
    print("Install with: pip install openai")
    sys.exit(1)


class IncrementalGenerator:
    """Generate progressively larger datasets with vLLM content"""

    # Define dataset sizes
    SIZES = [
        ("xxs", 100, 1000, 5000),  # Proof of concept: ~5 min
        ("xs", 500, 5000, 25000),  # Quick test: ~15 min
        ("small", 1000, 10000, 50000),  # ~30 min
        ("medium", 5000, 50000, 250000),  # ~1.5 hours
        ("large", 10000, 100000, 500000),  # ~2 hours
        ("xlarge", 50000, 500000, 2500000),  # ~5 hours
    ]

    def __init__(self, vllm_endpoint: str = "http://localhost:8000/v1"):
        self.vllm_endpoint = vllm_endpoint
        self.vllm_available = False
        self.model_name = None
        self.client = None

        # Initialize Faker with reproducible seed
        self.fake = Faker()
        Faker.seed(42)
        random.seed(42)

        # Try to initialize vLLM client
        self._init_vllm()

    def _init_vllm(self):
        """Initialize vLLM connection"""
        try:
            self.client = OpenAI(api_key="dummy", base_url=self.vllm_endpoint)

            # Fetch available models
            import requests

            models_response = requests.get(
                f"{self.vllm_endpoint.replace('/v1', '')}/v1/models"
            )
            if models_response.status_code == 200:
                models = models_response.json().get("data", [])
                if models:
                    self.model_name = models[0]["id"]
                else:
                    self.model_name = "/data/models/fp16/Ministral-3-8B-Instruct-2512"
            else:
                self.model_name = "/data/models/fp16/Ministral-3-8B-Instruct-2512"

            # Test connection
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
                temperature=0.1,
            )
            self.vllm_available = True
            print(f"✓ vLLM available: {self.model_name}")
        except Exception as e:
            print(f"⚠ vLLM not available: {e}")
            self.vllm_available = False

    def generate_size(
        self, name: str, user_count: int, post_count: int, comment_count: int
    ):
        """Generate a single dataset size"""
        db_path = f"datasets/fraiseql_{name}.db"

        print("\n" + "=" * 70)
        print(
            f"{name.upper()}: {user_count:,} users | {post_count:,} posts | {comment_count:,} comments"
        )
        print("=" * 70)

        start = time.time()

        # Clean start
        if Path(db_path).exists():
            Path(db_path).unlink()

        # Initialize database
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode = MEMORY")
        conn.execute("PRAGMA synchronous = OFF")

        # Create schema
        schema_path = Path("database/schema-sqlite-xs.sql")
        with open(schema_path) as f:
            conn.executescript(f.read())
        conn.commit()
        print("✓ Schema created")

        # Generate users
        user_ids = self._generate_users(conn, user_count)

        # Generate posts
        post_ids = self._generate_posts(conn, post_count, user_ids)

        # Generate comments
        self._generate_comments(conn, comment_count, post_ids, user_ids)

        # Generate relationships
        self._generate_relationships(conn, user_ids, post_ids)

        # Optimize and close
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        conn.close()

        # Report
        elapsed = time.time() - start
        size_mb = Path(db_path).stat().st_size / (1024 * 1024)
        size_str = f"{size_mb:.1f}MB" if size_mb < 1024 else f"{size_mb / 1024:.1f}GB"

        print(
            f"✓ {name.upper()} complete: {size_str} in {elapsed / 60:.1f} minutes ({elapsed:.0f}s)"
        )
        return elapsed

    def _generate_users(self, conn, count: int):
        """Generate users"""
        print(f"Generating {count:,} users...", flush=True)
        user_ids = []
        users = []

        for i in range(count):
            user_ids.append(i + 1)
            users.append(
                (
                    i + 1,
                    str(uuid.uuid4()),
                    f"user_{i + 1:06d}",
                    self.fake.unique.email(),
                    f"user_{i + 1}",
                    self.fake.name(),
                    self.fake.text(max_nb_chars=200) if random.random() > 0.3 else None,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                )
            )

            if (i + 1) % 10000 == 0 or i + 1 == count:
                conn.executemany(
                    "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", users
                )
                conn.commit()
                print(f"  ✓ {i + 1:,} users", flush=True)
                users = []

        return user_ids

    def _generate_posts(self, conn, count: int, user_ids: list):
        """Generate posts with vLLM content"""
        print(f"Generating {count:,} posts...")

        # Get titles
        print("  Generating titles from vLLM...", flush=True)
        titles = self._vllm_batch_generate(
            count,
            500,
            "Generate {n} unique, realistic blog post titles.",
            lambda batch_count: f"""Generate {batch_count} unique, realistic blog post titles.

Requirements:
- 5-12 words each
- Clickworthy but informative
- Varied topics (technology, culture, lifestyle, productivity)
- Professional tone

Format: One title per line, no numbering""",
            split_char="\n",
        )

        # Get content
        print("  Generating content from vLLM...", flush=True)
        contents = self._vllm_batch_generate(
            count,
            200,
            "Generate {n} short blog post bodies.",
            lambda batch_count: f"""Generate {batch_count} short blog post bodies.

Requirements:
- 300-800 words each
- Structured with 2-3 paragraphs
- Professional, informative tone
- Diverse topics

Separate each post with "---" on its own line.""",
            split_char="---",
        )

        # Insert posts
        print("  Inserting posts...", flush=True)
        post_ids = []
        posts = []

        for i in range(count):
            post_ids.append(i + 1)
            posts.append(
                (
                    i + 1,
                    str(uuid.uuid4()),
                    f"post_{i + 1:07d}",
                    titles[i] if i < len(titles) else f"Post {i + 1}",
                    contents[i] if i < len(contents) else f"Content for post {i + 1}",
                    random.choice(user_ids),
                    1 if random.random() > 0.2 else 0,
                    (
                        datetime.now() - timedelta(days=random.randint(0, 365))
                    ).isoformat(),
                    datetime.now().isoformat(),
                )
            )

            if (i + 1) % 50000 == 0 or i + 1 == count:
                conn.executemany(
                    "INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", posts
                )
                conn.commit()
                print(f"  ✓ {i + 1:,} posts", flush=True)
                posts = []

        return post_ids

    def _generate_comments(self, conn, count: int, post_ids: list, user_ids: list):
        """Generate comments with vLLM content"""
        print(f"Generating {count:,} comments...")

        # Get content
        print("  Generating content from vLLM...", flush=True)
        contents = self._vllm_batch_generate(
            count,
            100,
            "Generate {n} realistic blog comments.",
            lambda batch_count: f"""Generate {batch_count} realistic blog comments.

Requirements:
- 20-100 words each
- Sound like real user comments
- Can be positive, critical, or questioning
- Conversational tone
- Varied perspectives

Format: One comment per line""",
            split_char="\n",
        )

        # Insert comments
        print("  Inserting comments...", flush=True)
        comments = []

        for i in range(count):
            comments.append(
                (
                    i + 1,
                    str(uuid.uuid4()),
                    None,
                    contents[i] if i < len(contents) else f"Comment {i + 1}",
                    random.choice(post_ids),
                    random.choice(user_ids),
                    (
                        datetime.now() - timedelta(days=random.randint(0, 180))
                    ).isoformat(),
                    datetime.now().isoformat(),
                )
            )

            if (i + 1) % 100000 == 0 or i + 1 == count:
                conn.executemany(
                    "INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)", comments
                )
                conn.commit()
                print(f"  ✓ {i + 1:,} comments", flush=True)
                comments = []

    def _generate_relationships(self, conn, user_ids: list, post_ids: list):
        """Generate follows and likes"""
        print("Generating relationships...")

        # Scale relationships based on data size
        follow_count = max(int(len(user_ids) * 0.25), 1)
        like_count = max(int(len(post_ids) * 0.2), 1)

        follows = []
        for _ in range(follow_count):
            follower = random.choice(user_ids)
            following = random.choice(user_ids)
            if follower != following:
                follows.append((follower, following, datetime.now().isoformat()))

        conn.executemany("INSERT OR IGNORE INTO user_follows VALUES (?, ?, ?)", follows)

        likes = []
        for _ in range(like_count):
            likes.append(
                (
                    random.choice(user_ids),
                    random.choice(post_ids),
                    random.choice(["like", "love", "laugh", "angry", "sad"]),
                    datetime.now().isoformat(),
                )
            )

        conn.executemany("INSERT OR IGNORE INTO post_likes VALUES (?, ?, ?, ?)", likes)
        conn.commit()

        print(f"✓ {len(follows):,} follows, {len(likes):,} likes")

    def _vllm_batch_generate(
        self,
        total_count: int,
        batch_size: int,
        title: str,
        prompt_fn,
        split_char: str = "\n",
    ):
        """Generate content from vLLM in batches"""
        results = []

        if not self.vllm_available:
            return [f"Default {title} {i + 1}" for i in range(total_count)]

        for batch_start in range(0, total_count, batch_size):
            batch_count = min(batch_size, total_count - batch_start)

            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt_fn(batch_count)}],
                    max_tokens=batch_count * (20 if "title" in title.lower() else 100),
                    temperature=0.7,
                    top_p=0.95,
                )

                items = response.choices[0].message.content.split(split_char)
                results.extend(
                    [item.strip() for item in items if item.strip()][:batch_count]
                )

                progress = min(batch_start + batch_count, total_count)
                if progress % 50000 == 0 or progress == total_count:
                    print(f"    {progress:,}/{total_count:,}", flush=True)
            except Exception as e:
                print(f"  ⚠ vLLM error: {e}. Using fallback.")
                results.extend([f"Default {i + 1}" for i in range(batch_count)])

        return results[:total_count]

    def run_all(self):
        """Generate all sizes incrementally"""
        print("\n" + "=" * 70)
        print("INCREMENTAL DATABASE GENERATION")
        print("XS → Small → Medium → Large → XLarge → XXLarge")
        print("=" * 70)

        times = {}
        total_start = time.time()

        for name, users, posts, comments in self.SIZES:
            try:
                elapsed = self.generate_size(name, users, posts, comments)
                times[name] = elapsed
            except Exception as e:
                print(f"❌ {name.upper()} FAILED: {e}")
                import traceback

                traceback.print_exc()
                return False

        # Print summary
        total_elapsed = time.time() - total_start
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        for name, elapsed in times.items():
            print(f"  {name:10} {elapsed / 60:6.1f} min ({elapsed:7.0f}s)")
        print(
            f"  {'TOTAL':10} {total_elapsed / 3600:6.1f} hours ({total_elapsed:.0f}s)"
        )
        print("=" * 70)

        return True


if __name__ == "__main__":
    vllm_endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/v1"

    Path("datasets").mkdir(exist_ok=True)

    print(f"vLLM endpoint: {vllm_endpoint}\n")

    generator = IncrementalGenerator(vllm_endpoint)
    success = generator.run_all()

    sys.exit(0 if success else 1)
