#!/usr/bin/env python3
"""
Generate a CSV file with random post IDs from the database.
Used as test data for the blog-page JMeter workload.

Usage:
    python generate-post-ids.py [--count 1000] [--output ../data/post_ids.csv]
"""

import argparse
import os
import sys

# Add database common module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "frameworks", "common"))

try:
    import psycopg
except ImportError:
    print("Error: psycopg not installed. Run: pip install psycopg[binary]")
    sys.exit(1)


def get_connection_string() -> str:
    """Build PostgreSQL connection string from environment variables."""
    host = os.getenv("DATABASE_HOST", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")
    dbname = os.getenv("DATABASE_NAME", "fraiseql_benchmark")
    user = os.getenv("DATABASE_USER", "benchmark")
    password = os.getenv("DATABASE_PASSWORD", "benchmark123")
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


def generate_post_ids(count: int, output_path: str):
    """Fetch random post IDs from database and write to CSV."""
    conn_string = get_connection_string()

    print("Connecting to database...")
    print(f"Connection: {conn_string.replace(os.getenv('DATABASE_PASSWORD', 'benchmark123'), '***')}")

    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Get total post count
                cur.execute("SELECT COUNT(*) FROM benchmark.tb_post WHERE published = true")
                total_posts = cur.fetchone()[0]
                print(f"Total published posts in database: {total_posts}")

                if total_posts == 0:
                    print("Error: No posts found in database. Run seed script first.")
                    sys.exit(1)

                # Adjust count if necessary
                actual_count = min(count, total_posts)
                if actual_count < count:
                    print(f"Warning: Only {total_posts} posts available, using {actual_count}")

                # Fetch random post IDs
                cur.execute("""
                    SELECT id
                    FROM benchmark.tb_post
                    WHERE published = true
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (actual_count,))

                post_ids = [row[0] for row in cur.fetchall()]
                print(f"Fetched {len(post_ids)} random post IDs")

                # Write to CSV
                with open(output_path, 'w') as f:
                    f.write("POST_ID\n")
                    for post_id in post_ids:
                        f.write(f"{post_id}\n")

                print(f"Written to: {output_path}")
                print(f"Sample IDs: {post_ids[:5]}...")

    except psycopg.OperationalError as e:
        print(f"Error connecting to database: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'fraiseql_benchmark' exists")
        print("  3. Environment variables are set correctly:")
        print("     - DATABASE_HOST (default: localhost)")
        print("     - DATABASE_PORT (default: 5432)")
        print("     - DATABASE_NAME (default: fraiseql_benchmark)")
        print("     - DATABASE_USER (default: benchmark)")
        print("     - DATABASE_PASSWORD (default: benchmark123)")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate CSV file with random post IDs for JMeter testing"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1000,
        help="Number of post IDs to generate (default: 1000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "data", "post_ids.csv"),
        help="Output CSV file path (default: ../data/post_ids.csv)"
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    generate_post_ids(args.count, args.output)


if __name__ == "__main__":
    main()
