#!/usr/bin/env python3
"""
Import SQLite benchmark databases to PostgreSQL with schema mapping.

Handles the mismatch between SQLite schema (pk_user, fk_author) and
PostgreSQL schema (UUID pks, author_id).

Usage:
    python database/sqlite-to-postgres-import.py xxs
    python database/sqlite-to-postgres-import.py xs
    python database/sqlite-to-postgres-import.py xxlarge
"""

import os
import sqlite3
import sys
import time
import uuid as uuid_module
from pathlib import Path

import psycopg


def import_sqlite_to_postgres(db_name: str):
    """Import a SQLite database to PostgreSQL with schema mapping."""

    print("=" * 70)
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
    db_password = os.getenv("DB_PASSWORD")
    if not db_password:
        print("❌ Database password is required. Set DB_PASSWORD environment variable.")
        sqlite_conn.close()
        return False

    pg_conninfo = psycopg.conninfo.make_conninfo(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5435")),
        dbname=os.getenv("DB_NAME", "fraiseql_benchmark"),
        user=os.getenv("DB_USER", "benchmark"),
        password=db_password,
    )

    try:
        pg_conn = psycopg.connect(pg_conninfo)
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
        pg_cursor.execute("DELETE FROM benchmark.tb_comment")
        pg_cursor.execute("DELETE FROM benchmark.tb_post")
        pg_cursor.execute("DELETE FROM benchmark.tb_user")
        pg_conn.commit()

        # Create mapping table: SQLite pk_user → PostgreSQL UUID id
        print("Building user ID mapping...")
        sqlite_cursor.execute("SELECT pk_user, id FROM users ORDER BY pk_user")
        user_id_map = {row[0]: row[1] for row in sqlite_cursor.fetchall()}
        user_count = len(user_id_map)
        print(f"  ✓ Mapped {user_count} users")

        # Import users
        print(f"Importing {user_count} users...")
        sqlite_cursor.execute("SELECT id, email, username, full_name, bio, created_at, updated_at FROM users")
        users = sqlite_cursor.fetchall()

        for user_id, email, username, full_name, bio, created_at, updated_at in users:
            # Split full_name into first/last (simple: split on space)
            name_parts = (full_name or "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Convert timestamps (SQLite ISO format → PostgreSQL timestamp)
            created_at_pg = created_at.replace("T", " ") if created_at else None
            updated_at_pg = updated_at.replace("T", " ") if updated_at else None

            try:
                pg_cursor.execute("""
                    INSERT INTO benchmark.tb_user
                    (id, email, username, first_name, last_name, bio, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, true, %s, %s)
                """, (
                    uuid_module.UUID(user_id),  # SQLite text UUID → PostgreSQL UUID
                    email,
                    username,
                    first_name,
                    last_name,
                    bio,
                    created_at_pg,
                    updated_at_pg
                ))
            except ValueError as e:
                print(f"  ⚠ Skipping user {user_id}: invalid UUID - {e}")
                continue

        pg_conn.commit()
        print(f"  ✓ {user_count} users imported")

        # Create mapping table: SQLite pk_post → PostgreSQL UUID id + author mapping
        print("Building post ID mapping...")
        sqlite_cursor.execute("SELECT pk_post, id, fk_author FROM posts ORDER BY pk_post")
        post_rows = sqlite_cursor.fetchall()
        post_id_map = {row[0]: row[1] for row in post_rows}
        post_author_map = {row[0]: row[2] for row in post_rows}
        post_count = len(post_id_map)
        print(f"  ✓ Mapped {post_count} posts")

        # Import posts
        print(f"Importing {post_count} posts...")
        sqlite_cursor.execute("""
            SELECT id, title, content, fk_author, published, created_at, updated_at FROM posts
        """)
        posts = sqlite_cursor.fetchall()

        for post_id, title, content, fk_author, published, created_at, updated_at in posts:
            # Get author UUID from mapping
            author_uuid = user_id_map.get(fk_author)
            if not author_uuid:
                print(f"  ⚠ Skipping post {post_id}: author {fk_author} not found")
                continue

            # Convert timestamps
            created_at_pg = created_at.replace("T", " ") if created_at else None
            updated_at_pg = updated_at.replace("T", " ") if updated_at else None

            try:
                pg_cursor.execute("""
                    INSERT INTO benchmark.tb_post
                    (id, author_id, title, content, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    uuid_module.UUID(post_id),
                    uuid_module.UUID(author_uuid),
                    title,
                    content,
                    'published' if published else 'draft',  # Convert int flag to status
                    created_at_pg,
                    updated_at_pg
                ))
            except (ValueError, psycopg.Error) as e:
                print(f"  ⚠ Skipping post {post_id}: {e}")
                continue

        pg_conn.commit()
        print(f"  ✓ {post_count} posts imported")

        # Import comments
        print("Importing comments...")
        sqlite_cursor.execute("""
            SELECT id, content, fk_post, fk_author, created_at, updated_at FROM comments
        """)
        comments = sqlite_cursor.fetchall()

        comment_count = 0
        skipped_count = 0

        for comment_id, content, fk_post, fk_author, created_at, updated_at in comments:
            # Get post and author UUIDs from mappings
            post_uuid = post_id_map.get(fk_post)
            author_uuid = user_id_map.get(fk_author)

            if not post_uuid or not author_uuid:
                skipped_count += 1
                continue

            # Convert timestamps
            created_at_pg = created_at.replace("T", " ") if created_at else None
            updated_at_pg = updated_at.replace("T", " ") if updated_at else None

            try:
                pg_cursor.execute("""
                    INSERT INTO benchmark.tb_comment
                    (id, post_id, author_id, content, is_approved, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, true, %s, %s)
                """, (
                    uuid_module.UUID(comment_id),
                    uuid_module.UUID(post_uuid),
                    uuid_module.UUID(author_uuid),
                    content,
                    created_at_pg,
                    updated_at_pg
                ))
                comment_count += 1
            except (ValueError, psycopg.Error) as e:
                skipped_count += 1
                continue

        pg_conn.commit()
        print(f"  ✓ {comment_count} comments imported ({skipped_count} skipped)")

        # Import user follows
        print("Importing user follows...")
        sqlite_cursor.execute("""
            SELECT fk_follower, fk_following, created_at FROM user_follows
        """)
        follows = sqlite_cursor.fetchall()

        follow_count = 0
        for fk_follower, fk_following, created_at in follows:
            follower_uuid = user_id_map.get(fk_follower)
            following_uuid = user_id_map.get(fk_following)

            if not follower_uuid or not following_uuid:
                continue

            created_at_pg = created_at.replace("T", " ") if created_at else None

            try:
                pg_cursor.execute("""
                    INSERT INTO benchmark.user_follows
                    (follower_id, following_id, created_at)
                    VALUES (%s, %s, %s)
                """, (
                    uuid_module.UUID(follower_uuid),
                    uuid_module.UUID(following_uuid),
                    created_at_pg
                ))
                follow_count += 1
            except psycopg.Error:
                continue

        pg_conn.commit()
        print(f"  ✓ {follow_count} follows imported")

        # Import post likes
        print("Importing post likes...")
        sqlite_cursor.execute("""
            SELECT fk_user, fk_post, reaction_type, created_at FROM post_likes
        """)
        likes = sqlite_cursor.fetchall()

        like_count = 0
        for fk_user, fk_post, reaction_type, created_at in likes:
            user_uuid = user_id_map.get(fk_user)
            post_uuid = post_id_map.get(fk_post)

            if not user_uuid or not post_uuid:
                continue

            created_at_pg = created_at.replace("T", " ") if created_at else None

            try:
                pg_cursor.execute("""
                    INSERT INTO benchmark.post_likes
                    (user_id, post_id, reaction_type, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (
                    uuid_module.UUID(user_uuid),
                    uuid_module.UUID(post_uuid),
                    reaction_type,
                    created_at_pg
                ))
                like_count += 1
            except psycopg.Error:
                continue

        pg_conn.commit()
        print(f"  ✓ {like_count} likes imported")

        # Re-enable foreign key constraints
        print("Re-enabling foreign key constraints...")
        pg_cursor.execute("SET session_replication_role = 'origin'")
        pg_conn.commit()

        elapsed = time.time() - start_time

        # Validate import
        print("\nValidating import:")
        pg_cursor.execute("SELECT COUNT(*) FROM benchmark.tb_user")
        pg_users = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM benchmark.tb_post")
        pg_posts = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM benchmark.tb_comment")
        pg_comments = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM benchmark.user_follows")
        pg_follows = pg_cursor.fetchone()[0]

        pg_cursor.execute("SELECT COUNT(*) FROM benchmark.post_likes")
        pg_likes = pg_cursor.fetchone()[0]

        print(f"  ✓ Users:    {pg_users:,}")
        print(f"  ✓ Posts:    {pg_posts:,}")
        print(f"  ✓ Comments: {pg_comments:,}")
        print(f"  ✓ Follows:  {pg_follows:,}")
        print(f"  ✓ Likes:    {pg_likes:,}")

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
        print("Usage: python sqlite-to-postgres-import.py [xxs|xs|xxlarge]")
        sys.exit(1)

    db_name = sys.argv[1].lower()
    if db_name not in ['xxs', 'xs', 'xxlarge']:
        print("Error: Database name must be one of: xxs, xs, xxlarge")
        sys.exit(1)

    success = import_sqlite_to_postgres(db_name)
    sys.exit(0 if success else 1)
