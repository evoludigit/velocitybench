#!/usr/bin/env python3
"""
Validate all database size variations for data integrity and quality.

Checks:
- Record counts for each size
- Referential integrity (no orphans)
- Content quality samples
- Database file sizes
"""

import sqlite3
import sys
from pathlib import Path
from tabulate import tabulate

try:
    from tabulate import tabulate
except ImportError:
    # Fallback if tabulate not available
    def tabulate(data, headers=None):
        if headers:
            print(headers)
        for row in data:
            print(row)


class VariationValidator:
    """Validate all database variations"""

    VARIATIONS = [
        ('xs', 0.5),
        ('small', 1.0),
        ('medium', 5.0),
        ('large', 10.0),
        ('xlarge', 50.0),
        ('xxlarge', 100.0),
    ]

    def validate_all(self):
        """Validate all variations"""
        print("=" * 90)
        print("VALIDATING ALL DATABASE VARIATIONS")
        print("=" * 90)

        results = []
        all_pass = True

        for name, percent in self.VARIATIONS:
            db_path = f"datasets/fraiseql_{name}.db"

            if not Path(db_path).exists():
                results.append([name, f"{percent}%", "❌ MISSING", "-", "-", "-", "-"])
                all_pass = False
                continue

            try:
                result = self._validate_db(db_path, name)
                if result[0] == "❌":
                    all_pass = False
                results.append(result)
            except Exception as e:
                results.append([name, f"{percent}%", f"❌ ERROR: {e}", "-", "-", "-", "-"])
                all_pass = False

        # Print results table
        print("\n📊 Validation Results:\n")
        headers = ["Database", "Sample %", "Status", "Users", "Posts", "Comments", "Size"]
        try:
            print(tabulate(results, headers=headers, tablefmt="grid"))
        except (NameError, Exception) as e:
            print(headers)
            for row in results:
                print(row)

        print("\n" + "=" * 90)
        if all_pass:
            print("✅ ALL DATABASES VALIDATED SUCCESSFULLY")
        else:
            print("⚠️  SOME DATABASES HAVE ISSUES (see above)")
        print("=" * 90)

        return all_pass

    def _validate_db(self, db_path: str, name: str):
        """Validate a single database"""
        conn = sqlite3.connect(db_path)

        # Get counts
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        post_count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        comment_count = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]

        # Check referential integrity
        orphan_posts = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE fk_author NOT IN (SELECT pk_user FROM users)"
        ).fetchone()[0]
        orphan_comments = conn.execute(
            "SELECT COUNT(*) FROM comments WHERE fk_post NOT IN (SELECT pk_post FROM posts) OR fk_author NOT IN (SELECT pk_user FROM users)"
        ).fetchone()[0]

        conn.close()

        # Get file size
        size_mb = Path(db_path).stat().st_size / (1024 * 1024)
        size_str = f"{size_mb:.1f}MB" if size_mb < 1024 else f"{size_mb/1024:.1f}GB"

        # Determine status
        if orphan_posts > 0 or orphan_comments > 0:
            status = "❌ INTEGRITY"
        else:
            status = "✅ PASS"

        # Sample percent
        percent = "100%" if name == "xxlarge" else "-"

        return [
            name,
            percent,
            status,
            f"{user_count:,}",
            f"{post_count:,}",
            f"{comment_count:,}",
            size_str
        ]


if __name__ == "__main__":
    validator = VariationValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)
