#!/usr/bin/env python3
"""Load-generator headroom validation.

A load generator that cannot comfortably outrun the fastest framework is the
bottleneck, and every published number is a measurement of the wrong process.
The fastest framework in this suite does ~10k RPS, so the generator must
sustain >= 30k RPS (3x headroom) against a null target.

The null target is a canned-response nginx container; the load path is the
exact worker + pool machinery bench_sequential uses for GraphQL scenarios.

Usage: loadgen_headroom.py [--duration 5] [--concurrency 40] [--min-rps 30000]
Exit code 0 iff the measured RPS meets the threshold.
"""

import argparse
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bench_sequential import _entry_to_k6_steps, _run_k6, _worker_graphql  # noqa: E402

PORT = 18999
CONTAINER = "velocitybench-loadgen-nulltarget"
NGINX_CONF = """
server {
    listen 80;
    keepalive_requests 10000000;
    location / {
        default_type application/json;
        return 200 '{"data":{"users":[{"id":"00000000-0000-0000-0000-000000000001","username":"bench","fullName":"Bench User","bio":"canned"}]}}';
    }
}
"""


def start_null_target() -> None:
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True, check=False)
    conf = Path(tempfile.mkdtemp(prefix="loadgen-nulltarget-")) / "default.conf"
    conf.write_text(NGINX_CONF)
    subprocess.run(
        [
            "docker", "run", "--rm", "-d", "--name", CONTAINER,
            "-p", f"127.0.0.1:{PORT}:80",
            "-v", f"{conf}:/etc/nginx/conf.d/default.conf:ro",
            "nginx:alpine",
        ],
        check=True,
        capture_output=True,
    )
    time.sleep(1.5)


def stop_null_target() -> None:
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True, check=False)


QUERY = "{ users(limit: 20) { id username fullName bio } }"


def measure_python(duration: int, concurrency: int) -> float:
    url = f"http://127.0.0.1:{PORT}/graphql"
    end_time = time.monotonic() + duration
    total_requests = 0
    total_errors = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(_worker_graphql, url, QUERY, end_time)
            for _ in range(concurrency)
        ]
        for f in futures:
            latencies, errors, _breakdown, _samples = f.result()
            total_requests += len(latencies)
            total_errors += errors
    if total_errors:
        print(f"WARNING: {total_errors} errors against the null target", file=sys.stderr)
    return total_requests / duration


def measure_k6(duration: int, concurrency: int) -> float:
    entry = (f"http://127.0.0.1:{PORT}/graphql", QUERY)
    steps = _entry_to_k6_steps(entry, "graphql", "Q1")
    ok_cycles, errors, _pct = _run_k6(steps, concurrency, duration)
    if errors:
        print(f"WARNING: {errors} errors against the null target", file=sys.stderr)
    return ok_cycles / duration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=["k6", "python"], default="k6",
                        help="Load generator to validate (default: k6, the sweep path)")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=40)
    parser.add_argument("--min-rps", type=int, default=30_000)
    args = parser.parse_args()

    measure = measure_k6 if args.tool == "k6" else measure_python
    start_null_target()
    try:
        rps = measure(args.duration, args.concurrency)
    finally:
        stop_null_target()

    verdict = "OK" if rps >= args.min_rps else "INSUFFICIENT"
    print(
        f"{args.tool} load generator: {rps:,.0f} RPS at {args.concurrency} workers "
        f"(threshold {args.min_rps:,}) — {verdict}"
    )
    return 0 if rps >= args.min_rps else 1


if __name__ == "__main__":
    sys.exit(main())
