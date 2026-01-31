#!/usr/bin/env python3
"""
Import SQLite benchmark databases to PostgreSQL.

Usage:
    python database/import-to-postgresql.py [db_names]

Examples:
    python database/import-to-postgresql.py xxs xs xxlarge
    python database/import-to-postgresql.py                 # defaults to xxs, xs, xxlarge
"""

import sqlite3
import time
import sys
from pathlib import Path

import psycopg


def import_database(db_name: str):
    """Import a single SQLite database to PostgreSQL."""

    print(f"\n{'=' * 70}")
    print(f"IMPORTING: {db_name.upper()}")
    print("=" * 70)

    sqlite_path = f"datasets/fraiseql_{db_name}.db"
    if not Path(sqlite_path).exists():
        print(f"❌ SQLite database not found: {sqlite_path}")
        return False

    # Open SQLite database
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    try:
        pg_conn = psycopg.connect(
            "host=localhost dbname=fraiseql user=fraiseql password=fraiseql"
        )
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sqlite_conn.close()
        return False

    try:
        start_time = time.time()

        # Disable foreign key constraints during import
        print("Disabling foreign key constraints...")
        pg_cursor.execute("SET session_replication_role = 'replica'")
        pg_conn.commit()

        # Clear existing data
        print("Clearing existing data...")
        tables = ["post_likes", "user_follows", "comments", "posts", "users"]
        for table in tables:
            pg_cursor.execute(f"DELETE FROM {table}")
        pg_conn.commit()

        # Import each table
        print("\nImporting tables:")

        # Users table
        print("  Importing users...", flush=True)
        sqlite_cursor.execute(
            "SELECT id, identifier, email, username, full_name, bio, created_at, updated_at FROM users"
        )
        users = sqlite_cursor.fetchall()

        with pg_cursor.copy(
            "COPY tb_user (id, identifier, email, username, full_name, bio, created_at, updated_at) FROM STDIN"
        ) as copy:
            for user in users:
                copy.write(
                    b"\t".join(
                        [str(v).encode() if v is not None else b"\\N" for v in user]
                    )
                    + b"\n"
                )
        pg_conn.commit()
        print(f"    ✓ {len(users):,} users imported")

        # Posts table
        print("  Importing posts...", flush=True)
        sqlite_cursor.execute("""
            SELECT id, identifier, title, content, fk_author, published, created_at, updated_at
            FROM posts
        """)
        posts = sqlite_cursor.fetchall()

        with pg_cursor.copy(
            "COPY tb_post (id, identifier, title, content, fk_author, published, created_at, updated_at) FROM STDIN"
        ) as copy:
            for post in posts:
                # Convert published (int) to boolean
                post_list = list(post)
                post_list[5] = "true" if post_list[5] else "false"

                copy.write(
                    b"\t".join(
                        [
                            str(v).encode() if v is not None else b"\\N"
                            for v in post_list
                        ]
                    )
                    + b"\n"
                )
        pg_conn.commit()
        print(f"    ✓ {len(posts):,} posts imported")

        # Comments table
        print("  Importing comments...", flush=True)
        sqlite_cursor.execute("""
            SELECT id, content, fk_post, fk_author, created_at, updated_at
            FROM comments
        """)
        comments = sqlite_cursor.fetchall()

        with pg_cursor.copy(
            "COPY tb_comment (id, content, fk_post, fk_author, created_at, updated_at) FROM STDIN"
        ) as copy:
            for comment in comments:
                copy.write(
                    b"\t".join(
                        [str(v).encode() if v is not None else b"\\N" for v in comment]
                    )
                    + b"\n"
                )
        pg_conn.commit()
        print(f"    ✓ {len(comments):,} comments imported")

        # User follows table
        print("  Importing user_follows...", flush=True)
        sqlite_cursor.execute("""
            SELECT fk_follower, fk_following, created_at
            FROM user_follows
        """)
        follows = sqlite_cursor.fetchall()

        with pg_cursor.copy(
            "COPY tb_user_follows (fk_follower, fk_following, created_at) FROM STDIN"
        ) as copy:
            for follow in follows:
                copy.write(
                    b"\t".join(
                        [str(v).encode() if v is not None else b"\\N" for v in follow]
                    )
                    + b"\n"
                )
        pg_conn.commit()
        print(f"    ✓ {len(follows):,} follows imported")

        # Post likes table
        print("  Importing post_likes...", flush=True)
        sqlite_cursor.execute("""
            SELECT fk_user, fk_post, reaction, created_at
            FROM post_likes
        """)
        likes = sqlite_cursor.fetchall()

        with pg_cursor.copy(
            "COPY tb_post_likes (fk_user, fk_post, reaction, created_at) FROM STDIN"
        ) as copy:
            for like in likes:
                copy.write(
                    b"\t".join(
                        [str(v).encode() if v is not None else b"\\N" for v in like]
                    )
                    + b"\n"
                )
        pg_conn.commit()
        print(f"    ✓ {len(likes):,} likes imported")

        # Re-enable foreign key constraints
        print("\nRe-enabling foreign key constraints...")
        pg_cursor.execute("SET session_replication_role = 'origin'")
        pg_conn.commit()

        elapsed = time.time() - start_time

        # Validate import
        print("\nValidating import:")
        pg_cursor.execute("SELECT COUNT(*) FROM tb_user")
        pg_users = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM tb_post")
        pg_posts = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM tb_comment")
        pg_comments = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM tb_user_follows")
        pg_follows = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM tb_post_likes")
        pg_likes = pg_cursor.fetchone()[0]

        print(f"  ✓ Users:   {pg_users:,}")
        print(f"  ✓ Posts:   {pg_posts:,}")
        print(f"  ✓ Comments: {pg_comments:,}")
        print(f"  ✓ Follows: {pg_follows:,}")
        print(f"  ✓ Likes:   {pg_likes:,}")

        print(f"\n✅ Import complete in {elapsed:.1f} seconds")

        pg_conn.close()
        sqlite_conn.close()
        return True

    except Exception as e:
        print(f"❌ Error during import: {e}")
        import traceback

        traceback.print_exc()
        pg_conn.close()
        sqlite_conn.close()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        databases = ["xxs", "xs", "xxlarge"]
    else:
        databases = sys.argv[1:]

    print("POSTGRESQL IMPORT")
    print("=" * 70)
    print("Target database: fraiseql")
    print("PostgreSQL user: fraiseql")

    all_success = True
    for db_name in databases:
        success = import_database(db_name)
        all_success = all_success and success

    print("\n" + "=" * 70)
    if all_success:
        print("✅ All imports successful!")
    else:
        print("❌ Some imports failed")
    print("=" * 70)

    sys.exit(0 if all_success else 1)
