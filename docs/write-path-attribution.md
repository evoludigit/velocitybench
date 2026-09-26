# Write-path attribution — what one logical mutation physically costs

The July 2026 sweep reports M1 at **89 rps** and explains it as the pg_tviews
cascade: *"every write recomputes ~61 precomputed rows for always-consistent
reads."* That explanation is plausible, and the sweep cannot establish it.

`fraiseql-v-cache` and `fraiseql-v-nocache` — variants with no materialized
projections — write at **91 rps** in the same run. Not because the cascade is
innocent, but because **there is no cascade-free control**: every FraiseQL
service in `docker-compose.yml` points at the same database
(`velocitybench_benchmark`), every variant's `updateUser` maps to the same
`benchmark.fn_update_user`, and pg_tviews' triggers are installed for all of
them. The variants differ *only* in their read-side schema mapping
(`schema_v.compiled.json` vs `schema_tv.compiled.json`). So 89 rps is one write
path measured five times, and the candidate explanations — cascade work, row-lock
contention (M1 rotates **20** user rows under **40** workers, p50 223 ms / p99
3 349 ms), commit durability, and the runtime's own mutation path — are
unseparated.

`tests/benchmark/write_path_probe.py` separates them by measuring physical work
instead of inferring it from RPS.

## What it measures

| Axis | Cell | Question it answers |
|---|---|---|
| concurrency | `c=1` vs `c=40` | intrinsic per-mutation work, or serialisation? |
| cascade | triggers on vs off | how much of it is pg_tviews? |
| durability | `fsync=on` vs `off` | how much is the storage layer? |
| physical | WAL bytes, rows, HOT | what actually happened per mutation |
| runtime | `--driver sql` vs `graphql` | how much is FraiseQL above the database? |

Per cell it records: rows written per table, HOT ratio (`n_tup_hot_upd/n_tup_upd`),
WAL bytes and records per mutation, WAL FPIs, `wal_sync_time`, TOAST and index
blocks touched, commits, and latency percentiles.

## Running it

```bash
# the four-cell matrix and the classification
python3 tests/benchmark/write_path_probe.py --matrix --mutations 400

# the runtime's share: the same function via SQL and via the GraphQL runtime
python3 tests/benchmark/write_path_probe.py --driver both \
    --function benchmark.fn_update_user_full \
    --endpoint http://localhost:8818/graphql --mutations 400
```

It restores `fsync` and the trigger state on exit, and re-runs the sweep's
`resync_tview_user` equivalent after a cascade-off cell so the rig is never left
serving `tv_*` rows that disagree with `tb_user`.

## Measured on archbox, medium dataset (2026-09-26)

10 005 users / 100 005 posts / 500 005 comments, `benchmark.fn_update_user`,
400 mutations per cell. `reports/write-path/canonical-archbox-2026-09-26.json`.

| cell | rps | rows/mut | HOT | WAL KiB/mut | sync ms/mut | p50 ms |
|---|---:|---:|---:|---:|---:|---:|
| cascade on, fsync on, c=1 | 544 | 12.0 | 8% | 27.9 | 0.25 | 1.7 |
| cascade on, fsync on, c=40 | 269 | 12.0 | 8% | 30.4 | 1.11 | 90.1 |
| cascade off, fsync on, c=1 | 1 446 | 1.0 | 100% | 0.2 | 0.30 | 0.5 |
| cascade on, fsync off, c=1 | 653 | 12.0 | 8% | 25.6 | 0.00 | 1.3 |

Read together:

- **Concurrency is negative.** 40 workers deliver **0.49×** the throughput of one
  (269 vs 544 rps) and p50 goes 1.7 → 90.1 ms. The limit at load is
  serialisation on the 20 rotating rows, not per-mutation work. A single serial
  SQL client already beats the sweep's 40-worker figure by ~6×.
- **The cascade is the per-mutation cost.** It accounts for 11 of 12 rows written,
  27.7 of 27.9 KiB of WAL, and it collapses HOT from 100% to **8%** — which is the
  mechanism behind the April fresh-vs-fragmented effect, now measured rather than
  assumed. Disabling it is 2.66×.
- **Durability is not the constraint.** `fsync=off` buys 1.20×, and `wal_sync_time`
  is 0.25 ms of a 1.7 ms mutation. On this hardware no SLOG, ZIL or NVMe choice
  addresses this workload.
- **The runtime roughly doubles the mutation.** Same function, via SQL vs via
  GraphQL at c=1: 1.8 ms → 3.2 ms (489 → 306 rps), so **+1.4 ms** is FraiseQL and
  HTTP above the database.

⚠ **`rows/mutation` is data-dependent, not 61.** These 20 users fan out to 12 rows.
The report's ~61 is a different user population; fan-out scales with the user's
post and comment counts, so it is a property of the row, not of the architecture.

⚠ **WAL bytes per mutation is noisy** (25–63 KiB observed across runs) because
full-page images depend on checkpoint timing. Take medians of ≥3 runs before
quoting it, as the sweep does for RPS.

## Three traps this probe hit, and now guards against

1. **`fn_update_user` skips no-op writes.** It guards its UPDATE with
   `bio IS DISTINCT FROM p_bio`. The first version of the probe paired 20 users
   with 10 bios index-parallel, which gives user *k* the constant bio *k%10*
   whenever the pool sizes divide — so after one cycle every mutation wrote
   nothing while throughput looked nominal. The sweep's `_rotating_writes`
   documents the same trap; the probe now uses its cycle-based pairing, and each
   cell tags its values with a generation so a later cell cannot replay an
   earlier one's writes.
2. **A pooled driver holds its statistics.** Postgres flushes `pg_stat_*` and
   `pg_stat_wal` per backend at transaction end, at most once a second, and an
   idle pooled connection keeps them until PG's idle flush timeout. 200 verified
   GraphQL writes showed **0.1 rows/mutation** until the probe learned to wait for
   the counters to reach what the data says, and failing that to terminate the
   application's idle backends (a backend flushes on exit). Every cell records
   which path it took in `stats_flush`.
3. **A condition that silently does not apply.** Each cell verifies its own label
   before its numbers are kept: `SHOW fsync` must equal the claim, the trigger
   states must match, settings must not move mid-window, the target rows must
   actually carry this cell's values, and a cascade-on cell must observe non-zero
   `tv_*` writes while a cascade-off cell must observe **zero**. That last pair is
   deliberate: a cascade that is enabled and does nothing is exactly the beta.11
   early-return that invalidated the 2026-07-04 mutation numbers.

## On Hetzner

The numbers above are archbox (i7-13700K, mdadm RAID1 NVMe). They do not transfer:
`fsync` cost is a property of the device, and the concurrency result is a property
of the core count. Re-measure on the SUT.

See `docs/reproducing-on-hetzner.md` § "Write-path attribution" for the procedure.
The probe discovers the compose `postgres` service automatically, or takes
`--dsn`. Run it on the SUT itself, not from the load generator: it is a
measurement of the database host, and a network round trip per mutation would be
measured as work.
