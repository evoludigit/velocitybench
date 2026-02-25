#!/usr/bin/env python3
"""
VelocityBench — Framework Status Dashboard

Quick health check of all registered frameworks: container status,
health endpoint, and a single Q1 smoke query.

Usage:
    python tests/benchmark/status.py
    python tests/benchmark/status.py --json
"""

import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# Import framework registry from bench_sequential
sys.path.insert(0, str(Path(__file__).parent))
from bench_sequential import FRAMEWORKS, DEFAULT_FRAMEWORK_ORDER


def _check_container(service: str) -> str:
    """Check if a docker compose service is running. Returns 'UP' or 'DOWN'."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json", service],
            cwd=str(Path(__file__).parent.parent.parent),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return "DOWN"
        for line in result.stdout.strip().splitlines():
            try:
                info = json.loads(line)
                state = info.get("State", "").lower()
                if state == "running":
                    return "UP"
            except json.JSONDecodeError:
                continue
        return "DOWN"
    except (OSError, FileNotFoundError):
        return "DOWN"


def _check_health(url: str) -> str:
    """Curl health endpoint. Returns status code or error."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except (urllib.error.URLError, OSError):
        return "ERR"


def _check_q1(fw_config: dict) -> str:
    """Send one Q1 query and check for success."""
    q1 = fw_config["queries"].get("Q1")
    if q1 is None:
        return "N/A"
    try:
        if fw_config["type"] == "graphql":
            url, query = q1
            payload = json.dumps({"query": query}).encode()
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read())
                if resp.status == 200 and "data" in body and not body.get("errors"):
                    return "OK"
                return "FAIL"
        else:
            url = q1
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read())
                if resp.status == 200 and isinstance(body, (dict, list)):
                    return "OK"
                return "FAIL"
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return "FAIL"


def main() -> None:
    as_json = "--json" in sys.argv

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    results = []
    healthy_count = 0

    for fw_name in DEFAULT_FRAMEWORK_ORDER:
        fw = FRAMEWORKS[fw_name]
        container = _check_container(fw["compose_service"])
        health = _check_health(fw["health_url"]) if container == "UP" else "—"
        q1_smoke = _check_q1(fw) if health == "200" else "—"
        fw_type = fw["type"].upper()
        queries = [q for q, v in fw["queries"].items() if v is not None]

        is_healthy = container == "UP" and health == "200" and q1_smoke == "OK"
        if is_healthy:
            healthy_count += 1

        results.append(
            {
                "framework": fw_name,
                "container": container,
                "health": health,
                "q1_smoke": q1_smoke,
                "type": fw_type,
                "queries": queries,
                "healthy": is_healthy,
            }
        )

    if as_json:
        print(
            json.dumps(
                {
                    "date": date_str,
                    "total": len(results),
                    "healthy": healthy_count,
                    "frameworks": results,
                },
                indent=2,
            )
        )
        return

    # Pretty table output
    print(f"Framework Health Check ({date_str})")
    print("=" * 78)
    print(
        f" {'Framework':<24}{'Container':>10}  {'Health':>7}  {'Q1':>6}  {'Type':<10} Queries"
    )
    print("-" * 78)

    for r in results:
        c_icon = "UP" if r["container"] == "UP" else "DOWN"
        h_icon = r["health"]
        q_icon = r["q1_smoke"]
        queries_str = ",".join(r["queries"])
        print(
            f" {r['framework']:<24}{c_icon:>10}  {h_icon:>7}  {q_icon:>6}  {r['type']:<10} {queries_str}"
        )

    print("=" * 78)
    print(f" Summary: {healthy_count}/{len(results)} healthy")


if __name__ == "__main__":
    main()
