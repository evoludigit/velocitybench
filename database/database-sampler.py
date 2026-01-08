#!/usr/bin/env python3
"""
Database sampler - creates variations from XXLARGE master database.

Samples N% of users and their associated posts/comments to create
smaller benchmark databases with consistent data characteristics.

Usage:
    python database/database-sampler.py <xxlarge_db> <output_db> <sample_percent>

Examples:
    python database/database-sampler.py fraiseql_xxlarge.db fraiseql_xs.db 0.5
    python database/database-sampler.py fraiseql_xxlarge.db fraiseql_small.db 1.0
    python database/database-sampler.py fraiseql_xxlarge.db fraiseql_medium.db 5.0
    python database/database-sampler.py fraiseql_xxlarge.db fraiseql_large.db 10.0
    python database/database-sampler.py fraiseql_xxlarge.db fraiseql_xlarge.db 50.0
"""

import sqlite3
import sys
import time
import random
from pathlib import Path


class DatabaseSampler:
    """Sample users and their content from a master database"""

    def __init__(self, source_db: str, output_db: str, sample_percent: float):
        self.source_db = source_db
        self.output_db = output_db
        self.sample_percent = sample_percent

        if not Path(source_db).exists():
            print(f"❌ Source database not found: {source_db}")
            sys.exit(1)

        # Seed for reproducibility
        random.seed(42)

    def run(self):
        """Execute full sampling pipeline"""
        start = time.time()
        print("=" * 70)
        print(f"DATABASE SAMPLING: {self.sample_percent}% from {Path(self.source_db).name}")
        print("=" * 70)

        try:
            # Connect to source
            source_conn = sqlite3.connect(self.source_db)
            source_conn.row_factory = sqlite3.Row

            # Get total user count
            total_users = source_conn.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            sample_size = max(1, int(total_users * self.sample_percent / 100))
            print(f"\nSampling {sample_size:,} users from {total_users:,} total")

            # Step 1: Select random users
            print("Step 1: Selecting random users...", flush=True)
            all_user_pks = source_conn.execute(
                "SELECT pk_user FROM users ORDER BY pk_user"
            ).fetchall()
            sampled_user_pks = set(random.sample([row[0] for row in all_user_pks], sample_size))
            print(f"  ✓ Selected {len(sampled_user_pks):,} users")

            # Step 2: Get their posts
            print("Step 2: Getting posts from sampled users...", flush=True)
            posts = source_conn.execute(
                """SELECT pk_post FROM posts
                   WHERE fk_author IN ({})""".format(
                    ','.join('?' * len(sampled_user_pks))
                ),
                list(sampled_user_pks)
            ).fetchall()
            sampled_post_pks = set(row[0] for row in posts)
            print(f"  ✓ Found {len(sampled_post_pks):,} posts")

            # Step 3: Create output database with schema
            print("Step 3: Creating output database schema...", flush=True)
            self._create_schema(self.output_db)

            # Step 4: Copy sampled data
            print("Step 4: Copying sampled data...", flush=True)
            output_conn = sqlite3.connect(self.output_db)
            output_conn.execute("PRAGMA journal_mode = MEMORY")
            output_conn.execute("PRAGMA synchronous = OFF")

            # Copy users
            users = source_conn.execute(
                """SELECT * FROM users
                   WHERE pk_user IN ({})""".format(
                    ','.join('?' * len(sampled_user_pks))
                ),
                list(sampled_user_pks)
            ).fetchall()

            output_conn.executemany(
                """INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                users
            )
            output_conn.commit()
            print(f"  ✓ Copied {len(users):,} users")

            # Copy posts
            posts = source_conn.execute(
                """SELECT * FROM posts
                   WHERE pk_post IN ({})""".format(
                    ','.join('?' * len(sampled_post_pks))
                ),
                list(sampled_post_pks)
            ).fetchall()

            output_conn.executemany(
                """INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                posts
            )
            output_conn.commit()
            print(f"  ✓ Copied {len(posts):,} posts")

            # Copy comments (only for posts we're keeping)
            comments = source_conn.execute(
                """SELECT * FROM comments
                   WHERE fk_post IN ({})""".format(
                    ','.join('?' * len(sampled_post_pks))
                ),
                list(sampled_post_pks)
            ).fetchall()

            output_conn.executemany(
                """INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                comments
            )
            output_conn.commit()
            print(f"  ✓ Copied {len(comments):,} comments")

            # Copy follows (only between sampled users)
            follows = source_conn.execute(
                """SELECT * FROM user_follows
                   WHERE fk_follower IN ({}) AND fk_following IN ({})""".format(
                    ','.join('?' * len(sampled_user_pks)),
                    ','.join('?' * len(sampled_user_pks))
                ),
                list(sampled_user_pks) + list(sampled_user_pks)
            ).fetchall()

            if follows:
                output_conn.executemany(
                    """INSERT INTO user_follows VALUES (?, ?, ?)""",
                    follows
                )
                output_conn.commit()
            print(f"  ✓ Copied {len(follows):,} follows")

            # Copy likes (only for posts we're keeping)
            likes = source_conn.execute(
                """SELECT * FROM post_likes
                   WHERE fk_post IN ({})""".format(
                    ','.join('?' * len(sampled_post_pks))
                ),
                list(sampled_post_pks)
            ).fetchall()

            if likes:
                output_conn.executemany(
                    """INSERT INTO post_likes VALUES (?, ?, ?, ?)""",
                    likes
                )
                output_conn.commit()
            print(f"  ✓ Copied {len(likes):,} likes")

            # Step 5: Optimize
            print("Step 5: Optimizing database...", flush=True)
            output_conn.execute("VACUUM")
            output_conn.execute("ANALYZE")
            output_conn.close()
            source_conn.close()

            # Report size
            size_mb = Path(self.output_db).stat().st_size / (1024 * 1024)
            elapsed = time.time() - start

            print("\n" + "=" * 70)
            print(f"✅ Sampling complete in {elapsed:.1f}s")
            print(f"   Output: {Path(self.output_db).name} ({size_mb:.1f} MB)")
            print("=" * 70)
            return True

        except Exception as e:
            print(f"\n❌ Sampling failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_schema(self, db_path: str):
        """Create database schema in output database"""
        schema_path = Path("database/schema-sqlite-xs.sql")
        if not schema_path.exists():
            print(f"Error: {schema_path} not found")
            sys.exit(1)

        conn = sqlite3.connect(db_path)
        with open(schema_path) as f:
            conn.executescript(f.read())
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    source_db = sys.argv[1]
    output_db = sys.argv[2]
    sample_percent = float(sys.argv[3])

    print(f"Source: {source_db}")
    print(f"Output: {output_db}")
    print(f"Sample: {sample_percent}%\n")

    sampler = DatabaseSampler(source_db, output_db, sample_percent)
    success = sampler.run()

    sys.exit(0 if success else 1)
