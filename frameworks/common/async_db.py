"""
Shared async database pool for all Python frameworks.

Provides connection pooling with asyncpg, statement caching,
and unified interface for database operations.

Features:
- Connection pool with configurable min/max sizes
- Prepared statement caching
- Metrics collection (connection utilization, wait times)
- Automatic connection lifecycle management
"""

import asyncpg
import os
import time
from contextlib import asynccontextmanager
from typing import Any
import logging

logger = logging.getLogger(__name__)


class PoolMetrics:
    """Track connection pool usage metrics."""

    def __init__(self) -> None:
        self.total_connections_acquired = 0
        self.total_connections_released = 0
        self.max_concurrent_connections = 0
        self.current_concurrent_connections = 0
        self.total_wait_time_ms = 0
        self.statement_cache_hits = 0
        self.statement_cache_misses = 0

    def record_acquire(self) -> None:
        self.total_connections_acquired += 1
        self.current_concurrent_connections += 1
        self.max_concurrent_connections = max(
            self.max_concurrent_connections, self.current_concurrent_connections
        )

    def record_release(self) -> None:
        self.current_concurrent_connections = max(
            0, self.current_concurrent_connections - 1
        )
        self.total_connections_released += 1

    def record_wait(self, wait_time_ms: float) -> None:
        self.total_wait_time_ms += wait_time_ms

    def record_statement_hit(self) -> None:
        self.statement_cache_hits += 1

    def record_statement_miss(self) -> None:
        self.statement_cache_misses += 1

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary for logging/monitoring."""
        total_statements = self.statement_cache_hits + self.statement_cache_misses
        cache_hit_rate = (
            (self.statement_cache_hits / total_statements * 100)
            if total_statements > 0
            else 0
        )

        return {
            "connections_acquired": self.total_connections_acquired,
            "connections_released": self.total_connections_released,
            "max_concurrent": self.max_concurrent_connections,
            "current_concurrent": self.current_concurrent_connections,
            "avg_wait_time_ms": (
                self.total_wait_time_ms / self.total_connections_acquired
                if self.total_connections_acquired > 0
                else 0
            ),
            "statement_cache_hit_rate_pct": cache_hit_rate,
        }


class AsyncDatabase:
    """
    Shared async database pool for Python frameworks.

    Provides:
    - Connection pooling via asyncpg
    - Statement caching (100 prepared statements)
    - Metrics collection
    - Unified interface (fetch, fetchrow, execute, etc.)
    """

    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None
        self.metrics = PoolMetrics()
        self._connection_semaphore: asyncpg.pool.Pool | None = None

    async def connect(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        min_size: int = 10,
        max_size: int = 50,
        statement_cache_size: int = 100,
        max_cached_statement_lifetime: int = 300,
    ) -> None:
        """
        Initialize connection pool with production settings.

        Args:
            host: Database host (defaults to DB_HOST env var)
            port: Database port (defaults to DB_PORT env var)
            database: Database name (defaults to DB_NAME env var)
            user: Database user (defaults to DB_USER env var)
            password: Database password (defaults to DB_PASSWORD env var)
            min_size: Minimum pool size (default 10)
            max_size: Maximum pool size (default 50)
            statement_cache_size: Prepared statement cache (default 100)
            max_cached_statement_lifetime: Cache lifetime in seconds (default 300)
        """
        # Get connection parameters from args or environment
        host = host or os.getenv("DB_HOST", "postgres")
        port = port if port is not None else int(os.getenv("DB_PORT", "5432"))
        database = database or os.getenv("DB_NAME", "velocitybench_benchmark")
        user = user or os.getenv("DB_USER", "benchmark")

        # Password is REQUIRED - fail fast if not provided
        if not password:
            password = os.getenv("DB_PASSWORD")
            if not password:
                raise ValueError(
                    "Database password is required. "
                    "Set DB_PASSWORD environment variable."
                )

        logger.info(
            f"Creating asyncpg pool: {user}@{host}:{port}/{database} "
            f"(min={min_size}, max={max_size})"
        )

        try:
            self.pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                min_size=min_size,
                max_size=max_size,
                command_timeout=30,
                # Performance tuning
                statement_cache_size=statement_cache_size,
                max_cached_statement_lifetime=max_cached_statement_lifetime,
                # Connection initialization
                init=self._init_connection,
            )
            logger.info("✅ Connection pool created successfully")
        except (asyncpg.PostgresError, ConnectionError, TimeoutError, OSError) as e:
            logger.error(f"❌ Failed to create connection pool: {e}")
            raise

    async def _init_connection(self, conn: asyncpg.Connection) -> None:
        """Initialize each new connection with performance settings."""
        await conn.execute("SET application_name = 'fraiseql-benchmark';")

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            logger.info("Closing connection pool...")
            await self.pool.close()
            logger.info("✅ Connection pool closed")
            self._print_metrics()

    def _print_metrics(self) -> None:
        """Print metrics summary at shutdown."""
        summary = self.metrics.get_summary()
        logger.info("📊 Connection Pool Metrics:")
        for key, value in summary.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")

    async def fetch(
        self, query: str, *args, timeout: float | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute query and return results as list of dicts.

        Args:
            query: SQL query with $1, $2, etc. placeholders
            *args: Query parameters
            timeout: Query timeout in seconds

        Returns:
            List of result dictionaries
        """
        if not self.pool:
            raise RuntimeError("Database pool not connected")

        start_time = time.time()
        self.metrics.record_acquire()

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args, timeout=timeout)
                # Convert Record objects to dicts for consistency
                return [dict(row) for row in rows]
        finally:
            wait_time = (time.time() - start_time) * 1000
            self.metrics.record_release()
            self.metrics.record_wait(wait_time)

    async def fetchrow(
        self, query: str, *args, timeout: float | None = None
    ) -> dict[str, Any] | None:
        """
        Execute query and return single row as dict.

        Args:
            query: SQL query with $1, $2, etc. placeholders
            *args: Query parameters
            timeout: Query timeout in seconds

        Returns:
            Single result dictionary or None
        """
        if not self.pool:
            raise RuntimeError("Database pool not connected")

        start_time = time.time()
        self.metrics.record_acquire()

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args, timeout=timeout)
                return dict(row) if row else None
        finally:
            wait_time = (time.time() - start_time) * 1000
            self.metrics.record_release()
            self.metrics.record_wait(wait_time)

    async def fetchval(self, query: str, *args, timeout: float | None = None) -> Any:
        """
        Execute query and return single scalar value.

        Args:
            query: SQL query with $1, $2, etc. placeholders
            *args: Query parameters
            timeout: Query timeout in seconds

        Returns:
            Single scalar value
        """
        if not self.pool:
            raise RuntimeError("Database pool not connected")

        start_time = time.time()
        self.metrics.record_acquire()

        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args, timeout=timeout)
        finally:
            wait_time = (time.time() - start_time) * 1000
            self.metrics.record_release()
            self.metrics.record_wait(wait_time)

    async def execute(self, query: str, *args, timeout: float | None = None) -> str:
        """
        Execute query without returning results.

        Args:
            query: SQL query with $1, $2, etc. placeholders
            *args: Query parameters
            timeout: Query timeout in seconds

        Returns:
            Command completion status
        """
        if not self.pool:
            raise RuntimeError("Database pool not connected")

        start_time = time.time()
        self.metrics.record_acquire()

        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args, timeout=timeout)
        finally:
            wait_time = (time.time() - start_time) * 1000
            self.metrics.record_release()
            self.metrics.record_wait(wait_time)

    async def executemany(self, query: str, args, timeout: float | None = None) -> None:
        """
        Execute query multiple times with different parameter sets.

        Args:
            query: SQL query with $1, $2, etc. placeholders
            args: List of parameter tuples
            timeout: Query timeout in seconds
        """
        if not self.pool:
            raise RuntimeError("Database pool not connected")

        start_time = time.time()
        self.metrics.record_acquire()

        try:
            async with self.pool.acquire() as conn:
                return await conn.executemany(query, args, timeout=timeout)
        finally:
            wait_time = (time.time() - start_time) * 1000
            self.metrics.record_release()
            self.metrics.record_wait(wait_time)

    @asynccontextmanager
    async def transaction(self):
        """
        Start a transaction context manager.

        Usage:
            async with db.transaction():
                await db.execute("INSERT ...")
                await db.execute("UPDATE ...")
        """
        if not self.pool:
            raise RuntimeError("Database pool not connected")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics snapshot."""
        return self.metrics.get_summary()

    def get_pool_info(self) -> dict[str, Any]:
        """Get connection pool information."""
        if not self.pool:
            return {"status": "not_connected"}

        return {
            "status": "connected",
            "min_size": self.pool.get_min_size(),
            "max_size": self.pool.get_max_size(),
            "free_connections": self.pool.get_size(),
            "size": self.pool.get_size(),
        }


# Global instance for shared use
_db_instance: AsyncDatabase | None = None


def get_database() -> AsyncDatabase:
    """Get or create global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = AsyncDatabase()
    return _db_instance


async def initialize_database(
    min_size: int = 10, max_size: int = 50, **kwargs
) -> AsyncDatabase:
    """Initialize and return global database instance."""
    db = get_database()
    await db.connect(min_size=min_size, max_size=max_size, **kwargs)
    return db


async def close_database():
    """Close global database instance."""
    if _db_instance:
        await _db_instance.close()
