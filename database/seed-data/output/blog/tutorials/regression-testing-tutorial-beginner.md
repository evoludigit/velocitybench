```markdown
---
title: "Regression Testing for Backend Engineers: How to Keep Old Code Working"
date: 2024-02-15
author: Jane Doe
description: "A beginner-friendly guide to implementing regression testing in backend development. Learn why it matters, how to structure tests, and real-world examples to get started."
tags: ["backend", "testing", "regression testing", "api design", "software reliability"]
---

---

# **Regression Testing for Backend Engineers: How to Keep Old Code Working**

As backend engineers, we write APIs, databases, and services that power critical applications. Over time, these systems grow—new features are added, bugs are fixed, and dependencies evolve. But here’s the catch: **every change has the potential to break something that already worked**.

This is where **regression testing** comes in. Think of it as a safety net for your codebase—a way to catch unintended side effects when you make changes. Without regression tests, you’re playing a high-stakes game of "will it break?" every time you deploy.

In this guide, we’ll cover:
- Why regression testing is essential (and what happens when you skip it).
- How to structure regression tests for APIs and databases.
- Practical examples in Python, SQL, and REST APIs.
- Common pitfalls and how to avoid them.

Let’s dive in.

---

## **The Problem: Why Regression Testing Matters**

Imagine this scenario:
1. You deploy a new feature that adds pagination to your `GET /products` endpoint.
2. Everything works as expected—until a user reports that their old "favorites" list no longer displays correctly.
3. After debugging, you realize the pagination logic accidentally filters out products marked as favorites.

This isn’t hypothetical. It happens. **The longer your codebase grows, the harder it is to remember every edge case you’ve fixed in the past.** Regression testing helps prevent this by ensuring that new changes don’t break existing functionality.

### **Real-World Consequences of Skipping Regression Testing**
- **Broken production features**: Users encounter errors or unexpected behavior.
- **Technical debt accumulation**: Fixing regressions later becomes more time-consuming.
- **Loss of confidence**: Your team starts avoiding deployments because you’re afraid of breaking things.

Regression testing isn’t just about catching bugs—it’s about **building a robust foundation** for future changes.

---

## **The Solution: Structuring Regression Tests**

Regression tests fall into two broad categories:
1. **Unit tests**: Test small, isolated components (e.g., a single function or service method).
2. **Integration/API tests**: Test interactions between components or the entire system (e.g., API endpoints, database queries).

For this guide, we’ll focus on **API regression testing**, as it’s a common pain point for backend engineers. Our goal is to ensure that:
- Existing API endpoints return the same data format.
- New logic doesn’t break old behavior.
- Edge cases (e.g., invalid inputs) still work as intended.

---

## **Components of a Regression Testing Strategy**

To implement regression testing effectively, you need:
1. **Test cases**: A set of scenarios that cover critical functionality.
2. **Test automation**: Tools to run tests repeatedly (e.g., `pytest`, `Jest`, or `Postman`).
3. **Test data**: Realistic inputs and expected outputs.
4. **Test environments**: Staging or CI/CD pipelines to run tests before production.

Let’s explore how to build this step by step.

---

## **Code Examples: Practical Regression Testing in Action**

### **1. Testing a Simple REST API with Python and FastAPI**
Suppose we have a `/products` endpoint that returns a list of products. We want to ensure that:
- The endpoint returns the correct JSON schema.
- New pagination logic doesn’t break old queries.
- Error responses are consistent.

#### **Example API (FastAPI)**
```python
from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional

app = FastAPI()

# Mock database
products = [
    {"id": 1, "name": "Laptop", "price": 999.99, "is_favorite": True},
    {"id": 2, "name": "Phone", "price": 699.99, "is_favorite": False},
]

@app.get("/products", response_model=List[dict])
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100)
):
    start = (page - 1) * limit
    end = start + limit
    return products[start:end]
```

#### **Regression Test with `pytest`**
We’ll write tests to verify:
1. The endpoint returns the correct data structure.
2. Pagination works as expected.
3. Invalid inputs (e.g., `page < 1`) return an error.

```python
# test_products.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_products_returns_expected_schema():
    response = client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2  # Default pagination

def test_pagination_works():
    # Page 1 (default)
    response = client.get("/products?page=1")
    assert len(response.json()) == 2

    # Page 2 (should return empty list)
    response = client.get("/products?page=2")
    assert len(response.json()) == 0

def test_invalid_page_returns_error():
    response = client.get("/products?page=0")
    assert response.status_code == 422  # QueryParamValidationError
```

#### **Key Takeaways from This Example**
- Use `pytest` to write concise, readable tests.
- Test **happy paths** (normal use cases) and **error cases** (invalid inputs).
- Validate **data structure** (e.g., JSON schema) and **length** (e.g., pagination results).

---

### **2. Testing Database Queries for Regression**
Databases are another hotspot for regressions. A small change in a `SELECT` query or `JOIN` can break reports, dashboards, or user-facing data.

#### **Example: SQL Query Regression Test**
Suppose we have a `users` table and a query to fetch `active_users`:

```sql
-- users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    is_active BOOLEAN
);

-- Insert test data
INSERT INTO users (name, email, is_active) VALUES
('Alice', 'alice@example.com', TRUE),
('Bob', 'bob@example.com', FALSE),
('Charlie', 'charlie@example.com', TRUE);
```

#### **Regression Test: Ensure `active_users` Query Works**
We want to verify that the query:
1. Only returns `is_active = TRUE`.
2. Doesn’t return `NULL` or invalid rows.

```sql
-- Test query (should return Alice and Charlie)
SELECT name FROM users WHERE is_active = TRUE;
```

#### **Automating SQL Regression Tests**
To automate this, you can use a tool like **`pytest` with `SQLAlchemy`** or **PostgreSQL’s `pgTAP`**. Here’s a Python example:

```python
# test_active_users.py
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Setup test database
engine = create_engine("postgresql://user:pass@localhost/test_db")
Session = sessionmaker(bind=engine)
session = Session()

def test_active_users_query():
    # Query active users
    result = session.execute(select([users.name]).where(users.is_active == True))
    active_users = result.scalars().all()

    # Expected: ['Alice', 'Charlie']
    assert active_users == ['Alice', 'Charlie']

    # Test edge case: No active users
    session.execute("UPDATE users SET is_active = FALSE WHERE id = 1")
    result = session.execute(select([users.name]).where(users.is_active == True))
    assert result.scalars().all() == ['Charlie']
```

---

### **3. Testing API Contracts with OpenAPI/Swagger**
APIs evolve over time, and breaking changes can disrupt clients. To prevent this, you can:
1. Document your API with **OpenAPI/Swagger**.
2. Use tools like **`pytest-openapi`** or **`Spectral`** to validate schemas.

#### **Example: OpenAPI Schema Validation**
Our `/products` endpoint should have a stable schema. Let’s define it in `openapi.yaml`:

```yaml
openapi: 3.0.0
paths:
  /products:
    get:
      responses:
        '200':
          description: A list of products
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                    name:
                      type: string
                    price:
                      type: number
                    is_favorite:
                      type: boolean
```

#### **Test the Schema with `pytest-openapi`**
Install the package:
```bash
pip install pytest-openapi
```

Then write a test:
```python
# test_openapi_schema.py
import pytest
from pytest_openapi import ApiTester

def test_products_schema(api: ApiTester):
    response = api.get("/products")
    assert response.status_code == 200
    assert api.validate_response(response.json(), "/products", "get")
```

---

## **Implementation Guide: How to Start**

### **Step 1: Identify Critical Paths**
Not all functionality needs regression tests. Focus on:
- **User-facing features** (e.g., checkout, search).
- **High-traffic endpoints** (e.g., `/products`, `/users`).
- **Billing or payment flows**.

### **Step 2: Write Tests for New Features**
Every time you add a new feature, write:
1. **Unit tests** for core logic.
2. **API/integration tests** for endpoints.
3. **Edge case tests** (e.g., empty inputs, invalid data).

### **Step 3: Automate with CI/CD**
Integrate tests into your deployment pipeline (e.g., GitHub Actions, GitLab CI). Example:

```yaml
# .github/workflows/test.yml
name: Run Regression Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
```

### **Step 4: Maintain Test Data**
Use **test databases** (e.g., SQLite, Dockerized PostgreSQL) to avoid polluting production data. Example Docker setup:

```dockerfile
# docker-compose.yml
version: "3.8"
services:
  test-db:
    image: postgres:13
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5432:5432"
```

### **Step 5: Schedule Periodic Regression Suites**
Run a **full regression suite** every few weeks to catch slow-burning issues. Tools like **`locust`** (for load testing) or **`selenium`** (for UI regression) can help.

---

## **Common Mistakes to Avoid**

### **1. Ignoring Edge Cases**
- ❌ Only testing "happy path" examples.
- ✅ Testing invalid inputs, empty results, and error scenarios.

### **2. Overwriting Tests Without Context**
- ❌ Deleting tests when refactoring without documenting why.
- ✅ Add comments or tickets explaining test removals.

### **3. Not Updating Tests After Changes**
- ❌ Keeping tests that validate old behavior after you’ve changed the code.
- ✅ Update tests to reflect current functionality.

### **4. Running Tests Too Infrequently**
- ❌ Only running tests manually before releases.
- ✅ Automate tests in CI/CD and run them on every push.

### **5. Skipping Database Regression Tests**
- ❌ Assuming SQL queries are "obviously correct."
- ✅ Automate SQL query validation with tools like `pgTAP` or custom scripts.

---

## **Key Takeaways**
Here’s what you should remember:

✅ **Regression testing is proactive, not reactive.**
   - Catch bugs early before they reach production.

✅ **Focus on critical paths.**
   - Not every feature needs heavy testing, but high-value flows do.

✅ **Automate everything.**
   - Manual testing is error-prone and slow.

✅ **Test data structures, not just logic.**
   - Validate JSON schemas, database schemas, and response formats.

✅ **Keep tests in sync with your code.**
   - Update tests when you refactor or change behavior.

✅ **Use the right tools.**
   - `pytest` for Python, `Postman` for APIs, `pgTAP` for SQL.

---

## **Conclusion: Build Confidence with Regression Testing**

Regression testing isn’t about perfection—it’s about **reducing risk**. Every change you make, no matter how small, has the potential to introduce bugs. By writing and maintaining regression tests, you’re not just catching issues; you’re **giving yourself and your team peace of mind**.

### **Next Steps**
1. **Start small**: Pick one critical API endpoint and write regression tests for it.
2. **Automate**: Integrate tests into your CI/CD pipeline.
3. **Expand**: Add tests for database queries, edge cases, and OpenAPI schemas.
4. **Review**: Periodically run a full regression suite to catch slow-burning issues.

Regression testing is a **skill that improves with practice**. The more you test, the easier it becomes to catch issues before they reach users. Happy coding—and happy testing!

---

### **Further Reading**
- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [PostgreSQL Regression Testing with `pgTAP`](https://www.pgtap.org/)
- [OpenAPI Tools](https://www.openapis.org/tools)

---
```