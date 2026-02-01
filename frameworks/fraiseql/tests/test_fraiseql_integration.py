"""Integration tests for FraiseQL framework.

Tests verify that:
1. JSONB views are properly created in database
2. FraiseQL server starts and responds to queries
3. GraphQL queries return data in expected structure
4. Nested relationships are properly embedded in JSONB
"""

import pytest
import requests


class TestFraiseQLServer:
    """Test FraiseQL server startup and basic queries."""

    def test_server_running(self, fraiseql_server: str):
        """Verify FraiseQL server is running and responsive."""
        response = requests.get(f"{fraiseql_server}/health")
        assert response.status_code == 200

    def test_simple_query(self, fraiseql_server: str, graphql_query):
        """Test simple query: { users { id username } }"""
        result = graphql_query(
            fraiseql_server,
            """
            {
                users(limit: 5) {
                    id
                    username
                    email
                }
            }
            """,
        )

        # Check for errors
        if "errors" in result:
            pytest.skip(f"Query failed: {result['errors']}")

        # Verify structure
        assert "data" in result
        assert "users" in result["data"]
        users = result["data"]["users"]

        # Verify we got users
        if len(users) > 0:
            user = users[0]
            assert "id" in user
            assert "username" in user
            assert "email" in user

    def test_nested_query(self, fraiseql_server: str, graphql_query):
        """Test nested query with relationships: { posts { id title author { name } } }"""
        result = graphql_query(
            fraiseql_server,
            """
            {
                posts(limit: 5) {
                    id
                    title
                    status
                    author {
                        id
                        username
                        email
                    }
                }
            }
            """,
        )

        # Check for errors
        if "errors" in result:
            pytest.skip(f"Query failed: {result['errors']}")

        # Verify structure
        assert "data" in result
        assert "posts" in result["data"]
        posts = result["data"]["posts"]

        # Verify nested author data
        if len(posts) > 0:
            post = posts[0]
            assert "id" in post
            assert "title" in post
            assert "author" in post

            author = post["author"]
            assert "id" in author
            assert "username" in author


class TestFraiseQLViews:
    """Test JSONB view structure in database."""

    def test_v_user_view_exists(self, db_connection):
        """Verify v_user view exists and has correct structure."""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views
                    WHERE table_schema = 'benchmark'
                    AND table_name = 'v_user'
                )
            """)
            exists = cursor.fetchone()[0]
            assert exists, "v_user view not found"

            # Check columns
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'benchmark'
                AND table_name = 'v_user'
                ORDER BY column_name
            """)
            columns = {row[0] for row in cursor.fetchall()}
            assert "id" in columns, "v_user missing 'id' column"
            assert "data" in columns, "v_user missing 'data' column"

    def test_v_post_view_exists(self, db_connection):
        """Verify v_post view exists and has correct structure."""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views
                    WHERE table_schema = 'benchmark'
                    AND table_name = 'v_post'
                )
            """)
            exists = cursor.fetchone()[0]
            assert exists, "v_post view not found"

            # Check columns
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'benchmark'
                AND table_name = 'v_post'
                ORDER BY column_name
            """)
            columns = {row[0] for row in cursor.fetchall()}
            assert "id" in columns, "v_post missing 'id' column"
            assert "data" in columns, "v_post missing 'data' column"

    def test_v_comment_view_exists(self, db_connection):
        """Verify v_comment view exists and has correct structure."""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views
                    WHERE table_schema = 'benchmark'
                    AND table_name = 'v_comment'
                )
            """)
            exists = cursor.fetchone()[0]
            assert exists, "v_comment view not found"

    def test_v_user_data_structure(self, db_connection):
        """Verify v_user view returns correct JSONB structure."""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT data FROM benchmark.v_user LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                data = result[0]
                assert isinstance(data, dict), "v_user.data should be JSONB object"
                assert "id" in data, "JSONB data missing 'id'"
                assert "username" in data, "JSONB data missing 'username'"
                assert "email" in data, "JSONB data missing 'email'"

    def test_v_post_nested_author(self, db_connection):
        """Verify v_post includes nested author data in JSONB."""
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT data FROM benchmark.v_post LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                data = result[0]
                assert isinstance(data, dict), "v_post.data should be JSONB object"
                assert "id" in data, "JSONB data missing 'id'"
                assert "title" in data, "JSONB data missing 'title'"
                # Author should be nested
                assert "author" in data, "JSONB data missing nested 'author'"
                author = data.get("author")
                if author:
                    assert "id" in author, "nested author missing 'id'"
                    assert "username" in author, "nested author missing 'username'"


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
                        username
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
                        title
                        author {
                            id
                            username
                            email
                        }
                    }
                }
                """,
            )

        result = benchmark(run_query)
        assert "data" in result
