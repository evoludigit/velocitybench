#!/usr/bin/env python3
"""
Validate SQLite benchmark databases for data integrity and content quality.

Usage:
    python database/validate-databases.py [db_path1] [db_path2] ...
"""

import sqlite3
import sys
from pathlib import Path


def validate_database(db_path: str):
    """Validate a single database for integrity and content."""

    print(f"\n{'=' * 70}")
    print(f"VALIDATING: {Path(db_path).name}")
    print('=' * 70)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check record counts
    print("\nRecord counts:")
    tables = ['users', 'posts', 'comments', 'user_follows', 'post_likes']

    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        counts[table] = count
        print(f"  {table:20} {count:,}")

    # Check for primary key uniqueness
    print("\nPrimary key uniqueness:")
    pk_columns = {
        'users': 'pk_user',
        'posts': 'pk_post',
        'comments': 'pk_comment',
    }

    all_unique = True
    for table, pk_col in pk_columns.items():
        cursor.execute(f"SELECT COUNT(*), COUNT(DISTINCT {pk_col}) FROM {table}")
        total, unique = cursor.fetchone()
        status = "✓" if total == unique else "❌"
        all_unique = all_unique and (total == unique)
        print(f"  {status} {table}: {total} total, {unique} unique")

    # Check for referential integrity
    print("\nReferential integrity (foreign keys):")

    # Check posts.fk_author references users
    cursor.execute("""
        SELECT COUNT(*) FROM posts
        WHERE fk_author NOT IN (SELECT pk_user FROM users)
    """)
    orphaned = cursor.fetchone()[0]
    status = "✓" if orphaned == 0 else "❌"
    print(f"  {status} posts.fk_author → users.pk_user: {orphaned} orphaned")

    # Check comments.fk_post references posts
    cursor.execute("""
        SELECT COUNT(*) FROM comments
        WHERE fk_post NOT IN (SELECT pk_post FROM posts)
    """)
    orphaned = cursor.fetchone()[0]
    status = "✓" if orphaned == 0 else "❌"
    print(f"  {status} comments.fk_post → posts.pk_post: {orphaned} orphaned")

    # Check comments.fk_author references users
    cursor.execute("""
        SELECT COUNT(*) FROM comments
        WHERE fk_author NOT IN (SELECT pk_user FROM users)
    """)
    orphaned = cursor.fetchone()[0]
    status = "✓" if orphaned == 0 else "❌"
    print(f"  {status} comments.fk_author → users.pk_user: {orphaned} orphaned")

    # Check user_follows references users
    cursor.execute("""
        SELECT COUNT(*) FROM user_follows
        WHERE fk_follower NOT IN (SELECT pk_user FROM users)
           OR fk_following NOT IN (SELECT pk_user FROM users)
    """)
    orphaned = cursor.fetchone()[0]
    status = "✓" if orphaned == 0 else "❌"
    print(f"  {status} user_follows → users.pk_user: {orphaned} orphaned")

    # Check post_likes references posts and users
    cursor.execute("""
        SELECT COUNT(*) FROM post_likes
        WHERE fk_user NOT IN (SELECT pk_user FROM users)
           OR fk_post NOT IN (SELECT pk_post FROM posts)
    """)
    orphaned = cursor.fetchone()[0]
    status = "✓" if orphaned == 0 else "❌"
    print(f"  {status} post_likes → users/posts: {orphaned} orphaned")

    # Check content quality
    print("\nContent quality (sample check):")

    # Check for non-null content
    cursor.execute("SELECT COUNT(*) FROM posts WHERE content IS NULL OR content = ''")
    null_content = cursor.fetchone()[0]
    print(f"  Posts with null/empty content: {null_content}")

    cursor.execute("SELECT COUNT(*) FROM comments WHERE content IS NULL OR content = ''")
    null_content = cursor.fetchone()[0]
    print(f"  Comments with null/empty content: {null_content}")

    # Sample content to verify it's not templated
    print("\nContent samples:")

    cursor.execute("SELECT title FROM posts LIMIT 3")
    print("  Post titles:")
    for row in cursor.fetchall():
        print(f"    - {row[0][:60]}")

    cursor.execute("SELECT content FROM posts WHERE content IS NOT NULL LIMIT 1")
    row = cursor.fetchone()
    if row:
        content = row[0]
        preview = content[:100].replace('\n', ' ')
        print(f"  Post content preview: {preview}...")

    cursor.execute("SELECT content FROM comments WHERE content IS NOT NULL LIMIT 2")
    print("  Comment samples:")
    for row in cursor.fetchall():
        preview = row[0][:80].replace('\n', ' ')
        print(f"    - {preview}")

    # File size check
    size_mb = Path(db_path).stat().st_size / (1024 * 1024)
    size_str = f"{size_mb:.1f}MB" if size_mb < 1024 else f"{size_mb/1024:.1f}GB"
    print(f"\nFile size: {size_str}")

    conn.close()

    return all_unique and orphaned == 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to validating the three main databases
        databases = [
            "datasets/fraiseql_xxs.db",
            "datasets/fraiseql_xs.db",
            "datasets/fraiseql_xxlarge.db",
        ]
    else:
        databases = sys.argv[1:]

    print("DATABASE VALIDATION SUITE")
    print("=" * 70)

    all_valid = True
    for db_path in databases:
        if not Path(db_path).exists():
            print(f"\n❌ Database not found: {db_path}")
            all_valid = False
            continue

        try:
            valid = validate_database(db_path)
            all_valid = all_valid and valid
        except Exception as e:
            print(f"\n❌ Error validating {db_path}: {e}")
            all_valid = False

    print("\n" + "=" * 70)
    if all_valid:
        print("✅ All validations passed!")
    else:
        print("❌ Some validations failed")
    print("=" * 70)

    sys.exit(0 if all_valid else 1)
