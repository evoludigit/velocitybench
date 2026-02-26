# Dependency Audit Guide

VelocityBench includes `scripts/audit-dependencies.py` to audit dependencies across all 39 frameworks and Python components. This guide explains how to use the audit script, interpret results, and integrate it into CI/CD workflows.

## Overview

The dependency audit script checks:

1. **Security Vulnerabilities**: Known CVEs in dependencies (using `pip audit`, `npm audit`)
2. **Outdated Packages**: Dependencies with newer versions available
3. **Cross-Component Coverage**: Audits all Python venvs and Node.js frameworks

**Supported Languages**:
- ✅ Python (via `pip audit`, `pip list --outdated`)
- ✅ Node.js (via `npm audit`)
- ⚠️ Other languages: Manual auditing required (see Future Work section)

## Quick Start

```bash
# Run full audit
python scripts/audit-dependencies.py

# Output as JSON (for CI/CD)
python scripts/audit-dependencies.py --json

# Attempt to fix vulnerabilities (not yet implemented)
python scripts/audit-dependencies.py --fix
```

## Installation Requirements

The audit script requires the following tools:

### Python Components

**Required**:
- `pip` (bundled with Python)
- `pip-audit` (install in each venv)

**Installation** (per virtual environment):
```bash
# Example: FastAPI framework
source frameworks/fastapi-rest/.venv/bin/activate
pip install pip-audit
```

**Quick install across all venvs**:
```bash
# Script to install pip-audit in all Python venvs
for venv_path in venv database/.venv frameworks/*/.venv tests/qa/.venv; do
    if [ -f "$venv_path/bin/python" ]; then
        echo "Installing pip-audit in $venv_path"
        $venv_path/bin/python -m pip install pip-audit
    fi
done
```

### Node.js Components

**Required**:
- `npm` (bundled with Node.js)
- No additional packages needed (`npm audit` is built-in)

## Usage

### Basic Audit

```bash
python scripts/audit-dependencies.py
```

**Output**:
```
Starting dependency audit...

======================================================================
VelocityBench Dependency Audit Report
======================================================================

📦 FRAMEWORKS

  fastapi-rest:
    ✅ Python vulnerabilities: ok
    ⚠️  Python outdated: outdated (3 packages)

  flask-rest:
    ✅ Python vulnerabilities: ok
    ✅ Python outdated: ok (0 packages)

  express:
    ✅ Node.js vulnerabilities: ok

  apollo:
    ❌ Node.js vulnerabilities: vulnerable

🔧 GENERATORS (database)

  database:
    ✅ Python vulnerabilities: ok
    ⚠️  Python outdated: outdated (1 packages)

======================================================================
```

### JSON Output

For programmatic consumption (CI/CD, monitoring):

```bash
python scripts/audit-dependencies.py --json
```

**Output** (abbreviated):
```json
{
  "frameworks": {
    "fastapi-rest": {
      "python": {
        "vulnerabilities": {
          "status": "ok",
          "vulnerabilities": 0
        },
        "outdated": {
          "status": "outdated",
          "count": 3
        }
      }
    },
    "express": {
      "npm": {
        "status": "ok",
        "output": "found 0 vulnerabilities"
      }
    }
  },
  "generators": {
    "database": {
      "vulnerabilities": {
        "status": "ok"
      },
      "outdated": {
        "status": "outdated",
        "count": 1
      }
    }
  }
}
```

## Interpreting Results

### Python Vulnerability Status

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `ok` | No known vulnerabilities | None |
| `vulnerable` | CVEs found in dependencies | **Immediate action required** |
| `skip` | Venv not found | Check venv setup |
| `error` | Audit command failed | Check pip-audit installation |

### Python Outdated Status

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `ok` | All packages up to date | None |
| `outdated` | Newer versions available | Review and update when convenient |
| `skip` | Venv not found | Check venv setup |
| `error` | Command failed | Check pip installation |

### Node.js Vulnerability Status

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `ok` | No vulnerabilities found | None |
| `vulnerable` | Vulnerabilities detected | **Review npm audit output** |
| `skip` | No package.json found | Expected for non-Node.js frameworks |

## Exit Codes

The script returns exit codes for CI/CD integration:

- **0**: No vulnerabilities found (all green)
- **1**: Vulnerabilities detected (requires action)

**Example in CI**:
```bash
# CI will fail if vulnerabilities are found
python scripts/audit-dependencies.py || exit 1
```

## Understanding Audit Results

### Detailed Vulnerability Information

When vulnerabilities are found, the audit output includes:

```
  fastapi-rest:
    ❌ Python vulnerabilities: vulnerable
```

To see details, run `pip audit` directly in that venv:

```bash
source frameworks/fastapi-rest/.venv/bin/activate
pip audit

# Output:
Found 2 known vulnerabilities in 1 package
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name            │ Version │ ID                 │ Fix Versions      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ requests        │ 2.25.0  │ PYSEC-2023-74      │ >=2.31.0          │
│ requests        │ 2.25.0  │ GHSA-j8r2-6x86-q33q│ >=2.31.0          │
└─────────────────┴─────────┴────────────────────┴───────────────────┘
```

### Detailed Outdated Package Information

```bash
source frameworks/fastapi-rest/.venv/bin/activate
pip list --outdated

# Output:
Package    Version  Latest   Type
---------- -------- -------- -----
fastapi    0.104.0  0.109.0  wheel
pydantic   2.5.0    2.6.1    wheel
uvicorn    0.24.0   0.27.0   wheel
```

## Fixing Vulnerabilities

### Python Vulnerabilities

**Automatic fix** (update vulnerable packages):
```bash
source frameworks/fastapi-rest/.venv/bin/activate
pip audit --fix
```

**Manual fix** (update specific package):
```bash
source frameworks/fastapi-rest/.venv/bin/activate
pip install --upgrade requests>=2.31.0

# Update requirements.txt
pip freeze > requirements.txt
```

### Node.js Vulnerabilities

**Automatic fix** (where possible):
```bash
cd frameworks/express
npm audit fix

# For breaking changes:
npm audit fix --force
```

**Manual fix** (update specific package):
```bash
cd frameworks/express
npm install express@latest
npm audit
```

## Updating Outdated Packages

### Python Packages

**Update all packages** (use with caution):
```bash
source frameworks/fastapi-rest/.venv/bin/activate
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U

# Test thoroughly after updating
pytest tests/

# Update requirements.txt
pip freeze > requirements.txt
```

**Update specific package**:
```bash
source frameworks/fastapi-rest/.venv/bin/activate
pip install --upgrade fastapi
pip freeze > requirements.txt
```

### Node.js Packages

**Update all packages**:
```bash
cd frameworks/express
npm update

# Test thoroughly
npm test
```

**Update specific package**:
```bash
cd frameworks/express
npm install express@latest
```

## CI/CD Integration

### GitHub Actions

Add dependency auditing to your CI workflow:

```yaml
# .github/workflows/dependency-audit.yml
name: Dependency Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  pull_request:
    paths:
      - '**/requirements.txt'
      - '**/package.json'
      - 'scripts/audit-dependencies.py'

jobs:
  audit:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install pip-audit in all venvs
        run: |
          for venv_path in venv database/.venv frameworks/*/.venv; do
            if [ -f "$venv_path/bin/python" ]; then
              $venv_path/bin/python -m pip install pip-audit
            fi
          done

      - name: Run dependency audit
        run: |
          python scripts/audit-dependencies.py --json > audit-results.json

      - name: Check for vulnerabilities
        run: |
          if python scripts/audit-dependencies.py; then
            echo "✅ No vulnerabilities found"
          else
            echo "❌ Vulnerabilities detected!"
            python scripts/audit-dependencies.py
            exit 1
          fi

      - name: Upload audit results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: dependency-audit-results
          path: audit-results.json
```

### Pre-commit Hook

Run audit before committing dependency changes:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: dependency-audit
        name: Audit dependencies
        entry: python scripts/audit-dependencies.py
        language: system
        files: 'requirements\.txt|package\.json'
        pass_filenames: false
```

## Scheduled Audits

### Weekly Audit (Recommended)

Use cron or GitHub Actions to run weekly audits:

```bash
# crontab -e
0 9 * * 1 cd /path/to/velocitybench && python scripts/audit-dependencies.py --json > audit-$(date +\%Y\%m\%d).json
```

### Monthly Update Cycle

1. **Week 1**: Run audit, identify outdated packages
2. **Week 2**: Test updates in development environment
3. **Week 3**: Open PR with updates, run full test suite
4. **Week 4**: Merge if tests pass

## Audit Script Internals

### Components Audited

The script automatically discovers and audits:

1. **Python Virtual Environments**:
   - `venv/` (root venv)
   - `database/.venv`
   - `frameworks/*/.venv` (all framework venvs)
   - `tests/qa/.venv`

2. **Node.js Projects**:
   - `frameworks/*/package.json` (all frameworks with package.json)

### How It Works

```
1. Discover components (frameworks, generators)
   ↓
2. For each Python venv:
   - Run `pip audit` for vulnerabilities
   - Run `pip list --outdated` for outdated packages
   ↓
3. For each Node.js project:
   - Run `npm audit` for vulnerabilities
   ↓
4. Aggregate results
   ↓
5. Generate report (human-readable or JSON)
   ↓
6. Exit with code 0 (ok) or 1 (vulnerabilities found)
```

## Limitations

### Current Limitations

1. **No Auto-Fix**: `--fix` flag is not yet implemented
2. **Python/Node.js Only**: Other languages (Go, Rust, Java) not yet supported
3. **No Dependency Graph**: Doesn't show transitive dependency chains
4. **No SBOM**: Doesn't generate Software Bill of Materials

### Future Enhancements

Planned improvements:

1. **Auto-Fix Support**: Implement `--fix` to automatically update vulnerable packages
2. **Multi-Language Support**:
   - Go: `go list -m -u all`, `govulncheck`
   - Rust: `cargo audit`
   - Java: `mvn versions:display-dependency-updates`
   - PHP: `composer outdated`
   - Ruby: `bundle outdated`
3. **SBOM Generation**: Generate CycloneDX or SPDX SBOM
4. **Dependency Graphing**: Visualize dependency trees
5. **License Compliance**: Check for license incompatibilities

## Manual Auditing (Other Languages)

### Go Frameworks

```bash
cd frameworks/gin-rest
go list -m -u all
govulncheck ./...
```

### Rust Frameworks

```bash
cd frameworks/actix-web
cargo audit
cargo outdated
```

### Java Frameworks

```bash
cd frameworks/spring-boot
mvn versions:display-dependency-updates
mvn dependency:analyze
```

### PHP Frameworks

```bash
cd frameworks/laravel
composer outdated
composer audit
```

### Ruby Frameworks

```bash
cd frameworks/rails
bundle outdated
bundle audit
```

## Troubleshooting

### Issue: `pip audit` not found

**Cause**: `pip-audit` not installed in venv

**Solution**:
```bash
source frameworks/fastapi-rest/.venv/bin/activate
pip install pip-audit
```

### Issue: `npm audit` returns errors

**Cause**: `node_modules/` not installed

**Solution**:
```bash
cd frameworks/express
npm install
npm audit
```

### Issue: Venv not discovered

**Cause**: Venv naming doesn't match `.venv` or `venv` patterns

**Solution**: Update `audit_frameworks()` function in `scripts/audit-dependencies.py` to include the venv path.

### Issue: False positive vulnerabilities

**Cause**: Vulnerability doesn't apply to usage pattern

**Solution**: Document exception in `docs/security/EXCEPTIONS.md` and suppress in audit output (requires code change).

## Best Practices

1. **Run weekly**: Automate audits with GitHub Actions or cron
2. **Prioritize vulnerabilities**: Fix critical/high vulnerabilities immediately
3. **Test updates**: Always run full test suite after updating dependencies
4. **Pin versions**: Use `requirements.txt` with pinned versions for reproducibility
5. **Document exceptions**: If a vulnerability doesn't apply, document why
6. **Update in batches**: Group related updates (e.g., all FastAPI ecosystem packages)
7. **Monitor upstream**: Subscribe to security advisories for major dependencies

## References

- [pip-audit Documentation](https://github.com/pypa/pip-audit)
- [npm audit Documentation](https://docs.npmjs.com/cli/v9/commands/npm-audit)
- [Dependabot](https://github.com/dependabot) - Automated dependency updates
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [National Vulnerability Database](https://nvd.nist.gov/)
- [GitHub Advisory Database](https://github.com/advisories)
