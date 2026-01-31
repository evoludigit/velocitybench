# Testing Infrastructure Documentation

Welcome to VelocityBench's comprehensive testing guide. This documentation covers everything you need to write, run, and maintain tests across all framework implementations.

---

## 🎯 Quick Navigation

### For New Contributors
- **[FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md)** - Get your environment running (5-10 min)
- **[TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md)** - How to name tests
- **[FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)** - How to create test data

### For Test Development
- **[TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md)** - How test data stays clean
- **[CROSS_FRAMEWORK_TEST_DATA.md](CROSS_FRAMEWORK_TEST_DATA.md)** - Consistent data across frameworks
- **[TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md)** - Writing clear, discoverable tests

### For Performance Testing
- **[PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md)** - Capturing and comparing performance
- **[PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md)** - Optimizing queries and frameworks

### For Debugging & Troubleshooting
- **[TEST_ISOLATION_STRATEGY.md#debugging-test-failures](TEST_ISOLATION_STRATEGY.md#debugging-test-failures)** - Debug failed tests
- **[CROSS_FRAMEWORK_TEST_DATA.md#troubleshooting-consistency-issues](CROSS_FRAMEWORK_TEST_DATA.md#troubleshooting-consistency-issues)** - Data consistency issues

---

## 📋 Testing Overview

VelocityBench has **comprehensive test infrastructure** covering:

### Test Types

| Type | Purpose | Location | Markers |
|------|---------|----------|---------|
| **Unit Tests** | Test individual functions/components | `tests/` | `@pytest.mark.unit` |
| **Integration Tests** | Test against real database | `tests/integration/` | `@pytest.mark.integration` |
| **Performance Tests** | Measure latency and throughput | `tests/perf/` | `@pytest.mark.perf` |
| **Security Tests** | Test security validations | `tests/` | `@pytest.mark.security` |
| **Health Checks** | Test service readiness | `tests/health/` | N/A |

### Test Coverage

- **35+ frameworks** tested consistently
- **6 dimensional testing**: schema, queries, N+1, consistency, error handling, security
- **70% minimum coverage** enforced (`.coveragerc`)
- **Shared test infrastructure** (`tests/common/`) reduces duplication by 80%

### Key Features

✅ **Transaction-based isolation** - Clean data between tests (no manual cleanup)
✅ **Shared factory** - Consistent test data across all frameworks
✅ **Parametrized tests** - Run same test on multiple frameworks
✅ **Performance tracking** - Baseline management and regression detection
✅ **CI/CD integration** - Automated testing on every commit

---

## 🚀 Quick Start

### 1. Set Up Environment (5 minutes)

```bash
# Start database
docker-compose up -d postgres

# Install dependencies
cd frameworks/strawberry
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Run Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_users.py

# Specific test
pytest tests/test_users.py::test_user_creation

# Only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# With coverage
pytest tests/ --cov=frameworks/strawberry --cov-report=html
```

### 3. Write Your First Test

```python
# tests/test_hello.py
import pytest

def test_hello_world(db, factory):
    """Test creating a user."""
    user = factory.create_user("alice", "alice@example.com")
    assert user["username"] == "alice"
```

Run it:
```bash
pytest tests/test_hello.py -v
```

---

## 📖 Documentation Map

### Core Concepts

**[TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md)**
- How transaction-based isolation works
- Why it's better than manual cleanup
- Advanced patterns and workarounds
- Debugging isolation issues

**[FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)**
- Creating individual test entities (factory)
- Creating many entities efficiently (bulk_factory)
- Real-world test examples
- Performance tips

### Consistency & Quality

**[TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md)**
- File naming patterns
- Function naming patterns
- Class naming patterns
- Documentation in tests

**[CROSS_FRAMEWORK_TEST_DATA.md](CROSS_FRAMEWORK_TEST_DATA.md)**
- Shared schema across all frameworks
- Data consistency principles
- Framework-specific considerations
- Multi-framework test examples

### Performance

**[PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md)**
- What baselines are and why they matter
- Capturing baselines
- Comparing baselines
- CI/CD integration
- Update policies

**[PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md)**
- Query optimization patterns
- Connection pooling tuning
- Index strategies
- Load testing setup

---

## 🔍 Common Tasks

### Create Test Data

```python
from tests.common.fixtures import db, factory

def test_something(db, factory):
    """Create user and post."""
    user = factory.create_user("alice", "alice@example.com")
    post = factory.create_post(fk_author=user["pk_user"], title="Post")
    # Data automatically cleaned up after test
```

See: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)

### Name Your Test

```python
def test_user_creation_with_valid_data_succeeds(db, factory):
    """User creation with valid data succeeds."""
    # Given: valid data
    # When: user is created
    # Then: user is persisted
```

See: [TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md)

### Debug a Failed Test

```bash
# Run with output
pytest tests/test_users.py::test_user_creation -s

# Run with detailed output
pytest tests/test_users.py::test_user_creation -vv

# Run with pdb on failure
pytest tests/test_users.py::test_user_creation --pdb

# Run with logging
pytest tests/test_users.py::test_user_creation --log-cli-level=DEBUG
```

See: [TEST_ISOLATION_STRATEGY.md#debugging-test-failures](TEST_ISOLATION_STRATEGY.md#debugging-test-failures)

### Check Performance

```bash
# Run performance tests
pytest tests/perf/ -v --benchmark-only

# Compare against baseline
python tests/perf/scripts/compare_baselines.py \
    --before tests/perf/baselines/v1.0/strawberry.json \
    --after tests/perf/baselines/current/strawberry.json
```

See: [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md)

### Run Tests on Specific Framework

```bash
# FastAPI tests
cd frameworks/fastapi-rest
pytest tests/

# Strawberry tests
cd frameworks/strawberry
pytest tests/

# All frameworks
cd /path/to/root
pytest tests/qa/  # Cross-framework QA tests
```

---

## 🛠️ Tools & Configuration

### Configuration Files

| File | Purpose |
|------|---------|
| `pytest.ini` | Pytest configuration (markers, discovery, output) |
| `.coveragerc` | Coverage configuration (70% minimum, branch coverage) |
| `.pre-commit-config.yaml` | Pre-commit hooks (linting, formatting, security) |

### Test Markers

```bash
# Run only security tests
pytest -m security

# Run all except slow tests
pytest -m "not slow"

# Run integration or performance tests
pytest -m "integration or perf"
```

Available markers:
- `unit` - Unit tests
- `integration` - Integration tests
- `perf` - Performance tests
- `security` - Security tests
- `slow` - Slow-running tests
- `asyncio` - Async tests
- `query` - Query tests
- `mutation` - Mutation tests
- `schema` - Schema tests

### Common Commands

```bash
# Run all tests with coverage
pytest tests/ --cov=frameworks --cov-report=html

# Run tests in parallel (faster)
pytest tests/ -n auto

# Run with detailed output
pytest tests/ -vv --tb=short

# Run and exit on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Generate test report
pytest tests/ --html=report.html
```

---

## 🎓 Learning Path

### Level 1: Basic Testing (1-2 hours)

1. Read: [FIRST_TIME_SETUP.md](FIRST_TIME_SETUP.md)
2. Read: [TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md) - Overview section
3. Read: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md) - Basic patterns
4. **DO:** Write 3 simple tests using factory fixture
5. **DO:** Run tests and verify they pass

### Level 2: Intermediate Testing (2-4 hours)

1. Read: [TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md)
2. Read: [CROSS_FRAMEWORK_TEST_DATA.md](CROSS_FRAMEWORK_TEST_DATA.md) - Data consistency
3. Read: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md) - Advanced examples
4. **DO:** Write 5 tests with detailed naming and documentation
5. **DO:** Debug a failing test using techniques from [TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md#debugging-test-failures)

### Level 3: Advanced Testing (4+ hours)

1. Read: [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md)
2. Read: [PERFORMANCE_TUNING_GUIDE.md](PERFORMANCE_TUNING_GUIDE.md)
3. **DO:** Write performance tests and capture baseline
4. **DO:** Optimize a slow query and update baseline
5. **DO:** Create a parametrized test that runs across multiple frameworks

---

## 📊 Testing Statistics

### Current Test Suite

- **59 test files** across the project
- **1000+ test functions** covering all frameworks
- **70% minimum coverage** enforced
- **80% code duplication reduction** from test consolidation
- **35 frameworks** tested consistently

### Test Execution Times

| Category | Typical Duration |
|----------|-----------------|
| Unit tests | < 1 second |
| Integration tests | 5-10 seconds |
| Full test suite | 2-5 minutes |
| Performance suite | 5-15 minutes |
| All tests with coverage | 10-20 minutes |

---

## ❓ FAQ

### Q: How do I ensure test data is clean?
A: Use the `db` fixture. It automatically rolls back transactions after each test.

See: [TEST_ISOLATION_STRATEGY.md](TEST_ISOLATION_STRATEGY.md)

### Q: What's the difference between factory and bulk_factory?
A: `factory` creates individual entities with custom values. `bulk_factory` creates many entities efficiently.

See: [FIXTURE_FACTORY_GUIDE.md](FIXTURE_FACTORY_GUIDE.md)

### Q: How do I test the same thing on multiple frameworks?
A: Use parametrized fixtures or conftest.py setup.

See: [CROSS_FRAMEWORK_TEST_DATA.md](CROSS_FRAMEWORK_TEST_DATA.md)

### Q: How do I track performance regression?
A: Capture baselines and run regression tests in CI/CD.

See: [PERFORMANCE_BASELINE_MANAGEMENT.md](PERFORMANCE_BASELINE_MANAGEMENT.md)

### Q: What markers should I use?
A: Use markers from pytest.ini to categorize tests by type and purpose.

See: [TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md#marker-usage)

---

## 🤝 Contributing Tests

When adding new tests:

1. ✅ **Use fixtures** - Always use `db` and `factory` for consistency
2. ✅ **Follow naming** - Use `test_<what>_<scenario>_<expected>` pattern
3. ✅ **Document** - Add docstring with Given-When-Then format
4. ✅ **Mark appropriately** - Use `@pytest.mark.integration` etc.
5. ✅ **Check coverage** - Run with `--cov` to ensure you maintain 70%+
6. ✅ **Test across frameworks** - Verify test works on multiple frameworks

See: [TEST_NAMING_CONVENTIONS.md](TEST_NAMING_CONVENTIONS.md)

---

## 🔗 Related Documentation

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Full development setup guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview
- **[ADD_FRAMEWORK_GUIDE.md](ADD_FRAMEWORK_GUIDE.md)** - Adding new frameworks
- **[SECURITY.md](../SECURITY.md)** - Security testing guidelines

---

## 📞 Support

Having trouble?

1. **Check the FAQ** above
2. **Read relevant documentation** - Each topic has detailed guides
3. **Review example tests** - Search for `test_user_creation` in codebase
4. **Run with debug flags** - Use `-vv --log-cli-level=DEBUG`
5. **Ask in CONTRIBUTING.md** - See development guidelines

---

## 🎉 You're Ready!

You now have everything needed to write, run, and maintain tests in VelocityBench. Start with the Quick Start section above and reference specific guides as needed.

Happy testing! 🚀
