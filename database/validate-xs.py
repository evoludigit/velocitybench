#!/usr/bin/env python3
"""Quick validation of XS database"""

import sqlite3
import sys
from pathlib import Path


def validate(db_path: str):
    """Validate XS database integrity and content quality"""

    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)

    print("=" * 70)
    print("XS DATABASE VALIDATION")
    print("=" * 70)

    # Check record counts
    checks = {
        'users': (500, "SELECT COUNT(*) FROM users"),
        'posts': (5000, "SELECT COUNT(*) FROM posts"),
        'comments': (25000, "SELECT COUNT(*) FROM comments"),
        'follows': (2000, "SELECT COUNT(*) FROM user_follows"),  # At least
        'likes': (8000, "SELECT COUNT(*) FROM post_likes"),  # At least
    }

    print("\n📊 Record Counts:")
    all_pass = True
    for name, (expected, query) in checks.items():
        count = conn.execute(query).fetchone()[0]
        status = "✓" if count >= (expected * 0.9) else "✗"
        print(f"  {status} {name:12} {count:,} (expected ~{expected})")
        if count < (expected * 0.9):
            all_pass = False

    # Check referential integrity
    print("\n🔗 Referential Integrity:")
    orphan_posts = conn.execute(
        "SELECT COUNT(*) FROM posts WHERE fk_author NOT IN (SELECT pk_user FROM users)"
    ).fetchone()[0]
    orphan_comments = conn.execute(
        "SELECT COUNT(*) FROM comments WHERE fk_post NOT IN (SELECT pk_post FROM posts) OR fk_author NOT IN (SELECT pk_user FROM users)"
    ).fetchone()[0]

    print(f"  {'✓' if orphan_posts == 0 else '✗'} Orphaned posts: {orphan_posts}")
    print(f"  {'✓' if orphan_comments == 0 else '✗'} Orphaned comments: {orphan_comments}")

    if orphan_posts > 0 or orphan_comments > 0:
        all_pass = False

    # Check content quality
    print("\n📝 Sample Content Quality:")

    sample_posts = conn.execute(
        "SELECT title, LENGTH(content) FROM posts ORDER BY RANDOM() LIMIT 3"
    ).fetchall()

    print("  Post Samples:")
    for title, content_len in sample_posts:
        title_preview = title[:50] + "..." if len(title) > 50 else title
        print(f"    • {title_preview} (content: {content_len} chars)")

    sample_comments = conn.execute(
        "SELECT content FROM comments ORDER BY RANDOM() LIMIT 2"
    ).fetchall()

    print("  Comment Samples:")
    for (comment,) in sample_comments:
        comment_preview = comment[:60] + "..." if len(comment) > 60 else comment
        print(f"    • {comment_preview}")

    # Database size
    print("\n💾 Database Info:")
    db_size = Path(db_path).stat().st_size / (1024 * 1024)
    print(f"  File size: {db_size:.1f} MB")

    # Check for content diversity
    print("\n🎯 Content Analysis:")
    avg_post_title_len = conn.execute(
        "SELECT AVG(LENGTH(title)) FROM posts"
    ).fetchone()[0]
    avg_post_content_len = conn.execute(
        "SELECT AVG(LENGTH(content)) FROM posts"
    ).fetchone()[0]
    avg_comment_len = conn.execute(
        "SELECT AVG(LENGTH(content)) FROM comments"
    ).fetchone()[0]

    print(f"  Avg post title length: {avg_post_title_len:.0f} chars")
    print(f"  Avg post content length: {avg_post_content_len:.0f} chars")
    print(f"  Avg comment length: {avg_comment_len:.0f} chars")

    conn.close()

    print("\n" + "=" * 70)
    if all_pass and orphan_posts == 0 and orphan_comments == 0:
        print("✅ XS Database validation PASSED")
        print("=" * 70)
        return True
    else:
        print("⚠️  XS Database validation has issues (see above)")
        print("=" * 70)
        return False


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "datasets/fraiseql_xs_test.db"
    success = validate(db_path)
    sys.exit(0 if success else 1)
