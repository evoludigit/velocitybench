# Reproducing the Benchmark on Hetzner

Every published number in this repository was produced on rented Hetzner Cloud
hardware that anyone can rent and re-run with one command. Validated live on
2026-07-05.

## What you need

- A Hetzner Cloud project and the [`hcloud` CLI](https://github.com/hetznercloud/cli)
  authenticated (`hcloud context create <name>` or `HCLOUD_TOKEN`)
- A **dedicated-vCPU quota of at least 8 cores** (the CCX33 SUT uses all 8;
  request a limit increase if your project is lower)
- `ssh`, `rsync`, `python3` locally
- This repository checked out

## One command

```bash
scripts/hetzner/bench-run.sh          # prompts before destroying anything
scripts/hetzner/bench-run.sh --plan   # print every action, call nothing
```

The script provisions a **CCX33 SUT** (8 dedicated vCPU / 32 GB, the machine
under test) and a **CPX42 load generator** (8 shared vCPU — validated by a
mandatory headroom gate: k6 against a canned-response null target on the SUT
must sustain ≥30 000 RPS over the private network; measured 72–73k RPS,
2.4× the fastest framework). Framework ports are reachable only on the
private network; the public firewall allows SSH alone.

It then seeds the database (10 000 users · 50 000 posts · 200 000 comments +
500 005-row tview build, waited on over TCP), runs **two sequential sweeps**
of the publishable framework subset, rsyncs `reports/` back, prints the
session cost, and **destroys every resource it created** (all carry the label
`velocitybench=2026-07`; `--keep` skips destruction for debugging).

## The first sweep on a fresh database is a warm-up — discard it

Measured on 2026-07-05: the very first sweep after seeding stalls
write-heavy scenarios (342 deadlocks recorded in `pg_stat_database`;
lock-wait tails hitting the 30 s pool timeout) while PostgreSQL digests the
fresh bulk load. The second and third sweeps on the same box were spotless
(118/118 scenario rows, 0 errors, twice in a row). Publishable numbers must
come from warm sweeps only; run-to-run comparison of the two warm sweeps via

```bash
python3 scripts/bench-delta.py reports/hetzner-*/…sweep2.json reports/hetzner-*/…sweep3.json
```

showed stable throughput (12/118 RPS cells past ±5%) with the residual
variance concentrated in p99 tails.

## Cost (July 2026 prices, net)

| Resource | Rate | Session share |
|----------|-----:|--------------:|
| CCX33 SUT | €0.2219/h | ~6.4 h ≈ €1.42 |
| CPX42 loadgen | €0.1114/h | ~6.1 h ≈ €0.68 |
| **Full 3-sweep session** | €0.3333/h pair | **≈ €2.10** |

A single warm sweep takes ≈ 2 h 05 (12 frameworks × full scenario set at
30 s measure / 10 s warmup, cold-start restarts included). Nothing runs
overnight: the script destroys the instances at the end of the session.

## Write-path attribution

The published sweep answers *how fast*. It does not answer *why* M1 is 89 rps:
every FraiseQL variant shares one database, one `benchmark.fn_update_user` and one
set of pg_tviews triggers, so the sweep contains no cascade-free control and
cannot separate projection maintenance from row-lock contention, durability, and
the runtime's own cost. `docs/write-path-attribution.md` explains the four-cell
design; this is how to run it on the SUT.

```bash
scripts/hetzner/bench-run.sh --write-path          # sweeps, then the probe
scripts/hetzner/bench-run.sh --plan --write-path   # print the commands only
```

It adds roughly three minutes to a session and writes
`reports/write-path/matrix-<date>.json` plus
`reports/write-path/runtime-share-<date>.json`, rsynced back with the rest.

Three properties of the step matter:

- **It runs on the SUT, not the loadgen.** This measures the database host; a network round trip per mutation would be counted as per-mutation work. The sweeps are the opposite — they must cross the private network.
- **It runs after the last sweep, never beside one.** It toggles `fsync` and the pg_tviews triggers server-wide, which would corrupt a sweep in flight. It restores both on exit and resyncs `tv_*` after the cascade-off cell.
- **Its numbers are a property of this hardware.** `fsync` cost belongs to the device and the concurrency result to the core count, so archbox figures do not transfer to a CCX33 and vice versa. Each run JSON stamps the dataset sizes and the live server settings it observed.

Because the probe follows the warm sweeps, it measures a **fragmented** heap
rather than a freshly seeded one — which is the state a long-lived deployment is
actually in, and the state in which the April fresh-vs-post-cascade effect
appeared. To measure the fresh side instead, run it before the first sweep and
label it accordingly.
