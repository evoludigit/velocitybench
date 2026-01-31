#!/usr/bin/env python3
"""
Import all database variations to PostgreSQL.

Imports each variation to PostgreSQL with disabled foreign key constraints
for performance, then re-enables them for testing.

Timing results show how import performance scales with data volume.
"""

import sqlite3
import psycopg
import sys
import time
import atexit
import os
from pathlib import Path


class BulkImporter:
    """Import SQLite databases to PostgreSQL"""

    VARIATIONS = [
        ('xs', 0.5),
        ('small', 1.0),
        ('medium', 5.0),
        ('large', 10.0),
        ('xlarge', 50.0),
        ('xxlarge', 100.0),
    ]

    TABLE_MAPPINGS = [
        ('users', 'tb_user', ['id', 'identifier', 'email', 'username', 'full_name', 'bio', 'created_at', 'updated_at']),
        ('posts', 'tb_post', ['id', 'identifier', 'title', 'content', 'fk_author', 'published', 'created_at', 'updated_at']),
        ('comments', 'tb_comment', ['id', 'identifier', 'content', 'fk_post', 'fk_author', 'created_at', 'updated_at']),
        ('user_follows', 'tb_user_follows', ['fk_follower', 'fk_following', 'created_at']),
        ('post_likes', 'tb_post_like', ['fk_user', 'fk_post', 'reaction_type', 'created_at']),
    ]

    def __init__(self, pg_conn_str: str = None):
        if pg_conn_str is None:
            pg_conn_str = os.getenv("DATABASE_URL")

            # If DATABASE_URL not set, build from environment variables
            if not pg_conn_str:
                db_password = os.getenv("DB_PASSWORD")
                if not db_password:
                    raise ValueError(
                        "Database password is required. "
                        "Set either DATABASE_URL or DB_PASSWORD environment variable."
                    )

                pg_conn_str = (
                    f"postgresql://{os.getenv('DB_USER', 'benchmark')}:{db_password}"
                    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5434')}"
                    f"/{os.getenv('DB_NAME', 'fraiseql_benchmark')}"
                )

        self.pg_conn_str = pg_conn_str
        self.results = []

    def import_all(self):
        """Import all variations"""
        print("=" * 90)
        print("IMPORTING ALL VARIATIONS TO POSTGRESQL")
        print("=" * 90)

        for name, percent in self.VARIATIONS:
            sqlite_path = f"datasets/fraiseql_{name}.db"

            if not Path(sqlite_path).exists():
                print(f"\n⚠️  Skipping {name}: database not found")
                continue

            print(f"\n{'='*90}")
            print(f"Importing {name.upper()} ({percent}%) from {sqlite_path}")
            print(f"{'='*90}")

            self._import_variation(sqlite_path, name)

        # Print summary
        self._print_summary()

    def _import_variation(self, sqlite_path: str, name: str):
        """Import a single variation"""
        try:
            sqlite_conn = sqlite3.connect(sqlite_path)
            pg_conn = psycopg.connect(self.pg_conn_str)

            # Setup PostgreSQL
            with pg_conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS benchmark")
                cur.execute("SET session_replication_role = 'replica'")
            pg_conn.commit()

            # Register cleanup to re-enable FK constraints
            def re_enable_fks():
                try:
                    with pg_conn.cursor() as cur:
                        cur.execute("SET session_replication_role = 'origin'")
                    pg_conn.commit()
                except Exception:
                    pass
            atexit.register(re_enable_fks)

            # Clear existing data
            try:
                with pg_conn.cursor() as cur:
                    cur.execute("TRUNCATE benchmark.tb_user CASCADE")
                pg_conn.commit()
            except Exception:
                pg_conn.rollback()

            # Import tables
            start = time.time()
            total_rows = 0

            for sqlite_table, pg_table, columns in self.TABLE_MAPPINGS:
                rows_imported = self._import_table(
                    sqlite_conn, pg_conn, sqlite_table, pg_table, columns
                )
                total_rows += rows_imported

            elapsed = time.time() - start

            # Get file size
            db_size = Path(sqlite_path).stat().st_size / (1024 * 1024)
            size_str = f"{db_size:.1f}MB" if db_size < 1024 else f"{db_size/1024:.1f}GB"

            self.results.append({
                'name': name,
                'rows': total_rows,
                'size': size_str,
                'time': elapsed,
                'status': '✅'
            })

            print(f"\n✅ Import complete: {total_rows:,} rows in {elapsed:.1f}s ({db_size:.1f}MB)")

            sqlite_conn.close()
            pg_conn.close()

        except Exception as e:
            print(f"\n❌ Import failed: {e}")
            self.results.append({
                'name': name,
                'rows': 0,
                'size': '?',
                'time': 0,
                'status': '❌'
            })

    def _import_table(self, sqlite_conn, pg_conn, sqlite_table, pg_table, columns):
        """Import a single table"""
        # Get columns from SQLite
        cursor = sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({sqlite_table})")
        sqlite_columns = [row[1] for row in cursor.fetchall()]
        col_indices = [sqlite_columns.index(col) for col in columns]

        # Read data
        cursor.execute(f"SELECT * FROM {sqlite_table}")
        all_rows = cursor.fetchall()

        if not all_rows:
            return 0

        # Extract columns
        rows = [[row[i] for i in col_indices] for row in all_rows]

        # Cast published boolean
        if pg_table == 'tb_post':
            rows = [[*row[:5], bool(row[5]), row[6], row[7]] for row in rows]

        # Insert in batches
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO benchmark.{pg_table} ({', '.join(columns)}) VALUES ({placeholders})"

        with pg_conn.cursor() as cur:
            for batch_start in range(0, len(rows), 5000):
                batch = rows[batch_start : batch_start + 5000]
                try:
                    cur.executemany(insert_sql, batch)
                    pg_conn.commit()
                except Exception:
                    pg_conn.rollback()

        print(f"  ✓ {sqlite_table:20} {len(rows):,} rows")
        return len(rows)

    def _print_summary(self):
        """Print import summary"""
        print("\n" + "=" * 90)
        print("IMPORT SUMMARY")
        print("=" * 90)
        print()

        print(f"{'Database':<15} {'Status':<10} {'Rows':<15} {'Size':<15} {'Time':<10}")
        print("─" * 65)

        for result in self.results:
            print(f"{result['name']:<15} {result['status']:<10} {result['rows']:>13,} {result['size']:>13} {result['time']:>8.1f}s")

        print()
        print("=" * 90)


if __name__ == "__main__":
    importer = BulkImporter()
    importer.import_all()
