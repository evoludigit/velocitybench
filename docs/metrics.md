# Benchmark Metrics — Definitions and Measurement Windows

Companion to [scenarios.md](scenarios.md). Canonical implementation:
`tests/benchmark/bench_sequential.py` (`RssSampler`, `measure_cold_start`,
`format_cost_section`).

## rss_steady_mb / rss_max_mb (per sweep row)

Container RSS sampled every 2 s **strictly inside the measurement window** —
never during warmup — via `docker stats` on the SUT container (same cgroup
source and cadence for every framework; no per-framework special-casing).
`rss_steady_mb` is the median of the window's samples, `rss_max_mb` the max.
`null` when the SUT container is not locally visible (e.g. remote SUT via
`--target-host`) — absent, not zero.

**JVM caveat**: JVM RSS reflects the heap ceiling the GC has claimed, not live
demand. The `spring-boot*` rows are measured with default flags and must be
read as "memory the process holds", not "memory the workload needs". A
`-Xmx`-capped variant was considered and rejected for the headline table:
tuning one framework's memory flags and nobody else's is exactly the
per-framework special-casing this metric bans.

## cold_start_ms (per framework, stamped on every row)

Median of **5** repeats of: `docker compose stop` → `docker compose start` →
first Q1 request returning HTTP 200 with a correct body, polled at 50 ms.

**Inside the measured window**: docker CLI dispatch, container start, app
boot, config/metadata load, connection-pool setup, first query execution —
the operator-visible cost of "the service restarted".

**Outside by construction**: image pull/build (the container already exists)
and database seeding (PostgreSQL stays up throughout).

`null` when the framework has no plain Q1 document or a repeat exceeds the
framework's start timeout. Skipped entirely under `--no-isolation` (restarting
shared containers would disturb concurrently running services) and with
`--skip-cold-start`.

## Cost composite (report section)

`€ / 1M requests = price_month ÷ (Q1 RPS × 2 628 000 s) × 10⁶` and
`RPS per €/month = Q1 RPS ÷ price_month`, computed against the dated price
table `costs/instance-prices-2026-07.yaml` (Hetzner CCX23/CCX33, captured
2026-07-04 — note Hetzner raised CCX prices 122–173% on 2026-06-15).

Only meaningful for sweeps run **on** the priced instance class; on any other
hardware the column is a projection. The capacity-projection app under
`costs/` (assumed RPS-per-core, AWS/GCP/Azure recommendations) is
**superseded** by this derivation for report purposes — one measured cost
model, not two.
