"""write_path_probe: the parts that do not need a live database."""

import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import write_path_probe as probe


class FakePg:
    """Answers the population query with canned psql -At output."""

    def __init__(self, out: str):
        self.out = out
        self.statements: list[str] = []

    def sql(self, statement: str, *, check: bool = True) -> str:
        self.statements.append(statement)
        return self.out


def _closed_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_unreachable_endpoint_is_a_guard_failure_not_a_crash():
    """A crash here loses the SQL cell already measured; a guard failure keeps it."""
    url = f"http://127.0.0.1:{_closed_port()}/graphql"
    with pytest.raises(probe.GuardFailure, match="unreachable"):
        probe.drive_graphql(url, ["u1"], ["b"], 1, 1)


def test_population_reports_per_user_fan_out_predictors():
    pg = FakePg("u1|11|40|120\nu2|3|9|30")
    pop = probe.m1_population(pg, ["u1", "u2"])
    assert pop["users"] == [
        {"id": "u1", "posts": 11, "comments_authored": 40, "comments_on_posts": 120},
        {"id": "u2", "posts": 3, "comments_authored": 9, "comments_on_posts": 30},
    ]
    assert pop["mean_posts"] == 7.0
    assert pop["mean_comments_authored"] == 24.5


def test_population_keeps_the_callers_user_order():
    pg = FakePg("u1|1|0|0\nu2|2|0|0")
    probe.m1_population(pg, ["u1", "u2"])
    assert "u1" in pg.statements[0] and "u2" in pg.statements[0]


def test_population_refuses_a_user_that_does_not_exist():
    pg = FakePg("u1|1|0|0")
    with pytest.raises(probe.GuardFailure, match="u2"):
        probe.m1_population(pg, ["u1", "u2"])


class BarrierPg:
    """Fakes psql for the SQL driver: a DB clock, and one output per worker."""

    BARRIER = 1000.0
    FUNCTION = "benchmark.fn_update_user"

    def __init__(self, *, ready: float = 999.5, per_statement_s: float = 0.002):
        self.ready = ready
        self.per_statement_s = per_statement_s
        self.scripts: list[str] = []

    def sql(self, statement: str, *, check: bool = True) -> str:
        return str(self.BARRIER)

    def script(self, body: str) -> str:
        self.scripts.append(body)
        n = sum(1 for line in body.splitlines() if line.startswith(f"SELECT {self.FUNCTION}("))
        done = self.BARRIER + n * self.per_statement_s
        timings = "".join(f"\nTime: {self.per_statement_s * 1000:.3f} ms" for _ in range(n))
        return f"wp_ready {self.ready}\n{timings}\nwp_done {done}\n"


def _drive(pg: BarrierPg, mutations: int, concurrency: int):
    ids = [f"u{i}" for i in range(20)]
    return probe.drive_sql(pg, ids, probe.cell_bios("t"), mutations, concurrency,
                           BarrierPg.FUNCTION)


def test_sql_window_runs_from_the_barrier_to_the_last_worker():
    """Starting 40 `docker exec psql` took 0.86 s on the CCX33 and landed inside
    the timed window, so c=40 read 269 rps where the database did ~790+."""
    latencies, window = _drive(BarrierPg(), mutations=400, concurrency=40)
    assert len(latencies) == 400
    assert window == pytest.approx(10 * 0.002)


def test_every_worker_waits_on_the_same_barrier():
    pg = BarrierPg()
    _drive(pg, mutations=40, concurrency=4)
    assert len(pg.scripts) == 4
    assert all(f"pg_sleep_until(to_timestamp({BarrierPg.BARRIER}))" in s for s in pg.scripts)


def test_markers_are_outside_the_timed_statements():
    pg = BarrierPg()
    _drive(pg, mutations=10, concurrency=1)
    body = pg.scripts[0]
    assert body.index("wp_ready") < body.index("pg_sleep_until") < body.index("\\timing on")
    assert body.index("\\timing off") < body.index("wp_done")


def test_a_worker_that_misses_the_barrier_is_a_guard_failure():
    """A worker that arrives late runs with fewer peers, which is a lower
    concurrency than the label claims."""
    with pytest.raises(probe.GuardFailure, match="barrier"):
        _drive(BarrierPg(ready=BarrierPg.BARRIER + 0.2), mutations=40, concurrency=4)
