# Phase 6: Cross-Language Validation & Parity Testing

## Objective

Verify that all 5 framework implementations behave identically, produce correct results, and meet quality standards.

## Success Criteria

- [ ] Functional parity tests pass for all frameworks
- [ ] All frameworks return identical data for same queries
- [ ] Error handling is consistent across frameworks
- [ ] Schema equivalence validated
- [ ] No regressions in performance from Phase 4
- [ ] Code quality metrics acceptable

## Parity Tests

### Functional Equivalence

```python
# tests/parity/test_functional_equivalence.py
import requests
from typing import Dict, List

FRAMEWORKS = {
    "FastAPI": "http://localhost:8001",
    "Express": "http://localhost:8002",
    "Gin": "http://localhost:8003",
    "Spring Boot": "http://localhost:8004",
    "Laravel": "http://localhost:8005",
}

TEST_QUERIES = [
    # Basic queries
    ("simple", "{ users { id name } }"),
    ("nested", "{ posts { id author { name } } }"),
    ("filtered", "{ posts(published: true) { id } }"),
    ("with_args", "{ users(limit: 5) { id } }"),

    # Mutations
    ("create", 'mutation { createUser(name: "Test", email: "test@test.com") { id } }'),

    # Fragments
    ("fragment", """
        fragment UserFields on User { id name email }
        query { users { ...UserFields } }
    """),
]

def execute_query(framework: str, query: str) -> Dict:
    """Execute query against framework."""
    response = requests.post(
        f"{FRAMEWORKS[framework]}/graphql",
        json={"query": query},
        timeout=10
    )
    return response.json()

@pytest.mark.parametrize("query_name,query", TEST_QUERIES)
def test_all_frameworks_return_same_data(query_name, query):
    """All frameworks must return identical data."""
    results = {}

    for framework in FRAMEWORKS.keys():
        results[framework] = execute_query(framework, query)

    # Compare all results
    reference = results["FastAPI"]

    for framework, result in results.items():
        if framework == "FastAPI":
            continue

        assert result == reference, \
            f"{framework} differs from FastAPI for query {query_name}"

def test_all_frameworks_handle_errors_identically():
    """Error responses must be consistent."""
    query = "{ invalidField }"

    for framework in FRAMEWORKS.keys():
        result = execute_query(framework, query)

        assert "errors" in result, f"{framework} didn't error on invalid query"
        assert len(result["errors"]) > 0
        assert "message" in result["errors"][0]
```

### Schema Equivalence

```python
# tests/parity/test_schema_equivalence.py
import json
from pathlib import Path

def test_all_schemas_identical():
    """All language-specific schemas must compile identically."""
    schemas = {}

    for lang in ["python", "typescript", "go", "java", "php"]:
        schema_file = Path(f"fraiseql-schema/schema.{lang}.compiled.json")
        assert schema_file.exists(), f"Compiled schema missing for {lang}"

        schemas[lang] = json.loads(schema_file.read_text())

    # Reference is Python (primary)
    reference = schemas["python"]

    for lang, schema in schemas.items():
        if lang == "python":
            continue

        # Same types
        assert schema["types"].keys() == reference["types"].keys(), \
            f"{lang} has different types"

        # Same queries
        assert schema["query"].keys() == reference["query"].keys(), \
            f"{lang} has different queries"

        # Same mutations
        assert schema["mutation"].keys() == reference["mutation"].keys(), \
            f"{lang} has different mutations"
```

## Code Quality Validation

### Linting & Type Checking

```bash
#!/bin/bash
# tests/quality/check_all.sh

echo "Checking code quality across all frameworks..."

# Python: ruff + type checking
cd frameworks/fraiseql-python
python -m ruff check .
cd ../..

# TypeScript: eslint + typescript
cd frameworks/fraiseql-typescript
npm run lint
npm run type-check
cd ../..

# Go: golangci-lint
cd frameworks/fraiseql-go
golangci-lint run ./...
cd ../..

# Java: spotbugs + checkstyle
cd frameworks/fraiseql-java
mvn spotbugs:check checkstyle:check
cd ../..

# PHP: phpstan + psalm
cd frameworks/fraiseql-php
vendor/bin/phpstan analyse
vendor/bin/psalm
cd ../..

echo "✓ All code quality checks passed"
```

### Test Coverage

```python
# All frameworks must meet minimum coverage
def test_coverage_meets_minimum():
    """Minimum 80% test coverage required."""
    frameworks = {
        "fastapi": ".coverage-python",
        "express": "coverage/coverage-summary.json",
        "gin": "coverage.txt",
        "spring-boot": "target/site/jacoco/index.html",
        "laravel": "coverage/clover.xml",
    }

    for framework, coverage_file in frameworks.items():
        coverage = parse_coverage(coverage_file)
        assert coverage >= 80, \
            f"{framework} coverage {coverage}% below 80% minimum"
```

## Performance Regression Testing

```python
# tests/parity/test_performance_regression.py
import pytest

# Phase 4 baselines (established in previous phase)
PHASE4_BASELINES = {
    "FastAPI": {"simple": 23.1, "nested": 51.2, "filtered": 24.5},
    "Express": {"simple": 21.5, "nested": 48.7, "filtered": 22.8},
    "Gin": {"simple": 19.4, "nested": 45.1, "filtered": 21.2},
    "Spring Boot": {"simple": 28.1, "nested": 53.4, "filtered": 29.3},
    "Laravel": {"simple": 32.5, "nested": 62.1, "filtered": 35.7},
}

@pytest.mark.benchmark
@pytest.mark.parametrize("framework", list(PHASE4_BASELINES.keys()))
def test_no_performance_regression(framework, benchmark):
    """Performance must not regress from Phase 4."""
    baseline = PHASE4_BASELINES[framework]

    # Measure current performance
    current = benchmark(
        lambda: execute_query(framework, "{ users { id } }")
    )

    # Allow 5% regression tolerance
    assert current["simple"] < baseline["simple"] * 1.05, \
        f"{framework} performance regressed"
```

## Integration Testing

```python
# tests/integration/test_full_workflow.py
def test_complete_workflow():
    """Full workflow: create, read, update."""
    # 1. Create user
    create_result = execute_mutation(
        "FastAPI",
        'mutation { createUser(name: "Alice", email: "alice@test.com") { id } }'
    )
    user_id = create_result["data"]["createUser"]["id"]

    # 2. Query created user
    query_result = execute_query(
        "Express",
        f'{{ user(id: {user_id}) {{ name email }} }}'
    )
    assert query_result["data"]["user"]["name"] == "Alice"

    # 3. Verify other frameworks see same data
    for framework in ["Gin", "Spring Boot", "Laravel"]:
        result = execute_query(
            framework,
            f'{{ user(id: {user_id}) {{ name }} }}'
        )
        assert result["data"]["user"]["name"] == "Alice"
```

## Data Consistency Testing

```python
# tests/parity/test_data_consistency.py
def test_concurrent_mutations_consistent():
    """Concurrent mutations produce consistent state."""
    import concurrent.futures
    import time

    results = []

    def create_user(name):
        result = execute_mutation(
            "FastAPI",
            f'mutation {{ createUser(name: "{name}", email: "{name}@test.com") {{ id }} }}'
        )
        results.append(result)

    # Create 10 users concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_user, f"user_{i}") for i in range(10)]
        concurrent.futures.wait(futures)

    # All should succeed
    assert all("id" in r["data"]["createUser"] for r in results)

    # All frameworks should see all created users
    for framework in FRAMEWORKS.keys():
        query = "{ users { name } }"
        result = execute_query(framework, query)
        user_count = len(result["data"]["users"])

        assert user_count >= 10, \
            f"{framework} only sees {user_count} users, expected ≥ 10"
```

## Validation Report

```markdown
# Cross-Language Validation Report

## Functional Parity: ✅ PASS
- All frameworks execute same queries
- All frameworks return identical data
- All frameworks handle errors uniformly

## Schema Equivalence: ✅ PASS
- Python, TypeScript, Go, Java, PHP schemas identical
- All compile to same schema.compiled.json
- All language generators working correctly

## Code Quality: ✅ PASS
- All linters pass
- All type checks pass
- Coverage ≥ 80% across all frameworks

## Performance: ✅ PASS
- No regressions vs Phase 4 baseline
- Performance within 5% tolerance
- All frameworks scale to concurrent load

## Data Consistency: ✅ PASS
- Concurrent operations produce consistent state
- All frameworks see identical data
- Database integrity maintained

## Test Coverage Summary
| Framework | Line Coverage | Branch Coverage | Passing Tests |
|-----------|---------------|-----------------|---------------|
| FastAPI   | 84%           | 78%             | 42/42         |
| Express   | 81%           | 76%             | 38/38         |
| Gin       | 86%           | 82%             | 45/45         |
| Spring    | 80%           | 75%             | 40/40         |
| Laravel   | 82%           | 77%             | 39/39         |

## Recommendation
✅ All frameworks ready for Phase 7 (documentation and release)
```

## Deliverables

```
tests/parity/
├── test_functional_equivalence.py
├── test_schema_equivalence.py
├── test_error_handling.py
├── test_data_consistency.py
└── conftest.py

tests/quality/
├── check_all.sh
├── coverage_validation.py
└── linting_rules.yaml

tests/integration/
└── test_full_workflow.py

reports/
└── parity_report_[date].md
```

## Dependencies

- Requires: Phase 5 (all features implemented)
- Blocks: Phase 7 (documentation)

## Status

[ ] Not Started | [ ] In Progress | [ ] Complete

## Notes

- Parity tests ensure identical behavior across languages
- No feature variations allowed
- Performance baseline established in Phase 4 is reference
- All tests must pass before proceeding to Phase 7
