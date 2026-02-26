# Pytest Configuration Guide

VelocityBench uses pytest as its unified testing framework across all Python components. This guide explains the pytest configuration, test organization, and best practices.

## Configuration File

The project uses a centralized `pytest.ini` at the repository root to standardize test execution across all frameworks and components.

**Location**: `/home/lionel/code/velocitybench/pytest.ini`

## Test Discovery

Pytest automatically discovers tests using these patterns:

```ini
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
```

### File Naming Conventions

- **Test Files**: `test_*.py` or `*_test.py`
  - Good: `test_graphql_schema.py`, `api_test.py`
  - Bad: `tests.py`, `mytests.py`

- **Test Classes**: `Test*`
  - Good: `TestUserAPI`, `TestPostQueries`
  - Bad: `UserTests`, `APITestCase`

- **Test Functions**: `test_*`
  - Good: `test_create_user()`, `test_n1_prevention()`
  - Bad: `validate_user()`, `check_queries()`

### Test Directory Structure

```
tests/
├── qa/                          # Integration tests (all frameworks)
│   ├── test_rest_frameworks.py
│   ├── test_graphql_frameworks.py
│   └── validators/
│       ├── test_schema_validator.py
│       ├── test_query_validator.py
│       └── test_n1_detector.py
├── perf/                        # Performance tests
│   └── test_benchmarks.py
├── unit/                        # Unit tests
│   ├── test_trinity_pattern.py
│   └── test_async_db.py
└── fixtures/                    # Shared test fixtures
    ├── conftest.py
    └── expected_responses/
```

## Test Output and Reporting

### Console Output

Pytest is configured for verbose, informative output:

```ini
addopts =
    -v                    # Verbose output
    --tb=short            # Short traceback format
    --showlocals          # Show local variables in failures
    --color=yes           # Colored output
```

**Example output**:
```
tests/qa/test_rest_frameworks.py::TestFastAPI::test_get_users PASSED       [ 10%]
tests/qa/test_rest_frameworks.py::TestFastAPI::test_create_post FAILED     [ 20%]

=================================== FAILURES ===================================
___________________________ TestFastAPI.test_create_post _______________________

self = <test_rest_frameworks.TestFastAPI object at 0x7f8b4c>
framework_url = 'http://localhost:8000'

    def test_create_post(framework_url):
        response = requests.post(f"{framework_url}/posts", json={"title": "Test"})
>       assert response.status_code == 201
E       AssertionError: assert 400 == 201

framework_url = 'http://localhost:8000'
response = <Response [400]>

tests/qa/test_rest_frameworks.py:42: AssertionError
```

### Coverage Reports

VelocityBench is configured to generate multiple coverage report formats:

```ini
--cov-report=term-missing:skip-covered  # Terminal output (only show uncovered lines)
--cov-report=html                       # HTML report (coverage/index.html)
--cov-report=xml                        # XML report (for CI tools)
```

**Coverage Settings**:
```ini
[coverage:run]
branch = True                           # Measure branch coverage
source = frameworks, database, tests    # Directories to measure
omit =
    */site-packages/*                   # Exclude third-party packages
    */tests/*                           # Exclude test files from coverage

[coverage:report]
fail_under = 70                         # Fail if coverage < 70%
precision = 2                           # Report precision (e.g., 73.45%)
exclude_lines =
    pragma: no cover                    # Explicit exclusion marker
    def __repr__                        # Repr methods
    if __name__ == .__main__.:          # Script entry points
    raise AssertionError                # Defensive assertions
    raise NotImplementedError           # Abstract methods
    if TYPE_CHECKING:                   # Type checking blocks
    @abstractmethod                     # Abstract methods
```

### CI/CD Integration

Pytest generates JUnit XML for CI/CD integration:

```ini
--junit-xml=junit.xml
```

This XML file is consumed by GitHub Actions to display test results in the PR interface.

## Test Markers

VelocityBench uses markers to organize and selectively run tests:

```ini
markers =
    asyncio: marks tests as async (requires pytest-asyncio)
    integration: marks tests as integration tests
    performance: marks tests as performance benchmarks
    security: marks tests as security checks
    slow: marks tests as slow-running
    unit: marks tests as unit tests
```

### Using Markers

**In test code**:
```python
import pytest

@pytest.mark.unit
def test_user_validation():
    """Unit test for user validation logic."""
    assert validate_user({"name": "Alice"}) is True

@pytest.mark.asyncio
@pytest.mark.integration
async def test_graphql_query():
    """Integration test for GraphQL query."""
    response = await client.query("{ users { id } }")
    assert response["data"]["users"] is not None

@pytest.mark.slow
@pytest.mark.performance
def test_load_100k_users():
    """Performance test with 100k users."""
    users = load_users(100_000)
    assert len(users) == 100_000
```

**Running specific markers**:
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only async tests
pytest -m asyncio

# Exclude slow tests
pytest -m "not slow"

# Run integration OR performance tests
pytest -m "integration or performance"

# Run integration tests but not slow ones
pytest -m "integration and not slow"
```

## Async Testing

VelocityBench uses `pytest-asyncio` for async test support:

```ini
asyncio_mode = auto
```

**Auto mode** means:
- Async test functions are automatically detected (no need for `@pytest.mark.asyncio` in most cases)
- Event loop is created and torn down per test
- Fixtures can be async

**Example async test**:
```python
import pytest
from httpx import AsyncClient

async def test_async_graphql_query():
    """Test async GraphQL query."""
    async with AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/graphql",
            json={"query": "{ users { id } }"}
        )
        assert response.status_code == 200
```

**Async fixtures**:
```python
import pytest
from frameworks.common.async_db import AsyncDatabase

@pytest.fixture
async def db():
    """Provide async database connection."""
    db = AsyncDatabase("postgresql://localhost/test")
    await db.connect()
    yield db
    await db.disconnect()

async def test_query_users(db):
    """Test querying users from database."""
    users = await db.fetch_all("SELECT * FROM v_users LIMIT 10")
    assert len(users) == 10
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run tests in specific directory
pytest tests/qa/

# Run specific test file
pytest tests/qa/test_rest_frameworks.py

# Run specific test function
pytest tests/qa/test_rest_frameworks.py::test_get_users

# Run specific test class
pytest tests/qa/test_rest_frameworks.py::TestFastAPI

# Run with verbose output
pytest -v

# Run with extra verbosity (show individual assertions)
pytest -vv

# Run in quiet mode (minimal output)
pytest -q
```

### Advanced Commands

```bash
# Run only failed tests from last run
pytest --lf

# Run failed tests first, then all others
pytest --ff

# Stop after first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Show 10 slowest tests
pytest --durations=10

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run with coverage
pytest --cov=frameworks --cov-report=html

# Run and open HTML coverage report
pytest --cov=frameworks --cov-report=html && open htmlcov/index.html

# Generate JUnit XML report
pytest --junit-xml=results.xml
```

### Virtual Environment-Specific Testing

Since VelocityBench uses multiple venvs, run tests in the correct context:

```bash
# FastAPI framework tests
source frameworks/fastapi-rest/.venv/bin/activate
pytest frameworks/fastapi-rest/tests/

# Database tests
source database/.venv/bin/activate
pytest database/tests/

# QA integration tests (cross-framework)
source tests/qa/.venv/bin/activate
pytest tests/qa/
```

## Writing Effective Tests

### Test Structure (AAA Pattern)

```python
def test_create_user():
    """Test user creation."""
    # Arrange: Setup test data
    user_data = {
        "name": "Alice",
        "email": "alice@example.com"
    }

    # Act: Perform the action
    response = client.post("/users", json=user_data)

    # Assert: Verify the result
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"
    assert response.json()["email"] == "alice@example.com"
```

### Parameterized Tests

Test multiple inputs efficiently:

```python
import pytest

@pytest.mark.parametrize("email,is_valid", [
    ("alice@example.com", True),
    ("bob@test.co.uk", True),
    ("invalid", False),
    ("@missing-local.com", False),
    ("missing-at.com", False),
])
def test_email_validation(email, is_valid):
    """Test email validation with various inputs."""
    assert validate_email(email) == is_valid
```

### Fixtures

Share setup code across tests:

```python
import pytest

@pytest.fixture
def sample_user():
    """Provide a sample user for testing."""
    return {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com"
    }

def test_user_serialization(sample_user):
    """Test user serialization."""
    json_str = serialize_user(sample_user)
    assert "Alice" in json_str

def test_user_validation(sample_user):
    """Test user validation."""
    assert validate_user(sample_user) is True
```

### Test Naming

Follow these conventions:

- **Descriptive names**: `test_get_user_returns_404_when_not_found()`
- **What is being tested**: `test_graphql_query_with_nested_fields()`
- **Expected behavior**: `test_create_post_increases_count_by_one()`

## CI/CD Integration

### GitHub Actions

VelocityBench's GitHub Actions workflow uses pytest:

```yaml
# .github/workflows/unit-tests.yml
qa-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov pytest-asyncio

    - name: Run tests
      run: |
        pytest tests/ \
          --cov=frameworks \
          --cov=database \
          --cov-report=xml \
          --junit-xml=junit.xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml

    - name: Publish test results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always()
      with:
        files: junit.xml
```

### Pre-commit Hooks

Run tests before committing:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-fast
        name: Run fast tests
        entry: pytest -m "not slow" --tb=short
        language: system
        pass_filenames: false
        always_run: true
```

## Debugging Tests

### Using pdb

```python
def test_complex_query():
    """Test complex query logic."""
    result = execute_complex_query()

    # Drop into debugger to inspect state
    import pdb; pdb.set_trace()

    assert result is not None
```

### Verbose tracebacks

```bash
# Full traceback
pytest --tb=long

# Show all variables
pytest --showlocals

# Capture output (don't suppress print statements)
pytest -s
```

### Running single test with debugging

```bash
# Run single test with full output
pytest tests/qa/test_schema.py::test_graphql_schema -vv -s --tb=long
```

## Common Issues

### Issue: Tests not discovered

**Cause**: File/function naming doesn't match patterns

**Solution**: Ensure files start with `test_` and functions start with `test_`

### Issue: Import errors

**Cause**: Wrong virtual environment activated

**Solution**: Activate the correct venv for the component you're testing

```bash
# Wrong: Root venv for framework tests
source venv/bin/activate

# Right: Framework-specific venv
source frameworks/fastapi-rest/.venv/bin/activate
```

### Issue: Async tests failing

**Cause**: Missing `pytest-asyncio` or wrong asyncio mode

**Solution**: Install `pytest-asyncio` and ensure `asyncio_mode = auto` in pytest.ini

### Issue: Coverage too low

**Cause**: Missing test coverage for key code paths

**Solution**: Check HTML coverage report to identify uncovered lines

```bash
pytest --cov=frameworks --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Best Practices

1. **Test one thing**: Each test should validate one specific behavior
2. **Descriptive names**: Test names should explain what's being tested
3. **Fast tests**: Keep unit tests under 100ms, integration tests under 1s
4. **Isolated tests**: Tests shouldn't depend on each other's state
5. **Markers**: Use markers to organize tests logically
6. **Fixtures**: Use fixtures to avoid repetitive setup code
7. **Assertions**: Use pytest's rich assertions (no need for unittest's assertEqual)
8. **Coverage**: Aim for 70%+ coverage, but don't obsess over 100%

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest.ini Documentation](https://docs.pytest.org/en/stable/reference/customize.html#pytest-ini)
- [ADR-009: Six-Dimensional QA Testing](adr/009-six-dimensional-qa-testing.md)
