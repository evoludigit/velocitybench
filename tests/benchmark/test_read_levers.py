"""FraiseQL read-path levers (#222): CPU per process and the cache configuration.

A Q1-Q3 row can be server-bound (fraiseql-server saturating its cores while
PostgreSQL idles) or database-bound, and the throughput alone does not say which.
Every row records the median cores used by the framework's container and by the
PostgreSQL container, sampled inside the measurement window.

A FraiseQL variant named "cache" caches nothing unless a query carries a
cache_ttl_seconds. The run records, per FraiseQL variant, whether the cache is
enabled and which queries it may store, so a "cached" row that stores nothing is
visible as such.
"""

import json
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))
import bench_sequential as bench  # noqa: E402

SUT = "velocitybench-fraiseql-tv-nocache-1"
DB = "velocitybench-postgres-1"


# ---------------------------------------------------------------------------
# CPU per process
# ---------------------------------------------------------------------------


def test_stats_line_parses_both_containers():
    out = f"{SUT}\t120.5MiB / 1GiB\t197.50%\n{DB}\t2GiB / 8GiB\t124.00%\n"
    assert bench._parse_window_stats(out, SUT, DB) == (120.5, 197.5, 124.0)


def test_stats_line_order_does_not_matter():
    out = f"{DB}\t2GiB / 8GiB\t124.00%\n{SUT}\t120.5MiB / 1GiB\t197.50%\n"
    assert bench._parse_window_stats(out, SUT, DB) == (120.5, 197.5, 124.0)


def test_stats_without_the_database_keeps_the_server():
    out = f"{SUT}\t120.5MiB / 1GiB\t50.00%\n"
    assert bench._parse_window_stats(out, SUT, DB) == (120.5, 50.0, None)


def test_stats_without_the_server_records_nothing_for_it():
    out = f"{DB}\t2GiB / 8GiB\t124.00%\n"
    assert bench._parse_window_stats(out, SUT, DB) == (None, None, 124.0)


def test_sampler_reports_median_cores():
    sampler = bench.RssSampler("fraiseql-tv-nocache")
    for mem, server, db in [(100.0, 190.0, 120.0), (110.0, 200.0, 130.0), (105.0, 196.0, 90.0)]:
        sampler._record(mem, server, db)
    assert sampler.cpu_server_cores == 1.96
    assert sampler.cpu_db_cores == 1.2
    assert sampler.median_mb == 105.0


def test_sampler_without_samples_reports_none():
    sampler = bench.RssSampler("fraiseql-tv-nocache")
    assert sampler.cpu_server_cores is None
    assert sampler.cpu_db_cores is None


def test_sampler_unknown_container_degrades_to_none():
    import time

    with bench.RssSampler("no-such-service", interval_secs=0.2) as sampler:
        time.sleep(0.5)
    assert sampler.cpu_server_cores is None


def _row(**kw):
    base = {"framework": "fraiseql-tv", "query_name": "Q1", "duration_secs": 30, "concurrency": 40}
    return bench.BenchResult(**{**base, **kw})


def test_cpu_survives_the_json_round_trip():
    r = _row(ext_requests=3000, ext_p50_ms=1.0, ext_p95_ms=2.0, ext_p99_ms=3.0,
             cpu_server_cores=1.97, cpu_db_cores=1.24)
    env = {"duration_secs": 30, "concurrency": 40}
    row = json.loads(json.dumps(bench._result_row(r)))
    back = bench._result_from_row(row, env)
    assert (back.cpu_server_cores, back.cpu_db_cores) == (1.97, 1.24)


def test_report_shows_cpu_per_process_next_to_throughput():
    r = _row(ext_requests=3000, ext_p50_ms=1.0, ext_p95_ms=2.0, ext_p99_ms=3.0,
             cpu_server_cores=1.97, cpu_db_cores=1.24)
    lines = bench.format_cpu_section([r])
    assert any("fraiseql-tv" in ln and "| Q1 |" in ln and "1.97" in ln and "1.24" in ln
               and "100" in ln for ln in lines)


def test_report_omits_cpu_section_when_nothing_was_sampled():
    assert bench.format_cpu_section([_row(ext_requests=10, ext_p50_ms=1.0,
                                          ext_p95_ms=1.0, ext_p99_ms=1.0)]) == []


# ---------------------------------------------------------------------------
# Cache configuration
# ---------------------------------------------------------------------------

_SCHEMA_NO_TTL = json.dumps({"queries": [
    {"name": "users", "sql_source": "tv_user"},
    {"name": "user", "sql_source": "tv_user", "cache_ttl_seconds": None},
]})
_SCHEMA_TTL = json.dumps({"queries": [
    {"name": "users", "sql_source": "tv_user"},
    {"name": "user", "sql_source": "tv_user", "cache_ttl_seconds": 0},
    {"name": "post", "sql_source": "tv_post", "cache_ttl_seconds": 60},
]})


def test_enabled_cache_with_no_ttl_caches_nothing():
    cfg = bench.fraiseql_cache_config("cache_enabled = true\n", _SCHEMA_NO_TTL)
    assert cfg == {"cache_enabled": True, "cached_queries": {}}
    assert "caches nothing" in bench.describe_cache_config(cfg)


def test_queries_with_a_ttl_are_the_cached_ones():
    cfg = bench.fraiseql_cache_config("cache_enabled = true\n", _SCHEMA_TTL)
    assert cfg == {"cache_enabled": True, "cached_queries": {"user": 0, "post": 60}}
    text = bench.describe_cache_config(cfg)
    assert "user (until invalidated)" in text
    assert "post (60s)" in text


def test_disabled_cache_caches_nothing_whatever_the_ttls():
    cfg = bench.fraiseql_cache_config("cache_enabled = false\n", _SCHEMA_TTL)
    assert cfg["cache_enabled"] is False
    assert "disabled" in bench.describe_cache_config(cfg)


def test_missing_cache_key_is_disabled():
    cfg = bench.fraiseql_cache_config("[validation]\nmax_query_depth = 5\n", _SCHEMA_TTL)
    assert cfg["cache_enabled"] is False


def test_report_lists_cache_configuration_per_variant():
    lines = bench.format_cache_section({
        "fraiseql-tv-cache": {"cache_enabled": True, "cached_queries": {}},
        "fraiseql-tv": {"cache_enabled": False, "cached_queries": {}},
    })
    text = "\n".join(lines)
    assert "| fraiseql-tv-cache |" in text and "caches nothing" in text
    assert "| fraiseql-tv |" in text and "disabled" in text


def test_report_omits_cache_section_without_fraiseql():
    assert bench.format_cache_section({}) == []


def test_regenerated_report_keeps_the_cache_section(tmp_path):
    r = _row(ext_requests=3000, ext_p50_ms=1.0, ext_p95_ms=2.0, ext_p99_ms=3.0)
    doc = {
        "environment": {"duration_secs": 30, "concurrency": 40, "timestamp": "2026-10-28T00:00:00"},
        "results": [bench._result_row(r)],
        "framework_config": {"fraiseql-tv": {"cache_enabled": True, "cached_queries": {}}},
    }
    path = tmp_path / "run.json"
    path.write_text(json.dumps(doc))
    md = bench.regenerate_report_from_json(path)
    assert "| fraiseql-tv |" in md and "caches nothing" in md


def test_regenerated_report_keeps_the_cpu_section(tmp_path):
    r = _row(ext_requests=3000, ext_p50_ms=1.0, ext_p95_ms=2.0, ext_p99_ms=3.0,
             cpu_server_cores=1.97, cpu_db_cores=1.24)
    doc = {
        "environment": {"duration_secs": 30, "concurrency": 40, "timestamp": "2026-10-28T00:00:00"},
        "results": [bench._result_row(r)],
    }
    path = tmp_path / "run.json"
    path.write_text(json.dumps(doc))
    md = bench.regenerate_report_from_json(path)
    assert "## CPU per Process" in md and "| 1.97 | 1.24 |" in md


# ---------------------------------------------------------------------------
# L1 / L2 read-path lever scenarios
# ---------------------------------------------------------------------------

import scenario_parity  # noqa: E402

LEVER_ENGINES = [
    name for name, cfg in bench.FRAMEWORKS.items() if "L1" in cfg["queries"]
]


def test_lever_engines_are_the_offset_and_order_capable_ones():
    assert sorted(LEVER_ENGINES) == sorted([
        "async-graphql", "hasura", "postgraphile",
        "fraiseql-tv", "fraiseql-tv-cache", "fraiseql-v-nocache", "fraiseql-v-cache",
    ])


def test_every_lever_engine_wires_both_scenarios_and_an_l2_template():
    for name in LEVER_ENGINES:
        cfg = bench.FRAMEWORKS[name]
        assert cfg["queries"]["L2"] == "L2", name
        assert cfg["l2_template"] in bench._L2_TEMPLATES, name


def test_every_l1_states_its_offset():
    for name in LEVER_ENGINES:
        _url, doc = bench.FRAMEWORKS[name]["queries"]["L1"]
        assert "offset: 1000" in doc, name


def test_l2_resolves_on_the_l1_url_with_the_given_post():
    cfg = {"queries": {"L1": ("http://h:1/graphql", "{}"), "L2": "L2"},
           "l2_template": "hasura"}
    url, doc = bench._resolve_l2(cfg, "11111111-2222-3333-4444-555555555555")
    assert url == "http://h:1/graphql"
    assert '_eq: "11111111-2222-3333-4444-555555555555"' in doc
    assert "order_by: {createdAt: desc}" in doc


def test_l2_without_a_post_is_skipped():
    cfg = {"queries": {"L1": ("http://h:1/graphql", "{}"), "L2": "L2"},
           "l2_template": "fraiseql"}
    assert bench._resolve_l2(cfg, None) is None


def test_every_l2_template_formats_to_one_document():
    for key, template in bench._L2_TEMPLATES.items():
        doc = template.format(post_id="p")
        assert doc.count("{") == doc.count("}"), key
        assert '"p"' in doc and ": 3" in doc, key


def test_parity_unwraps_a_post_holding_its_comment_connection():
    data = {"tbPostByRowId": {"tbCommentsByFkPost": {"nodes": [{"id": "a"}, {"id": "b"}]}}}
    rows = scenario_parity._rows(data, scenario_parity._ALIASES["postgraphile"])
    assert scenario_parity._ids(rows) == ["a", "b"]


def test_parity_audits_the_lever_scenarios_in_order():
    assert set(scenario_parity.ORDERED) == {"L1", "L2"}
    assert {"L1", "L2"} <= set(scenario_parity.SCENARIOS)
    assert scenario_parity.EXPECTED_COUNTS["L1"] == 20
    assert scenario_parity.EXPECTED_COUNTS["L2"] == 3
