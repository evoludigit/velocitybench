# Repository Health & Cleanliness Guide

## Overview

Guidelines and checklists for keeping VelocityBench clean, organized, and maintainable. Agents should follow these practices when making changes.

---

## Code Cleanliness Standards

### Python Code

#### ✅ DO: Follow Ruff Standards

```python
# ✅ CORRECT: Type hints, clear naming, proper length
def get_user_by_id(user_id: str) -> dict[str, Any]:
    """Get user by UUID.

    Args:
        user_id: User UUID string

    Returns:
        User dict with id, username, email, etc.
    """
    return db.fetch_one("SELECT * FROM tb_user WHERE id = $1", user_id)

# ❌ WRONG: No type hints, poor naming, long line
def getUser(uid):
    return db.fetch_one("SELECT id,username,email,first_name,last_name,bio,avatar_url,is_active,created_at,updated_at FROM tb_user WHERE id=%s",uid)
```

#### Ruff Configuration Check

All Python files should respect:
- **Max line length**: 88 characters
- **Type hints**: Required for all public functions
- **Imports**: Absolute imports, sorted (stdlib → third-party → local)
- **Docstrings**: Google-style for public functions

**Run before committing**:
```bash
cd frameworks/{framework-name}
make quality          # Runs: lint, format, type-check
pytest tests/ --cov  # Coverage check
```

#### ❌ DON'T: Leave Artifacts

```python
# ❌ Commented-out code
def create_user(username: str, email: str):
    """Create user."""
    # db.execute("INSERT INTO tb_user (username) VALUES (%s)", username)
    # user = db.fetch_one("SELECT * FROM tb_user WHERE username = %s", username)
    # return user
    pass

# ❌ Debug prints
def get_post(post_id: str):
    print(f"DEBUG: Getting post {post_id}")  # Remove!
    print(post_id)                           # Remove!
    result = db.fetch_one("SELECT * FROM tb_post WHERE id = $1", post_id)
    print(f"Result: {result}")                # Remove!
    return result

# ❌ TODO/FIXME without action
def list_posts():
    # TODO: Add pagination  # Fix immediately or remove
    # FIXME: N+1 query     # Fix or document why not fixing
    pass
```

---

### File Organization

#### Python Framework Structure

```
frameworks/{name}/
├── main.py                 # Entry point (FastAPI, Flask, GraphQL server)
├── requirements.txt        # Dependencies
├── requirements-dev.txt    # Dev dependencies
├── README.md              # Framework documentation
├── Makefile               # Build/test/run commands
├── pytest.ini             # Pytest configuration
├── common/                # Framework-specific utilities
│   ├── __init__.py
│   ├── models.py          # Pydantic/ORM models
│   └── db.py              # Database utilities
├── tests/
│   ├── conftest.py        # Pytest fixtures
│   ├── test_users.py
│   ├── test_posts.py
│   └── test_comments.py
├── venv/ or .venv/        # Virtual environment (gitignored)
└── .env                   # Local config (gitignored)
```

**Naming Rules**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_CASE`

#### Documentation Structure

```
docs/
├── README.md                          # Overview/navigation
├── CODEBASE_NAVIGATION.md             # Structure + entry points
├── DATABASE_SCHEMA.md                 # Schema reference
├── API_SCHEMAS.md                     # API specifications
├── QUERY_PATTERNS.md                  # Query examples
├── MODIFICATION_GUIDE.md              # How to modify code
├── ERROR_CATALOG.md                   # Error solutions
├── TESTING_README.md                  # Testing guide
├── FIXTURE_FACTORY_GUIDE.md           # Test fixtures
├── TEST_ISOLATION_STRATEGY.md         # Test isolation
├── TEST_NAMING_CONVENTIONS.md         # Test naming
├── PERFORMANCE_BASELINE_MANAGEMENT.md # Performance tracking
├── CROSS_FRAMEWORK_TEST_DATA.md       # Test consistency
├── AGENT_QUICKSTART.md                # Agent onboarding
├── REPOSITORY_HEALTH.md               # This file
└── archive/                           # Completed phase docs
    ├── README.md
    └── completed-docs/
```

---

## Git Practices

### Commit Message Format

```
<type>(<scope>): <description>

<body>

<footer>
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code restructuring
- `test` - Test additions
- `docs` - Documentation
- `chore` - Maintenance/CI/dependency

**Examples**:

```
feat(api): add category filtering to post list

Implements category parameter on GET /posts endpoint.
Filters published posts by category slug.

Closes #123
```

```
fix(database): prevent N+1 query in get_post_with_comments

Changed separate queries to single JOIN query.
Reduces database calls from O(n) to O(1).
```

```
docs: improve error catalog with agent examples

Added 10 new error examples with detailed solutions.
All patterns cover REST, GraphQL, and common pitfalls.
```

### Branch Naming

```
feat/add-categories
fix/n-plus-one-post-query
docs/database-schema-reference
refactor/extract-query-builders
test/add-concurrent-access-tests
```

### Pre-Commit Checklist

Before committing:

- [ ] **All tests pass**: `pytest tests/ -v`
- [ ] **Code quality**: `make quality` (lint, format, type-check)
- [ ] **No debug code**: `grep -r "print(" frameworks/ | grep -v test`
- [ ] **No TODOs**: `grep -r "TODO\|FIXME" *.py` (none should be there)
- [ ] **Documentation updated**: Any code changes have docs?
- [ ] **Clean commit message**: Follows format above

---

## Documentation Standards

### Required Documentation

Every significant code change needs:

1. **Code comments** (for complex logic):
   ```python
   # Use SERIAL pk_user for FK, UUID id for public API
   # This improves performance while preventing ID guessing
   db.execute(
       "INSERT INTO tb_post (fk_author, title) VALUES (%s, %s)",
       user['pk_user'],  # Use pk_user, NOT id!
       title
   )
   ```

2. **Docstrings** (for public functions):
   ```python
   def get_post_with_author(db, post_id: str) -> dict:
       """Get post with author information included.

       Uses single JOIN query to avoid N+1 problem.

       Args:
           db: Database connection
           post_id: Post UUID string

       Returns:
           Post dict with nested author dict

       Raises:
           ValueError: If post_id is not valid UUID
       """
   ```

3. **README updates** (for framework changes):
   ```markdown
   ## Changes in v1.1

   - Added category filtering to POST /posts endpoint
   - Fixed N+1 query in get_post_with_comments
   - Updated pagination to start at 0 offset
   ```

4. **Cross-reference links** (in docstrings):
   ```python
   def create_user(...):
       """Create new user.

       See docs/MODIFICATION_GUIDE.md for adding endpoints.
       See docs/DATABASE_SCHEMA.md for field constraints.
       """
   ```

---

## Dependency Management

### Python Dependencies

**Keep minimal**:
```
frameworks/fastapi-rest/requirements.txt:
fastapi>=0.104.1
uvicorn>=0.24.0
asyncpg>=0.29.0
pydantic>=2.0.0
```

**Update via**:
```bash
cd frameworks/{name}
pip install --upgrade -r requirements.txt
pip freeze > requirements-updated.txt
# Review changes
cp requirements-updated.txt requirements.txt
```

**Never**:
- Pin to exact patch version (except asyncpg for benchmarking consistency)
- Add unnecessary dependencies
- Include version conflicts

### Dependency Audit

```bash
# Check for security vulnerabilities
pip audit

# Update dependencies safely
pip install --upgrade pip setuptools wheel
pip install --upgrade -r requirements.txt
```

---

## Database Cleanliness

### Schema Changes

**DO**:
- [ ] Update `database/schema-template.sql` first
- [ ] Create migration in `database/migrations/`
- [ ] Test with fresh database: `docker-compose down && docker-compose up`
- [ ] Update all ORM models
- [ ] Update tests

**DON'T**:
- [ ] Make manual schema changes without migration
- [ ] Change schema without updating docs
- [ ] Add breaking changes without deprecation period

---

## Test Cleanliness

### Test Organization

```
tests/
├── common/                # Shared fixtures
│   ├── conftest.py       # Global pytest config
│   ├── fixtures.py       # db, factory fixtures
│   ├── factory.py        # Entity creation
│   └── bulk_factory.py   # Bulk operations
├── qa/                    # Cross-framework tests
│   ├── test_users.py
│   ├── test_posts.py
│   └── framework_registry.yaml
└── perf/                  # Performance tests
    ├── test_performance.py
    └── baselines/
```

### Test Standards

```python
# ✅ DO: Clear naming, proper fixtures, docstring
def test_user_creation_with_valid_data_succeeds(db, factory):
    """Create user with valid data succeeds.

    Given: Valid user data (username, email)
    When: User is created via factory
    Then: User is persisted with correct values
    """
    user = factory.create_user("alice", "alice@example.com")

    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"

# ❌ DON'T: Generic name, no docstring, multiple assertions
def test_user(factory):
    user = factory.create_user("a", "a@example.com")
    assert user
    assert user["username"]
    assert user["email"]
    post = factory.create_post(...)  # Wrong - test 2 things
    assert post
```

---

## Documentation Cleanliness

### Content Standards

**DO**:
- ✅ Use clear section headers
- ✅ Include code examples (with output)
- ✅ Cross-reference related docs
- ✅ Use tables for quick reference
- ✅ Include "What NOT to do" anti-patterns
- ✅ Keep doc updated with code

**DON'T**:
- ❌ Outdated examples
- ❌ Broken links to docs
- ❌ Vague descriptions
- ❌ Missing context
- ❌ Incomplete code snippets

### Documentation Updates

When modifying code:

```bash
# Find documentation that mentions this feature
grep -r "feature_name" docs/

# Update all references
# Update examples if behavior changed
# Run check: no broken links
python scripts/check_doc_links.py
```

---

## Development Artifacts Cleanup

### Before Committing

**Remove**:
```bash
# Commented code
grep -r "^#.*=" frameworks/  # Review these

# Print statements (except logging)
grep -r "print(" frameworks/ --include="*.py" | grep -v test | grep -v "#"

# Debug settings
grep -r "DEBUG.*=.*True" frameworks/ --include="*.py"

# Temporary files
find . -name "*.tmp" -o -name ".DS_Store" -o -name "Thumbs.db"

# Large generated files (should be gitignored)
find . -name "*.log" -size +1M
```

**Keep**:
```bash
# Unit tests (these are NOT artifacts)
tests/

# Type hint files
py.typed

# Configuration files
pytest.ini, .coveragerc, pyproject.toml
```

---

## Performance & Size Monitoring

### Repository Size

```bash
# Check total size
du -sh .

# Find large files
find . -type f -size +10M

# Large directories
du -sh frameworks/* | sort -rh | head -10
```

**Targets**:
- Repo without venv: < 500MB
- Database seed data: < 100MB
- Any single file: < 10MB

### Dependency Size

```bash
# Check venv size (should clean between tests)
du -sh frameworks/*/venv/

# These should be in .gitignore, not committed!
```

---

## CI/CD Cleanliness

### GitHub Actions Workflows

**Ensure**:
- [ ] All checks pass (lint, type, coverage, tests)
- [ ] No warnings in build logs
- [ ] Build time < 5 minutes (for critical path)
- [ ] No flaky tests

**Check**:
```bash
# Verify workflows
ls .github/workflows/

# Check for correct permissions
grep -r "permissions:" .github/workflows/
```

---

## Regular Maintenance

### Weekly Cleanup

```bash
# Run full test suite
make quality && pytest tests/ -v

# Check for stale branches
git branch -a | grep -v main | head

# Update dependencies
pip list --outdated
```

### Monthly Cleanup

```bash
# Archive old baselines
ls tests/perf/baselines/

# Review error logs
docker logs postgres | tail -100

# Check documentation currency
find docs/ -type f -name "*.md" | xargs grep -l "FIXME\|TODO\|OUTDATED"

# Security audit
pip audit
```

### Per-Release Cleanup

```bash
# Before release:
grep -r "TODO\|FIXME\|DEBUG\|HACK" frameworks/ tests/ --include="*.py"
# Should return: 0 results

# Verify version consistency
cat VERSION
grep version pyproject.toml
grep version package.json

# Ensure all docs current
grep -r "v1\.0" docs/  # Update version refs
```

---

## Checklists

### Before Submitting PR

- [ ] Code passes linting: `make quality`
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No debug code: `grep print, console.log, etc.`
- [ ] No commented code: `grep "^#.*=" or "^//"`
- [ ] Documentation updated
- [ ] Commit message clear and formatted
- [ ] Related issues referenced
- [ ] Tests added for new features

### Before Merging PR

- [ ] All CI checks pass (green ✅)
- [ ] Code review approved
- [ ] Test coverage maintained (70%+)
- [ ] No merge conflicts
- [ ] Documentation complete
- [ ] Performance impact assessed (if applicable)

---

## Troubleshooting Cleanliness Issues

| Issue | Solution |
|-------|----------|
| Large .venv in git | Use .gitignore, never commit venv/ |
| Commented code accumulating | Delete instead of commenting, git history persists |
| Tests failing inconsistently | Fix isolation issues (see TEST_ISOLATION_STRATEGY.md) |
| Documentation out of sync | Run grep to find references, update all at once |
| Dependencies conflicts | Use exact versions in requirements.txt, audit regularly |
| Repository size growing | Find/archive large files, optimize seed data |
| CI/CD slow | Profile workflows, parallelize where possible |

---

## Tool Recommendations

### Local Development

```bash
# Code formatting (automatic)
make format

# Linting (catches issues)
make lint

# Type checking
make type-check

# All three
make quality

# Tests
pytest tests/ -v --cov

# Database reset
docker-compose down postgres && docker-compose up postgres
```

### Pre-Commit Hooks (Optional)

```bash
# Install pre-commit framework
pip install pre-commit

# Configure for project
cp .pre-commit-config.yaml ./

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

---

## Repository Health Dashboard

Use these commands to assess health:

```bash
# Code quality
make quality  # Should show: ✓ lint, ✓ format, ✓ type-check

# Test coverage
pytest tests/ --cov=frameworks --cov-report=term-missing | grep "TOTAL"
# Should show: 70%+

# No development markers
grep -r "TODO\|FIXME\|DEBUG\|HACK\|XXX" frameworks/ tests/ --include="*.py" | wc -l
# Should show: 0

# No commented code
grep -r "^#.*=" frameworks/ --include="*.py" | wc -l
# Should show: very small number (only legitimate comments)

# Repository size
du -sh . | grep -o "[0-9]*M\|[0-9]*G"
# Should show: < 500M (without venv)
```

---

## Related Documentation

- **Code Modification**: `docs/MODIFICATION_GUIDE.md` - How to change code properly
- **Testing**: `docs/TESTING_README.md` - Test standards and practices
- **Version Control**: Git best practices above
- **CI/CD**: `.github/workflows/` - Automated checks

