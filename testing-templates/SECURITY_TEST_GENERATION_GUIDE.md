# Phase 1: Security Test Suite Generation Guide
## Automated Generation for All 38 Frameworks

### Overview
This document provides the master generation strategy for creating security tests across all 38 frameworks using template-based code generation.

### Master Templates Available
1. **SECURITY_TEST_TEMPLATE_PYTHON.py** - For Python frameworks (7)
2. **SECURITY_TEST_TEMPLATE_TYPESCRIPT.ts** - For Node.js frameworks (8)
3. **SECURITY_TEST_TEMPLATE_GO.go** - For Go frameworks (4)
4. **SECURITY_TEST_TEMPLATE_RUST.rs** - For Rust frameworks (3)
5. **SECURITY_TEST_TEMPLATE_JAVA.java** - For Java frameworks (7)
6. **SECURITY_TEST_TEMPLATE_RUBY.rb** - For Ruby frameworks (3)
7. **SECURITY_TEST_TEMPLATE_PHP.php** - For PHP frameworks (2)
8. **SECURITY_TEST_TEMPLATE_SCALA.scala** - For Scala frameworks (1)

### Test Files to Generate Per Framework
Each framework needs 2-3 security test files:

```
frameworks/{framework}/tests/
├── test_security_injection.{ext}       # SQL injection prevention
├── test_security_auth.{ext}            # Authentication validation
└── test_security_rate_limit.{ext}      # Rate limiting tests
```

### Generation Process

#### Step 1: Identify Framework Metadata
```python
{
  "framework": "fastapi-rest",
  "language": "Python",
  "template": "SECURITY_TEST_TEMPLATE_PYTHON.py",
  "test_dir": "frameworks/fastapi-rest/tests",
  "factory_class": "TestFactory",
  "exception_types": {
    "auth": "AuthenticationError",
    "notfound": "NotFoundError",
    "ratelimit": "RateLimitError"
  },
  "factory_methods": {
    "create_user": "create_user(username, email, full_name, bio)",
    "get_user_by_username": "get_user_by_username(username)",
    "get_auth_token": "get_auth_token(user_id)",
    "query_users": "query_users(auth_token=None)"
  }
}
```

#### Step 2: Adapt Template to Framework
Use local AI model to:
1. Replace template placeholders with framework-specific method names
2. Adjust exception types to framework conventions
3. Add framework-specific imports
4. Handle async/await patterns correctly

Example prompt for local model:
```
Adapt the Python security test template to FastAPI framework:

1. Replace {factory.create_user(...)} with actual FastAPI test pattern
2. Replace {AuthenticationError} with FastAPI's actual exception (HTTPException?)
3. Add appropriate imports for FastAPI testing
4. Ensure tests work with FastAPI's test client

Template: [full template]

FastAPI reference test: [example from fastapi-rest/tests/]

Output: Complete adapted test file ready to use
```

#### Step 3: Add Framework-Specific Assertions
Some frameworks need custom assertions for:
- Response status codes (200, 401, 403, 429)
- Error response format
- Rate limit headers (X-RateLimit-*)
- Auth token format

#### Step 4: Integrate with Existing Tests
- Use existing `conftest.py` factory
- Follow existing test organization
- Maintain naming conventions
- Use existing database setup

### Language-Specific Notes

#### Python Frameworks (7 total)
- fastapi-rest, flask-rest, strawberry, graphene, fraiseql, ariadne, asgi-graphql
- Use existing `conftest.py` fixtures
- Tests can be sync or async (use `@pytest.mark.asyncio` for async)
- Exception: `HTTPException`, `ValidationError`, `ValueError`
- Rate limit: Check for X-RateLimit-* headers or custom exceptions

#### Node.js Frameworks (8 total)
- express-rest, apollo-server, fastify-graphql, graphql-yoga, apollo-orm, express-orm, express-graphql, mercurius
- Use vitest testing framework
- Tests are async/await based
- Exception: `Error`, `HttpError`, status codes
- Rate limit: Check response status 429
- Use supertest or framework's test client

#### Go Frameworks (4 total)
- gin-rest, go-gqlgen, go-graphql-go, graphql-go
- Use `testing.T`
- Tests use `*http.Response` and status codes
- Exception: Check error != nil
- Rate limit: Check response status 429
- Use framework's test helpers

#### Rust Frameworks (3 total)
- actix-web-rest, async-graphql, juniper
- Use cargo test framework
- Tests are async with #[tokio::test]
- Exception: Custom error types
- Rate limit: Check response status 429

#### Java Frameworks (7 total)
- java-spring-boot, spring-boot-orm, spring-graphql, etc.
- Use JUnit 5 (@Test)
- Tests can use TestRestTemplate or GraphQL client
- Exception: HttpClientErrorException, custom exceptions
- Rate limit: Check HTTP 429 status

#### Ruby Frameworks (3 total)
- hanami, rails, ruby-rails
- Use RSpec (Rack::Test for HTTP)
- Tests are RSpec blocks
- Exception: StandardError, custom errors
- Rate limit: Check response status 429

#### PHP Frameworks (2 total)
- php-laravel, webonyx-graphql-php
- Use PHPUnit
- Tests extend TestCase
- Exception: Exception, custom exceptions
- Rate limit: Check HTTP 429 status

#### Scala (1 total)
- play-graphql
- Use ScalaTest
- Tests can be sync or async
- Exception: Scala exceptions
- Rate limit: Check HTTP 429 status

### Prompting Strategy for Local Models

**Good prompt (specific and actionable):**
```
Adapt this Python security test template to FastAPI:

Input template: [full test file]
Reference FastAPI test: [example from existing tests]

Required changes:
1. Replace mock factory calls with real FastAPI test client patterns
2. Replace pytest exceptions with FastAPI HTTPException patterns
3. Add framework-specific imports at top
4. Ensure all tests follow FastAPI test conventions

Output: Complete test file ready to copy to frameworks/fastapi-rest/tests/
```

**Bad prompt (vague, won't work well):**
```
Make security tests for FastAPI
```

### Quality Checklist Per Framework

- [ ] All 3 test files created (injection, auth, rate limit)
- [ ] Tests import correct framework libraries
- [ ] Tests use framework's existing test factory/conftest
- [ ] All test assertions match framework conventions
- [ ] Exception types match framework's actual exceptions
- [ ] Auth token handling works with framework's auth
- [ ] Rate limit tests check correct response codes/headers
- [ ] Tests can be discovered by framework's test runner
- [ ] Tests pass without errors (or document expected failures)

### Generation Timeline

**With Local AI Models** (estimate 20-30 hours):
- Framework analysis & metadata: 2 hours
- Template adaptation per language: 12 hours (local model: 6 hours)
- Integration & testing: 10 hours (local model: 5 hours)
- Review & fixes: 6 hours

### Expected Output

✅ 114 total test files (38 frameworks × 3 files)
✅ ~35-40 test assertions per file
✅ 100% framework coverage for:
  - SQL injection prevention
  - Authentication validation
  - Rate limiting enforcement
  - Input sanitization
✅ Tests follow framework conventions
✅ Tests pass with existing infrastructure

### Next Steps After Phase 1

1. Run all security tests: `make test-security` or equivalent
2. Verify all tests pass across all frameworks
3. Commit with message: "test(security): Add comprehensive security test suite"
4. Move to Phase 2: Performance Benchmarks

---

## Framework-Specific Implementation Notes

### FastAPI-REST (Python)
- Factory already exists in conftest.py
- Use async tests with @pytest.mark.asyncio
- HTTPException for auth errors
- 429 status code for rate limiting

### Flask-REST (Python)
- Use test_client() from Flask app
- Tests are sync, not async
- ValueError or custom exceptions
- Check response status codes

### Apollo-Server (Node)
- Use apollo test client or supertest
- All tests are async/await
- ApolloError or HttpError
- Check response status codes

### Express-REST (Node)
- Use supertest for HTTP testing
- All tests are async/await
- Express throws Error objects
- Check response status codes

### Gin-REST (Go)
- Use httptest package
- Check response status codes
- Errors use error interface
- Parse JSON responses

### java-spring-boot (Java)
- Use TestRestTemplate
- @Test methods
- HttpClientErrorException
- Check HTTP status codes

### Hanami (Ruby)
- Use Rack::Test helpers
- RSpec block style
- Check response status codes
- Errors raise standard Ruby exceptions

---

## Success Definition

✅ **Security tests are complete when:**
1. All 38 frameworks have test files
2. All tests follow language conventions
3. Tests cover all security categories
4. Tests pass or failures are documented
5. Tests are integrated into CI/CD pipeline
