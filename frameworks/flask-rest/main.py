#!/usr/bin/env python3
"""Flask REST Comparative Benchmarking Implementation.

Traditional synchronous REST API using psycopg3 connection pool
(demonstrates N+1 problem).
"""

import os
import sys
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path as PathlibPath
from typing import Any

import prometheus_client
import psutil
import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


# Custom error classes for Flask-REST
class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        self.error_code = "APP_ERROR"
        super().__init__(self.message)

    def to_dict(self):
        return {"error": self.error_code, "message": self.message}


class InputValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, 400)
        self.error_code = "VALIDATION_ERROR"


class ResourceNotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__(message, 404)
        self.error_code = "NOT_FOUND"


# Simple logging middleware for Flask-REST
class FlaskLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Simple logging - just log the request
        print(f"Request: {environ['REQUEST_METHOD']} {environ['PATH_INFO']}")
        return self.app(environ, start_response)


# Simple validator class for Flask-REST
class Validator:
    @staticmethod
    def validate_uuid(value: str, field_name: str) -> str:
        """Validate UUID format"""
        import uuid

        try:
            uuid.UUID(value)
            return value
        except ValueError:
            raise InputValidationError(f"Invalid {field_name}: must be a valid UUID")

    @staticmethod
    def validate_uuid_list(value: str, max_count: int = 100) -> list[str]:
        """Validate comma-separated UUID list"""
        uuids = [uuid.strip() for uuid in value.split(",") if uuid.strip()]
        if len(uuids) > max_count:
            raise InputValidationError(f"Too many UUIDs: maximum {max_count} allowed")
        for uuid in uuids:
            Validator.validate_uuid(uuid, "uuid")
        return uuids

    @staticmethod
    def validate_limit(value: int, min_val: int = 1, max_val: int = 100) -> int:
        """Validate limit parameter"""
        if not isinstance(value, int) or value < min_val or value > max_val:
            raise InputValidationError(f"Limit must be between {min_val} and {max_val}")
        return value

    @staticmethod
    def validate_include_fields(value: str, allowed_includes: list[str]) -> list[str]:
        """Validate include fields"""
        if not value:
            return []
        includes = [inc.strip() for inc in value.split(",") if inc.strip()]
        invalid = [inc for inc in includes if inc not in allowed_includes]
        if invalid:
            raise InputValidationError(
                f"Invalid include fields: {', '.join(invalid)}. Allowed: {', '.join(allowed_includes)}"
            )
        return includes


# Validator class defined above

# Metrics
REQUEST_COUNT = prometheus_client.Counter(
    "flask_rest_requests_total", "Total requests", ["method", "endpoint"]
)
REQUEST_LATENCY = prometheus_client.Histogram(
    "flask_rest_request_duration_seconds", "Request latency", ["method", "endpoint"]
)


app = Flask(__name__)

# Initialize request logging middleware
FlaskLoggingMiddleware(app)

# Health check startup time
app.config["START_TIME"] = time.time()
app.config["VERSION"] = "1.0.0"
app.config["SERVICE_NAME"] = "flask-rest"
app.config["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "development")

# Allowed fields for user updates (whitelist for SQL injection prevention)
ALLOWED_UPDATE_FIELDS = {"full_name", "bio"}


# Validation functions
def validate_update_user_data(data: dict[str, Any]) -> list[dict[str, str]]:
    """Validate user update data and return list of validation errors."""
    errors = []

    # Check for unknown fields
    allowed_fields = ALLOWED_UPDATE_FIELDS
    for field in data:
        if field not in allowed_fields:
            errors.append({"field": field, "error": f"Unknown field: {field}"})

    # Validate full_name
    if "full_name" in data:
        full_name = data["full_name"]
        if not isinstance(full_name, str):
            errors.append({"field": "full_name", "error": "Full name must be a string"})
        elif len(full_name) > 255:
            errors.append(
                {
                    "field": "full_name",
                    "error": "Full name must be at most 255 characters",
                }
            )

    # Validate bio
    if "bio" in data:
        bio = data["bio"]
        if not isinstance(bio, str):
            errors.append({"field": "bio", "error": "Bio must be a string"})
        elif len(bio) > 1000:
            errors.append(
                {"field": "bio", "error": "Bio must be at most 1000 characters"}
            )

    return errors


def init_pool() -> ConnectionPool:
    """Initialize psycopg3 connection pool in app context."""
    # Password is REQUIRED - fail fast if not provided
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise ValueError(
            "Database password is required. Set DB_PASSWORD environment variable."
        )

    conninfo = psycopg.conninfo.make_conninfo(
        host=os.getenv("DB_HOST", "postgres"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "fraiseql_benchmark"),
        user=os.getenv("DB_USER", "benchmark"),
        password=password,
    )

    pool = ConnectionPool(
        conninfo=conninfo,
        min_size=10,
        max_size=50,
        timeout=30.0,
        max_idle=300.0,
        max_lifetime=3600.0,
    )

    app.config["DB_POOL"] = pool
    return pool


@contextmanager
def get_db_connection() -> Any:
    """Get database connection from app context."""
    pool = app.config["DB_POOL"]
    with pool.connection() as conn:
        yield conn


def execute_query(query: str, params: tuple | None = None) -> list[dict[str, Any]]:
    """Execute query and return results."""
    with get_db_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params or ())
        if cur.description:
            return cur.fetchall()
        return []


# Initialize pool before first request
_pool_initialized = False


@app.before_request
def setup_db() -> None:
    """Initialize database pool on first request."""
    global _pool_initialized
    if not _pool_initialized:
        init_pool()
        _pool_initialized = True


# Register cleanup on app teardown
@app.teardown_appcontext
def teardown_db(exception: BaseException | None = None) -> None:
    """Close pool on app shutdown."""
    pool = app.config.get("DB_POOL")
    if pool:
        pool.close()


def _check_database() -> dict[str, Any]:
    """Check database health."""
    try:
        pool = app.config.get("DB_POOL")
        if not pool:
            return {"status": "down", "error": "Database pool not initialized"}

        start = time.time()
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()

        response_time = (time.time() - start) * 1000

        # Get pool stats
        pool_stats = pool.get_stats()

        return {
            "status": "up",
            "response_time_ms": round(response_time, 2),
            "pool_size": pool_stats.get("pool_size", 0),
            "pool_available": pool_stats.get("pool_available", 0),
        }
    except (psycopg.DatabaseError, ConnectionError, TimeoutError, OSError) as e:
        return {"status": "down", "error": f"Database error: {e!s}"}


def _check_memory() -> dict[str, Any]:
    """Check memory usage."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        rss_mb = memory_info.rss / 1024 / 1024

        virtual_mem = psutil.virtual_memory()
        total_mb = virtual_mem.total / 1024 / 1024
        utilization = (rss_mb / total_mb) * 100

        status = "up"
        warning = None
        if utilization > 90:
            status = "degraded"
            warning = f"High memory usage ({utilization:.1f}%)"

        result = {
            "status": status,
            "used_mb": round(rss_mb, 2),
            "total_mb": round(total_mb, 2),
            "utilization_percent": round(utilization, 2),
        }
        if warning:
            result["warning"] = warning

        return result
    except (OSError, PermissionError) as e:
        return {"status": "degraded", "warning": f"Memory check error: {e!s}"}


def _get_health_response(probe_type: str) -> tuple[Any, int]:
    """Generate health check response."""
    checks = {}

    if probe_type in ["readiness", "startup"]:
        checks["database"] = _check_database()

    checks["memory"] = _check_memory()

    # Compute overall status
    statuses = [c.get("status") for c in checks.values()]
    if "down" in statuses:
        overall_status = "down"
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "up"

    uptime_ms = int((time.time() - app.config["START_TIME"]) * 1000)

    response = {
        "status": overall_status,
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime_ms": uptime_ms,
        "version": app.config["VERSION"],
        "service": app.config["SERVICE_NAME"],
        "environment": app.config["ENVIRONMENT"],
        "probe_type": probe_type,
        "checks": checks,
    }

    status_code = 503 if overall_status == "down" else 200
    return jsonify(response), status_code


@app.route("/health")
def health():
    """Combined health check (defaults to readiness)"""
    return _get_health_response("readiness")


@app.route("/health/live")
def health_live():
    """Liveness probe - Is the process alive?"""
    return _get_health_response("liveness")


@app.route("/health/ready")
def health_ready():
    """Readiness probe - Can the service handle traffic?"""
    return _get_health_response("readiness")


@app.route("/health/startup")
def health_startup():
    """Startup probe - Has initialization completed?"""
    return _get_health_response("startup")


@app.route("/ping")
def ping():
    """Simple ping endpoint for throughput testing"""
    REQUEST_COUNT.labels(method="GET", endpoint="/ping").inc()
    return jsonify({"message": "pong"})


@app.route("/users")
def list_users():
    """List users (basic info only) or batch fetch by IDs"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users").inc()

    # Check for batch fetch by IDs
    ids = request.args.get("ids")
    if ids:
        try:
            id_list = Validator.validate_uuid_list(ids, max_count=100)
        except InputValidationError:
            raise
        if not id_list:
            return jsonify({"users": []})

        # Use ANY array for batch fetch
        users = execute_query(
            """
            SELECT id, username, full_name, bio, avatar_url
            FROM benchmark.tb_user
            WHERE id = ANY(%s::uuid[])
        """,
            (id_list,),
        )
        return jsonify({"users": users})

    try:
        limit = Validator.validate_limit(
            request.args.get("limit", 10), min_val=1, max_val=100
        )
    except InputValidationError:
        raise
    users = execute_query(
        """
        SELECT id, username, full_name, bio
        FROM benchmark.tb_user
        ORDER BY created_at DESC
        LIMIT %s
    """,
        (limit,),
    )

    return jsonify({"users": users})


@app.route("/users/<user_id>")
def get_user(user_id):
    """Get user by ID with optional includes"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{id}").inc()

    # Validate user_id format
    try:
        Validator.validate_uuid(user_id, "user_id")
    except InputValidationError:
        raise

    user = execute_query(
        """
        SELECT id, username, full_name, bio
        FROM benchmark.tb_user
        WHERE id = %s
    """,
        (user_id,),
    )

    if not user:
        raise ResourceNotFoundError(f"User with ID {user_id} not found")

    user_data = user[0]

    # Handle includes parameter
    allowed_includes = ["posts", "posts.comments", "posts.comments.author"]
    include = request.args.get("include", "")
    if include:
        try:
            includes = Validator.validate_include_fields(include, allowed_includes)
        except InputValidationError:
            raise
    else:
        includes = []

    if "posts" in includes:
        posts = execute_query(
            """
            SELECT p.id, p.title, p.content
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            WHERE u.id = %s
            ORDER BY p.created_at DESC
            LIMIT 10
        """,
            (user_id,),
        )
        user_data["posts"] = posts

    return jsonify(user_data)


@app.route("/users/<user_id>/posts")
def get_user_posts(user_id):
    """Get user's posts (separate endpoint - causes N+1)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/users/{id}/posts").inc()

    posts = execute_query(
        """
        SELECT p.id, p.title, p.content
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        WHERE u.id = %s
        ORDER BY p.created_at DESC
        LIMIT 10
    """,
        (user_id,),
    )

    return jsonify({"posts": posts})


# Note: Removed followers/following endpoints - tb_user_follows table doesn't exist


@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    REQUEST_COUNT.labels(method="PUT", endpoint="/users/{id}").inc()

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate input data
    validation_errors = validate_update_user_data(data)
    if validation_errors:
        return jsonify({"error": "Validation Error", "details": validation_errors}), 400

    # Update user using whitelist of allowed fields
    update_fields = []
    params = []
    for field in ALLOWED_UPDATE_FIELDS:
        if field in data:
            update_fields.append(f"{field} = %s")
            params.append(data[field])

    if update_fields:
        params.append(user_id)
        update_clause = ", ".join(update_fields)
        execute_query(
            f"UPDATE benchmark.tb_user SET {update_clause}, updated_at = NOW() WHERE id = %s",
            tuple(params),
        )

    # Return updated user
    return get_user(user_id)


@app.route("/posts")
def list_posts():
    """List posts with optional includes"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts").inc()

    try:
        limit = Validator.validate_limit(
            request.args.get("limit", 10), min_val=1, max_val=100
        )
    except InputValidationError:
        raise

    allowed_includes = ["author", "comments", "comments.author"]
    include = request.args.get("include", "")
    if include:
        try:
            includes = Validator.validate_include_fields(include, allowed_includes)
        except InputValidationError:
            raise
    else:
        includes = []

    # Query posts with author if needed
    if "author" in includes:
        posts = execute_query(
            """
            SELECT p.id, p.title, p.content,
                   u.id as author_id, u.username as author_username
            FROM benchmark.tb_post p
            JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
            ORDER BY p.created_at DESC
            LIMIT %s
        """,
            (limit,),
        )

        # Add author as nested object
        for post in posts:
            post["author"] = {
                "id": post["author_id"],
                "username": post["author_username"],
            }
            del post["author_id"]
            del post["author_username"]
    else:
        posts = execute_query(
            """
            SELECT p.id, p.title, p.content
            FROM benchmark.tb_post p
            ORDER BY p.created_at DESC
            LIMIT %s
        """,
            (limit,),
        )

    return jsonify({"posts": posts})


@app.route("/posts/<post_id>")
def get_post(post_id):
    """Get post by ID (basic info only - matches benchmarking expectations)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}").inc()

    # Validate post_id format
    try:
        Validator.validate_uuid(post_id, "post_id")
    except InputValidationError:
        raise

    post = execute_query(
        """
        SELECT id, title, content
        FROM benchmark.tb_post
        WHERE id = %s
    """,
        (post_id,),
    )

    if not post:
        raise ResourceNotFoundError(f"Post with ID {post_id} not found")

    return jsonify(post[0])


@app.route("/posts/<post_id>/author")
def get_post_author(post_id):
    """Get post's author (separate endpoint - N+1)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}/author").inc()

    # Validate post_id format
    try:
        Validator.validate_uuid(post_id, "post_id")
    except InputValidationError:
        raise

    author = execute_query(
        """
        SELECT u.id, u.username
        FROM benchmark.tb_post p
        JOIN benchmark.tb_user u ON p.fk_author = u.pk_user
        WHERE p.id = %s
    """,
        (post_id,),
    )

    if not author:
        raise ResourceNotFoundError(f"Post with ID {post_id} not found")

    return jsonify(author[0])


@app.route("/comments/<comment_id>")
def get_comment(comment_id):
    """Get comment by ID (basic info only)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/comments/{id}").inc()

    # Validate comment_id format
    try:
        Validator.validate_uuid(comment_id, "comment_id")
    except InputValidationError:
        raise

    comment = execute_query(
        """
        SELECT id, content
        FROM benchmark.tb_comment
        WHERE id = %s
    """,
        (comment_id,),
    )

    if not comment:
        raise ResourceNotFoundError(f"Comment with ID {comment_id} not found")

    return jsonify(comment[0])


@app.route("/posts/<post_id>/comments")
def get_post_comments(post_id):
    """Get comments for a specific post"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}/comments").inc()

    # Validate post_id format
    try:
        Validator.validate_uuid(post_id, "post_id")
    except InputValidationError:
        raise

    try:
        limit = Validator.validate_limit(
            request.args.get("limit", 10), min_val=1, max_val=100
        )
    except InputValidationError:
        raise

    comments = execute_query(
        """
        SELECT c.id, c.content, c.created_at, c.is_approved,
               u.id as author_id, u.username as author_username,
               u.avatar_url as author_avatar
        FROM benchmark.tb_comment c
        JOIN benchmark.tb_post p ON c.fk_post = p.pk_post
        JOIN benchmark.tb_user u ON c.fk_author = u.pk_user
        WHERE p.id = %s
        ORDER BY c.created_at DESC
        LIMIT %s
    """,
        (post_id, limit),
    )

    return jsonify(comments)


@app.route("/metrics")
def metrics():
    return prometheus_client.generate_latest()


# Error handlers
@app.errorhandler(AppError)
def handle_app_error(error: AppError):
    """Handle application errors with proper status codes."""
    app.logger.error(
        f"Application error: {error.message}",
        extra={"error_code": error.error_code},
    )
    return jsonify(error.to_dict()), error.status_code


@app.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors."""
    return jsonify(
        {"error": "Not Found", "message": "The requested resource was not found"}
    ), 404


@app.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 internal server errors."""
    app.logger.error(f"Internal server error: {error}")
    return jsonify(
        {"error": "Internal Server Error", "message": "An unexpected error occurred"}
    ), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions."""
    app.logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify(
        {"error": "Internal Server Error", "message": "An unexpected error occurred"}
    ), 500


@app.errorhandler(psycopg.Error)
def handle_database_error(error):
    """Handle database-specific errors."""
    app.logger.error(f"Database error: {error}")
    return jsonify(
        {"error": "Database Error", "message": "A database error occurred"}
    ), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004, debug=False)
