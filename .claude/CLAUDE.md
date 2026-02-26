# VelocityBench Development Guide

## Overview

VelocityBench is a comprehensive benchmarking suite with multiple Python frameworks and development environments. This guide documents the project structure, virtual environments, and development workflows.

---

## Virtual Environments

The project uses **multiple isolated Python virtual environments**, each with specific dependencies for their respective components. Understanding which venv to use is critical for development.

### 1. Root/Global Virtual Environment

**Location**: `/home/lionel/code/velocitybench/venv`

**Python Version**: 3.13.7

**Purpose**:
- Blog generation (FraiseQL pattern documentation)
- Makefile execution
- General project utilities

**Dependencies**:
- `requests` (HTTP client)
- `pyyaml` (YAML parsing)

**Activation**:
```bash
source /home/lionel/code/velocitybench/venv/bin/activate
# or directly use:
/home/lionel/code/velocitybench/venv/bin/python
```

**When to use**:
- Running `make blog-*` commands
- Working with blog generation scripts
- General project-level utilities

### 2. Database Virtual Environment

**Location**: `/home/lionel/code/velocitybench/database/.venv`

**Python Version**: 3.11.14

**Purpose**:
- Database management and seeding
- Schema migrations
- Data fixtures and test data generation

**File**: `database/pyproject.toml` (uv package manager)

**Activation**:
```bash
source /home/lionel/code/velocitybench/database/.venv/bin/activate
# or:
/home/lionel/code/velocitybench/database/.venv/bin/python
```

**When to use**:
- Database schema changes
- Seed data generation/updates
- Database utility scripts
- Migration testing

### 3. FastAPI-REST Framework

**Location**: `/home/lionel/code/velocitybench/frameworks/fastapi-rest/.venv`

**Python Version**: 3.13.7 (inferred)

**Purpose**: FastAPI + REST API implementation

**Files**:
- `requirements.txt` - Core dependencies
- `requirements-dev.txt` - Development dependencies
- `pyproject.toml` - Project configuration

**Activation**:
```bash
source /home/lionel/code/velocitybench/frameworks/fastapi-rest/.venv/bin/activate
# or:
/home/lionel/code/velocitybench/frameworks/fastapi-rest/.venv/bin/python
```

**When to use**:
- Developing/testing FastAPI implementation
- Running FastAPI-specific tests
- Working on REST API endpoints

### 4. Flask-REST Framework

**Location**: `/home/lionel/code/velocitybench/frameworks/flask-rest/.venv`

**Python Version**: 3.13.7 (inferred)

**Purpose**: Flask + REST API implementation

**Files**:
- `requirements.txt` - Core dependencies
- `requirements-dev.txt` - Development dependencies

**Activation**:
```bash
source /home/lionel/code/velocitybench/frameworks/flask-rest/.venv/bin/activate
```

**When to use**:
- Developing/testing Flask implementation
- Running Flask-specific tests
- Working on REST API endpoints in Flask

### 5. Strawberry-GraphQL Framework

**Location**: `/home/lionel/code/velocitybench/frameworks/strawberry/.venv`

**Python Version**: 3.13.7 (inferred)

**Purpose**: Strawberry GraphQL implementation

**Files**:
- `requirements.txt` - Core dependencies
- `requirements-dev.txt` - Development dependencies

**Activation**:
```bash
source /home/lionel/code/velocitybench/frameworks/strawberry/.venv/bin/activate
```

**When to use**:
- Developing/testing Strawberry GraphQL
- Running Strawberry-specific tests
- Working on GraphQL schema and resolvers

### 6. Graphene-GraphQL Framework

**Location**: `/home/lionel/code/velocitybench/frameworks/graphene/.venv`

**Python Version**: 3.13.7 (inferred)

**Purpose**: Graphene GraphQL implementation

**Files**:
- `requirements.txt` - Core dependencies
- `requirements-dev.txt` - Development dependencies

**Activation**:
```bash
source /home/lionel/code/velocitybench/frameworks/graphene/.venv/bin/activate
```

**When to use**:
- Developing/testing Graphene GraphQL
- Running Graphene-specific tests
- Working on GraphQL schema in Graphene

### 7. FraiseQL Framework

**Location**: `/home/lionel/code/velocitybench/frameworks/fraiseql/.venv`

**Python Version**: 3.13.7

**Purpose**: FraiseQL (custom GraphQL framework) implementation

**Files**:
- `requirements.txt` - Core dependencies
- `requirements-dev.txt` - Development dependencies

**Activation**:
```bash
source /home/lionel/code/velocitybench/frameworks/fraiseql/.venv/bin/activate
# or:
/home/lionel/code/velocitybench/frameworks/fraiseql/.venv/bin/python
```

**When to use**:
- Developing/testing FraiseQL framework
- Working on custom GraphQL resolver patterns
- Testing FraiseQL-specific features

### 8. QA Testing Virtual Environment

**Location**: `/home/lionel/code/velocitybench/tests/qa/.venv`

**Python Version**: 3.13.7 (inferred)

**Purpose**: QA and integration testing

**Files**:
- `requirements.txt` - Testing dependencies

**Activation**:
```bash
source /home/lionel/code/velocitybench/tests/qa/.venv/bin/activate
```

**When to use**:
- Running integration tests
- QA and testing workflows
- Cross-framework testing

---

## Virtual Environment Quick Reference

| Component | Location | Python | Purpose |
|-----------|----------|--------|---------|
| **Root** | `venv/` | 3.13.7 | Blog generation, Makefiles |
| **Database** | `database/.venv` | 3.11.14 | Database management, seeding |
| **FastAPI** | `frameworks/fastapi-rest/.venv` | 3.13.7 | FastAPI REST framework |
| **Flask** | `frameworks/flask-rest/.venv` | 3.13.7 | Flask REST framework |
| **Strawberry** | `frameworks/strawberry/.venv` | 3.13.7 | Strawberry GraphQL |
| **Graphene** | `frameworks/graphene/.venv` | 3.13.7 | Graphene GraphQL |
| **FraiseQL** | `frameworks/fraiseql/.venv` | 3.13.7 | FraiseQL framework |
| **QA** | `tests/qa/.venv` | 3.13.7 | Integration testing |

---

## Virtual Environment Naming Convention

All framework virtual environments use `.venv` (hidden directory). This is consistent across all frameworks including FraiseQL.

---

## Working with Virtual Environments

### Checking Which Venv You're Using

```bash
# Check Python executable location
which python

# Expected output patterns:
# - Blog generation: /home/lionel/code/velocitybench/venv/bin/python
# - FastAPI: /home/lionel/code/velocitybench/frameworks/fastapi-rest/.venv/bin/python
# - FraiseQL: /home/lionel/code/velocitybench/frameworks/fraiseql/.venv/bin/python
```

### Verifying Dependencies

```bash
# In activated venv:
pip list

# Or without activating:
/path/to/venv/bin/pip list
```

### Installing Dependencies

**Using requirements.txt**:
```bash
# Framework directory
cd /home/lionel/code/velocitybench/frameworks/fastapi-rest
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Using pyproject.toml (uv)**:
```bash
# Database directory
cd /home/lionel/code/velocitybench/database
uv sync  # Installs all dependencies from pyproject.toml
```

---

## Running Commands in Specific Venvs

### Method 1: Activate, Then Run

```bash
source /home/lionel/code/velocitybench/frameworks/fastapi-rest/.venv/bin/activate
python your_script.py
deactivate
```

### Method 2: Direct Path (Recommended)

```bash
/home/lionel/code/velocitybench/frameworks/fastapi-rest/.venv/bin/python your_script.py
```

### Method 3: Using Makefile (Root Venv)

```bash
make blog-all  # Uses root venv automatically
```

---

## IDE Configuration

### VS Code

**settings.json** for different workspace folders:

```json
{
  "python.defaultInterpreterPath": "/home/lionel/code/velocitybench/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintPath": "/home/lionel/code/velocitybench/venv/bin/pylint"
}
```

**Per-folder overrides**:
- `frameworks/fastapi-rest/.vscode/settings.json`:
  ```json
  {
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
  }
  ```

### PyCharm

1. Go to **Settings → Project → Python Interpreter**
2. Click the gear icon → **Add...**
3. Select **Existing Environment**
4. Choose the appropriate venv path

---

## Development Workflows

### Blog Generation (Root Venv)

```bash
cd /home/lionel/code/velocitybench
make blog-all           # Generate all blog posts
make blog-fraisier      # Generate FraiseQL pattern blogs
make blog-pattern PATTERN=deployment-history-tracking  # Single pattern
```

**Dependencies**: `requests`, `pyyaml`

### Framework Development (Framework-Specific Venv)

```bash
cd /home/lionel/code/velocitybench/frameworks/fastapi-rest
source .venv/bin/activate
python -m pytest tests/  # Run tests
python app.py            # Run application
```

### Database Management (Database Venv)

```bash
cd /home/lionel/code/velocitybench/database
source .venv/bin/activate
python scripts/migrate.py  # Run migrations
python scripts/seed.py     # Seed test data
```

### Running Tests Across All Frameworks

```bash
# Would require activating each venv
# See tests/qa for integration testing setup
cd /home/lionel/code/velocitybench/tests/qa
source .venv/bin/activate
python -m pytest
```

---

## Troubleshooting

### `ModuleNotFoundError`

**Problem**: Script fails with "No module named 'X'"

**Solution**:
1. Verify you're using the correct venv
   ```bash
   which python  # Check active venv
   ```
2. Verify dependencies are installed
   ```bash
   pip list | grep module-name
   ```
3. Install missing dependencies
   ```bash
   pip install -r requirements.txt
   ```

### Makefile Errors

**Problem**: `make blog-all` fails with missing module

**Solution**: The Makefile now automatically installs required dependencies:
```bash
make blog-all  # Runs pip install requests pyyaml automatically
```

If this fails, manually install:
```bash
/home/lionel/code/velocitybench/venv/bin/pip install requests pyyaml
```

### Wrong Python Version

**Problem**: Wrong Python version for a framework

**Solution**: Check the venv's Python version:
```bash
/path/to/venv/bin/python --version

# Expected for most frameworks: Python 3.13.7
# Expected for database: Python 3.11.14
```

If version is wrong, recreate the venv.

---

## Maintenance

### Updating Dependencies

**Framework dependencies** (e.g., FastAPI):
```bash
cd /home/lionel/code/velocitybench/frameworks/fastapi-rest
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

**Database dependencies** (using uv):
```bash
cd /home/lionel/code/velocitybench/database
uv sync --upgrade
```

**Root dependencies** (Makefile execution):
```bash
/home/lionel/code/velocitybench/venv/bin/pip install --upgrade requests pyyaml
```

### Recreating a Venv (If Corrupted)

```bash
# Remove old venv
rm -rf /home/lionel/code/velocitybench/frameworks/fastapi-rest/.venv

# Recreate with current Python
cd /home/lionel/code/velocitybench/frameworks/fastapi-rest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## Best Practices

1. **Always use the correct venv** for the component you're working on
2. **Don't mix venvs** - Never install framework dependencies in the root venv
3. **Use absolute paths** when scripting (don't rely on activation state)
4. **Document Python version requirements** if different from 3.13.7
5. **Keep requirements files updated** when adding new dependencies
6. **Use `-r` flag** with pip to install from requirements files:
   ```bash
   pip install -r requirements.txt  # Good
   pip install some-package         # Bad - not tracked
   ```

---

## Framework Matrix

| Framework | Type | Location | Venv | Python | Status |
|-----------|------|----------|------|--------|--------|
| FastAPI | REST | `frameworks/fastapi-rest/` | `.venv` | 3.13.7 | Active |
| Flask | REST | `frameworks/flask-rest/` | `.venv` | 3.13.7 | Active |
| Strawberry | GraphQL | `frameworks/strawberry/` | `.venv` | 3.13.7 | Active |
| Graphene | GraphQL | `frameworks/graphene/` | `.venv` | 3.13.7 | Active |
| FraiseQL | GraphQL | `frameworks/fraiseql/` | `.venv` | 3.13.7 | Active |
| Database | Utilities | `database/` | `.venv` | 3.11.14 | Active |

---

## Related Documentation

- **Blog Generation**: See `Makefile` for blog generation targets
- **Database Schema**: See `database/` directory
- **Framework Tests**: See `tests/qa/` for integration testing
- **FraiseQL Details**: See `frameworks/fraiseql/` README

