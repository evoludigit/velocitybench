# FraiseQL 2.14.0 vs 2.15.0 — A/B preflight (no performance measurement)

**Date:** 2026-08-22 · **Branch:** `bench/fraiseql-215-ab`

## Verdict

**No verdict on performance. Nothing was measured.** The benchmark run was not
executed and nothing was billed — the operator elected to hold until `v2.15.0` is
actually tagged, because at the time of writing no such tag existed and the 2.15
side could only be built from a moving `dev`.

Everything that can be established without renting hardware **was** established,
and all preflight gates pass. The campaign is ready to run against a tagged
2.15.0 after rebuilding the 2.15 side at the tag.

### `dev` moved during this session

The 2.15 side was built from `dev` at `1a0894eb0`. Roughly ninety minutes later,
within this same session, `dev` had advanced to `4388c7130`:

```
4388c7130 test(federation): re-bless the subgraph SDL fixtures for the typed filter inputs
```

That commit is test-fixture-only and changes nothing at runtime, so it does not
invalidate anything measured here. The point is the rate: a branch that gains a
commit inside a single working session is not a stable basis for a published
performance comparison. Pinning the build by SHA rather than by branch name is
what makes this report reproducible, and it is a concrete argument for holding
the paid campaign until `v2.15.0` is tagged.

## What was built

| Side | Ref | Commit | Toolchain |
|---|---|---|---|
| 2.14 | tag `v2.14.0` | `c2a610cf6` | rustc 1.94.1 |
| 2.15 | `dev` HEAD | `1a0894eb0` | rustc 1.94.1 |

`release/2.15.0` was **stale at `0fe785b07`, 24 commits behind `dev`**, and was
correctly ignored. No `v2.15.0` tag existed locally or on origin.

Both sides, identical commands:

```
cargo +1.94.1 build --release --package fraiseql --features cli,server,postgres
cargo +1.94.1 build --release --package fraiseql-server
```

| | cli | server |
|---|---|---|
| 2.14 @ 1.94.1 | 16,861,600 | 18,664,680 |
| 2.15 @ 1.94.1 | 20,489,968 | 24,250,240 |
| 2.14 @ 1.92 (fingerprint only) | 17,191,896 | 19,053,576 |

### The toolchain confound — not in the original plan

`v2.14.0` pins rustc **1.92**; `dev` pins **1.94.1**. Building each side at its
own pin charges a compiler difference to the version. Measured directly: the same
2.14 source, same features, same commands, built at 1.92 vs 1.94.1 differs by
**−330,296 bytes (cli) and −388,896 bytes (server)** — roughly 2% of codegen.
That is well within the range that moves throughput by a few percent, and it would
have been silently attributed to 2.15's validation work.

Both measured binaries are therefore built at **1.94.1**, so the only difference
between the A and B sides is source. A third build (2.14 @ 1.92) exists solely to
validate the feature set against a known constant, and is not shipped.

### The feature-set fingerprint is path-length-dependent

The plan specifies that a correct lean 2.14 cli is **exactly 17,191,512 bytes**.
The rebuild produced **17,191,896** — 384 bytes over. This is *not* a feature-set
error. Both binaries embed their build directory exactly **30 times**; the
reference was built in `/home/lionel/code/fraiseql` (26 chars) and this one in a
worktree at `/home/lionel/code/fraiseql-vbench-214` (37 chars). 30 × 11 = **330
bytes**, against a measured `.rodata.str1.1` delta of **+326** (the 4-byte gap is
ordinary string-table dedup). Total embedded path bytes: 2,293 vs 2,623.

Corroborating evidence that the feature set is identical:

- **29 of 32 ELF sections byte-identical in size.** Only `.rodata.str1.1` (+326,
  the paths), `.relro_padding` (−384, compensating) and `.text` (+64) move.
- **`.text` differs by 64 bytes out of 13,358,657** — 0.0005%. A feature-set
  change moves `.text` by megabytes (cf. the lean 18 MB vs full 103 MB artifacts).
- **`--help` byte-identical**, same subcommands, differing only in the program's
  own name (`fraiseql-cli` vs `fraiseql`, i.e. the post-build rename).

*Not* available as evidence: both binaries are stripped, so the static symbol
table comparison — which would have been the cleanest proof — returned nothing.

**Recommendation:** restate the fingerprint as "17,191,512 **when built at a
26-character path**". As written it fails for anyone building in a worktree,
which is what the plan instructs.

## Preflight gates

| Gate | Result |
|---|---|
| 0 — branch intact | 8 modified tracked files, 2 predating untracked reports |
| 1 — builds | both sides, identical commands, feature set proven identical |
| 2 — proof-of-build | **PASS** |
| 3 — artifact equivalence | **PASS**, both variants |
| 4 — runtime equivalence | **PASS**, 28/28 |
| Trap 4 — new rejected config keys on dev | none |

### Gate 2 — proof the tightened build is what would be measured

`{ users(limit: 2, bogusArg: 1) { id } }`, all four variant pairs:

- 2.14 (8815/8816/8817/8819): **answers**, argument silently dropped.
- 2.15 (8825/8826/8827/8829): **refused** — `Validation error: Unknown argument
  'bogusArg' on field 'Query.users'` (`VALIDATION_ERROR`).

This gate is **load-bearing, not a double-check** — see the `input_types`
correction below.

### Gate 3 — compiled artifact equivalence

Measured surface **identical** on both the `v` and `tv` variants: 7 queries
(`comment comments post postFull posts user users`), 2 mutations (`createPost`
`updateUser`), 4 types, matching enums / interfaces / subscriptions /
session_variables / naming_convention.

Differences confined to the three permitted keys: `_content_hash`, `input_types`
(47,693 B → empty), `security` (5,989 B → 1,073 B).

### Gate 4 — local runtime equivalence

Q1/Q2/Q2b/Q3/F1/F2/F3 across all four pairs: **28/28 identical** on parsed JSON.
`updateUser` succeeds on both sides. Queries were taken verbatim from
`tests/benchmark/bench_sequential.py` rather than reconstructed.

## What actually moved between 2.14 and 2.15

Measured at runtime via introspection, not inferred:

| | 2.14 | 2.15 |
|---|---|---|
| `Query.users(where:)` | `JSON` | `UserWhereInput` |
| `Query.users(orderBy:)` | `JSON` | `UserOrderByInput` |
| `INPUT_OBJECT` count | 49 | 10 |
| total published types | 66 | 28 |

2.14 ships 49 generic pre-baked filter inputs, nearly all irrelevant to this
schema (`APIKeyWhereInput`, `CIDRWhereInput`, `AirportCodeWhereInput`, …). 2.15
derives 10 from the schema itself. This is `31ae3b41c` working as intended, and
it explains the compiled artifact shrinking 97 KB → 15 KB.

It changes the **published** surface, not the **measured** surface, so the A/B
remains valid.

## Corrections to the plan

1. **Teardown was not trapped on `EXIT`** — the most expensive error in the plan.
   `trap 'collect_results || true; cost_note' EXIT` never called `destroy_all`,
   which ran only on the success path. A failed sweep (the script `exit 1`s on
   one) or any interruption left **both instances billing**. Provisioning had no
   trap at all. Fixed on this branch: an `on_abort` handler armed before the first
   billable resource exists, which collects results, destroys without an
   interactive confirm (an abort nobody is watching must not block on `read`),
   reports cost, and exits with the original code. `--keep` still wins. Both paths
   verified in `--plan` mode.

2. **`input_types` is not a build-freshness signal**, contrary to an early
   assumption made here. A `dev`-built (`1a0894eb0`) artifact is **byte-identical**
   to one built from the stale `0fe785b07` — 15,465 and 15,505 bytes, `cmp` clean.
   `31ae3b41c` adds `crates/fraiseql-core/src/schema/derived_inputs.rs` and touches
   `introspection/*`, deriving the typed inputs at introspection time rather than
   materialising them into the compiled JSON. The compiled artifact therefore
   **cannot** distinguish the two builds; only the Gate 2 runtime probe can.

3. **The disk claim was wrong in both halves.** Not "work volume 36%, guard fires
   at 80%": `/var` is **82% used (35 GB free)** — the "36%" appears to be 36 GB
   misread as a percentage — and the guard is
   `_check_disk_space(min_gb=5.0)` in `bench_sequential.py`, an absolute 5 GB floor
   on `/`, which has 92 GB free. It watches a different filesystem from the one
   that fills, and will not fire on a `/var` exhaustion.

4. **The fingerprint is path-length-dependent** (above).

5. **`scripts/hetzner/bench-run.sh` was already among the 8 modified files**, so
   the teardown fix does not change the Phase 0 file count.

## Fixed while here

**Bio drift was silently biasing reads.** `bench_bio_snapshot` snapshots bios *at
sweep start from whatever is in the database*, so it preserves drift rather than
restoring seed values. Three users carried short smoke-test bios — `alice =
smoke-215` and `dave = b17-verify` from earlier sessions, and `bob` from this
session's Gate 4 mutation. The harness docstring notes seeded bios are TOAST-sized
and that shrinking them makes reads measure faster. All three restored from
`database/fraiseql_cqrs_schema.sql` (42/48/42 chars); tview cascade verified
consistent at 10005/10005.

This would have biased **absolute** numbers against the published 2026-07-25 run.
It would **not** have biased the A/B delta, since the pairs are interleaved on one
box under one seed.

## What was NOT measured — stated plainly

- **Everything performance.** No latency, no throughput, no error rate, no RSS,
  for any scenario or variant. No Hetzner instance was ever provisioned; `hcloud
  server list` was empty before and after.
- **Whether `validate_argument_names` on the hot path costs anything.** That is
  the entire open question and it remains open. `QueryDefinition::accepted_argument_names()`
  returning a `Vec<String>` per request is still an unmeasured allocation.
- **The noise floor.** postgraphile / hasura / async-graphql were never run, so
  there is no baseline against which a fraiseql delta could be judged.
- **`orderBy` validation (`411947890`) is not covered by this benchmark at all.**
  `_FRAISEQL_F3` is `{ users(limit: 20) { id username fullName } }` — identical to
  Q1, with a source comment saying `orderBy` was deferred "once syntax confirmed".
  No scenario exercises `orderBy`, so the tightened sort validation would go
  unmeasured even if the campaign ran. Changing F3 would break comparability with
  the published run, so this is reported rather than silently altered.
- **Correctness.** This is a performance gate; correctness is a separate
  workstream.
- Local equivalence was checked on a loaded workstation (load ~14.5/24 with a
  concurrent test suite running). That is fine for equivalence, which is what it
  was used for, and it is *not* evidence about timing.

## To resume when v2.15.0 is tagged

1. Rebuild the 2.15 side at the tag — the binaries in `frameworks/fraiseql/` are
   `dev` `1a0894eb0`, **not** a release. See `fraiseql-cli-2.PROVENANCE.txt`.
   The 2.14 side is built at the immutable `v2.14.0` tag and can be reused.
2. Re-run gates 2–4 (~5 minutes; all scripts retained).
3. `FRAMEWORKS="fraiseql-tv fraiseql215-tv fraiseql-tv-cache fraiseql215-tv-cache \
   fraiseql-v-nocache fraiseql215-v-nocache fraiseql-v-cache fraiseql215-v-cache \
   postgraphile hasura async-graphql" scripts/hetzner/bench-run.sh --sweeps=3`
4. Prove `hcloud server list` is empty afterwards regardless of what the script says.
