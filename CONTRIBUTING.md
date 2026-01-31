# Contributing to VelocityBench

Thank you for your interest in contributing to VelocityBench! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Message Format](#commit-message-format)
- [Pull Request Process](#pull-request-process)
- [Adding New Frameworks](#adding-new-frameworks)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

By participating in this project, you agree to:
- Be respectful and inclusive in all interactions
- Provide constructive feedback
- Accept criticism gracefully
- Focus on what is best for the community

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for database)
- Git
- Pre-commit hooks (recommended)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/velocitybench/velocitybench.git
cd velocitybench

# Set up pre-commit hooks (recommended)
pip install pre-commit
pre-commit install

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start Docker containers
docker-compose up -d postgres
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions including framework-specific venvs.

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feat/your-feature-name
# For bug fixes: git checkout -b fix/your-bug-name
# For docs: git checkout -b docs/your-docs-name
```

Branch naming conventions:
- `feat/` - New feature
- `fix/` - Bug fix
- `refactor/` - Code refactoring
- `test/` - Test additions
- `docs/` - Documentation
- `chore/` - Maintenance

### 2. Make Your Changes

- Keep commits focused on a single concern
- Write descriptive commit messages (see [Commit Message Format](#commit-message-format))
- Follow the code quality standards (see below)

### 3. Test Your Changes

```bash
# Run tests for your framework/component
cd frameworks/fastapi-rest
python -m pytest tests/ -v

# Run linting and formatting
make lint
make format

# Run type checking
make type-check

# All quality checks at once
make quality
```

### 4. Push and Create Pull Request

```bash
git push origin feat/your-feature-name
```

Then create a PR on GitHub following the template.

---

## Code Quality Standards

### Python Code Style

We use **Ruff** for linting and formatting:

```bash
# Check code style
ruff check <file-or-directory>

# Auto-fix issues
ruff check --fix <file-or-directory>

# Format code
ruff format <file-or-directory>
```

### Type Hints

All Python functions should have complete type hints:

```python
from pathlib import Path

def generate_report(
    data: list[dict],
    output_path: Path,
    verbose: bool = False,
) -> dict[str, int]:
    """Generate a summary report from data.

    Args:
        data: List of data records
        output_path: Where to save the report
        verbose: Enable verbose output

    Returns:
        Summary statistics as a dict
    """
    ...
```

### Docstrings

Use clear, concise docstrings for public functions:

```python
def calculate_statistics(values: list[float]) -> dict[str, float]:
    """Calculate min, max, mean, and median of values.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with 'min', 'max', 'mean', 'median' keys

    Raises:
        ValueError: If values list is empty
    """
    if not values:
        raise ValueError("values cannot be empty")
    ...
```

### Line Length

- Maximum line length: **88 characters** (configured in ruff)
- Exception: URLs in comments may exceed this

### Imports

- Use absolute imports: `from database.models import User` ✅
- Avoid relative imports: `from .models import User` ❌
- Import groups: stdlib → third-party → local (sorted alphabetically within groups)

```python
# Standard library
import json
from pathlib import Path

# Third-party
import requests
from fastapi import FastAPI

# Local
from database.models import User
from utils.logging import setup_logger
```

---

## Testing Requirements

### Test Coverage

- New features must include tests
- Minimum coverage threshold: **70%** (enforced in CI/CD)
- Run coverage reports with: `pytest --cov=src --cov-report=html`

### Test Organization

```python
import pytest

# Use descriptive test names
def test_user_creation_with_valid_data():
    """Test that valid user data creates a user."""
    ...

def test_user_creation_fails_with_invalid_email():
    """Test that invalid email raises ValueError."""
    with pytest.raises(ValueError, match="Invalid email"):
        create_user(email="not-an-email")
```

### Test Markers

Use pytest markers to organize tests:

```python
@pytest.mark.unit
def test_calculation():
    ...

@pytest.mark.integration
def test_database_connection():
    ...

@pytest.mark.asyncio
async def test_async_function():
    ...
```

Run specific tests:
```bash
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m "not slow"    # Skip slow tests
```

---

## Commit Message Format

We follow the Conventional Commits specification:

```
<type>(<scope>): <description>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring (no feature change)
- `test`: Test additions or updates
- `docs`: Documentation changes
- `chore`: Maintenance, CI/CD, tooling
- `perf`: Performance improvements
- `style`: Formatting (handled by pre-commit)

### Examples

Good commit messages:

```
feat(api): add support for GraphQL subscriptions

This commit adds real-time subscription support to the GraphQL
resolver, enabling clients to receive updates via WebSockets.

Closes #234
```

```
fix(database): resolve connection pool exhaustion under load

The connection pool was not properly releasing connections in
error scenarios. Added explicit cleanup in exception handlers.

Closes #156
```

```
docs: improve vLLM setup instructions

Added troubleshooting section and clarified GPU memory requirements.
```

### What NOT to do

❌ `fixed stuff`
❌ `update`
❌ `WIP`
❌ `asdf`
❌ `PR feedback`

---

## Pull Request Process

### Before Creating a PR

1. ✅ Ensure your branch is up-to-date with main:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. ✅ Run all tests locally:
   ```bash
   make quality
   pytest tests/
   ```

3. ✅ Write a clear PR description following the template

4. ✅ Ensure commits are logical and well-organized

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Added/updated tests
- [ ] Tests pass locally
- [ ] Coverage meets threshold (70%)

## Verification
- [ ] Code follows style guidelines
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Documentation updated

## Related Issues
Closes #123
Related to #456
```

### Code Review Checklist

Reviewers will check:

- [ ] Code follows the style guidelines
- [ ] Type hints are complete
- [ ] Tests are included and passing
- [ ] Documentation is clear and updated
- [ ] No hardcoded credentials or secrets
- [ ] Performance impact is acceptable
- [ ] Commit messages are descriptive
- [ ] No unnecessary dependencies added

### Merging

- Require at least 1 approval before merge
- Ensure all CI checks pass
- Squash commits for cleaner history (optional but recommended)
- Delete feature branch after merging

---

## Adding New Frameworks

Adding a new framework to VelocityBench involves implementing API endpoints, tests, Docker configuration, and registration. We provide comprehensive guidance:

### Full Implementation Guide
👉 **[docs/ADD_FRAMEWORK_GUIDE.md](docs/ADD_FRAMEWORK_GUIDE.md)** - Complete step-by-step tutorial covering:
- Framework directory structure
- Endpoint implementation (REST or GraphQL)
- Test setup and coverage
- Health checks
- Docker configuration
- Framework registration
- Documentation
- Verification checklist
- Troubleshooting

**Time required**: 3-8 hours depending on API type

### Quick Checklist
For experienced contributors:

1. ✅ Create framework directory with standard structure
2. ✅ Implement all required endpoints (REST or GraphQL)
3. ✅ Add tests with minimum 70% coverage
4. ✅ Implement health check endpoint
5. ✅ Register in `tests/qa/framework_registry.yaml`
6. ✅ Create Dockerfile
7. ✅ Update `docker-compose.yml`
8. ✅ Write comprehensive README.md
9. ✅ Verify CI/CD passes
10. ✅ Test with smoke tests

### Reference Implementations
Study these before adding your framework:
- **Python REST**: `frameworks/fastapi-rest/`
- **Python GraphQL**: `frameworks/strawberry/`
- **Node REST**: `frameworks/express-rest/`
- **Node GraphQL**: `frameworks/apollo-server/`
- **Go GraphQL**: `frameworks/go-gqlgen/`
- **Rust GraphQL**: `frameworks/async-graphql/`

---

## Reporting Issues

### Before Creating an Issue

1. Search existing issues to avoid duplicates
2. Check [Troubleshooting](DEVELOPMENT.md#troubleshooting) section
3. Verify the issue is reproducible
4. Gather relevant information (error messages, logs, environment)

### Minimal Reproducible Example

For bugs, provide:

```bash
# Steps to reproduce
1. Run: `make blog-all`
2. Check: `ls database/seed-data/output/`
3. Error occurs when: ...

# Expected behavior
...

# Actual behavior
...

# Environment
- Python: 3.11.5
- OS: Linux/macOS/Windows
- vLLM: running/not running
- Database: PostgreSQL 14
```

---

## Questions?

- 📖 See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide
- 🚀 See [README.md](README.md) for project overview
- 🔐 See [SECURITY.md](SECURITY.md) for security policies
- 🐛 Open an issue for questions or problems

---

## Recognition

Contributors will be recognized in:
- Project README
- Release notes
- GitHub Contributors graph

Thank you for making VelocityBench better! 🎉
