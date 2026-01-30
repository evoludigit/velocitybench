#!/usr/bin/env python
"""
Load validated blog comments into PostgreSQL database.

Converts comment JSON files to TSV format and loads using PostgreSQL COPY.
Maps comments to posts and assigns random authors from generated users.

Usage:
    python load_comments_to_db.py --comments-dir /tmp/blog_comments/accepted \
                                  --num-users 5000 \
                                  --connection "postgresql://user:pass@localhost/db"

    python load_comments_to_db.py --comments-dir /tmp/blog_comments/accepted \
                                  --num-users 5000 \
                                  --dry-run
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    import psycopg
except ImportError:
    print("Error: psycopg not installed")
    print("Install with: pip install psycopg")
    import sys
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
BLOG_DIR = SCRIPT_DIR.parent / "output" / "blog"

# Comment loading
DEFAULT_NUM_USERS = 5000


# ============================================================================
# Database Models
# ============================================================================


class PersonaToUserMapper:
    """Maps comment author_id (pk_user from persona) to valid user PKs.

    With updated persona generation, author_id is the pk_user directly from the persona.
    This mapper ensures consistency and validates the PK is within the available users range.
    """

    def __init__(self, num_users: int = DEFAULT_NUM_USERS):
        self.num_users = num_users

    def get_user_pk_for_persona(self, author_id: int | None, author_name: str | None) -> int:
        """
        Get valid user PK for a comment author.

        With new persona schema, author_id is already the pk_user from the persona.
        Falls back to round-robin if author_id is not provided.
        """
        if author_id is not None:
            # author_id is already pk_user from the persona, ensure it's valid
            return 1 + ((author_id - 1) % self.num_users)
        elif author_name:
            # Hash author name to get consistent ID
            persona_key = hash(author_name) % 10000
            return 1 + ((persona_key - 1) % self.num_users)
        else:
            # Fallback to random
            return random.randint(1, self.num_users)


class BlogCommentLoader:
    """Load comments from JSON to PostgreSQL."""

    def __init__(self, num_users: int = DEFAULT_NUM_USERS):
        self.num_users = num_users
        self.persona_mapper = PersonaToUserMapper(num_users)
        self.stats = {
            "files_processed": 0,
            "comments_loaded": 0,
            "posts_with_comments": 0,
            "failed_posts": 0,
            "duration": 0,
        }

    def discover_comment_files(self, comments_dir: Path) -> list[Path]:
        """Find all comment JSON files."""
        if not comments_dir.exists():
            print(f"Error: Comments directory not found: {comments_dir}")
            return []

        files = list(comments_dir.glob("*_comments.json"))
        print(f"Found {len(files)} comment files")
        return sorted(files)

    def find_post_by_filename(self, post_filename: str) -> tuple[int, str] | None:
        """
        Find post in database by filename.

        Returns (pk_post, title) or None if not found.

        For now, we'll use a simple approach:
        - Parse filename to get title
        - We'll need to query the database to find matching post

        This requires database connection.
        """
        # This will be implemented with actual DB query
        return None

    def generate_comment_author(self, comment_index: int, author_id: int | None = None, author_name: str | None = None) -> int:
        """
        Assign author to comment.

        If author_id or author_name provided, maps to consistent user PK.
        Otherwise falls back to round-robin on comment index.
        """
        if author_id is not None or author_name is not None:
            return self.persona_mapper.get_user_pk_for_persona(author_id, author_name)
        return 1 + (comment_index % self.num_users)

    def generate_comment_dates(
        self, post_published_at: datetime
    ) -> tuple[datetime, datetime]:
        """
        Generate realistic comment dates.

        Comments appear 1-60 days after post was published.
        """
        # Random days after publication
        days_offset = random.randint(1, 60)
        created_at = post_published_at + timedelta(days=days_offset)

        # Updated at = created at + 0-7 days (for edits)
        updated_at = created_at + timedelta(days=random.randint(0, 7))

        return created_at, updated_at

    def prepare_comments_tsv(
        self, comments_dir: Path, output_file: Path
    ) -> tuple[int, Path]:
        """
        Convert comment JSON files to TSV format for PostgreSQL COPY.

        Returns: (total_comments_count, tsv_file_path)
        """
        print(f"\nPreparing comments TSV file...", flush=True)

        comment_files = self.discover_comment_files(comments_dir)
        if not comment_files:
            return 0, output_file

        total_comments = 0

        with open(output_file, "w", encoding="utf-8") as tsv_file:
            for file_idx, comment_file in enumerate(comment_files):
                try:
                    with open(comment_file) as f:
                        data = json.load(f)

                    post_title = data.get("post_title", "")
                    comments = data.get("comments", [])

                    for comment_idx, comment in enumerate(comments):
                        comment_text = comment.get("text", "").strip()

                        if not comment_text:
                            continue

                        # Generate comment data
                        comment_id = str(uuid.uuid4())

                        # Extract author information from comment (persona-based)
                        author_id = comment.get("author_id")
                        author_name = comment.get("author_name")

                        fk_author = self.generate_comment_author(
                            file_idx * 100 + comment_idx,
                            author_id=author_id,
                            author_name=author_name
                        )

                        # For now, created_at is current time
                        # In actual implementation, would fetch post published_at from DB
                        created_at = datetime.now()
                        updated_at = created_at

                        # Format for TSV
                        # Columns: id, fk_post, fk_author, fk_parent, content, is_approved, created_at, updated_at
                        row = [
                            comment_id,           # id (UUID)
                            "\\N",                # fk_post (NULL, will be filled with UPDATE)
                            str(fk_author),       # fk_author (1-5000)
                            "\\N",                # fk_parent (NULL for primary comments)
                            self._escape_tsv(comment_text),  # content
                            "true",               # is_approved (hardcoded true)
                            created_at.isoformat(),  # created_at
                            updated_at.isoformat(),  # updated_at
                        ]

                        tsv_file.write("\t".join(row) + "\n")
                        total_comments += 1

                    self.stats["files_processed"] += 1

                except Exception as e:
                    print(f"  Warning: Failed to process {comment_file}: {e}")
                    self.stats["failed_posts"] += 1

        print(f"✓ Prepared {total_comments} comments in TSV format")
        return total_comments, output_file

    def load_to_postgres(
        self,
        comments_tsv: Path,
        connection_string: str,
        comments_dir: Path,
    ) -> bool:
        """
        Load comments to PostgreSQL using COPY command.

        Uses a two-phase approach:
        1. Load comments with NULL fk_post values
        2. Update fk_post by matching comment identifier to post filename
        """
        print(f"\nLoading comments to PostgreSQL...", flush=True)

        try:
            with psycopg.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    # Load comments initially with NULL fk_post, then update in batch
                    print(f"  Loading comments (without post associations)...")
                    with open(comments_tsv, "r", encoding="utf-8") as f:
                        with cur.copy(
                            "COPY benchmark.tb_comment (id, fk_post, fk_author, fk_parent, content, is_approved, created_at, updated_at) FROM STDIN"
                        ) as copy:
                            for line in f:
                                copy.write(line.encode("utf-8"))

                    # Count loaded
                    cur.execute("SELECT COUNT(*) FROM benchmark.tb_comment;")
                    count = cur.fetchone()[0]
                    print(f"  ✓ Loaded {count:,} comments")

                    # Update fk_post by matching post titles
                    print(f"  Associating comments with posts...")
                    comment_files = self.discover_comment_files(comments_dir)

                    updates_made = 0
                    for comment_file in comment_files:
                        try:
                            with open(comment_file) as f:
                                data = json.load(f)

                            post_file = data.get("post_file", "")
                            post_title = data.get("post_title", "")

                            if not post_title:
                                continue

                            # Find post by title (fuzzy match)
                            cur.execute(
                                """
                                SELECT pk_post FROM benchmark.tb_post
                                WHERE title ILIKE %s
                                LIMIT 1
                                """,
                                (f"%{post_title}%",),
                            )

                            result = cur.fetchone()
                            if result:
                                pk_post = result[0]

                                # Update comments that reference this post
                                # We use the post file name as a proxy
                                cur.execute(
                                    """
                                    UPDATE benchmark.tb_comment
                                    SET fk_post = %s
                                    WHERE fk_post IS NULL
                                    AND identifier LIKE %s
                                    LIMIT 100
                                    """,
                                    (pk_post, f"{post_title[:10]}%"),
                                )

                                updates_made += cur.rowcount

                        except Exception as e:
                            print(f"    Warning: Failed to update for {post_file}: {e}")

                    print(f"  ✓ Associated {updates_made:,} comments with posts")

                    conn.commit()

                    # Verify counts
                    cur.execute(
                        "SELECT COUNT(*) FROM benchmark.tb_comment WHERE fk_post IS NOT NULL"
                    )
                    associated = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM benchmark.tb_comment")
                    total = cur.fetchone()[0]

                    print(
                        f"\n  Final: {associated:,}/{total:,} comments associated with posts"
                    )
                    self.stats["comments_loaded"] = total

                    return True

        except Exception as e:
            print(f"❌ Error loading to PostgreSQL: {e}")
            return False

    @staticmethod
    def _escape_tsv(value: str) -> str:
        """Escape special characters for TSV format."""
        value = value.replace("\\", "\\\\")
        value = value.replace("\t", "\\t")
        value = value.replace("\n", "\\n")
        value = value.replace("\r", "\\r")
        return value

    def run(
        self,
        comments_dir: Path,
        connection_string: str | None = None,
        output_tsv: Path | None = None,
        dry_run: bool = False,
    ) -> dict:
        """
        Main workflow: validate files, prepare TSV, load to database.

        Returns statistics.
        """
        start_time = time.time()

        # Determine output path
        if not output_tsv:
            output_tsv = comments_dir.parent / "comments.tsv"

        print(f"\n{'='*70}")
        print(f"BLOG COMMENTS DATABASE LOADER")
        print(f"{'='*70}")
        print(f"Comments directory:  {comments_dir}")
        print(f"Output TSV:          {output_tsv}")
        print(f"Num users:           {self.num_users:,}")
        if connection_string:
            print(f"Database:            {connection_string.split('@')[-1]}")
        print(f"Dry run:             {dry_run}")
        print(f"{'='*70}\n")

        # Prepare TSV
        num_comments, tsv_path = self.prepare_comments_tsv(comments_dir, output_tsv)

        if num_comments == 0:
            print("No comments found. Exiting.")
            return self.stats

        # Load to database
        if dry_run:
            print("\n⚠️  DRY RUN - No database loading")
        elif connection_string:
            success = self.load_to_postgres(tsv_path, connection_string, comments_dir)
            if not success:
                print("❌ Database loading failed")
        else:
            print("\n⚠️  No database connection - TSV file prepared but not loaded")

        # Calculate duration
        self.stats["duration"] = time.time() - start_time

        # Print summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Files processed:         {self.stats['files_processed']:,}")
        print(f"Comments prepared:       {num_comments:,}")
        if connection_string and not dry_run:
            print(f"Comments loaded:         {self.stats['comments_loaded']:,}")
        print(f"Failed posts:            {self.stats['failed_posts']:,}")
        print(f"Duration:                {self.stats['duration']:.1f}s")
        print(f"\nOutput files:")
        print(f"  TSV: {tsv_path}")
        print(f"{'='*70}\n")

        return self.stats


# ============================================================================
# CLI
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Load blog comments to PostgreSQL database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load comments to database
  python load_comments_to_db.py --comments-dir /tmp/blog_comments/accepted \\
                                 --num-users 5000 \\
                                 --connection "postgresql://user:pass@localhost/db"

  # Generate TSV only (no database load)
  python load_comments_to_db.py --comments-dir /tmp/blog_comments/accepted \\
                                 --generate-only

  # Dry run (validate only)
  python load_comments_to_db.py --comments-dir /tmp/blog_comments/accepted \\
                                 --dry-run
        """,
    )

    parser.add_argument(
        "--comments-dir",
        type=Path,
        required=True,
        help="Directory with validated comment JSON files",
    )

    parser.add_argument(
        "--num-users",
        type=int,
        default=DEFAULT_NUM_USERS,
        help=f"Number of users for author assignment (default: {DEFAULT_NUM_USERS})",
    )

    parser.add_argument(
        "--connection",
        type=str,
        help="PostgreSQL connection string",
    )

    parser.add_argument(
        "--output-tsv",
        type=Path,
        help="Output TSV file path",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate files without loading to database",
    )

    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Generate TSV file only (no database load)",
    )

    args = parser.parse_args()

    # Run loader
    loader = BlogCommentLoader(num_users=args.num_users)

    connection_string = None if (args.dry_run or args.generate_only) else args.connection

    if not args.dry_run and not args.generate_only and not args.connection:
        parser.error("Either --connection, --dry-run, or --generate-only is required")

    stats = loader.run(
        comments_dir=args.comments_dir,
        connection_string=connection_string,
        output_tsv=args.output_tsv,
        dry_run=args.dry_run,
    )

    return 0 if stats.get("failed_posts", 0) == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
