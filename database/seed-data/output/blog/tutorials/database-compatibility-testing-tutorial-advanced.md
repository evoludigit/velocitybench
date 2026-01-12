```markdown
# **Database Compatibility Testing: Ensuring Your APIs Work Everywhere**

You’ve just spent months building a high-performance API. You’ve tested it locally, locally with Docker, and in your staging environment. Everything runs smoothly. But then—disaster. Production deploys, and suddenly your API behaves unpredictably because your database schema doesn’t match the region-specific cloud provider’s quirks. Or worse, you discover a critical bug that exists only when your app runs against an older database version.

**Database compatibility testing** is the often-overlooked layer that bridges the gap between feature development and real-world deployment. It ensures your schema, queries, and application logic work seamlessly across different database flavors, versions, and edge cases. But how do we implement this effectively without slowing down development?

In this post, we’ll explore the **Database Compatibility Testing pattern**, covering:
- Why compatibility testing is critical in modern distributed systems
- Real-world pain points and their tradeoffs
- A hands-on approach to testing PostgreSQL vs. MySQL vs. Snowflake
- Practical code examples with tools like **Docker**, **SQL schema diffs**, and **unit testing**
- Common pitfalls and how to avoid them

---

## **The Problem: Why Database Compatibility Testing Matters**

Imagine this scenario: Your backend team ships a new feature that queries a union of two tables. Locally, everything works fine because you’re using PostgreSQL. Your staging environment also uses PostgreSQL, but in production, your cloud provider has migrated to Aurora MySQL. Suddenly, your query fails because MySQL doesn’t handle `UNION ALL` the same way. Or perhaps you’re using dynamically generated SQL (via ORMs like Prisma or Django ORM), and a `LIMIT` statement in your query breaks in Snowflake because it only supports `FETCH FIRST`.

These are classic signs of **database compatibility issues**, which can manifest in:
- **Schema differences**: Column defaults, collations, or data types vary (e.g., `TINYINT` in MySQL vs. `SMALLINT` in PostgreSQL).
- **Query parsing discrepancies**: Syntax for window functions, `LEFT JOIN` semantics, or abstracted functions like `DATEADD` vary across databases.
- **Performance regressions**: Index usage, optimizer behavior, or parallel query execution differs.
- **Transaction isolation bugs**: PostgreSQL’s `READ COMMITTED` vs. MySQL’s default `REPEATABLE READ` can lead to phantom reads in unexpected ways.
- **Vendor-specific extensions**: Some databases support extensions (e.g., PostgreSQL’s `jsonb`, Snowflake’s snowflake functions) that aren’t available elsewhere.

Without proactive testing, these issues often surface **post-deployment**, when they’re exponentially harder and more expensive to fix. In a microservices architecture, where databases can be multi-region or polyglot, the problem compounds.

---

## **The Solution: Database Compatibility Testing Patterns**

The goal of database compatibility testing is to **catch inconsistencies early** and ensure your application behaves predictably across environments. Here’s how we’ll approach it:

1. **Schema validation**: Ensure your database schema is portable and aligns with your target databases.
2. **Query testing**: Verify SQL and ORM-generated queries work across databases.
3. **Data consistency checks**: Test edge cases like data truncation, collation, and timezone handling.
4. **Performance testing**: Compare SQL performance across databases.
5. **Automated pipelines**: Integrate compatibility checks into CI/CD.

We’ll focus on a **hybrid approach**: static checks (schema diffs, linting) and dynamic testing (executing queries in test databases).

---

## **Components of the Solution**

### 1. **Infrastructure: Test Databases in CI/CD**
To test compatibility, you need **isolated, reproducible environments**. We’ll use `docker-compose` to spin up test databases in CI (e.g., GitHub Actions, GitLab CI).

#### Example: `docker-compose.yml` for Multi-DB Testing
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: test
      POSTGRES_DB: test_db
    ports:
      - "5432:5432"

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: test
      MYSQL_DATABASE: test_db
    ports:
      - "3306:3306"

  snowflake:
    image: snowflake/snowflake-cli:latest
    volumes:
      - ./snowflake-config:/etc/snowflake
    environment:
      ACCOUNT: xxxx.us-east-1
      USER: test_user
      PASSWORD: test_pass
```

> **Note**: Snowflake requires an external connection; we use a pre-configured CLI image for simplicity. Replace `xxxx` with a real account.

### 2. **Schema Validation: Detect Incompatible Definitions**
Use tools like:
- **SQLFluff** (linting SQL files)
- **SchemaCrawler** (schema diffing)
- **Prisma’s Schema Validation** (if using Prisma ORM)

#### Example: SQLFluff to Catch Syntax Errors
```bash
# Install SQLFluff
pip install sqlfluff

# Lint a SQL file for PostgreSQL
sqlfluff lint --dialect postgresql app/migrations/v1_init.sql
```

If you’re using an ORM like Prisma, its `schema.prisma` file should be written with **database-agnostic abstractions** (e.g., `Int` instead of `INTEGER`). Prisma handles the backend-specific conversions.

#### Example: Prisma Schema (Cross-DB Friendly)
```prisma
model User {
  id     Int       @id @default(autoincrement())
  email  String    @unique
  name   String?
  createdAt DateTime @default(now())
}
```
Prisma generates SQL that works in PostgreSQL, MySQL, and SQLite.

### 3. **Dynamic Query Testing: Execute SQL Across Databases**
Use **pytest + SQLAlchemy** (with connection pooling) to run queries against multiple databases in parallel.

#### Example: `conftest.py` for Test Fixtures
```python
import pytest
from sqlalchemy import create_engine
import os

@pytest.fixture(scope="session")
def postgres_engine():
    return create_engine(f"postgresql://postgres:test@localhost:5432/test_db")

@pytest.fixture(scope="session")
def mysql_engine():
    return create_engine(f"mysql://root:test@localhost:3306/test_db")
```

#### Example: Test File for Query Compatibility
```python
import pytest
from sqlalchemy import text

def test_union_all_compatibility(postgres_engine, mysql_engine):
    # Test UNION ALL in both databases
    query = text("""
        SELECT 'postgres' as db
        UNION ALL
        SELECT 'mysql' as db
        LIMIT 2
    """)

    # Execute in PostgreSQL
    result = postgres_engine.execute(query).fetchall()
    assert len(result) == 2
    assert all(row["db"] in ["postgres", "mysql"] for row in result)

    # Execute in MySQL
    result = mysql_engine.execute(query).fetchall()
    assert len(result) == 2
    assert all(row["db"] in ["postgres", "mysql"] for row in result)

# Note: This will fail in MySQL because 'now()' is different.
def test_datetime_function_compatibility(postgres_engine, mysql_engine):
    query = text("SELECT CURRENT_TIMESTAMP as timestamp")
    # Replace CURRENT_TIMESTAMP with DB-specific functions if needed
    # or abstract them via ORM.
```

> **Tradeoff**: Writing queries that work everywhere is tedious. Tools like **DuckDB** (a portable SQL engine) can help abstract differences, but they may not catch all edge cases.

### 4. **ORM-Specific Testing**
If using an ORM (e.g., Django, Prisma, SQLAlchemy), test ORM-generated queries explicitly.

#### Example: Django Model Test with Different Backends
```python
from django.test import TestCase, override_settings
from django.db import connections

class QueryCompatibilityTest(TestCase):
    @override_settings(DATABASES={
        'default': {'ENGINE': 'django.db.backends.postgresql'}
    })
    def test_postgres_query(self):
        pass

    @override_settings(DATABASES={
        'default': {'ENGINE': 'django.db.backends.mysql'}
    })
    def test_mysql_query(self):
        pass
```

### 5. **Automated Schema Migration Testing**
Use tools like **Flyway** or **Alembic** to test migrations across databases.

#### Example: Flyway Migration Test
```bash
# Run a migration in both PostgreSQL and MySQL
docker-compose run mysql flyway migrate
docker-compose run postgres flyway migrate
```

---

## **Implementation Guide: Step-by-Step**

### Step 1: Define Test Databases in CI
Add a `./scripts/start-test-dbs.sh` script to spin up databases:

```bash
#!/bin/bash
docker-compose -f docker-compose.yml up -d postgres mysql
```

Then, run it in CI using GitHub Actions:
```yaml
jobs:
  test:
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/start-test-dbs.sh
      - run: pytest tests/query_compatibility/
```

### Step 2: Lint SQL with SQLFluff
Add a pre-commit hook to catch syntax errors early:
```bash
# .git/hooks/pre-commit
#!/bin/sh
sqlfluff lint app/migrations/*.sql
```

### Step 3: Test ORM Queries
For Prisma, add a test suite using its `generate` command:
```bash
# Install Prisma CLI
npm install -g prisma

# Generate types and run tests
npx prisma generate
pytest tests/prisma_compatibility/
```

### Step 4: Catch Data Type Mismatches
Write tests that check columns of expected types:
```python
def test_enum_compatibility(postgres_engine, mysql_engine):
    with postgres_engine.connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (status ENUM('active', 'inactive'))")
    with mysql_engine.connect() as conn:
        # MySQL uses VARCHAR instead of ENUM; test fallback
        conn.execute("CREATE TABLE IF NOT EXISTS users (status VARCHAR(20))")
```

### Step 5: Integrate with CI/CD
Add a final stage in CI that runs compatibility tests after code reviews:
```yaml
  compatibility:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/run_compatibility_tests.sh
```

---

## **Common Mistakes to Avoid**

1. **Ignoring Vendor-Specific Extensions**
   - Avoid relying on PostgreSQL’s `jsonb` or Snowflake’s `SNOWFLAKE_TEXT_SEARCH` without fallbacks.
   - **Solution**: Use abstracted types (e.g., `String` in Prisma) or provide `IF NOT EXISTS` logic.

2. **Assuming ORMs Handle Everything**
   - ORMs like Django ORM or SQLAlchemy can abstract many differences, but they don’t catch **all** SQL quirks.
   - **Solution**: Test ORM-generated queries directly with raw SQL.

3. **Not Testing Performance Differences**
   - A query that works in PostgreSQL might be slow in MySQL due to missing indexes.
   - **Solution**: Use `EXPLAIN` in each database and benchmark.

4. **Schema Drift Without Checks**
   - If your team writes schemas manually, schema drift becomes inevitable.
   - **Solution**: Use tools like **SchemaCrawler** to detect discrepancies before migration.

5. **Overlooking Edge Cases**
   - Non-ASCII characters, timezone handling, and auto-increment behavior can differ.
   - **Solution**: Write tests for these explicitly.

---

## **Key Takeaways**

✅ **Test early and often**: Catch compatibility issues in CI, not production.
✅ **Use abstractions**: Prefer `Int`, `String`, and `DateTime` in ORMs to avoid dialect-specific types.
✅ **Test both static and dynamic**: Use linting + query execution tests.
✅ **Isolate databases**: Use Docker or cloud VMs for test environments.
✅ **Benchmark SQL**: Compare performance across databases.
✅ **Automate**: Integrate compatibility checks into your CI/CD pipeline.
✅ **Document assumptions**: Note known quirks (e.g., "MySQL doesn’t support `CURRENT_TIMESTAMP` in FROM clauses").

---

## **Conclusion: Future-Proof Your Database Layers**

Database compatibility testing isn’t about perfection—it’s about **reducing risk**. In a world where databases are polyglot and cloud providers introduce subtle changes, proactive testing is your best defense.

Your API will never be "100% compatible" with every database, but by:
1. Writing database-agnostic schemas and queries,
2. Testing across multiple engines early,
3. Documenting exceptions,
you’ll minimize surprises and ship with confidence.

### Next Steps
1. Set up a minimal compatibility suite (Docker + SQLAlchemy + pytest).
2. Start with a single database mismatch (e.g., `LIMIT` vs. `OFFSET` in Snowflake).
3. Expand gradually to cover your entire codebase.

Would you like a deeper dive into any specific part of this workflow? Let me know—I’m happy to explore tools like **DuckDB for cross-DB testing** or **custom ORM wrappers** next!

---
```

This blog post provides a comprehensive, actionable guide to database compatibility testing, balancing practicality with honest tradeoffs. The code examples are realistic and directly applicable to real-world backend development.