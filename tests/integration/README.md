# Integration Test Suite

Comprehensive integration tests for the FraiseQL Performance Assessment project. These tests verify that all frameworks are running correctly and responding to health checks and API requests.

## Test Scripts

### 1. Quick Smoke Test (`smoke-test.sh`)

**Purpose**: Fast health-check verification of all frameworks.

**Usage**:
```bash
./smoke-test.sh
```

**What it tests**:
- ✅ Health endpoint responds with HTTP 200
- ✅ Framework is accessible on configured port

**Output**:
```
╔═══════════════════════════════════════════════════════════════════╗
║  Quick Smoke Test - Framework Health Check                       ║
╚═══════════════════════════════════════════════════════════════════╝

✓ fraiseql              http://localhost:4000
✓ strawberry            http://localhost:8011
✓ graphene              http://localhost:8002
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Running:  14
  Stopped:  0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All frameworks are running!
```

**Exit codes**:
- `0` - All frameworks healthy
- `1` - One or more frameworks down

**Runtime**: ~5-10 seconds

---

### 2. Comprehensive Integration Tests (`test-all-frameworks.sh`)

**Purpose**: Full integration test suite with detailed verification.

**Usage**:
```bash
# Test all frameworks
./test-all-frameworks.sh

# Test only GraphQL frameworks
./test-all-frameworks.sh --type=graphql

# Test only REST frameworks
./test-all-frameworks.sh --type=rest

# Test specific framework
./test-all-frameworks.sh --framework=fraiseql

# Verbose output
./test-all-frameworks.sh --verbose
```

**What it tests**:
- ✅ Port is listening (TCP connection)
- ✅ Health endpoint returns HTTP 200
- ✅ API endpoint functionality:
  - **GraphQL**: Introspection query (`{ __typename }`)
  - **REST**: List endpoint returns valid JSON
- ✅ Metrics endpoint (optional, passes if 200 or 404)

**Output**:
```
╔═══════════════════════════════════════════════════════════════════╗
║  FraiseQL Performance Assessment - Integration Test Suite        ║
║  Testing all frameworks for health and functionality             ║
╚═══════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Testing: fraiseql (Port: 4000, Type: graphql)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓  Port 4000 is listening
✓  Health check passed: /health
✓  GraphQL introspection query passed
○  Metrics endpoint not implemented (optional)

  ✓ fraiseql: All tests passed (4/4)
...

╔═══════════════════════════════════════════════════════════════════╗
║  Test Summary                                                     ║
╚═══════════════════════════════════════════════════════════════════╝

  Total Tests:    56
  Passed:         56
  Failed:         0
  Skipped:        0

  Success Rate:   100%

  Results saved to: ./results/test-results-20251220_143022.json
  Logs saved to:    ./results/test-run-20251220_143022.log
```

**Exit codes**:
- `0` - All tests passed
- `1` - One or more tests failed

**Results**:
- JSON results file: `results/test-results-{timestamp}.json`
- Detailed logs: `results/test-run-{timestamp}.log`

**Runtime**: ~30-60 seconds (all frameworks)

---

### 3. Python Test Suite (`test_frameworks.py`)

**Purpose**: Advanced integration tests with retry logic and detailed reporting.

**Usage**:
```bash
# Test all frameworks
./test_frameworks.py

# Test specific framework
./test_frameworks.py --framework=fraiseql

# Test only GraphQL frameworks
./test_frameworks.py --type=graphql

# Test only REST frameworks
./test_frameworks.py --type=rest

# Custom timeout (default: 5 seconds)
./test_frameworks.py --timeout=10
```

**What it tests**:
- ✅ Health endpoint verification
- ✅ GraphQL introspection queries (for GraphQL frameworks)
- ✅ REST endpoint validation (for REST frameworks)
- ✅ Metrics endpoint availability
- ✅ Response time tracking
- ✅ Automatic retries on transient failures

**Output**:
```
======================================================================
  FraiseQL Performance Assessment - Integration Test Suite
  Testing all frameworks for health and functionality
======================================================================

Testing 14 frameworks...

======================================================================
Testing: fraiseql (Port: 4000, Type: graphql)
======================================================================
  → Testing health endpoint...
    ✓ Health check passed (15.3ms)
  → Testing GraphQL introspection...
    ✓ API test passed (23.7ms)
  → Testing metrics endpoint...
    ✓ Metrics check passed - not implemented (optional)

======================================================================
  Test Summary
======================================================================

  Total Tests:    42
  ✓ Passed:       42
  ✗ Failed:       0

  Success Rate:   100.0%

  Framework Summary:
  ------------------------------------------------------------------
  ✓ fraiseql              3/3
  ✓ strawberry            3/3
  ✓ graphene              3/3
  ...

  Results saved to: results/test-results-20251220_143045.json
```

**Exit codes**:
- `0` - All tests passed
- `1` - One or more tests failed

**Results**:
- JSON file: `results/test-results-{timestamp}.json`
- Includes per-test duration, error messages, and response data

**Runtime**: ~45-90 seconds (all frameworks)

---

## Framework Configuration

All test scripts use `framework-config.json` for framework definitions:

```json
{
  "frameworks": {
    "fraiseql": {
      "port": 4000,
      "type": "graphql",
      "health": "/health",
      "endpoint": "/graphql",
      "language": "python",
      "category": "graphql-framework"
    },
    "express-rest": {
      "port": 8005,
      "type": "rest",
      "health": "/health",
      "endpoint": "/users",
      "language": "typescript",
      "category": "rest-library"
    }
    // ... more frameworks
  }
}
```

To add a new framework, edit this configuration file.

---

## Prerequisites

### Starting All Frameworks

Before running tests, ensure all frameworks are running:

```bash
# From project root
docker-compose up -d

# Wait for all services to be healthy (30-60 seconds)
docker-compose ps
```

### Python Dependencies (for test_frameworks.py)

The Python test suite requires:
```bash
pip install requests
```

Or using the project's package manager:
```bash
uv pip install requests
```

---

## Test Results

All test scripts save results to `tests/integration/results/`:

- `test-results-{timestamp}.json` - Structured test results
- `test-run-{timestamp}.log` - Detailed execution logs (Bash script only)

**Example JSON result**:
```json
{
  "timestamp": "20251220_143045",
  "total_tests": 42,
  "passed": 42,
  "failed": 0,
  "tests": [
    {
      "framework": "fraiseql",
      "test_name": "health_check",
      "passed": true,
      "duration_ms": 15.3,
      "error_message": null,
      "response_data": {"status": "healthy"}
    }
  ]
}
```

---

## Troubleshooting

### Framework Not Running

**Symptom**:
```
✗ fraiseql              http://localhost:4000 (status: 000)
```

**Fix**:
```bash
# Check if docker containers are running
docker-compose ps

# Start specific framework
docker-compose up -d fraiseql

# View framework logs
docker-compose logs fraiseql
```

### Connection Timeout

**Symptom**:
```
✗ Port 4000 is NOT listening (framework may not be running)
```

**Fix**:
```bash
# Increase timeout
./test_frameworks.py --timeout=10

# Check if port is bound
netstat -tlnp | grep :4000

# Restart framework
docker-compose restart fraiseql
```

### GraphQL Introspection Failed

**Symptom**:
```
✗ GraphQL introspection query failed
```

**Fix**:
```bash
# Test manually
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}'

# Check framework logs for errors
docker-compose logs fraiseql
```

### REST Endpoint Invalid JSON

**Symptom**:
```
✗ REST endpoint failed or returned invalid JSON
```

**Fix**:
```bash
# Test manually
curl http://localhost:8005/users?limit=5

# Verify endpoint path in framework-config.json
cat framework-config.json | grep -A5 "express-rest"
```

---

## CI/CD Integration

These tests are designed for integration into CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start frameworks
        run: docker-compose up -d
      - name: Wait for services
        run: sleep 30
      - name: Run integration tests
        run: cd tests/integration && ./test-all-frameworks.sh
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: tests/integration/results/
```

### GitLab CI Example

```yaml
integration-tests:
  stage: test
  script:
    - docker-compose up -d
    - sleep 30
    - cd tests/integration && ./test-all-frameworks.sh
  artifacts:
    paths:
      - tests/integration/results/
    expire_in: 1 week
```

---

## Test Coverage

| Framework | Type | Port | Health | API Endpoint | Metrics |
|-----------|------|------|--------|-------------|---------|
| fraiseql | GraphQL | 4000 | ✅ | ✅ | ✅ |
| strawberry | GraphQL | 8011 | ✅ | ✅ | ✅ |
| graphene | GraphQL | 8002 | ✅ | ✅ | ✅ |
| apollo-server | GraphQL | 4002 | ✅ | ✅ | ✅ |
| apollo-orm | GraphQL | 4005 | ✅ | ✅ | ✅ |
| async-graphql | GraphQL | 8016 | ✅ | ✅ | ✅ |
| go-gqlgen | GraphQL | 4001 | ✅ | ✅ | ✅ |
| ruby-rails | GraphQL | 3001 | ✅ | ✅ | ✅ |
| express-rest | REST | 8005 | ✅ | ✅ | ✅ |
| express-orm | REST | 8007 | ✅ | ✅ | ✅ |
| fastapi-rest | REST | 8003 | ✅ | ✅ | ✅ |
| flask-rest | REST | 8004 | ✅ | ✅ | ✅ |
| actix-web-rest | REST | 8015 | ✅ | ✅ | ✅ |
| gin-rest | REST | 8006 | ✅ | ✅ | ✅ |
| java-spring-boot | Hybrid | 8018 | ✅ | ✅ | ✅ |

---

## Development Workflow

### Quick Development Cycle

```bash
# 1. Make code changes to a framework
vim frameworks/fraiseql/src/main.py

# 2. Rebuild and restart
docker-compose up -d --build fraiseql

# 3. Run smoke test
./smoke-test.sh

# 4. If healthy, run full tests
./test-all-frameworks.sh --framework=fraiseql
```

### Pre-commit Testing

```bash
# Run all tests before committing
./test-all-frameworks.sh

# If all pass, commit
git add .
git commit -m "feat: add new feature"
```

---

## Future Enhancements

- [ ] Load testing with concurrent requests
- [ ] Database state validation
- [ ] Performance regression detection
- [ ] GraphQL schema validation
- [ ] REST API contract testing (OpenAPI)
- [ ] Authentication/authorization testing
- [ ] Error scenario testing (invalid inputs, missing data)
- [ ] Integration with JMeter for stress testing
