"""
FraiseQL CQRS Data Sync

Tests that v_* views and tv_* tables are correctly populated with nested JSONB data.
"""

import os

import psycopg2
import psycopg2.extras
import pytest


@pytest.fixture(scope="session")
def pg_conn():
    conn = psycopg2.connect(
        host="localhost",
        port=int(os.environ.get("POSTGRES_PORT", "5434")),
        dbname="velocitybench_benchmark",
        user="benchmark",
        password="benchmark123",
    )
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# v_* view tests (Variant A — on-the-fly JSONB)
# ---------------------------------------------------------------------------


def test_v_user_view_exists(pg_conn):
    """benchmark.v_user view must exist after init."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.views
        WHERE table_schema = 'benchmark' AND table_name = 'v_user'
    """)
    assert cur.fetchone()[0] == 1, "v_user view does not exist"


def test_v_post_view_exists(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.views
        WHERE table_schema = 'benchmark' AND table_name = 'v_post'
    """)
    assert cur.fetchone()[0] == 1, "v_post view does not exist"


def test_v_comment_view_exists(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.views
        WHERE table_schema = 'benchmark' AND table_name = 'v_comment'
    """)
    assert cur.fetchone()[0] == 1, "v_comment view does not exist"


def test_v_user_returns_data(pg_conn):
    """v_user must return at least 5 fixture rows."""
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.v_user")
    assert cur.fetchone()[0] >= 5


def test_v_post_nested_author_username(pg_conn):
    """v_post.data must contain a nested author.username field."""
    cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT data->'author'->>'username' AS author_username
        FROM benchmark.v_post
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None, "v_post has no rows"
    assert row["author_username"] is not None, "v_post author.username is null"


def test_v_comment_nested_author_and_post(pg_conn):
    """v_comment.data must contain nested author.username and post.title."""
    cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            data->'author'->>'username' AS author_username,
            data->'post'->>'title'      AS post_title
        FROM benchmark.v_comment
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None, "v_comment has no rows"
    assert row["author_username"] is not None, "v_comment author.username is null"
    assert row["post_title"] is not None, "v_comment post.title is null"


def test_v_user_jsonb_uses_camelcase(pg_conn):
    """v_user.data JSONB must use camelCase keys (fullName, createdAt)."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT
            data ? 'fullName'  AS has_full_name,
            data ? 'createdAt' AS has_created_at,
            data ? 'updatedAt' AS has_updated_at
        FROM benchmark.v_user
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None
    has_full_name, has_created_at, has_updated_at = row
    assert has_full_name, "v_user JSONB missing 'fullName' key"
    assert has_created_at, "v_user JSONB missing 'createdAt' key"
    assert has_updated_at, "v_user JSONB missing 'updatedAt' key"


def test_v_user_count_medium(pg_conn):
    """v_user is a live view — count matches tb_user at medium scale."""
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.v_user")
    assert cur.fetchone()[0] == 10_000


def test_v_post_count_medium(pg_conn):
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.v_post")
    assert cur.fetchone()[0] == 50_000


# ---------------------------------------------------------------------------
# tv_* table tests (Variant B — pre-computed JSONB)
# ---------------------------------------------------------------------------


def test_tv_user_has_rows(pg_conn):
    """tv_user must be populated at init time."""
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public.tv_user")
    assert cur.fetchone()[0] >= 5


def test_tv_post_has_rows(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public.tv_post")
    assert cur.fetchone()[0] >= 5


def test_tv_comment_has_rows(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public.tv_comment")
    assert cur.fetchone()[0] >= 5


def test_tv_user_jsonb_uses_camelcase(pg_conn):
    """tv_user.data JSONB must have camelCase keys to match schema_tv.py."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT
            data ? 'fullName'  AS has_full_name,
            data ? 'createdAt' AS has_created_at,
            data ? 'updatedAt' AS has_updated_at
        FROM public.tv_user
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None
    has_full_name, has_created_at, has_updated_at = row
    assert has_full_name, "tv_user JSONB missing 'fullName' — sync function mismatch"
    assert has_created_at, "tv_user JSONB missing 'createdAt' — sync function mismatch"
    assert has_updated_at, "tv_user JSONB missing 'updatedAt' — sync function mismatch"


def test_tv_post_nested_author_username(pg_conn):
    """tv_post.data must contain nested author.username (pre-computed at seed time)."""
    cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT data->'author'->>'username' AS author_username
        FROM public.tv_post
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None, "tv_post has no rows"
    assert row["author_username"] is not None, "tv_post author.username is null"


def test_tv_comment_nested_author_and_post(pg_conn):
    """tv_comment.data must contain nested author.username and post.title."""
    cur = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            data->'author'->>'username' AS author_username,
            data->'post'->>'title'      AS post_title
        FROM public.tv_comment
        LIMIT 1
    """)
    row = cur.fetchone()
    assert row is not None, "tv_comment has no rows"
    assert row["author_username"] is not None, "tv_comment author.username is null"
    assert row["post_title"] is not None, "tv_comment post.title is null"


def test_tv_user_alice_fixture_synced(pg_conn):
    """alice's fixture row must exist in tv_user after init sync."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT data->>'username' FROM public.tv_user
        WHERE data->>'username' = 'alice'
    """)
    row = cur.fetchone()
    assert row is not None, "alice not found in tv_user"


def test_tv_post_fixture_synced(pg_conn):
    """At least one fixture post must be in tv_post."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM public.tv_post
        WHERE data->>'identifier' = 'getting-started-graphql'
    """)
    assert cur.fetchone()[0] == 1, "fixture post not found in tv_post"


def test_tv_user_count_medium(pg_conn):
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public.tv_user")
    assert cur.fetchone()[0] == 10_000


def test_tv_post_count_medium(pg_conn):
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public.tv_post")
    assert cur.fetchone()[0] == 50_000


def test_tv_comment_count_medium(pg_conn):
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM public.tv_comment")
    assert cur.fetchone()[0] == 200_000
