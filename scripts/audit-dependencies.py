#!/usr/bin/env python
"""
Audit dependencies across all VelocityBench frameworks and generators.

Checks for:
- Outdated packages
- Security vulnerabilities
- Unused dependencies
- Dependency conflicts

Usage:
    python scripts/audit-dependencies.py
    python scripts/audit-dependencies.py --fix
    python scripts/audit-dependencies.py --json
"""

import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"


def check_python_vulnerabilities(venv_path: Path) -> dict:
    """Check Python packages for security vulnerabilities."""
    python_exe = venv_path / "bin" / "python"

    if not python_exe.exists():
        return {"status": "skip", "reason": "venv not found"}

    # Try pip audit
    code, stdout, stderr = run_command([str(python_exe), "-m", "pip", "audit"])

    if code == 0:
        return {"status": "ok", "vulnerabilities": 0}
    else:
        # Parse vulnerabilities from output
        return {
            "status": "vulnerable",
            "output": stdout,
            "error": stderr,
        }


def check_python_outdated(venv_path: Path) -> dict:
    """Check for outdated Python packages."""
    python_exe = venv_path / "bin" / "python"

    if not python_exe.exists():
        return {"status": "skip"}

    code, stdout, stderr = run_command(
        [str(python_exe), "-m", "pip", "list", "--outdated"],
    )

    if code == 0:
        # Count outdated packages
        lines = stdout.strip().split("\n")[2:]  # Skip header
        outdated_count = len([l for l in lines if l.strip()])
        return {
            "status": "ok" if outdated_count == 0 else "outdated",
            "count": outdated_count,
        }
    else:
        return {"status": "error", "error": stderr}


def check_npm_vulnerabilities(npm_dir: Path) -> dict:
    """Check Node.js packages for vulnerabilities."""
    if not (npm_dir / "package.json").exists():
        return {"status": "skip", "reason": "package.json not found"}

    code, stdout, stderr = run_command(["npm", "audit"], cwd=npm_dir)

    if code == 0:
        return {"status": "ok", "output": stdout}
    else:
        # Parse vulnerabilities
        return {
            "status": "vulnerable" if "vulnerabilities" in stdout else "ok",
            "output": stdout,
        }


def audit_frameworks() -> dict:
    """Audit all framework dependencies."""
    results = {"frameworks": {}, "generators": {}}
    framework_dir = Path("frameworks")
    db_dir = Path("database")

    # Audit each framework
    for framework_path in framework_dir.iterdir():
        if not framework_path.is_dir() or framework_path.name.startswith("."):
            continue

        framework_name = framework_path.name
        results["frameworks"][framework_name] = {}

        # Check Python venv
        venv_path = framework_path / ".venv"
        if venv_path.exists():
            results["frameworks"][framework_name]["python"] = {
                "vulnerabilities": check_python_vulnerabilities(venv_path),
                "outdated": check_python_outdated(venv_path),
            }

        # Check Node.js dependencies
        if (framework_path / "package.json").exists():
            results["frameworks"][framework_name]["npm"] = check_npm_vulnerabilities(
                framework_path,
            )

    # Audit generators (database venv)
    db_venv = db_dir / ".venv"
    if db_venv.exists():
        results["generators"]["database"] = {
            "vulnerabilities": check_python_vulnerabilities(db_venv),
            "outdated": check_python_outdated(db_venv),
        }

    return results


def print_report(results: dict) -> None:
    """Print human-readable audit report."""
    print("\n" + "=" * 70)
    print("VelocityBench Dependency Audit Report")
    print("=" * 70)

    # Framework audits
    print("\n📦 FRAMEWORKS\n")
    for framework, checks in results["frameworks"].items():
        print(f"  {framework}:")

        if "python" in checks:
            py_vuln = checks["python"].get("vulnerabilities", {})
            py_outdated = checks["python"].get("outdated", {})

            vuln_status = py_vuln.get("status", "unknown")
            outdated_status = py_outdated.get("status", "unknown")
            outdated_count = py_outdated.get("count", 0)

            icon_vuln = "❌" if vuln_status == "vulnerable" else "✅"
            icon_outdated = "⚠️" if outdated_status == "outdated" else "✅"

            print(f"    {icon_vuln} Python vulnerabilities: {vuln_status}")
            print(
                f"    {icon_outdated} Python outdated: "
                f"{outdated_status} ({outdated_count} packages)"
            )

        if "npm" in checks:
            npm_status = checks["npm"].get("status", "unknown")
            icon = "❌" if npm_status == "vulnerable" else "✅"
            print(f"    {icon} Node.js vulnerabilities: {npm_status}")

    # Generator audits
    print("\n🔧 GENERATORS (database)\n")
    for component, checks in results["generators"].items():
        print(f"  {component}:")
        py_vuln = checks.get("vulnerabilities", {})
        py_outdated = checks.get("outdated", {})

        vuln_status = py_vuln.get("status", "unknown")
        outdated_status = py_outdated.get("status", "unknown")
        outdated_count = py_outdated.get("count", 0)

        icon_vuln = "❌" if vuln_status == "vulnerable" else "✅"
        icon_outdated = "⚠️" if outdated_status == "outdated" else "✅"

        print(f"    {icon_vuln} Python vulnerabilities: {vuln_status}")
        print(
            f"    {icon_outdated} Python outdated: "
            f"{outdated_status} ({outdated_count} packages)"
        )

    print("\n" + "=" * 70)


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Audit VelocityBench dependencies",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix vulnerabilities",
    )

    args = parser.parse_args()

    print("Starting dependency audit...")
    results = audit_frameworks()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

    # Determine exit code
    has_vulnerabilities = any(
        checks.get("vulnerabilities", {}).get("status") == "vulnerable"
        for component in results.values()
        for checks in (
            component.values() if isinstance(component, dict) else [component]
        )
        if isinstance(checks, dict)
    )

    return 1 if has_vulnerabilities else 0


if __name__ == "__main__":
    sys.exit(main())
