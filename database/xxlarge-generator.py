#!/usr/bin/env python3
"""
XXLARGE database generator for comprehensive benchmark suite.
Generates: 100K users, 1M posts, 5M comments in ~4-5 hours with vLLM.

This is the master dataset from which all other sizes are sampled.

Usage:
    python database/xxlarge-generator.py [output_db_path] [vllm_endpoint]
"""

import sqlite3
import uuid
import random
import time
import sys
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


class XXLargeGenerator:
    """Generate XXLARGE test dataset with vLLM content"""

    def __init__(self, db_path: str, vllm_endpoint: str = "http://localhost:8000/v1"):
        self.db_path = db_path
        self.vllm_endpoint = vllm_endpoint
        self.vllm_available = False

        # Initialize database
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode = MEMORY")
        self.conn.execute("PRAGMA synchronous = OFF")

        # Initialize Faker with reproducible seed
        self.fake = Faker()
        Faker.seed(42)
        random.seed(42)

        # Try to initialize vLLM client
        try:
            self.client = OpenAI(api_key="dummy", base_url=vllm_endpoint)

            # Fetch available models and use the first one (keep full path)
            import requests
            models_response = requests.get(f"{vllm_endpoint.replace('/v1', '')}/v1/models")
            if models_response.status_code == 200:
                models = models_response.json().get("data", [])
                if models:
                    # Use full model ID (which may be a path like /data/models/fp16/ModelName)
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
                temperature=0.1
            )
            self.vllm_available = True
            print("✓ vLLM available at", vllm_endpoint)
            print(f"  Model: {self.model_name}")
        except Exception as e:
            print(f"⚠ vLLM not available: {e}")
            print("  Will use fallback content generation")
            self.vllm_available = False
            self.model_name = None

        # Store IDs for relationships
        self.user_ids = []
        self.post_ids = []

    def create_schema(self):
        """Create SQLite schema"""
        print("Creating schema...", flush=True)
        schema_path = Path("database/schema-sqlite-xs.sql")
        if not schema_path.exists():
            print(f"Error: {schema_path} not found")
            sys.exit(1)

        with open(schema_path) as f:
            self.conn.executescript(f.read())
        self.conn.commit()
        print("✓ Schema created")

    def generate_users(self, count: int = 100000):
        """Generate users with Faker"""
        print(f"Generating {count:,} users...", flush=True)

        users = []
        for i in range(count):
            user_id = str(uuid.uuid4())
            self.user_ids.append(i + 1)  # Store pk_user (1-indexed)

            users.append((
                i + 1,  # pk_user
                user_id,  # id
                f"user_{i+1:06d}",  # identifier
                self.fake.unique.email(),  # email
                f"user_{i+1}",  # username
                self.fake.name(),  # full_name
                self.fake.text(max_nb_chars=200) if random.random() > 0.3 else None,  # bio
                datetime.now().isoformat(),  # created_at
                datetime.now().isoformat(),  # updated_at
            ))

            # Batch insert every 10K users
            if (i + 1) % 10000 == 0:
                cursor = self.conn.cursor()
                cursor.executemany(
                    """INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    users
                )
                self.conn.commit()
                print(f"  ✓ {i+1:,} users created", flush=True)
                users = []

        # Insert remaining
        if users:
            cursor = self.conn.cursor()
            cursor.executemany(
                """INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                users
            )
            self.conn.commit()
            print(f"✓ {count:,} users created")

    def generate_posts(self, count: int = 1000000):
        """Generate posts: structure with Faker, content with vLLM"""
        print(f"Generating {count:,} posts...")

        # Step 1: Get vLLM titles in batches
        print("  Generating titles from vLLM...", flush=True)
        titles = self._vllm_batch_titles(count, batch_size=100)

        # Step 2: Get vLLM content in batches
        print("  Generating content from vLLM...", flush=True)
        contents = self._vllm_batch_content(count, batch_size=50)

        # Step 3: Insert posts in batches
        print("  Inserting posts...", flush=True)
        posts = []
        for i in range(count):
            post_id = str(uuid.uuid4())
            self.post_ids.append(i + 1)

            posts.append((
                i + 1,  # pk_post
                post_id,  # id
                f"post_{i+1:07d}",  # identifier
                titles[i] if i < len(titles) else f"Post {i+1}",  # title
                contents[i] if i < len(contents) else f"Content for post {i+1}",  # content
                random.choice(self.user_ids),  # fk_author
                1 if random.random() > 0.2 else 0,  # published
                (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),  # created_at
                datetime.now().isoformat(),  # updated_at
            ))

            # Batch insert every 50K posts
            if (i + 1) % 50000 == 0:
                cursor = self.conn.cursor()
                cursor.executemany(
                    """INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    posts
                )
                self.conn.commit()
                print(f"  ✓ {i+1:,} posts created", flush=True)
                posts = []

        # Insert remaining
        if posts:
            cursor = self.conn.cursor()
            cursor.executemany(
                """INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                posts
            )
            self.conn.commit()
            print(f"✓ {count:,} posts created")

    def generate_comments(self, count: int = 5000000):
        """Generate comments: structure with Faker, content with vLLM"""
        print(f"Generating {count:,} comments...")

        # Step 1: Get vLLM content
        print("  Generating comment content from vLLM...", flush=True)
        contents = self._vllm_batch_comments(count, batch_size=50)

        # Step 2: Insert comments in batches
        print("  Inserting comments...", flush=True)
        comments = []
        for i in range(count):
            comment_id = str(uuid.uuid4())

            comments.append((
                i + 1,  # pk_comment
                comment_id,  # id
                None,  # identifier
                contents[i] if i < len(contents) else f"Comment {i+1}",  # content
                random.choice(self.post_ids),  # fk_post
                random.choice(self.user_ids),  # fk_author
                (datetime.now() - timedelta(days=random.randint(0, 180))).isoformat(),  # created_at
                datetime.now().isoformat(),  # updated_at
            ))

            # Batch insert every 100K comments
            if (i + 1) % 100000 == 0:
                cursor = self.conn.cursor()
                cursor.executemany(
                    """INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    comments
                )
                self.conn.commit()
                print(f"  ✓ {i+1:,} comments created", flush=True)
                comments = []

        # Insert remaining
        if comments:
            cursor = self.conn.cursor()
            cursor.executemany(
                """INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                comments
            )
            self.conn.commit()
            print(f"✓ {count:,} comments created")

    def generate_relationships(self):
        """Generate follows and likes"""
        print("Generating relationships...")

        # Follows: 50K (0.5 per user average)
        follows = []
        for _ in range(50000):
            follower = random.choice(self.user_ids)
            following = random.choice(self.user_ids)

            if follower != following:
                follows.append((
                    follower,
                    following,
                    datetime.now().isoformat()
                ))

        cursor = self.conn.cursor()
        cursor.executemany(
            """INSERT OR IGNORE INTO user_follows VALUES (?, ?, ?)""",
            follows
        )

        # Likes: 200K (0.2 per post average)
        likes = []
        for _ in range(200000):
            likes.append((
                random.choice(self.user_ids),
                random.choice(self.post_ids),
                random.choice(['like', 'love', 'laugh', 'angry', 'sad']),
                datetime.now().isoformat()
            ))

        cursor.executemany(
            """INSERT OR IGNORE INTO post_likes VALUES (?, ?, ?, ?)""",
            likes
        )

        self.conn.commit()
        print(f"✓ {len(follows):,} follows, {len(likes):,} likes created")

    def _vllm_batch_titles(self, count: int, batch_size: int = 100):
        """Generate blog post titles from vLLM"""
        results = []

        if not self.vllm_available:
            return [f"Blog Post {i+1}" for i in range(count)]

        for batch_start in range(0, count, batch_size):
            batch_count = min(batch_size, count - batch_start)

            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{
                        "role": "user",
                        "content": f"""Generate {batch_count} unique, realistic blog post titles.

Requirements:
- 5-12 words each
- Clickworthy but informative
- Varied topics (technology, culture, lifestyle, productivity)
- Professional tone

Format: One title per line, no numbering"""
                    }],
                    max_tokens=batch_count * 20,
                    temperature=0.7,
                    top_p=0.95
                )

                titles = response.choices[0].message.content.strip().split('\n')
                results.extend([t.strip() for t in titles if t.strip()][:batch_count])

                progress = min(batch_start + batch_count, count)
                if progress % 50000 == 0 or progress == count:
                    print(f"    Titles: {progress:,}/{count:,}", flush=True)
            except Exception as e:
                print(f"  ⚠ vLLM error: {e}. Using fallback titles.")
                results.extend([f"Blog Post {i}" for i in range(batch_count)])

        return results[:count]

    def _vllm_batch_content(self, count: int, batch_size: int = 50):
        """Generate blog post bodies from vLLM"""
        results = []

        if not self.vllm_available:
            return [f"Content for post. " * 50 for i in range(count)]

        for batch_start in range(0, count, batch_size):
            batch_count = min(batch_size, count - batch_start)

            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{
                        "role": "user",
                        "content": f"""Generate {batch_count} short blog post bodies.

Requirements:
- 300-800 words each
- Structured with 2-3 paragraphs
- Professional, informative tone
- Diverse topics

Separate each post with "---" on its own line."""
                    }],
                    max_tokens=batch_count * 300,
                    temperature=0.7,
                    top_p=0.95
                )

                posts = response.choices[0].message.content.split('---')
                results.extend([p.strip() for p in posts if p.strip()][:batch_count])

                progress = min(batch_start + batch_count, count)
                if progress % 100000 == 0 or progress == count:
                    print(f"    Content: {progress:,}/{count:,}", flush=True)
            except Exception as e:
                print(f"  ⚠ vLLM error: {e}. Using fallback content.")
                results.extend([f"Content for post {i}. " * 50 for i in range(batch_count)])

        return results[:count]

    def _vllm_batch_comments(self, count: int, batch_size: int = 50):
        """Generate comments from vLLM"""
        results = []

        if not self.vllm_available:
            return [f"Great post! Thanks for sharing." for i in range(count)]

        for batch_start in range(0, count, batch_size):
            batch_count = min(batch_size, count - batch_start)

            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{
                        "role": "user",
                        "content": f"""Generate {batch_count} realistic blog comments.

Requirements:
- 20-100 words each
- Sound like real user comments
- Can be positive, critical, or questioning
- Conversational tone
- Varied perspectives

Format: One comment per line"""
                    }],
                    max_tokens=batch_count * 100,
                    temperature=0.7,
                    top_p=0.95
                )

                comments = response.choices[0].message.content.strip().split('\n')
                results.extend([c.strip() for c in comments if c.strip()][:batch_count])

                progress = min(batch_start + batch_count, count)
                if progress % 250000 == 0 or progress == count:
                    print(f"    Comments: {progress:,}/{count:,}", flush=True)
            except Exception as e:
                print(f"  ⚠ vLLM error: {e}. Using fallback comments.")
                results.extend([f"Great comment #{i}!" for i in range(batch_count)])

        return results[:count]

    def finalize(self):
        """Optimize database"""
        print("Optimizing database...", flush=True)
        self.conn.execute("VACUUM")
        self.conn.execute("ANALYZE")
        self.conn.close()

        # Show file size
        size_gb = Path(self.db_path).stat().st_size / (1024 * 1024 * 1024)
        print(f"✓ Database optimized: {size_gb:.2f} GB")

    def run(self):
        """Run full generation pipeline"""
        start = time.time()
        print("=" * 70)
        print("XXLARGE DATABASE GENERATION")
        print("100K users | 1M posts | 5M comments")
        print("=" * 70)

        try:
            self.create_schema()
            self.generate_users(100000)
            self.generate_posts(1000000)
            self.generate_comments(5000000)
            self.generate_relationships()
            self.finalize()

            elapsed = time.time() - start
            hours = elapsed / 3600
            print("=" * 70)
            print(f"✅ XXLARGE generation complete in {hours:.1f} hours ({elapsed:.0f}s)")
            print("=" * 70)
            return True
        except Exception as e:
            print(f"\n❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "datasets/fraiseql_xxlarge.db"
    vllm_endpoint = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000/v1"

    # Create datasets directory
    Path("datasets").mkdir(exist_ok=True)

    print(f"Target database: {db_path}")
    print(f"vLLM endpoint: {vllm_endpoint}\n")

    generator = XXLargeGenerator(db_path, vllm_endpoint)
    success = generator.run()

    sys.exit(0 if success else 1)
