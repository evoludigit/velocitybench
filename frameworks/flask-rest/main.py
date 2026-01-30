#!/usr/bin/env python3
"""
Flask REST Comparative Benchmarking Implementation
Traditional synchronous REST API using psycopg3 connection pool (demonstrates N+1 problem).
"""

import asyncio
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import asyncpg
import prometheus_client
import psutil
import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# Metrics
REQUEST_COUNT = prometheus_client.Counter(
    "flask_rest_requests_total", "Total requests", ["method", "endpoint"]
)
REQUEST_LATENCY = prometheus_client.Histogram(
    "flask_rest_request_duration_seconds", "Request latency", ["method", "endpoint"]
)


app = Flask(__name__)

# Health check startup time
app.config["START_TIME"] = time.time()
app.config["VERSION"] = "1.0.0"
app.config["SERVICE_NAME"] = "flask-rest"
app.config["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "development")

# Allowed fields for user updates (whitelist for SQL injection prevention)
ALLOWED_UPDATE_FIELDS = {"full_name", "bio"}


# Validation functions
def validate_update_user_data(data):
    """Validate user update data and return list of validation errors."""
    errors = []

    # Check for unknown fields
    allowed_fields = ALLOWED_UPDATE_FIELDS
    for field in data.keys():
        if field not in allowed_fields:
            errors.append({"field": field, "error": f"Unknown field: {field}"})

    # Validate full_name
    if "full_name" in data:
        full_name = data["full_name"]
        if not isinstance(full_name, str):
            errors.append({"field": "full_name", "error": "Full name must be a string"})
        elif len(full_name) > 255:
            errors.append(
                {"field": "full_name", "error": "Full name must be at most 255 characters"}
            )

    # Validate bio
    if "bio" in data:
        bio = data["bio"]
        if not isinstance(bio, str):
            errors.append({"field": "bio", "error": "Bio must be a string"})
        elif len(bio) > 1000:
            errors.append({"field": "bio", "error": "Bio must be at most 1000 characters"})

    return errors


def init_pool():
    """Initialize psycopg3 connection pool in app context."""
    conninfo = psycopg.conninfo.make_conninfo(
        host=os.getenv("DATABASE_HOST", "postgres"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        dbname=os.getenv("DATABASE_NAME", "fraiseql_benchmark"),
        user=os.getenv("DATABASE_USER", "benchmark"),
        password=os.getenv("DATABASE_PASSWORD", "benchmark123"),
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
def get_db_connection():
    """Get database connection from app context."""
    pool = app.config["DB_POOL"]
    with pool.connection() as conn:
        yield conn


def execute_query(query: str, params: tuple | None = None):
    """Execute query and return results."""
    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params or ())
            if cur.description:
                return cur.fetchall()
            return []


# Initialize pool in app context on first request
@app.before_serving
def setup_db():
    """Initialize database pool."""
    init_pool()


# Register cleanup on app teardown
@app.teardown_appcontext
def teardown_db(exception=None):
    """Close pool on app shutdown."""
    pool = app.config.get("DB_POOL")
    if pool:
        pool.close()


def _check_database():
    """Check database health."""
    try:
        pool = app.config.get("DB_POOL")
        if not pool:
            return {
                "status": "down",
                "error": "Database pool not initialized"
            }

        start = time.time()
        with pool.connection() as conn:
            with conn.cursor() as cur:
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
        return {
            "status": "down",
            "error": f"Database error: {str(e)}"
        }


def _check_memory():
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
        return {
            "status": "degraded",
            "warning": f"Memory check error: {str(e)}"
        }


def _get_health_response(probe_type):
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_ms": uptime_ms,
        "version": app.config["VERSION"],
        "service": app.config["SERVICE_NAME"],
        "environment": app.config["ENVIRONMENT"],
        "probe_type": probe_type,
        "checks": checks
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
        id_list = [id.strip() for id in ids.split(",") if id.strip()]
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

    limit = int(request.args.get("limit", 10))
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

    user = execute_query(
        """
        SELECT id, username, full_name, bio
        FROM benchmark.tb_user
        WHERE id = %s
    """,
        (user_id,),
    )

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = user[0]

    # Handle includes parameter
    include = request.args.get("include", "")
    if include:
        includes = include.split(",")

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
        execute_query(
            f"UPDATE benchmark.tb_user SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s",
            tuple(params),
        )

    # Return updated user
    return get_user(user_id)


@app.route("/posts")
def list_posts():
    """List posts with optional includes"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts").inc()

    limit = int(request.args.get("limit", 10))
    include = request.args.get("include", "")

    # Query posts with author if needed
    if "author" in include:
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

    post = execute_query(
        """
        SELECT id, title, content
        FROM benchmark.tb_post
        WHERE id = %s
    """,
        (post_id,),
    )

    if not post:
        return jsonify({"error": "Post not found"}), 404

    return jsonify(post[0])


@app.route("/posts/<post_id>/author")
def get_post_author(post_id):
    """Get post's author (separate endpoint - N+1)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}/author").inc()

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
        return jsonify({"error": "Post not found"}), 404

    return jsonify(author[0])


@app.route("/comments/<comment_id>")
def get_comment(comment_id):
    """Get comment by ID (basic info only)"""
    REQUEST_COUNT.labels(method="GET", endpoint="/comments/{id}").inc()

    comment = execute_query(
        """
        SELECT id, content
        FROM benchmark.tb_comment
        WHERE id = %s
    """,
        (comment_id,),
    )

    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    return jsonify(comment[0])


@app.route("/posts/<post_id>/comments")
def get_post_comments(post_id):
    """Get comments for a specific post"""
    REQUEST_COUNT.labels(method="GET", endpoint="/posts/{id}/comments").inc()

    limit = int(request.args.get("limit", 10))

    comments = execute_query(
        """
        SELECT c.id, c.content, c.created_at, c.is_approved,
               u.id as author_id, u.username as author_username, u.avatar_url as author_avatar
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


@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "framework": "flask-rest"})


@app.route("/metrics")
def metrics():
    return prometheus_client.generate_latest()


# Error handlers
@app.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not Found", "message": "The requested resource was not found"}), 404


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
    return jsonify({"error": "Database Error", "message": "A database error occurred"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004, debug=False)
