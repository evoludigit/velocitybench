"""
Seed Data Verification

Tests that the database is seeded with the correct number of rows.
"""

import os

import psycopg2
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


def test_fixture_alice_at_pk1(pg_conn):
    """alice must always be pk_user=1 regardless of DATA_VOLUME."""
    cur = pg_conn.cursor()
    cur.execute("SELECT username FROM benchmark.tb_user WHERE pk_user = 1")
    row = cur.fetchone()
    assert row is not None, "No user at pk_user=1"
    assert row[0] == "alice"


def test_fixture_users_all_present(pg_conn):
    """The 5 named fixture users must always exist."""
    cur = pg_conn.cursor()
    cur.execute(
        "SELECT username FROM benchmark.tb_user WHERE pk_user <= 5 ORDER BY pk_user"
    )
    usernames = [r[0] for r in cur.fetchall()]
    assert usernames == ["alice", "bob", "carol", "dave", "eve"]


def test_post_author_fk_integrity(pg_conn):
    """Every post must reference an existing user."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM benchmark.tb_post p
        WHERE NOT EXISTS (
            SELECT 1 FROM benchmark.tb_user u WHERE u.pk_user = p.fk_author
        )
    """)
    orphans = cur.fetchone()[0]
    assert orphans == 0, f"{orphans} orphan posts found"


def test_comment_fk_integrity(pg_conn):
    """Every comment must reference an existing user and post."""
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM benchmark.tb_comment c
        WHERE NOT EXISTS (SELECT 1 FROM benchmark.tb_user u WHERE u.pk_user = c.fk_author)
           OR NOT EXISTS (SELECT 1 FROM benchmark.tb_post p WHERE p.pk_post = c.fk_post)
    """)
    orphans = cur.fetchone()[0]
    assert orphans == 0, f"{orphans} orphan comments found"


def test_user_count_medium(pg_conn):
    """DATA_VOLUME=medium must result in exactly 10,000 users."""
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.tb_user")
    assert cur.fetchone()[0] == 10_000


def test_post_count_medium(pg_conn):
    """DATA_VOLUME=medium must result in exactly 50,000 posts."""
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.tb_post")
    assert cur.fetchone()[0] == 50_000


def test_comment_count_medium(pg_conn):
    """DATA_VOLUME=medium must result in exactly 200,000 comments."""
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.tb_comment")
    assert cur.fetchone()[0] == 200_000


def test_tv_user_count_medium(pg_conn):
    """tv_user (query side) must be synced to match tb_user count."""
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.tv_user")
    assert cur.fetchone()[0] == 10_000


def test_tv_post_count_medium(pg_conn):
    """tv_post (query side) must be synced to match tb_post count."""
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.tv_post")
    assert cur.fetchone()[0] == 50_000


def test_tv_comment_count_medium(pg_conn):
    """tv_comment (query side) must be synced to match tb_comment count."""
    if os.environ.get("DATA_VOLUME") != "medium":
        pytest.skip("Requires DATA_VOLUME=medium")
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.tv_comment")
    assert cur.fetchone()[0] == 200_000


def test_first_20_users_exist(pg_conn):
    """At least 20 users must exist for framework pagination queries."""
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM benchmark.tb_user WHERE pk_user <= 20")
    assert cur.fetchone()[0] == 20
