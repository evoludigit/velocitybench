# ADR-008: Multi-Virtual Environment Architecture

**Status**: Accepted
**Date**: 2025-01-30
**Author**: VelocityBench Team

## Context

VelocityBench supports 6 Python frameworks (FastAPI, Flask, Strawberry, Graphene, FraiseQL, ASGI-GraphQL), plus additional Python tooling for database management, blog generation, and QA testing. This creates a dependency management challenge:

1. **Version Conflicts**: Different frameworks require different versions of shared libraries (e.g., SQLAlchemy, pytest)
2. **Isolation**: Benchmarks must be fair - each framework should use its preferred dependencies
3. **Development Experience**: Developers need to work on multiple frameworks without constant venv switching
4. **Disk Space**: Multiple venvs consume significant disk space (~19GB total)
5. **Python Versions**: Some tools require different Python versions (database tooling uses 3.11, frameworks use 3.13)

## Decision

**Use isolated virtual environments for each Python component, accepting the disk space overhead in exchange for clean dependency isolation.**

### Virtual Environment Structure

VelocityBench uses **8 distinct virtual environments**:

| Component | Location | Python | Purpose | Size (est.) |
|-----------|----------|--------|---------|-------------|
| **Root** | `venv/` | 3.13.7 | Blog generation, Makefiles | ~500 MB |
| **Database** | `database/.venv` | 3.11.14 | Database management, seeding | ~800 MB |
| **FastAPI** | `frameworks/fastapi-rest/.venv` | 3.13.7 | FastAPI framework | ~1.2 GB |
| **Flask** | `frameworks/flask-rest/.venv` | 3.13.7 | Flask framework | ~900 MB |
| **Strawberry** | `frameworks/strawberry/.venv` | 3.13.7 | Strawberry GraphQL | ~1.1 GB |
| **Graphene** | `frameworks/graphene/.venv` | 3.13.7 | Graphene GraphQL | ~1.0 GB |
| **FraiseQL** | `frameworks/fraiseql/venv` | 3.13.7 | FraiseQL framework | ~1.0 GB |
| **QA** | `tests/qa/.venv` | 3.13.7 | Integration testing | ~1.5 GB |

**Total Disk Space**: ~8-10 GB of Python dependencies (19 GB with caches)

### Naming Convention

⚠️ **Inconsistency Note**: The project uses both `.venv` and `venv` naming:

- **Most frameworks**: `.venv` (hidden directory) - Modern Python convention
- **FraiseQL**: `venv` (visible directory) - Older convention
- **Root**: `venv` (visible directory) - Compatibility with existing Makefiles

**Recommendation for new components**: Use `.venv` to follow modern Python conventions.

### Directory Structure Example

```
/home/lionel/code/velocitybench/
├── venv/                                # Root venv for blog generation
│   ├── bin/python -> Python 3.13.7
│   └── lib/python3.13/site-packages/
│       ├── requests/
│       └── pyyaml/
├── database/
│   └── .venv/                          # Database tooling (Python 3.11)
│       ├── bin/python -> Python 3.11.14
│       └── lib/python3.11/site-packages/
│           ├── psycopg[binary]/
│           └── faker/
├── frameworks/
│   ├── fastapi-rest/
│   │   └── .venv/                      # FastAPI dependencies
│   │       └── lib/python3.13/site-packages/
│   │           ├── fastapi==0.104.1
│   │           ├── pydantic==2.5.0
│   │           └── uvicorn[standard]
│   ├── flask-rest/
│   │   └── .venv/                      # Flask dependencies
│   │       └── lib/python3.13/site-packages/
│   │           ├── flask==3.0.0
│   │           └── werkzeug==3.0.1
│   └── fraiseql/
│       └── venv/                       # FraiseQL (note: not .venv)
│           └── lib/python3.13/site-packages/
│               └── fraiseql/
└── tests/qa/
    └── .venv/                          # QA testing
        └── lib/python3.13/site-packages/
            ├── pytest==7.4.3
            └── httpx==0.25.1
```

## Consequences

### Positive

✅ **Clean Isolation**: No dependency conflicts between frameworks
✅ **Fair Benchmarking**: Each framework uses its preferred library versions
✅ **Multiple Python Versions**: Database tooling (3.11) coexists with frameworks (3.13)
✅ **Independent Updates**: Update one framework's dependencies without affecting others
✅ **Clear Boundaries**: Each component's dependencies are self-documented
✅ **Reproducibility**: `requirements.txt` per framework ensures consistent environments
✅ **Parallel Development**: Multiple developers can work on different frameworks simultaneously

### Negative

❌ **Disk Space**: ~10 GB (19 GB with caches) for Python dependencies
❌ **Setup Time**: Installing 8 venvs takes ~15-20 minutes on first setup
❌ **Maintenance Overhead**: Security updates must be applied to 8+ requirements.txt files
❌ **IDE Complexity**: Developers must configure IDE to recognize multiple venvs
❌ **Mental Model**: New contributors must understand which venv to use for which task
❌ **Duplication**: Common libraries (pytest, httpx) installed multiple times

## Alternatives Considered

### Alternative 1: Monolithic Venv

- **Approach**: Single venv with all dependencies
- **Pros**: Simple, low disk usage, easy IDE setup
- **Cons**:
  - Dependency conflicts (FastAPI requires Pydantic v2, Graphene might pin v1)
  - Unfair benchmarking (forced to use lowest-common-denominator versions)
  - No isolation between frameworks
- **Rejected**: Violates fair benchmarking and isolation principles

### Alternative 2: Docker-Only

- **Approach**: Each framework in its own Docker container, no local venvs
- **Pros**: Ultimate isolation, matches production deployment
- **Cons**:
  - Slow development cycle (rebuild container for each change)
  - Poor IDE integration (remote debugging required)
  - High disk usage (containers + layers > venvs)
  - Complexity for local development
- **Rejected**: Developer experience too poor for active development

### Alternative 3: Poetry Workspaces

- **Approach**: Use Poetry's workspace feature to manage dependencies
- **Pros**: Single lock file, shared cache, better dependency resolution
- **Cons**:
  - Not all frameworks use Poetry (some use pip, uv, or requirements.txt)
  - Lock file conflicts in multi-framework development
  - Doesn't solve Python version mismatch (3.11 vs 3.13)
- **Rejected**: Doesn't support multi-Python-version requirement

### Alternative 4: Conda Environments

- **Approach**: Use Conda to manage environments and Python versions
- **Pros**: Handles Python version switching well, binary dependencies
- **Cons**:
  - Slow environment creation (5-10 minutes per env)
  - Larger disk usage than venv
  - Not standard Python tooling
  - Conda package availability lags PyPI
- **Rejected**: Slower and less standard than venv

### Alternative 5: UV-Based Workspaces

- **Approach**: Use `uv` (Astral's fast Python package manager) for all venvs
- **Pros**: 10-100x faster than pip, smart caching reduces disk usage
- **Cons**:
  - Database component already uses uv (good!)
  - Migration effort for existing frameworks
  - UV still relatively new (2024)
- **Future Consideration**: Migrate to UV once it's more mature

## Related Decisions

- **ADR-002**: Framework Isolation - Extends isolation from databases to Python dependencies
- **ADR-005**: Ruff Linting - Development dependencies managed per-venv
- **ADR-007**: Framework Selection - 6 Python frameworks necessitate this architecture

## Implementation Status

✅ **Complete** - All 8 venvs operational

## Usage Guide

Developers working with VelocityBench should reference `.claude/CLAUDE.md` for the complete virtual environment guide, including:

- Activation commands for each venv
- When to use which venv
- Common troubleshooting (ModuleNotFoundError, wrong Python version)
- IDE configuration (VS Code, PyCharm)

### Quick Reference

```bash
# Root venv (blog generation)
source /home/lionel/code/velocitybench/venv/bin/activate

# Database management
source /home/lionel/code/velocitybench/database/.venv/bin/activate

# FastAPI development
source /home/lionel/code/velocitybench/frameworks/fastapi-rest/.venv/bin/activate

# FraiseQL development (note: venv not .venv)
source /home/lionel/code/velocitybench/frameworks/fraiseql/venv/bin/activate

# QA testing
source /home/lionel/code/velocitybench/tests/qa/.venv/bin/activate
```

## Future Improvements

1. **Standardize naming**: Migrate FraiseQL to `.venv` for consistency
2. **UV migration**: Evaluate migrating all frameworks to `uv` for faster installs
3. **Shared cache**: Investigate UV's shared cache to reduce disk usage
4. **Dependency monitoring**: Automated dependency update PRs (Dependabot per venv)

## References

- [PEP 405 - Python Virtual Environments](https://peps.python.org/pep-0405/)
- [uv Documentation](https://github.com/astral-sh/uv) - Fast Python package manager
- [.claude/CLAUDE.md](../../.claude/CLAUDE.md) - VelocityBench venv usage guide
- [ADR-002](002-framework-isolation.md) - Framework isolation principles
