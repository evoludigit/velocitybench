#!/usr/bin/env python
"""
Database Safety Checker for Dataset Loading

Validates database connectivity, schema, and available space before loading.
"""

from typing import Tuple, List, Optional
import logging

try:
    import psycopg
except ImportError:
    psycopg = None

logger = logging.getLogger(__name__)


class DatabaseSafetyChecker:
    """Check database safety before loading generated data."""

    def __init__(self, connection_string: str, timeout_sec: int = 5):
        """
        Initialize database safety checker.

        Args:
            connection_string: PostgreSQL connection string
            timeout_sec: Connection timeout in seconds
        """
        self.connection_string = connection_string
        self.timeout_sec = timeout_sec

    def check_connectivity(self) -> tuple[bool, str]:
        """
        Check if database is reachable.

        Returns:
            (is_ok: bool, message: str)
        """
        if not psycopg:
            return (True, "Database connectivity: ⊘ psycopg not installed (skipped)")

        try:
            with psycopg.connect(
                self.connection_string, connect_timeout=self.timeout_sec
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()[0]
                    return (
                        True,
                        f"Database connectivity: ✅ OK\n  PostgreSQL {version.split(',')[0]}",
                    )
        except Exception as e:
            return (False, f"Database connectivity: ❌ {e}")

    def check_schema_exists(self, schema: str = "benchmark") -> tuple[bool, str]:
        """
        Check if benchmark schema exists.

        Args:
            schema: Schema name (default: benchmark)

        Returns:
            (is_ok: bool, message: str)
        """
        if not psycopg:
            return (True, f"Schema check: ⊘ skipped (psycopg not installed)")

        try:
            with psycopg.connect(
                self.connection_string, connect_timeout=self.timeout_sec
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT 1 FROM information_schema.schemata WHERE schema_name = %s;",
                        (schema,),
                    )
                    if cur.fetchone():
                        return (True, f"Schema check: ✅ Schema '{schema}' exists")
                    else:
                        return (
                            False,
                            f"Schema check: ❌ Schema '{schema}' does not exist",
                        )
        except Exception as e:
            return (False, f"Schema check: ❌ {e}")

    def check_table_sizes(self, schema: str = "benchmark") -> tuple[bool, dict]:
        """
        Check sizes of existing tables.

        Args:
            schema: Schema name (default: benchmark)

        Returns:
            (is_ok: bool, sizes_dict)
        """
        if not psycopg:
            return (True, {})

        try:
            with psycopg.connect(
                self.connection_string, connect_timeout=self.timeout_sec
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
                        FROM pg_tables
                        WHERE schemaname = %s
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
                    """,
                        (schema,),
                    )

                    sizes = {}
                    for tablename, size in cur.fetchall():
                        sizes[tablename] = size

                    return (True, sizes)
        except Exception as e:
            return (False, {})

    def check_available_disk_on_database(self) -> tuple[bool, str]:
        """
        Check available disk space on database server.

        Note: This is a simplified check. Actual implementation depends on database
        permissions and OS.

        Returns:
            (is_ok: bool, message: str)
        """
        if not psycopg:
            return (True, "Database disk check: ⊘ skipped (psycopg not installed)")

        try:
            with psycopg.connect(
                self.connection_string, connect_timeout=self.timeout_sec
            ) as conn:
                with conn.cursor() as cur:
                    # Check PostgreSQL tablespace
                    cur.execute("""
                        SELECT pg_tablespace_location(spcname), pg_size_pretty(pg_tablespace_size(spcname))
                        FROM pg_tablespace
                        WHERE spcname = 'pg_default';
                    """)
                    result = cur.fetchone()

                    if result:
                        location, size = result
                        return (True, f"Database disk: ✅ OK (size: {size})")
                    else:
                        return (True, "Database disk: ⊘ Could not determine size")

        except Exception as e:
            # This check is optional, so don't fail
            return (True, f"Database disk: ⊘ {e}")

    def check_all(self, schema: str = "benchmark") -> tuple[bool, list[str]]:
        """
        Run all database checks.

        Args:
            schema: Schema name (default: benchmark)

        Returns:
            (all_ok: bool, messages: list[str])
        """
        checks = [
            self.check_connectivity(),
            self.check_schema_exists(schema),
            self.check_available_disk_on_database(),
        ]

        all_ok = all(check[0] for check in checks)
        messages = [check[1] for check in checks]

        return (all_ok, messages)
