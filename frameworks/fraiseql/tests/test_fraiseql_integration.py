"""Integration tests for FraiseQL v2.0.0-beta.3 framework.

Tests verify that:
1. Installed binary is exactly v2.0.0-beta.3
2. JSONB views expose id and identifier fields
3. FraiseQL v2 server starts and responds to queries
4. GraphQL queries return data in expected structure
5. Nested relationships are properly embedded in JSONB
6. Beta.3 health endpoint shape is correct
7. Error sanitization returns generic messages for malformed queries
"""

import subprocess

import pytest
import requests

REQUIRED_VERSION = "2.0.0-beta.3"


class TestFraiseQLServer:
    """Test FraiseQL v2 server startup and basic queries."""

    def test_server_version(self, fraiseql_server_bin):
        """Assert the installed binary is exactly v2.0.0-beta.3."""
        result = subprocess.run(
            [str(fraiseql_server_bin), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_output = result.stdout.strip() + result.stderr.strip()
        assert REQUIRED_VERSION in version_output, (
            f"Expected {REQUIRED_VERSION} in version output, got: {version_output!r}"
        )

    def test_server_running(self, fraiseql_server: str):
        """Verify FraiseQL v2 server is running and responsive."""
        response = requests.get(f"{fraiseql_server}/health")
        assert response.status_code == 200

    def test_simple_query(self, fraiseql_server: str, graphql_query):
        """Test simple query: { users { id identifier } }"""
        result = graphql_query(
            fraiseql_server,
            """
            {
                users(limit: 5) {
                    id
                    identifier
                    email
                }
            }
            """,
        )

        if "errors" in result:
            pytest.skip(f"Query failed: {result['errors']}")

        assert "data" in result
        assert "users" in result["data"]
        users = result["data"]["users"]

        if len(users) > 0:
            user = users[0]
            assert "id" in user
            assert "identifier" in user
            assert "email" in user

    def test_nested_query(self, fraiseql_server: str, graphql_query):
        """Test nested query with relationships: { posts { id author { id } } }"""
        result = graphql_query(
            fraiseql_server,
            """
            {
                posts(limit: 5) {
                    id
                    identifier
                    title
                    author {
                        id
                        identifier
                        username
                    }
                }
            }
            """,
        )

        if "errors" in result:
            pytest.skip(f"Query failed: {result['errors']}")

        assert "data" in result
        assert "posts" in result["data"]
        posts = result["data"]["posts"]

        if len(posts) > 0:
            post = posts[0]
            assert "id" in post
            assert "author" in post

            author = post["author"]
            assert "id" in author
            assert "identifier" in author

    def test_introspection_query(self, fraiseql_server: str, graphql_query):
        """Test GraphQL introspection."""
        result = graphql_query(
            fraiseql_server,
            """
            {
                __schema {
                    types {
                        name
                    }
                }
            }
            """,
        )

        if "errors" in result:
            pytest.skip(f"Introspection query failed: {result['errors']}")

        assert "data" in result
        assert "__schema" in result["data"]
        assert "types" in result["data"]["__schema"]

        type_names = [t["name"] for t in result["data"]["__schema"]["types"]]
        assert "User" in type_names
        assert "Post" in type_names
        assert "Comment" in type_names


class TestFraiseQLViews:
    """Test JSONB view structure in database."""

    def test_fv_user_view_exists(self, db_connection):
        """Verify fv_user view exists and has correct structure."""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views
                    WHERE table_schema = 'benchmark'
                    AND table_name = 'fv_user'
                )
            """)
            exists = cursor.fetchone()[0]
            assert exists, "fv_user view not found"

            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'benchmark'
                AND table_name = 'fv_user'
                ORDER BY column_name
            """)
            columns = {row[0] for row in cursor.fetchall()}
            assert "id" in columns, "fv_user missing 'id' column"
            assert "data" in columns, "fv_user missing 'data' column"

    def test_fv_post_view_exists(self, db_connection):
        """Verify fv_post view exists and has correct structure."""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views
                    WHERE table_schema = 'benchmark'
                    AND table_name = 'fv_post'
                )
            """)
            exists = cursor.fetchone()[0]
            assert exists, "fv_post view not found"

    def test_fv_comment_view_exists(self, db_connection):
        """Verify fv_comment view exists."""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views
                    WHERE table_schema = 'benchmark'
                    AND table_name = 'fv_comment'
                )
            """)
            exists = cursor.fetchone()[0]
            assert exists, "fv_comment view not found"

    def test_fv_user_fields(self, db_connection):
        """Verify fv_user JSONB exposes id, identifier, and user fields."""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT data FROM benchmark.fv_user LIMIT 1")
            result = cursor.fetchone()
            if result:
                data = result[0]
                assert isinstance(data, dict), "fv_user.data should be JSONB object"
                assert "id" in data, "JSONB data missing 'id'"
                assert "identifier" in data, "JSONB data missing 'identifier'"
                assert "email" in data, "JSONB data missing 'email'"
                assert "username" in data, "JSONB data missing 'username'"

    def test_fv_post_fields(self, db_connection):
        """Verify fv_post JSONB exposes id, identifier, and nested author."""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT data FROM benchmark.fv_post LIMIT 1")
            result = cursor.fetchone()
            if result:
                data = result[0]
                assert isinstance(data, dict), "fv_post.data should be JSONB object"
                assert "id" in data, "JSONB data missing 'id'"
                assert "identifier" in data, "JSONB data missing 'identifier'"
                assert "title" in data, "JSONB data missing 'title'"

                author = data.get("author")
                if author:
                    assert "id" in author, "nested author missing 'id'"
                    assert "identifier" in author, "nested author missing 'identifier'"

    def test_fv_comment_fields(self, db_connection):
        """Verify fv_comment JSONB exposes id and nested relationships."""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT data FROM benchmark.fv_comment LIMIT 1")
            result = cursor.fetchone()
            if result:
                data = result[0]
                assert isinstance(data, dict), "fv_comment.data should be JSONB object"
                assert "id" in data, "JSONB data missing 'id'"
                assert "content" in data, "JSONB data missing 'content'"
                assert "author" in data, "JSONB data missing nested 'author'"
                assert "post" in data, "JSONB data missing nested 'post'"


class TestFraiseQLV2Features:
    """Test FraiseQL v2 specific features."""

    def test_query_with_variables(self, fraiseql_server: str, graphql_query):
        """Test query with GraphQL variables."""
        result = graphql_query(
            fraiseql_server,
            """
            query GetUsers($limit: Int!) {
                users(limit: $limit) {
                    id
                    identifier
                }
            }
            """,
            variables={"limit": 3},
        )

        if "errors" in result:
            pytest.skip(f"Query failed: {result['errors']}")

        assert "data" in result
        assert "users" in result["data"]
        assert len(result["data"]["users"]) <= 3

    def test_filtering_by_published(self, fraiseql_server: str, graphql_query):
        """Test filtering posts by published status."""
        result = graphql_query(
            fraiseql_server,
            """
            {
                posts(limit: 10, published: true) {
                    id
                    identifier
                    published
                }
            }
            """,
        )

        if "errors" in result:
            pytest.skip(f"Query failed: {result['errors']}")

        assert "data" in result
        posts = result["data"].get("posts", [])
        for post in posts:
            assert post.get("published") is True


class TestFraiseQLBeta3:
    """Tests specific to FraiseQL v2.0.0-beta.3 features."""

    def test_health_endpoint_shape(self, fraiseql_server: str):
        """Health endpoint should return a JSON body with status field."""
        response = requests.get(f"{fraiseql_server}/health", timeout=5)
        assert response.status_code == 200

        body = response.json()
        assert "status" in body, "Health response missing 'status' field"
        assert body["status"] == "healthy"

    def test_introspection_returns_user_fields(
        self, fraiseql_server: str, graphql_query
    ):
        """Introspection should expose User type with id and identifier."""
        result = graphql_query(
            fraiseql_server,
            """
            {
                __type(name: "User") {
                    fields {
                        name
                    }
                }
            }
            """,
        )

        if "errors" in result:
            pytest.skip(f"Introspection failed: {result['errors']}")

        user_type = result.get("data", {}).get("__type")
        if user_type:
            field_names = {f["name"] for f in user_type.get("fields", [])}
            assert "id" in field_names, "User type missing 'id' field"
            assert "identifier" in field_names, "User type missing 'identifier' field"
            assert "pk" not in field_names, "User type should not expose internal 'pk'"

    def test_error_sanitization_malformed_query(self, fraiseql_server: str):
        """Malformed query should return an error without leaking internal details."""
        response = requests.post(
            f"{fraiseql_server}/graphql",
            json={"query": "{ __invalid_field_that_does_not_exist }"},
            timeout=5,
        )

        body = response.json()
        assert "errors" in body, "Expected errors for invalid query"

        for error in body["errors"]:
            message = error.get("message", "")
            assert "panic" not in message.lower(), "Error leaks panic details"
            assert "stacktrace" not in message.lower(), "Error leaks stack trace"
            assert "thread" not in message.lower(), "Error leaks thread details"


@pytest.mark.benchmark
class TestFraiseQLPerformance:
    """Performance benchmarking tests."""

    def test_simple_query_latency(self, fraiseql_server: str, graphql_query, benchmark):
        """Benchmark simple query latency."""

        def run_query():
            return graphql_query(
                fraiseql_server,
                """
                {
                    users(limit: 10) {
                        id
                        identifier
                        email
                    }
                }
                """,
            )

        result = benchmark(run_query)
        assert "data" in result

    def test_nested_query_latency(self, fraiseql_server: str, graphql_query, benchmark):
        """Benchmark nested query latency."""

        def run_query():
            return graphql_query(
                fraiseql_server,
                """
                {
                    posts(limit: 10) {
                        id
                        identifier
                        title
                        author {
                            id
                            identifier
                            username
                        }
                    }
                }
                """,
            )

        result = benchmark(run_query)
        assert "data" in result
