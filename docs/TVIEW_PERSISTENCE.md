# TVIEW Persistence: Logged vs UNLOGGED

pg_tviews creates its `tv_*` tables **logged** unless a TVIEW's options say
`{"logged": false}`. The benchmark database initializes with logged tables
unless told otherwise.

## The trade

| | Logged (default) | UNLOGGED |
|---|---|---|
| WAL | written | skipped |
| Write throughput | baseline | ~2–3× faster |
| Crash recovery | full | **table truncated** |
| Physical replication | yes | no |

UNLOGGED is a legitimate production choice for derived data — pg_tviews can
rebuild a truncated tview from its base tables (see `src/lifecycle.rs` crash
detection) — but published mutation throughput numbers must not silently ride
on skipped WAL. The publishable profile therefore benchmarks logged tables;
UNLOGGED results belong in a clearly-labeled appendix.

## Selecting the mode

The mode is fixed at **cluster init** (tviews are created by the init scripts):

```bash
# Logged (default)
docker compose up -d postgres

# UNLOGGED (appendix runs)
docker compose down -v
TVIEW_PERSISTENCE=unlogged docker compose up -d postgres
```

Implemented by `database/01z-tview-persistence.sh`, which records the TVIEW
options (`{"logged": false}` for UNLOGGED) in `velocitybench.tview_options` at
the database level; `database/fraiseql_cqrs_schema.sql` passes them to each
`tviews.pg_tviews_create()`. pg_tviews takes persistence as a TVIEW option, not
a setting.

## The guard

`bench_sequential.py` refuses to run when the live tables contradict the
claimed mode:

```bash
python tests/benchmark/bench_sequential.py --tview-mode logged   # default
python tests/benchmark/bench_sequential.py --tview-mode unlogged # appendix
```

The check reads `pg_class.relpersistence` for `benchmark.tv_*`; any mismatch
aborts the sweep, and the mode that actually ran is recorded in the run JSON
(`environment.tview_mode`). `tests/benchmark/test_tview_persistence.py` runs
the same check standalone.
