"""TVIEW persistence guard.

pg_tviews creates tv_* tables UNLOGGED by default — a durability trade that
must never ride into a publishable run unnoticed. The guard reads the live
DB's relpersistence and the sweep aborts when it contradicts the claimed mode.
Requires the compose postgres service to be up (skips otherwise).
"""

import pytest

from bench_sequential import detect_tview_persistence


@pytest.fixture(scope="module")
def live_mode():
    mode = detect_tview_persistence()
    if mode is None:
        pytest.skip("postgres not reachable via docker compose")
    return mode


def test_detects_a_definite_mode(live_mode):
    assert live_mode in ("logged", "unlogged"), (
        f"tv_* tables have mixed persistence: {live_mode!r}"
    )


def test_publishable_profile_runs_logged(live_mode):
    assert live_mode == "logged", (
        "tv_* tables are UNLOGGED — recreate the postgres volume with "
        "TVIEW_PERSISTENCE=logged (compose default) before a publishable run, "
        "or pass --tview-mode unlogged explicitly for appendix runs"
    )
