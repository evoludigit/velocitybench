#!/usr/bin/env python
"""
Load blog posts into PostgreSQL for VelocityBench framework benchmarking.

Generates 5000 realistic users with Faker, parses 2243 markdown blog posts,
and loads them into tb_user and tb_post tables using PostgreSQL COPY.

Usage:
    python load_blog_posts.py --connection "postgresql://user:pass@localhost/db"
    python load_blog_posts.py --users 500 --connection "postgresql://..."
    python load_blog_posts.py --dry-run
    python load_blog_posts.py --generate-only --output output/sql/03-data-blog.sql
"""

from __future__ import annotations

import argparse
import random
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
import sys

try:
    from faker import Faker
    import psycopg
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Install with: pip install faker psycopg")
    sys.exit(1)

# Import our markdown parser
from markdown_parser import extract_blog_metadata


class BlogPostLoader:
    """Loader for blog posts with Faker-generated users."""

    def __init__(self, num_users: int = 5000, output_dir: Path | None = None):
        """
        Initialize blog post loader.

        Args:
            num_users: Number of users to generate (default 5000)
            output_dir: Directory for TSV output files (default: /tmp)
        """
        self.num_users = num_users
        self.output_dir = output_dir or Path('/tmp')

        # Initialize Faker with reproducible seed
        self.fake = Faker()
        Faker.seed(42)
        random.seed(42)

        # Blog posts directory
        self.blog_dir = Path(__file__).parent.parent / 'output' / 'blog'

        # Statistics
        self.stats = {
            'users_generated': 0,
            'total_files': 0,
            'parsed': 0,
            'failed': 0,
            'loaded': 0,
            'duration': 0,
        }

    def generate_users(self) -> List[dict]:
        """
        Generate realistic users with Faker.

        Returns:
            List of user dicts with: pk_user, id, email, username, first_name,
                                     last_name, bio, is_active, created_at, updated_at
        """
        print(f"Generating {self.num_users} users with Faker...", flush=True)
        start = time.time()

        users = []
        used_usernames = set()  # Track used usernames to ensure uniqueness

        for i in range(self.num_users):
            # Generate user data
            email = self.fake.unique.email()
            username = email.split('@')[0]  # Use email prefix as username

            # Ensure username is unique (append number if needed)
            if username in used_usernames:
                counter = 1
                while f"{username}{counter}" in used_usernames:
                    counter += 1
                username = f"{username}{counter}"

            used_usernames.add(username)
            full_name = self.fake.name()

            # Split name into first/last (handle single names)
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[-1] if len(name_parts) > 1 else ""

            # Generate bio (70% of users have a bio)
            bio = self.fake.text(max_nb_chars=200) if random.random() > 0.3 else None

            user = {
                'pk_user': i + 1,  # 1-indexed
                'id': str(uuid.uuid4()),
                'email': email,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'bio': bio,
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
            }
            users.append(user)

        elapsed = time.time() - start
        self.stats['users_generated'] = len(users)
        print(f"✓ Generated {len(users)} users in {elapsed:.2f}s")

        return users

    def discover_posts(self) -> List[Path]:
        """
        Find all markdown files in blog output directory.

        Returns:
            List of Path objects to markdown files
        """
        print(f"Discovering blog posts in {self.blog_dir}...", flush=True)

        if not self.blog_dir.exists():
            print(f"Error: Blog directory not found: {self.blog_dir}")
            return []

        # Find all .md files recursively
        md_files = list(self.blog_dir.rglob('*.md'))
        self.stats['total_files'] = len(md_files)

        print(f"✓ Found {len(md_files)} markdown files")
        return md_files

    def assign_author(self, post_index: int) -> int:
        """
        Assign author to post using round-robin distribution.

        Args:
            post_index: Index of post (0-based)

        Returns:
            pk_user (1-indexed)
        """
        # Round-robin across all users
        return 1 + (post_index % self.num_users)

    def parse_post(self, file_path: Path, post_index: int) -> dict | None:
        """
        Parse markdown file and prepare post data.

        Args:
            file_path: Path to markdown file
            post_index: Index for pk_post (0-based, will be 1-indexed)

        Returns:
            Post dict ready for tb_post table, or None if parse fails
        """
        metadata = extract_blog_metadata(file_path)

        if not metadata:
            return None

        # Prepare post data
        post = {
            'pk_post': post_index + 1,  # 1-indexed
            'id': str(uuid.uuid4()),
            'title': metadata['title'],
            'content': metadata['content'],
            'excerpt': metadata['excerpt'],
            'fk_author': self.assign_author(post_index),
            'status': 'published',
            'published_at': metadata['published_at'],
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }

        return post

    def generate_users_tsv(self, users: List[dict]) -> Path:
        """
        Generate TSV file for tb_user table.

        Args:
            users: List of user dicts

        Returns:
            Path to generated TSV file
        """
        print(f"Generating users TSV file...", flush=True)

        tsv_path = self.output_dir / 'blog_users.tsv'

        with open(tsv_path, 'w', encoding='utf-8') as f:
            for user in users:
                # Format: pk_user\tid\temail\tusername\tfirst_name\tlast_name\tbio\tis_active\tcreated_at\tupdated_at
                row = [
                    str(user['pk_user']),
                    user['id'],
                    user['email'],
                    user['username'],
                    user['first_name'],
                    user['last_name'],
                    user['bio'] if user['bio'] else '\\N',  # NULL for None
                    'true' if user['is_active'] else 'false',
                    user['created_at'].isoformat(),
                    user['updated_at'].isoformat(),
                ]

                # Escape special characters for TSV
                row = [self._escape_tsv(str(v)) for v in row]

                f.write('\t'.join(row) + '\n')

        print(f"✓ Generated {tsv_path}")
        return tsv_path

    def generate_posts_tsv(self, posts: List[dict]) -> Path:
        """
        Generate TSV file for tb_post table.

        Args:
            posts: List of post dicts

        Returns:
            Path to generated TSV file
        """
        print(f"Generating posts TSV file...", flush=True)

        tsv_path = self.output_dir / 'blog_posts.tsv'

        with open(tsv_path, 'w', encoding='utf-8') as f:
            for post in posts:
                # Format: pk_post\tid\ttitle\tcontent\texcerpt\tfk_author\tstatus\tpublished_at\tcreated_at\tupdated_at
                row = [
                    str(post['pk_post']),
                    post['id'],
                    post['title'],
                    post['content'],
                    post['excerpt'] if post['excerpt'] else '\\N',
                    str(post['fk_author']),
                    post['status'],
                    post['published_at'].isoformat(),
                    post['created_at'].isoformat(),
                    post['updated_at'].isoformat(),
                ]

                # Escape special characters for TSV
                row = [self._escape_tsv(str(v)) for v in row]

                f.write('\t'.join(row) + '\n')

        print(f"✓ Generated {tsv_path}")
        return tsv_path

    @staticmethod
    def _escape_tsv(value: str) -> str:
        """
        Escape special characters for PostgreSQL TSV COPY format.

        Args:
            value: String value to escape

        Returns:
            Escaped string
        """
        # Replace backslashes first
        value = value.replace('\\', '\\\\')

        # Escape tabs and newlines
        value = value.replace('\t', '\\t')
        value = value.replace('\n', '\\n')
        value = value.replace('\r', '\\r')

        return value

    def load_to_postgres(self, users_tsv: Path, posts_tsv: Path, connection_string: str) -> bool:
        """
        Load TSV files to PostgreSQL using COPY command.

        Args:
            users_tsv: Path to users TSV file
            posts_tsv: Path to posts TSV file
            connection_string: PostgreSQL connection string

        Returns:
            True if successful, False otherwise
        """
        print(f"Loading data to PostgreSQL...", flush=True)

        try:
            with psycopg.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    # Load users first (no FK dependencies)
                    print(f"  Loading {self.stats['users_generated']} users...", flush=True)
                    with open(users_tsv, 'r', encoding='utf-8') as f:
                        with cur.copy("COPY benchmark.tb_user (pk_user, id, email, username, first_name, last_name, bio, is_active, created_at, updated_at) FROM STDIN") as copy:
                            for line in f:
                                copy.write(line.encode('utf-8'))

                    # Load posts (FK to users already loaded, so no FK violations)
                    print(f"  Loading {self.stats['parsed']} posts...", flush=True)
                    with open(posts_tsv, 'r', encoding='utf-8') as f:
                        with cur.copy("COPY benchmark.tb_post (pk_post, id, title, content, excerpt, fk_author, status, published_at, created_at, updated_at) FROM STDIN") as copy:
                            for line in f:
                                copy.write(line.encode('utf-8'))

                    # Validate row counts
                    cur.execute("SELECT COUNT(*) FROM benchmark.tb_user;")
                    user_count = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM benchmark.tb_post;")
                    post_count = cur.fetchone()[0]

                    conn.commit()

                    print(f"✓ Loaded {user_count} users, {post_count} posts")
                    self.stats['loaded'] = post_count

                    return user_count == self.stats['users_generated'] and post_count == self.stats['parsed']

        except Exception as e:
            print(f"❌ Error loading to PostgreSQL: {e}")
            return False

    def run(self, connection_string: str | None = None, dry_run: bool = False) -> dict:
        """
        Main workflow: generate users, parse posts, load to database.

        Args:
            connection_string: PostgreSQL connection string (None for TSV-only mode)
            dry_run: If True, only validate files without loading

        Returns:
            Statistics dict
        """
        start_time = time.time()

        # Step 1: Generate users
        users = self.generate_users()

        # Step 2: Discover markdown files
        md_files = self.discover_posts()

        if not md_files:
            print("No markdown files found. Exiting.")
            return self.stats

        # Step 3: Parse each file
        print(f"Parsing {len(md_files)} markdown files...", flush=True)
        posts = []

        for i, md_file in enumerate(md_files):
            post = self.parse_post(md_file, i)

            if post:
                posts.append(post)
                self.stats['parsed'] += 1
            else:
                self.stats['failed'] += 1
                print(f"  Warning: Failed to parse {md_file.name}")

            # Progress indicator every 100 files
            if (i + 1) % 100 == 0:
                print(f"  Parsed {i + 1}/{len(md_files)} files...", flush=True)

        print(f"✓ Parsed {self.stats['parsed']} posts ({self.stats['failed']} failed)")

        # Step 4: Generate TSV files
        users_tsv = self.generate_users_tsv(users)
        posts_tsv = self.generate_posts_tsv(posts)

        # Step 5: Load to PostgreSQL (unless dry run or TSV-only mode)
        if dry_run:
            print("\n⚠️  DRY RUN - No database loading")
        elif connection_string:
            success = self.load_to_postgres(users_tsv, posts_tsv, connection_string)
            if not success:
                print("❌ Database loading failed")
        else:
            print("\n⚠️  TSV-only mode (no database connection)")

        # Calculate duration
        self.stats['duration'] = time.time() - start_time

        # Print summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Users generated: {self.stats['users_generated']:,}")
        print(f"Files discovered: {self.stats['total_files']:,}")
        print(f"Posts parsed: {self.stats['parsed']:,}")
        print(f"Parse failures: {self.stats['failed']:,}")
        if connection_string and not dry_run:
            print(f"Posts loaded: {self.stats['loaded']:,}")
        print(f"Duration: {self.stats['duration']:.2f}s")
        print(f"\nTSV files:")
        print(f"  Users: {users_tsv}")
        print(f"  Posts: {posts_tsv}")

        return self.stats


def main():
    parser = argparse.ArgumentParser(
        description="Load blog posts into PostgreSQL for VelocityBench",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load to database (default: 5000 users)
  python load_blog_posts.py --connection "postgresql://user:pass@localhost/db"

  # Custom user count (for testing)
  python load_blog_posts.py --users 500 --connection "postgresql://..."

  # Dry run (validate only, no database load)
  python load_blog_posts.py --dry-run

  # Generate TSV only (no database load)
  python load_blog_posts.py --generate-only --output output/sql
        """
    )

    parser.add_argument(
        '--users',
        type=int,
        default=5000,
        help='Number of users to generate (default: 5000)'
    )

    parser.add_argument(
        '--connection',
        type=str,
        help='PostgreSQL connection string (e.g., postgresql://user:pass@localhost/db)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate files without loading to database'
    )

    parser.add_argument(
        '--generate-only',
        action='store_true',
        help='Generate TSV files only (no database load)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path('/tmp'),
        help='Output directory for TSV files (default: /tmp)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.generate_only and not args.connection:
        parser.error("Either --connection, --dry-run, or --generate-only is required")

    # Run loader
    loader = BlogPostLoader(
        num_users=args.users,
        output_dir=args.output
    )

    connection_string = args.connection if not args.generate_only else None
    stats = loader.run(connection_string=connection_string, dry_run=args.dry_run)

    # Exit with status code
    if stats['failed'] > 0:
        print(f"\n⚠️  Warning: {stats['failed']} files failed to parse")
        sys.exit(1)

    print("\n✅ Success!")
    sys.exit(0)


if __name__ == '__main__':
    main()
