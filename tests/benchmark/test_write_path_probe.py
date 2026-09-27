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
