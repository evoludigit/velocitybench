#!/usr/bin/env python3
"""Write-path attribution probe: what one logical mutation physically costs.

The July 2026 sweep reports M1 at 89 rps for every FraiseQL variant and
attributes it to the pg_tviews cascade ("every write recomputes ~61 precomputed
rows"). That attribution is not isolated by the sweep: `-v` and `-tv` variants
differ ONLY in their read-side schema mapping. They share one database, one
`benchmark.fn_update_user`, and one set of pg_tviews triggers, so 89 rps is one
write path measured five times. Row-lock contention (M1 rotates 20 user rows
under 40 workers, p50 223 ms / p99 3 349 ms), commit durability, and the runtime's
own mutation path are all unaccounted for.

This probe measures the physical work instead of inferring it from RPS, along
four axes that separate the competing hypotheses:

    concurrency 1 vs N   -> intrinsic work vs lock contention
    cascade on vs off    -> how much of it is pg_tviews
    fsync on vs off      -> how much is durability
    WAL bytes + HOT      -> what physically happened, per mutation

Every claimed condition is verified against the live server before the numbers
are kept, because a flag that silently does nothing is worse than no flag: a
cascade-off run must observe ZERO tv_* row writes, and a cascade-on run must
observe some. See `docs/write-path-attribution.md`.

Usage
-----
    # one cell
    python3 tests/benchmark/write_path_probe.py --mutations 200 --driver sql

    # the full matrix and the classification table
    python3 tests/benchmark/write_path_probe.py --matrix --mutations 200

    # through the runtime instead of straight to SQL
    python3 tests/benchmark/write_path_probe.py --driver graphql \\
        --endpoint http://localhost:8006/graphql --mutations 200 --concurrency 40
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO / "docker-compose.yml"
DB_USER = "benchmark"
DB_NAME = "velocitybench_benchmark"
SCHEMA = "benchmark"

# The settings whose value changes what a mutation physically costs. Captured on
# both sides of every window, so a run can never silently disagree with its label.
TRACKED_SETTINGS = (
    "fsync",
    "full_page_writes",
    "synchronous_commit",
    "wal_level",
    "wal_compression",
    "track_wal_io_timing",
    "track_io_timing",
    "autovacuum",
)

# M1's contention profile, from docs/scenarios.md: 20 user UUIDs x 10 bio values,
# rotating. Reproduced here so a concurrency sweep is comparable to the sweep's
# 89 rps rather than measuring a different workload.
M1_USER_COUNT = 20
M1_BIO_COUNT = 10


def cell_bios(generation: str) -> list[str]:
    """The 10 rotating values, tagged with a per-CELL generation.

    Within a cell the values rotate exactly as M1 does. Across cells they must
    differ: a second cell replaying the first cell's pairs writes values the
    rows already hold, and fn_update_user's `IS DISTINCT FROM` guard makes
    every one of them a no-op. The guard caught this too.
    """
    return [f"probe bio {i} gen {generation}" for i in range(M1_BIO_COUNT)]


def rotating_writes(user_ids: list[str], bios: list[str], count: int) -> list[tuple[str, str]]:
    """Cycle-based (user_id, bio) pairing, matching the sweep's `_rotating_writes`.

    Each full pass over the user pool advances the bio, so consecutive visits to
    the same user always write a different value. This is load-bearing, not
    cosmetic: `benchmark.fn_update_user` guards its UPDATE with
    `bio IS DISTINCT FROM p_bio`, so index-parallel pairing (`bios[i % len(bios)]`)
    makes every call after the first cycle a NO-OP when len(users) is a multiple
    of len(bios) -- 20 users x 10 bios gives user k the constant bio k%10. The
    probe's first version did exactly that and measured zero row writes at
    nominal throughput; the guard caught it.
    """
    pairs = [(uid, bios[cycle % len(bios)]) for cycle in range(len(bios)) for uid in user_ids]
    return [pairs[i % len(pairs)] for i in range(count)]


# ---------------------------------------------------------------------------
# talking to postgres
# ---------------------------------------------------------------------------


class Postgres:
    """psql access, the way the sweep already does it (no new Python deps)."""

    def __init__(self, container: str | None = None, dsn: str | None = None):
        self.dsn = dsn
        self.container = container if dsn is None else None
        if self.dsn is None and self.container is None:
            self.container = self._discover_container()

    @staticmethod
    def _discover_container() -> str:
        """Prefer the compose service; fall back to the conventional name."""
        if COMPOSE_FILE.exists() and shutil.which("docker"):
            out = subprocess.run(
                ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "-q", "postgres"],
                capture_output=True, text=True, cwd=REPO, check=False,
            )
            cid = out.stdout.strip().splitlines()
            if cid and cid[0]:
                return cid[0]
        return "velocitybench-postgres-1"

    def sql(self, statement: str, *, check: bool = True) -> str:
        if self.dsn:
            cmd = ["psql", self.dsn]
        else:
            cmd = ["docker", "exec", "-i", self.container, "psql", "-U", DB_USER, "-d", DB_NAME]
        cmd += ["-v", "ON_ERROR_STOP=1", "-At", "-c", statement]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if check and res.returncode != 0:
            raise RuntimeError(f"psql failed: {res.stderr.strip()[:400]}\nSQL: {statement[:200]}")
        return res.stdout.strip()

    def script(self, body: str) -> str:
        """Run a multi-statement script in ONE session, returning psql's output."""
        if self.dsn:
            cmd = ["psql", self.dsn]
        else:
            cmd = ["docker", "exec", "-i", self.container, "psql", "-U", DB_USER, "-d", DB_NAME]
        cmd += ["-v", "ON_ERROR_STOP=1", "-At"]
        res = subprocess.run(cmd, input=body, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"psql script failed: {res.stderr.strip()[:400]}")
        return res.stdout

    def superuser_sql(self, statement: str) -> str:
        """ALTER SYSTEM needs superuser or pg_write_all_settings.

        In this rig the bench role IS the superuser (the official image makes
        POSTGRES_USER one, and no separate `postgres` role exists), so this runs
        on the same connection. It stays a distinct method so a rig where the
        role is NOT privileged fails here with a message naming the reason,
        rather than silently skipping a condition the run claims to have set.
        """
        try:
            return self.sql(statement)
        except RuntimeError as exc:
            raise GuardFailure(
                f"cannot apply a server setting as {DB_USER}: {exc}. The probe needs "
                "superuser or pg_write_all_settings to toggle fsync; grant it or run "
                "the matrix without the fsync axis."
            ) from exc

    def can_alter_system(self) -> bool:
        return self.sql(
            "SELECT rolsuper OR pg_has_role(current_user, 'pg_write_all_settings', 'member') "
            "FROM pg_roles WHERE rolname = current_user"
        ) == "t"


# ---------------------------------------------------------------------------
# the snapshot
# ---------------------------------------------------------------------------

SNAPSHOT_SQL = f"""
SELECT json_build_object(
  'lsn_bytes', (pg_current_wal_lsn() - '0/0'::pg_lsn)::numeric,
  'wal',       (SELECT to_jsonb(w) FROM pg_stat_wal w),
  'db',        (SELECT to_jsonb(d) FROM pg_stat_database d WHERE d.datname = current_database()),
  'tables',    (SELECT jsonb_object_agg(relname, to_jsonb(t))
                  FROM pg_stat_user_tables t WHERE t.schemaname = '{SCHEMA}'),
  'io',        (SELECT jsonb_object_agg(relname, to_jsonb(s))
                  FROM pg_statio_user_tables s WHERE s.schemaname = '{SCHEMA}'),
  'settings',  (SELECT jsonb_object_agg(name, setting)
                  FROM pg_settings WHERE name IN ({','.join("'" + s + "'" for s in TRACKED_SETTINGS)}))
)::text
"""


def snapshot(pg: Postgres) -> dict:
    return json.loads(pg.sql(SNAPSHOT_SQL))


def _num(value) -> float:
    """Stats columns arrive as text or null; absent counters must not read as 0."""
    if value is None:
        return float("nan")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _table_delta(before: dict, after: dict, key: str, field_name: str) -> float:
    b = (before.get("tables") or {}).get(key) or {}
    a = (after.get("tables") or {}).get(key) or {}
    return _num(a.get(field_name)) - _num(b.get(field_name))


# ---------------------------------------------------------------------------
# derived metrics
# ---------------------------------------------------------------------------


@dataclass
class Amplification:
    mutations: int
    wal_bytes: float
    wal_records: float
    wal_fpi: float
    wal_sync_time_ms: float
    wal_sync_count: float
    rows_by_table: dict[str, float]
    hot_by_table: dict[str, tuple[float, float]]  # relname -> (hot_upd, upd)
    toast_blocks: float
    index_blocks: float
    commits: float
    latencies_ms: list[float] = field(default_factory=list)

    @property
    def rows_total(self) -> float:
        return sum(self.rows_by_table.values())

    @property
    def fan_out(self) -> float:
        return self.rows_total / self.mutations if self.mutations else float("nan")

    @property
    def wal_per_mutation(self) -> float:
        return self.wal_bytes / self.mutations if self.mutations else float("nan")

    @property
    def hot_ratio(self) -> float:
        hot = sum(h for h, _ in self.hot_by_table.values())
        upd = sum(u for _, u in self.hot_by_table.values())
        return hot / upd if upd else float("nan")

    @property
    def sync_ms_per_mutation(self) -> float:
        if self.mutations and self.wal_sync_time_ms == self.wal_sync_time_ms:
            return self.wal_sync_time_ms / self.mutations
        return float("nan")

    def as_dict(self) -> dict:
        lat = sorted(self.latencies_ms)
        pct = (lambda p: lat[min(int(len(lat) * p), len(lat) - 1)]) if lat else (lambda p: None)
        return {
            "mutations": self.mutations,
            "wal_bytes_total": self.wal_bytes,
            "wal_bytes_per_mutation": self.wal_per_mutation,
            "wal_records_per_mutation": self.wal_records / self.mutations if self.mutations else None,
            "wal_fpi_total": self.wal_fpi,
            "wal_sync_count": self.wal_sync_count,
            "wal_sync_time_ms_total": self.wal_sync_time_ms,
            "wal_sync_ms_per_mutation": self.sync_ms_per_mutation,
            "rows_written_total": self.rows_total,
            "rows_written_per_mutation": self.fan_out,
            "rows_written_by_table": self.rows_by_table,
            "hot_ratio": self.hot_ratio,
            "hot_by_table": {k: {"hot_upd": h, "upd": u} for k, (h, u) in self.hot_by_table.items()},
            "toast_blocks_touched": self.toast_blocks,
            "index_blocks_touched": self.index_blocks,
            "commits": self.commits,
            "latency_ms_p50": pct(0.50),
            "latency_ms_p95": pct(0.95),
            "latency_ms_mean": statistics.fmean(lat) if lat else None,
        }


def derive(before: dict, after: dict, mutations: int, latencies: list[float]) -> Amplification:
    wal_b, wal_a = before.get("wal") or {}, after.get("wal") or {}
    tables = set((before.get("tables") or {})) | set((after.get("tables") or {}))

    rows_by_table: dict[str, float] = {}
    hot_by_table: dict[str, tuple[float, float]] = {}
    toast = index = 0.0
    for t in sorted(tables):
        written = sum(
            _table_delta(before, after, t, f) for f in ("n_tup_ins", "n_tup_upd", "n_tup_del")
        )
        if written and written == written and written != 0:
            rows_by_table[t] = written
        upd = _table_delta(before, after, t, "n_tup_upd")
        hot = _table_delta(before, after, t, "n_tup_hot_upd")
        if upd and upd == upd and upd != 0:
            hot_by_table[t] = (hot, upd)
        io_b = (before.get("io") or {}).get(t) or {}
        io_a = (after.get("io") or {}).get(t) or {}
        for prefix, acc in (("toast_blks", "toast"), ("tidx_blks", "toast"), ("idx_blks", "index")):
            for suffix in ("read", "hit"):
                d = _num(io_a.get(f"{prefix}_{suffix}")) - _num(io_b.get(f"{prefix}_{suffix}"))
                if d == d and d > 0:
                    if acc == "toast":
                        toast += d
                    else:
                        index += d

    db_b, db_a = before.get("db") or {}, after.get("db") or {}
    return Amplification(
        mutations=mutations,
        wal_bytes=_num(wal_a.get("wal_bytes")) - _num(wal_b.get("wal_bytes")),
        wal_records=_num(wal_a.get("wal_records")) - _num(wal_b.get("wal_records")),
        wal_fpi=_num(wal_a.get("wal_fpi")) - _num(wal_b.get("wal_fpi")),
        wal_sync_time_ms=_num(wal_a.get("wal_sync_time")) - _num(wal_b.get("wal_sync_time")),
        wal_sync_count=_num(wal_a.get("wal_sync")) - _num(wal_b.get("wal_sync")),
        rows_by_table=rows_by_table,
        hot_by_table=hot_by_table,
        toast_blocks=toast,
        index_blocks=index,
        commits=_num(db_a.get("xact_commit")) - _num(db_b.get("xact_commit")),
        latencies_ms=latencies,
    )


# ---------------------------------------------------------------------------
# conditions, and proving they were in effect
# ---------------------------------------------------------------------------


class GuardFailure(RuntimeError):
    """A run whose measured conditions contradict its label is discarded."""


def tview_trigger_state(pg: Postgres) -> dict[str, str]:
    rows = pg.sql(
        "SELECT t.tgname, t.tgenabled FROM pg_trigger t "
        "JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
        f"WHERE n.nspname = '{SCHEMA}' AND c.relname = 'tb_user' "
        "AND NOT t.tgisinternal AND t.tgname LIKE 'trg_tview_%'"
    )
    return dict(line.split("|")[:2] for line in rows.splitlines() if "|" in line) if rows else {}


def set_cascade(pg: Postgres, enabled: bool) -> None:
    names = list(tview_trigger_state(pg))
    if not names:
        raise GuardFailure(
            "no trg_tview_* triggers on benchmark.tb_user -- pg_tviews is not installed "
            "on this database, so a cascade on/off comparison would be meaningless"
        )
    action = "ENABLE" if enabled else "DISABLE"
    pg.sql("; ".join(f"ALTER TABLE {SCHEMA}.tb_user {action} TRIGGER {n}" for n in names))
    state = tview_trigger_state(pg)
    want = "O" if enabled else "D"
    bad = {n: v for n, v in state.items() if v != want}
    if bad:
        raise GuardFailure(f"cascade={'on' if enabled else 'off'} not in effect: {bad}")


def resync_tview_user(pg: Postgres) -> int:
    """Recompute tv rows that drifted while the cascade was disabled.

    Same mechanism as the sweep's `resync_tview_user`: an identity update
    (bio = bio) on exactly the drifted rows re-fires the cascade without a
    full refresh. Triggers fire on UPDATE regardless of whether the value
    changed, which is why this works where fn_update_user's IS DISTINCT FROM
    guard would skip. A cascade-off cell that skipped this would leave the rig
    serving tv_* rows that disagree with tb_user -- silently wrong reads for
    every later measurement on the host.
    """
    return int(pg.sql(
        "WITH fixed AS ("
        f"  UPDATE {SCHEMA}.tb_user tb SET bio = tb.bio"
        f"  FROM {SCHEMA}.tv_user tv"
        "   WHERE tv.pk_user = tb.pk_user"
        "   AND tv.data->>'bio' IS DISTINCT FROM tb.bio"
        "   RETURNING 1"
        ") SELECT count(*) FROM fixed"
    ) or 0)


def set_fsync(pg: Postgres, value: str) -> None:
    """fsync is SIGHUP-changeable, so no restart is needed."""
    pg.superuser_sql(f"ALTER SYSTEM SET fsync = {value}")
    pg.superuser_sql("SELECT pg_reload_conf()")
    for _ in range(20):
        live = pg.sql("SHOW fsync")
        if live == value:
            return
        time.sleep(0.25)
    raise GuardFailure(f"fsync={value} claimed but server reports {pg.sql('SHOW fsync')}")


def ensure_wal_timing(pg: Postgres) -> bool:
    """wal_sync_time is the direct durability measurement; 0 would otherwise lie."""
    if pg.sql("SHOW track_wal_io_timing") == "on":
        return True
    try:
        pg.superuser_sql("ALTER SYSTEM SET track_wal_io_timing = on")
        pg.superuser_sql("SELECT pg_reload_conf()")
        time.sleep(0.5)
        return pg.sql("SHOW track_wal_io_timing") == "on"
    except RuntimeError:
        return False


def guard_window(label: str, before: dict, after: dict, amp: Amplification,
                 *, cascade: bool, mutations: int,
                 written_rows: int | None = None, expected_rows: int = 0) -> None:
    """Refuse to keep a measurement whose conditions moved under it."""
    for name in ("fsync", "full_page_writes", "synchronous_commit"):
        b = (before.get("settings") or {}).get(name)
        a = (after.get("settings") or {}).get(name)
        if b != a:
            raise GuardFailure(f"{label}: {name} changed mid-window ({b} -> {a})")

    # Stats-based check, kept loose: with a pooled driver these counters can lag
    # even after quiescence polling. The authoritative check is `written_rows`
    # below, read from the data itself.
    tb_user_upd = amp.rows_by_table.get("tb_user", 0.0)
    if written_rows is not None and written_rows < expected_rows:
        raise GuardFailure(
            f"{label}: only {written_rows} of the {expected_rows} target rows carry this "
            "cell's values -- the driver did not write what this run claims"
        )
    if written_rows is None and tb_user_upd < mutations * 0.9:
        raise GuardFailure(
            f"{label}: {mutations} mutations requested but tb_user shows only "
            f"{tb_user_upd:.0f} row writes -- the driver did not write what this run claims"
        )

    tv_writes = sum(v for k, v in amp.rows_by_table.items() if k.startswith("tv_"))
    if cascade and tv_writes <= 0:
        raise GuardFailure(
            f"{label}: cascade=on but ZERO tv_* row writes were observed. The triggers "
            "are enabled and did nothing -- exactly the beta.11 early-return shape that "
            "invalidated the 2026-07-04 mutation numbers."
        )
    if not cascade and tv_writes > 0:
        raise GuardFailure(
            f"{label}: cascade=off but {tv_writes:.0f} tv_* row writes were observed -- "
            "the disable did not take effect, so this cell is not a control"
        )


# ---------------------------------------------------------------------------
# drivers
# ---------------------------------------------------------------------------


def m1_user_ids(pg: Postgres, count: int = M1_USER_COUNT) -> list[str]:
    rows = pg.sql(f"SELECT id FROM {SCHEMA}.tb_user ORDER BY id LIMIT {count}")
    ids = [r for r in rows.splitlines() if r]
    if len(ids) < count:
        raise GuardFailure(f"need {count} users for M1's contention profile, found {len(ids)}")
    return ids


TIMING_RE = re.compile(r"^Time:\s+([0-9.]+)\s+ms", re.MULTILINE)


def drive_sql(pg: Postgres, ids: list[str], bios: list[str], mutations: int,
              concurrency: int, function: str) -> list[float]:
    """One statement per transaction, straight to the mutation function.

    This is the DB-only cost: no GraphQL parse, no runtime, no HTTP. Comparing it
    with the graphql driver attributes the runtime's share.

    All statements for a worker run in ONE psql session and latency comes from
    psql's own `\\timing`, not from wall-clock around the process. A first version
    spawned `docker exec psql` per mutation and reported 78.5 ms p50 for work that
    is a fraction of that -- the spawn was most of the measurement.
    """
    work = rotating_writes(ids, bios, mutations)

    def run_batch(batch: list[tuple[str, str]]) -> list[float]:
        if not batch:
            return []
        script = "\\timing on\n" + "".join(
            f"SELECT {function}('{uid}', '{bio}');\n" for uid, bio in batch
        )
        out = pg.script(script)
        times = [float(m) for m in TIMING_RE.findall(out)]
        if len(times) != len(batch):
            raise GuardFailure(
                f"psql reported {len(times)} timings for {len(batch)} statements -- "
                "the SQL driver cannot account for every mutation it claims to have run"
            )
        return times

    if concurrency <= 1:
        return run_batch(work)

    chunks: list[list[tuple[str, str]]] = [[] for _ in range(concurrency)]
    for i, job in enumerate(work):
        chunks[i % concurrency].append(job)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        return [t for batch in pool.map(run_batch, chunks) for t in batch]


def drive_graphql(endpoint: str, ids: list[str], bios: list[str], mutations: int,
                  concurrency: int) -> list[float]:
    """The same logical mutation through the FraiseQL runtime over HTTP."""
    work = rotating_writes(ids, bios, mutations)
    query = "mutation($id: ID!, $bio: String) { updateUser(id: $id, bio: $bio) { id bio } }"

    def one(job: tuple[str, str]) -> float:
        uid, bio = job
        body = json.dumps({"query": query, "variables": {"id": uid, "bio": bio}}).encode()
        req = urllib.request.Request(
            endpoint, data=body, headers={"Content-Type": "application/json"}
        )
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read())
        elapsed = (time.perf_counter() - t0) * 1000.0
        if "errors" in payload:
            raise GuardFailure(f"GraphQL error: {str(payload['errors'])[:200]}")
        return elapsed

    if concurrency <= 1:
        return [one(j) for j in work]
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        return list(pool.map(one, work))


# ---------------------------------------------------------------------------
# one cell of the matrix
# ---------------------------------------------------------------------------

STATS_SETTLE_SECONDS = 1.5   # a backend flushes pending stats at transaction end
STATS_QUIESCE_MAX_SECONDS = 25  # covers PG's idle-backend stats flush timeout (~10 s)


def wait_for_stats_quiescence(pg: Postgres, *, max_wait: float = STATS_QUIESCE_MAX_SECONDS) -> bool:
    """Block until the statistics views stop moving, or give up and say so.

    A fixed sleep is not enough with a POOLED driver. Postgres accumulates
    pg_stat_* and pg_stat_wal counters per backend and flushes them at
    transaction end, no more often than once a second; an idle pooled connection
    holds its pending counters until PG's idle flush timeout (~10 s) fires.
    Measured here: 5 GraphQL mutations that demonstrably wrote 5 rows (readback
    confirmed) moved n_tup_upd by 1. Polling to quiescence makes the window
    honest for both drivers instead of silently undercounting the pooled one.
    """
    probe = ("SELECT (SELECT wal_bytes FROM pg_stat_wal)::text || '/' || "
             "coalesce((SELECT n_tup_upd::text FROM pg_stat_user_tables "
             f"WHERE schemaname = '{SCHEMA}' AND relname = 'tb_user'), '0')")
    last, stable_since = None, None
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        now = pg.sql(probe)
        if now == last:
            if stable_since is None:
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= 1.5:
                return True
        else:
            last, stable_since = now, None
        time.sleep(0.75)
    return False


def flush_pooled_stats(pg: Postgres, *, expect_rows: int, max_wait: float = 14.0) -> str:
    """Make a pooled driver's pending statistics land, and say how.

    A backend's pg_stat_* / pg_stat_wal counters are flushed at transaction end
    (min 1 s apart) or, once idle, after PG's idle flush timeout. A quiescence
    poll cannot distinguish "flushed" from "never flushed": both look stable.
    Measured: 200 GraphQL mutations whose writes were verified in the data showed
    0.1 rows/mutation, because the pool sat idle holding its counters.

    So: wait for the counters to reach what the data says was written, and if
    they do not, terminate the application's idle backends -- a backend flushes
    pending stats on exit -- and report which path was taken, because a number
    obtained either way must be labelled.
    """
    target_sql = (f"SELECT coalesce((SELECT n_tup_upd FROM pg_stat_user_tables "
                  f"WHERE schemaname = '{SCHEMA}' AND relname = 'tb_user'), 0)")
    start = int(pg.sql(target_sql) or 0)
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        if int(pg.sql(target_sql) or 0) - start >= expect_rows:
            return "flushed-by-timeout"
        time.sleep(1.0)
    killed = pg.sql(
        "SELECT count(*) FROM ("
        "  SELECT pg_terminate_backend(pid) FROM pg_stat_activity"
        "  WHERE datname = current_database() AND pid <> pg_backend_pid()"
        "    AND coalesce(application_name, '') NOT LIKE 'psql%'"
        ") t"
    )
    time.sleep(2.0)
    return f"flushed-by-terminating-{killed}-backends"


def run_cell(pg: Postgres, *, cascade: bool, fsync: str, concurrency: int, mutations: int,
             driver: str, endpoint: str | None, function: str, wal_timing: bool,
             generation: str) -> dict:
    label = f"cascade={'on' if cascade else 'off'} fsync={fsync} c={concurrency} driver={driver}"
    print(f"  -> {label} ... ", end="", flush=True)

    set_cascade(pg, cascade)
    set_fsync(pg, fsync)
    ids = m1_user_ids(pg)
    bios = cell_bios(generation)

    wait_for_stats_quiescence(pg)
    before = snapshot(pg)
    t0 = time.perf_counter()
    if driver == "sql":
        latencies = drive_sql(pg, ids, bios, mutations, concurrency, function)
    else:
        if not endpoint:
            raise GuardFailure("--driver graphql needs --endpoint")
        latencies = drive_graphql(endpoint, ids, bios, mutations, concurrency)
    wall = time.perf_counter() - t0
    quiesced = wait_for_stats_quiescence(pg)
    flush_note = "quiesced" if quiesced else "not-quiesced"
    if driver != "sql":
        # The pool holds its counters; make them land before the after-snapshot.
        flush_note = flush_pooled_stats(pg, expect_rows=min(len(ids), mutations))
    after = snapshot(pg)

    # Authoritative, timing-independent: how many of the target rows actually
    # carry this cell's generation.
    written_rows = int(pg.sql(
        f"SELECT count(*) FROM {SCHEMA}.tb_user WHERE bio LIKE '%gen {generation}'"
    ) or 0)
    expected_rows = min(len(ids), mutations)

    amp = derive(before, after, mutations, latencies)
    guard_window(label, before, after, amp, cascade=cascade, mutations=mutations,
                 written_rows=written_rows, expected_rows=expected_rows)

    row = {
        "label": label,
        "cascade": "on" if cascade else "off",
        "fsync": fsync,
        "concurrency": concurrency,
        "driver": driver,
        "function": function if driver == "sql" else None,
        "endpoint": endpoint if driver == "graphql" else None,
        "wall_seconds": wall,
        "throughput_rps": mutations / wall if wall else None,
        "wal_timing_available": wal_timing,
        "stats_quiesced": quiesced,
        "stats_flush": flush_note,
        "rows_verified_written": written_rows,
        "settings": after.get("settings"),
        **amp.as_dict(),
    }
    print(f"{row['throughput_rps']:.0f} rps, {amp.wal_per_mutation/1024:.1f} KiB WAL/mutation, "
          f"{amp.fan_out:.1f} rows/mutation")
    return row


# ---------------------------------------------------------------------------
# classification
# ---------------------------------------------------------------------------


def classify(rows: list[dict]) -> list[str]:
    """Apply the decision rules the matrix exists to answer."""
    out: list[str] = []

    def find(**kw):
        for r in rows:
            if all(r.get(k) == v for k, v in kw.items()):
                return r
        return None

    def ratio(a, b, key="throughput_rps"):
        if a and b and a.get(key) and b.get(key):
            return b[key] / a[key]
        return None

    c1 = find(cascade="on", fsync="on", concurrency=1)
    cN = next((r for r in rows if r["cascade"] == "on" and r["fsync"] == "on"
               and r["concurrency"] > 1), None)
    if c1 and cN:
        per_mutation_ms = c1.get("latency_ms_mean")
        scale = ratio(c1, cN)
        out.append(
            f"intrinsic work: one mutation costs {per_mutation_ms:.1f} ms at concurrency 1 "
            f"({c1['throughput_rps']:.0f} rps serial); at concurrency {cN['concurrency']} "
            f"throughput scales {scale:.2f}x"
        )
        if scale is not None and scale < 1.5:
            out.append(
                "  => CONTENTION-BOUND: added concurrency buys almost nothing, so the limit is "
                "serialisation (M1 rotates 20 rows), not per-mutation work"
            )

    on = find(cascade="on", fsync="on", concurrency=1)
    off = find(cascade="off", fsync="on", concurrency=1)
    if on and off:
        gain = ratio(on, off)
        wal_drop = (on["wal_bytes_per_mutation"] - off["wal_bytes_per_mutation"])
        out.append(
            f"cascade share: disabling pg_tviews changes throughput {gain:.2f}x and removes "
            f"{wal_drop/1024:.1f} KiB WAL/mutation "
            f"({on['rows_written_per_mutation']:.1f} -> {off['rows_written_per_mutation']:.1f} rows/mutation)"
        )
        if gain and gain > 2:
            out.append("  => PROJECTION-MAINTENANCE-BOUND: the cascade dominates the write path")
        elif gain and gain < 1.3:
            out.append(
                "  => NOT cascade-bound: the sweep's attribution of 89 rps to the cascade does "
                "not survive this control"
            )

    fon = find(cascade="on", fsync="on", concurrency=1)
    foff = find(cascade="on", fsync="off", concurrency=1)
    if fon and foff:
        gain = ratio(fon, foff)
        out.append(f"durability share: fsync=off changes throughput {gain:.2f}x")
        if gain and gain > 2:
            out.append("  => DURABILITY-BOUND: storage engineering (WAL device, ZFS, SLOG) is on the critical path")
        elif gain and gain < 1.3:
            out.append(
                "  => NOT fsync-bound: no amount of NVMe/SLOG/ZIL tuning addresses this workload"
            )
        if fon.get("wal_sync_ms_per_mutation") == fon.get("wal_sync_ms_per_mutation"):
            out.append(
                f"     direct check: {fon['wal_sync_ms_per_mutation']:.2f} ms of wal_sync_time per "
                f"mutation out of {fon['latency_ms_mean']:.1f} ms total"
            )

    sql_row = find(driver="sql", cascade="on", fsync="on", concurrency=1)
    gql_row = find(driver="graphql", cascade="on", fsync="on", concurrency=1)
    if sql_row and gql_row:
        overhead = gql_row["latency_ms_mean"] - sql_row["latency_ms_mean"]
        out.append(
            f"runtime share: {overhead:.1f} ms per mutation above the SQL-only path "
            f"({sql_row['latency_ms_mean']:.1f} ms SQL vs {gql_row['latency_ms_mean']:.1f} ms GraphQL)"
        )

    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mutations", type=int, default=200, help="mutations per cell (default 200)")
    p.add_argument("--concurrency", type=int, default=1)
    p.add_argument("--driver", choices=("sql", "graphql", "both"), default="sql",
                   help="both runs the same function via SQL and via the runtime, "
                        "so the difference attributes the runtime share")
    p.add_argument("--endpoint", help="GraphQL endpoint for --driver graphql")
    p.add_argument("--function", default=f"{SCHEMA}.fn_update_user",
                   help="mutation function for --driver sql")
    p.add_argument("--cascade", choices=("on", "off"), default="on")
    p.add_argument("--fsync", choices=("on", "off"), default="on")
    p.add_argument("--matrix", action="store_true",
                   help="run cascade x fsync x concurrency{1,N} and classify")
    p.add_argument("--matrix-concurrency", type=int, default=40)
    p.add_argument("--container", help="postgres container (default: compose service)")
    p.add_argument("--dsn", help="connect with this DSN instead of docker exec")
    p.add_argument("--out", help="write the run JSON here")
    args = p.parse_args()

    pg = Postgres(container=args.container, dsn=args.dsn)
    original_fsync = pg.sql("SHOW fsync")
    original_triggers = tview_trigger_state(pg)
    wal_timing = ensure_wal_timing(pg)
    if not wal_timing:
        print("note: track_wal_io_timing is off and could not be enabled; "
              "wal_sync_time will be reported as unavailable rather than 0", flush=True)

    print(f"write-path probe: {args.mutations} mutations/cell, driver={args.driver}", flush=True)
    rows: list[dict] = []
    failures: list[str] = []
    try:
        if args.matrix:
            cells = [
                (True, "on", 1, "sql"), (True, "on", args.matrix_concurrency, "sql"),
                (False, "on", 1, "sql"), (True, "off", 1, "sql"),
            ]
        elif args.driver == "both":
            cells = [
                (args.cascade == "on", args.fsync, args.concurrency, "sql"),
                (args.cascade == "on", args.fsync, args.concurrency, "graphql"),
            ]
        else:
            cells = [(args.cascade == "on", args.fsync, args.concurrency, args.driver)]
        for cascade, fsync, conc, driver in cells:
            try:
                rows.append(run_cell(
                    pg, cascade=cascade, fsync=fsync, concurrency=conc,
                    mutations=args.mutations, driver=driver, endpoint=args.endpoint,
                    function=args.function, wal_timing=wal_timing,
                    generation=f"{int(time.time())}-{len(rows)}",
                ))
            except GuardFailure as exc:
                print(f"GUARD FAILED\n     {exc}", flush=True)
                failures.append(str(exc))
    finally:
        # Leave the rig exactly as it was found: a benchmark host that quietly
        # keeps fsync=off would poison every later measurement on it.
        try:
            set_fsync(pg, original_fsync)
            if original_triggers and all(v == "O" for v in original_triggers.values()):
                set_cascade(pg, True)
                drifted = resync_tview_user(pg)
                if drifted:
                    print(f"resynced {drifted} tv_user rows that drifted while the "
                          "cascade was disabled", flush=True)
            print(f"restored: fsync={pg.sql('SHOW fsync')}, "
                  f"tview triggers={set(tview_trigger_state(pg).values())}", flush=True)
        except Exception as exc:  # noqa: BLE001 - restoration failure must be loud
            print(f"WARNING: could not restore rig state: {exc}", flush=True)

    if rows:
        print("\n=== per-mutation physical cost " + "=" * 44)
        hdr = f"{'cell':38} {'rps':>7} {'rows':>6} {'HOT':>6} {'WAL KiB':>8} {'sync ms':>8} {'p50 ms':>7}"
        print(hdr)
        for r in rows:
            hot = r["hot_ratio"]
            sync = r["wal_sync_ms_per_mutation"]
            print(f"{r['label'][:38]:38} {r['throughput_rps']:7.0f} "
                  f"{r['rows_written_per_mutation']:6.1f} "
                  f"{(f'{hot*100:.0f}%' if hot == hot else 'n/a'):>6} "
                  f"{r['wal_bytes_per_mutation']/1024:8.1f} "
                  f"{(f'{sync:.2f}' if sync == sync else 'n/a'):>8} "
                  f"{r['latency_ms_p50']:7.1f}")

        verdicts = classify(rows)
        if verdicts:
            print("\n=== classification " + "=" * 57)
            for line in verdicts:
                print(line)

    out_path = Path(args.out) if args.out else (
        REPO / "reports" / "write-path" /
        f"probe-{datetime.now(timezone.utc):%Y-%m-%dT%H%M%SZ}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            k: int(pg.sql(f"SELECT count(*) FROM {SCHEMA}.{k}"))
            for k in ("tb_user", "tb_post", "tb_comment", "tv_user", "tv_post", "tv_comment")
        },
        "args": vars(args),
        "cells": rows,
        "guard_failures": failures,
        "classification": classify(rows) if rows else [],
    }, indent=2))
    try:
        shown = out_path.resolve().relative_to(REPO)
    except ValueError:
        shown = out_path
    print(f"\nrun JSON: {shown}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
