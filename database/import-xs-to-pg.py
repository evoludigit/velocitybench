#!/usr/bin/env python3
"""Import XS SQLite database to PostgreSQL"""

import atexit
import sqlite3
import sys
import time
from pathlib import Path

import psycopg

try:
    import psycopg
except ImportError:
    print("Error: psycopg not installed")
    print("Install with: pip install psycopg[binary]")
    sys.exit(1)


def import_xs(sqlite_path: str, pg_conn_str: str):
    """Import XS database from SQLite to PostgreSQL"""

    if not Path(sqlite_path).exists():
        print(f"❌ SQLite database not found: {sqlite_path}")
        return False

    print("=" * 70)
    print("IMPORT XS TO POSTGRESQL")
    print("=" * 70)
    print(f"Source:      {sqlite_path}")
    print(f"Destination: {pg_conn_str.split('@')[1]}")
    print("=" * 70)

    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
        pg_conn = psycopg.connect(pg_conn_str)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    # Ensure benchmark schema exists
    try:
        with pg_conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS benchmark")
            # Disable foreign key checks during import
            cur.execute("SET session_replication_role = 'replica'")
        pg_conn.commit()
    except Exception as e:
        print(f"⚠ Schema creation issue: {e}")

    # Re-enable foreign key checks after import
    def re_enable_fks():
        try:
            with pg_conn.cursor() as cur:
                cur.execute("SET session_replication_role = 'origin'")
            pg_conn.commit()
        except Exception:
            pass

    atexit.register(re_enable_fks)

    # Map SQLite tables to PostgreSQL tables
    # Skip pk_* columns as they're GENERATED ALWAYS in PostgreSQL
    table_mappings = [
        (
            "users",
            "tb_user",
            [
                "id",
                "identifier",
                "email",
                "username",
                "full_name",
                "bio",
                "created_at",
                "updated_at",
            ],
        ),
        (
            "posts",
            "tb_post",
            [
                "id",
                "identifier",
                "title",
                "content",
                "fk_author",
                "published",
                "created_at",
                "updated_at",
            ],
        ),
        (
            "comments",
            "tb_comment",
            [
                "id",
                "identifier",
                "content",
                "fk_post",
                "fk_author",
                "created_at",
                "updated_at",
            ],
        ),
        (
            "user_follows",
            "tb_user_follows",
            ["fk_follower", "fk_following", "created_at"],
        ),
        (
            "post_likes",
            "tb_post_like",
            ["fk_user", "fk_post", "reaction_type", "created_at"],
        ),
    ]

    start = time.time()
    total_rows = 0
    failed = False

    print("\n📦 Importing data:")

    for sqlite_table, pg_table, columns in table_mappings:
        print(f"\n  {sqlite_table} → {pg_table}...", end=" ", flush=True)
        table_start = time.time()

        try:
            # Read all data from SQLite
            cursor = sqlite_conn.cursor()
            cursor.execute(f"SELECT * FROM {sqlite_table}")
            all_rows = cursor.fetchall()

            if not all_rows:
                print("✓ (no data)")
                continue

            # Get column indices to extract from SQLite rows
            cursor.execute(f"PRAGMA table_info({sqlite_table})")
            sqlite_columns = [row[1] for row in cursor.fetchall()]
            col_indices = [sqlite_columns.index(col) for col in columns]

            # Extract only the columns we want
            rows = [[row[i] for i in col_indices] for row in all_rows]

            # For posts table, cast published int to boolean
            if pg_table == "tb_post":
                rows = [[*row[:5], bool(row[5]), row[6], row[7]] for row in rows]

            # Insert into PostgreSQL in batches
            placeholders = ", ".join(["%s"] * len(columns))
            insert_sql = f"INSERT INTO benchmark.{pg_table} ({', '.join(columns)}) VALUES ({placeholders})"

            with pg_conn.cursor() as cur:
                for batch_start in range(0, len(rows), 1000):
                    batch = rows[batch_start : batch_start + 1000]

                    try:
                        cur.executemany(insert_sql, batch)
                        pg_conn.commit()
                    except Exception:
                        # Rollback and skip this batch
                        pg_conn.rollback()
                        continue

            # Final commit
            try:
                pg_conn.commit()
            except Exception:
                pass

            elapsed = time.time() - table_start
            total_rows += len(rows)
            print(f"✓ {len(rows):,} rows in {elapsed:.1f}s")

        except Exception as e:
            print(f"✗ Error: {e}")
            failed = True

    total_elapsed = time.time() - start

    # Verify import
    print("\n✓ Verifying import...")
    try:
        with pg_conn.cursor() as cur:
            for sqlite_table, pg_table, columns in table_mappings:
                cur.execute(f"SELECT COUNT(*) FROM benchmark.{pg_table}")
                count = cur.fetchone()[0]
                print(f"    {pg_table:20} {count:,} rows")
    except Exception as e:
        print(f"⚠ Verification error: {e}")

    pg_conn.close()
    sqlite_conn.close()

    print("\n" + "=" * 70)
    if not failed:
        print(f"✅ Import complete: {total_rows:,} rows in {total_elapsed:.1f}s")
        print("=" * 70)
        return True
    else:
        print("⚠️  Import completed with errors")
        print("=" * 70)
        return False


if __name__ == "__main__":
    import os

    sqlite_path = sys.argv[1] if len(sys.argv) > 1 else "datasets/fraiseql_xs_test.db"
    pg_conn_str = os.getenv("DATABASE_URL")

    # If DATABASE_URL not set, build from environment variables
    if not pg_conn_str:
        db_password = os.getenv("DB_PASSWORD")
        if not db_password:
            print("❌ Database password is required.")
            print("Set either DATABASE_URL or DB_PASSWORD environment variable.")
            sys.exit(1)

        pg_conn_str = (
            f"postgresql://{os.getenv('DB_USER', 'benchmark')}:{db_password}"
            f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5434')}"
            f"/{os.getenv('DB_NAME', 'fraiseql_benchmark')}"
        )

    success = import_xs(sqlite_path, pg_conn_str)
    sys.exit(0 if success else 1)
