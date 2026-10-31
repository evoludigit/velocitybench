"""M1d: the jsonb_delta write path must patch a populated tvd_* and survive concurrency.

Finding #247:
- the tvd_* tables were seeded from tv_* in init 05, before the bulk sync (06)
  filled tv_*, so they held a handful of rows and every M1d "mutation" patched
  next to nothing;
- fn_update_user_delta updated a user's tvd_comment rows in two unordered
  scans (comments the user wrote, then comments on the user's posts), so two
  users who comment on each other's posts deadlocked.
"""

import subprocess
import sys
from pathlib import Path

import pytest

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import bench_sequential as bench  # noqa: E402


def _postgres_running() -> bool:
    out = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False,
    )
    return "velocitybench-postgres-1" in out.stdout


pytestmark = pytest.mark.skipif(
    not _postgres_running(), reason="postgres container not running"
)


def test_tvd_tables_hold_every_seeded_row():
    """tvd_* start as a full copy of tv_*. Posts can be created after init
    (createPost), so tvd_post is compared up to the last commented post."""
    # Serial plan: the anti-joins over 500k comments overflow the container's
    # /dev/shm when run with parallel workers. psql prints SET's tag first.
    missing = bench._psql(
        "SET max_parallel_workers_per_gather = 0;"
        "SELECT"
        " (SELECT count(*) FROM benchmark.tv_user tv"
        "   WHERE NOT EXISTS (SELECT 1 FROM benchmark.tvd_user d"
        "                     WHERE d.pk_user = tv.pk_user)),"
        " (SELECT count(*) FROM benchmark.tv_post tv"
        "   WHERE tv.pk_post <= (SELECT max(fk_post) FROM benchmark.tb_comment)"
        "   AND NOT EXISTS (SELECT 1 FROM benchmark.tvd_post d"
        "                   WHERE d.pk_post = tv.pk_post)),"
        " (SELECT count(*) FROM benchmark.tv_comment tv"
        "   WHERE NOT EXISTS (SELECT 1 FROM benchmark.tvd_comment d"
        "                     WHERE d.pk_comment = tv.pk_comment))"
    )[-1]
    assert missing == ["0", "0", "0"], (
        f"tv rows absent from tvd (user, post, comment): {missing}"
    )


def _crossed_pair() -> tuple[str, str]:
    """Two users who each commented on a post of the other."""
    rows = bench._psql(
        "SELECT ua.id, ub.id"
        " FROM benchmark.tb_comment c1"
        " JOIN benchmark.tb_post p1 ON p1.pk_post = c1.fk_post"
        " JOIN benchmark.tb_comment c2 ON c2.fk_author = p1.fk_author"
        " JOIN benchmark.tb_post p2 ON p2.pk_post = c2.fk_post"
        "   AND p2.fk_author = c1.fk_author"
        " JOIN benchmark.tb_user ua ON ua.pk_user = c1.fk_author"
        " JOIN benchmark.tb_user ub ON ub.pk_user = p1.fk_author"
        " WHERE c1.fk_author <> p1.fk_author"
        " LIMIT 1"
    )
    assert rows, "dataset has no pair of users commenting on each other's posts"
    return rows[0][0], rows[0][1]


def _delta_stream(user_id: str, calls: int) -> subprocess.Popen:
    """A psql session issuing `calls` single-statement transactions."""
    script = "".join(
        f"SELECT succeeded FROM benchmark.fn_update_user_delta("
        f"'{user_id}', 'm1d-lock-{i % 2}');\n"
        for i in range(calls)
    )
    proc = subprocess.Popen(
        ["docker", "compose", "exec", "-T", "postgres",
         "psql", "-U", "benchmark", "-d", "velocitybench_benchmark", "-At"],
        cwd=str(BENCH_DIR.parent.parent),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdin is not None
    proc.stdin.write(script)
    proc.stdin.close()
    return proc


def test_concurrent_delta_writes_on_crossed_users_do_not_deadlock():
    user_a, user_b = _crossed_pair()
    bios = {
        uid: bench._psql(
            "SELECT data->>'bio' FROM benchmark.tvd_user d"
            " JOIN benchmark.tb_user tb USING (pk_user)"
            f" WHERE tb.id = '{uid}'"
        )[0][0]
        for uid in (user_a, user_b)
    }
    try:
        streams = [_delta_stream(uid, 300) for uid in (user_a, user_b)]
        errors = [proc.communicate(timeout=300)[1] for proc in streams]
        deadlocks = sum(err.count("deadlock detected") for err in errors)
        assert deadlocks == 0, f"{deadlocks} deadlocks:\n{''.join(errors)[:2000]}"
        assert not any(err.strip() for err in errors), "".join(errors)[:2000]
    finally:
        for uid, bio in bios.items():
            value = "NULL" if bio == "" else "'" + bio.replace("'", "''") + "'"
            bench._psql(
                f"SELECT 1 FROM benchmark.fn_update_user_delta('{uid}', {value})"
            )
