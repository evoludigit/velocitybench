"""M1/MC1 redesign: every mutation request must perform a real write.

Finding 2026-07-04 (phase-artifacts/finding-m1-design-invalid-2026-07-04.md):
- fraiseql M1 sent a constant bio → fn_update_user's no-op short circuit made
  21k "mutations"/s that never wrote;
- classical M1 baked ONE user UUID → 40 workers serialized on a single row's
  ~30 ms tview cascade (~45 RPS for every framework, actix included);
- M1d's pairing (bios[i % 10] over users*10 with 20 users) gave each user a
  CONSTANT bio — no-ops after the first cycle.

The fix: cycle-based rotation (each full pass over the user pool advances the
bio), applied to M1, M1d, MC1, and M1_APQ for every framework; pg_tviews
triggers scoped to the FraiseQL stacks; and a live write-effect probe per
framework at sweep time.
"""

import subprocess
import sys
import uuid
from pathlib import Path

import pytest

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import bench_sequential as bench  # noqa: E402


# ── Rotation pairing ────────────────────────────────────────────────────────

def test_rotating_writes_covers_full_grid():
    users = [str(uuid.uuid4()) for _ in range(20)]
    bios = [f"bio-{i}" for i in range(10)]
    pairs = bench._rotating_writes(users, bios)
    assert len(pairs) == 200
    assert {(u, b) for u, b in pairs} == {(u, b) for u in users for b in bios}


def test_rotating_writes_consecutive_visits_change_bio():
    """The M1d regression: same user's consecutive visits must differ in bio,
    even when len(users) is a multiple of len(bios)."""
    users = [f"u{i}" for i in range(20)]
    bios = [f"bio-{i}" for i in range(10)]
    pairs = bench._rotating_writes(users, bios)
    last_bio: dict[str, str] = {}
    for u, b in pairs:
        assert last_bio.get(u) != b, f"user {u} visited twice with bio {b}"
        last_bio[u] = b


# ── Templates parametrize bio ───────────────────────────────────────────────

def test_m1_templates_have_no_hardcoded_bio():
    for tmpl in (bench._GQL_M1_TMPL, bench._GQL_M1_FLAT_TMPL,
                 bench._HASURA_M1_TMPL, bench._PG_M1_TMPL):
        assert "{bio}" in tmpl, f"template must parametrize bio: {tmpl[:60]}"
        assert 'bio: "bench"' not in tmpl
    for fw_name, cfg in bench.FRAMEWORKS.items():
        tmpl = cfg.get("m1_template")
        if isinstance(tmpl, str):
            assert 'bio: "bench"' not in tmpl and 'bio: \\"bench\\"' not in tmpl, \
                f"{fw_name} m1_template hardcodes bio"


# ── k6 translation of the rotating modes ────────────────────────────────────

def test_k6_graphql_rotating_mode():
    entry = {"mode": "graphql_rotating", "url": "http://x/graphql",
             "payloads": [b'{"query":"a"}', b'{"query":"b"}']}
    steps = bench._entry_to_k6_steps(entry, "graphql", "M1")
    assert len(steps) == 1
    assert steps[0]["bodies"] == ['{"query":"a"}', '{"query":"b"}']


def test_k6_rest_rotating_mode():
    entry = {"mode": "rest_rotating", "method": "PUT",
             "urls": ["http://x/users/1", "http://x/users/2"],
             "bodies": ['{"bio":"bio-0"}', '{"bio":"bio-1"}']}
    steps = bench._entry_to_k6_steps(entry, "rest", "M1")
    assert len(steps) == 1
    assert steps[0]["urls"] == entry["urls"]
    assert steps[0]["bodies"] == entry["bodies"]
    assert steps[0]["method"] == "PUT"


def test_k6_mc1_classical_rotates_mutation_bodies():
    entry = {"mode": "mc1_classical", "url": "http://x/graphql",
             "m1_payloads": [b'{"query":"m1"}', b'{"query":"m2"}'],
             "q1_payload": b'{"query":"q"}'}
    steps = bench._entry_to_k6_steps(entry, "graphql", "MC1")
    assert len(steps) == 2
    assert steps[0]["bodies"] == ['{"query":"m1"}', '{"query":"m2"}']
    assert steps[1]["body"] == '{"query":"q"}'


def test_k6_script_supports_url_rotation():
    src = (BENCH_DIR / "k6" / "scenario.js").read_text()
    assert "urls" in src, "scenario.js must rotate step.urls like step.bodies"


# ── Trigger scoping ─────────────────────────────────────────────────────────

def test_only_fraiseql_frameworks_keep_tview_triggers():
    for fw_name, cfg in bench.FRAMEWORKS.items():
        if fw_name.startswith("fraiseql"):
            assert cfg.get("tview_triggers") is True, fw_name
        else:
            assert not cfg.get("tview_triggers"), fw_name


def test_trigger_scoping_helpers_exist():
    assert callable(bench.set_tview_triggers)
    assert callable(bench.resync_tview_user)


def _postgres_running() -> bool:
    out = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False,
    )
    return "velocitybench-postgres-1" in out.stdout


@pytest.mark.skipif(not _postgres_running(), reason="postgres container not running")
def test_trigger_disable_resync_roundtrip():
    """Disable triggers → write drifts tv_user → enable + resync restores it."""
    sql = bench._psql  # tiny helper: run SQL via docker compose exec, return rows
    row = sql("SELECT id, bio FROM benchmark.tb_user ORDER BY pk_user LIMIT 1")[0]
    uid, orig_bio = row[0], row[1]
    try:
        bench.set_tview_triggers(False)
        sql(f"UPDATE benchmark.tb_user SET bio = 'drift-test' WHERE id = '{uid}'")
        stale = sql(
            "SELECT tv.data->>'bio' FROM benchmark.tv_user tv "
            f"JOIN benchmark.tb_user tb USING (pk_user) WHERE tb.id = '{uid}'"
        )[0][0]
        assert stale != "drift-test", "trigger fired while disabled"
        bench.set_tview_triggers(True)
        resynced = bench.resync_tview_user()
        assert resynced >= 1
        fresh = sql(
            "SELECT tv.data->>'bio' FROM benchmark.tv_user tv "
            f"JOIN benchmark.tb_user tb USING (pk_user) WHERE tb.id = '{uid}'"
        )[0][0]
        assert fresh == "drift-test"
    finally:
        bench.set_tview_triggers(True)
        orig = "NULL" if orig_bio is None else f"'{orig_bio}'"
        sql(f"UPDATE benchmark.tb_user SET bio = {orig} WHERE id = '{uid}'")
        bench.resync_tview_user()


# ── Bio snapshot/restore (dataset hygiene across frameworks) ───────────────

@pytest.mark.skipif(not _postgres_running(), reason="postgres container not running")
def test_bio_snapshot_restore_roundtrip():
    """Rotating writes shrink the TOASTed bios Q1 reads — restore must return
    the dataset to its seeded state between frameworks."""
    sql = bench._psql
    row = sql("SELECT id, bio FROM benchmark.tb_user ORDER BY pk_user LIMIT 1")[0]
    uid, orig_bio = row[0], row[1]
    bench.snapshot_user_bios()
    try:
        sql(f"UPDATE benchmark.tb_user SET bio = 'bio-7' WHERE id = '{uid}'")
        restored = bench.restore_user_bios()
        assert restored >= 1
        live = sql(f"SELECT bio FROM benchmark.tb_user WHERE id = '{uid}'")[0][0]
        assert live == orig_bio
    finally:
        bench.restore_user_bios()


def test_reset_postgres_state_restores_bios():
    src = (BENCH_DIR / "bench_sequential.py").read_text()
    reset_fn = src.split("def _reset_postgres_state")[1].split("\ndef ")[0]
    assert "restore_user_bios" in reset_fn, \
        "_reset_postgres_state must restore canonical bios before measuring"


# ── Write-effect probe wired into the sweep ────────────────────────────────

def test_write_effect_probe_exists_and_is_called():
    assert callable(bench.verify_m1_write_effect)
    src = (BENCH_DIR / "bench_sequential.py").read_text()
    assert "verify_m1_write_effect(" in src.split("def main()")[1], \
        "main() must probe write effect after resolving M1"
