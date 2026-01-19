# **[Pattern] Testing Setup – Reference Guide**

---

## **Overview**
The **Testing Setup** pattern ensures predictable and reusable test environments by centralizing dependencies, state management, and initialization logic. It abstracts common setup tasks (e.g., database seeding, mock services, or test data generation) into modular, configurable components, reducing boilerplate and improving test maintainability. This pattern is critical for **unit, integration, and end-to-end tests**, especially in microservices, scalable applications, or CI/CD pipelines where consistency is paramount.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| Component          | Purpose                                                                 | Example Use Cases                                  |
|--------------------|-------------------------------------------------------------------------|----------------------------------------------------|
| **Test Fixtures**  | Predefined test data, configurations, or mocks shared across tests.    | Database tables, API endpoints, user roles.         |
| **Setup Hooks**    | Initialization logic (e.g., `beforeAll`, `beforeEach`) executed in a fixed order. | Authentication state, environment variables.       |
| **Test Containers** | Lightweight, isolated environments (e.g., Dockerized databases).        | Testing database migrations, service dependencies. |
| **Dependency Injection** | Isolated, mockable services for unit tests; real services for integration tests. | HTTP clients, databases, external APIs.            |
| **State Management** | Strategies to reset or control test state (e.g., transaction rollbacks). | Cleaning up after tests, avoiding test pollution. |

### **2. When to Use**
- **Unit Tests**: Mock external dependencies (e.g., `jest.mock()` for Node.js).
- **Integration Tests**: Spin up real services (e.g., Testcontainers for PostgreSQL).
- **End-to-End Tests**: Simulate user flows with pre-configured environments.
- **CI/CD Pipelines**: Ensure tests run in a consistent, reproducible state.

### **3. Anti-Patterns to Avoid**
- **Hardcoded Dependencies**: Avoid inline database calls or file system writes in tests.
- **Global State Pollution**: Reset test state after each test to prevent interference.
- **Overly Complex Setups**: Balance realism and simplicity; mock when possible, containerize when necessary.

---

## **Schema Reference**

### **1. Test Fixture Schema**
| Field               | Type          | Description                                                                 | Example Value                     |
|---------------------|---------------|-----------------------------------------------------------------------------|-----------------------------------|
| `name`              | String        | Unique identifier for the fixture.                                           | `"user_fixtures"`                 |
| `data`              | Object/Array  | Predefined test data (e.g., JSON, YAML).                                    | `{ "users": [...] }`               |
| `dependencies`      | Array         | Required fixtures or services.                                              | `[{"fixture": "database"}]`       |
| `scope`             | Enum          | Lifetime of the fixture (`singleton`, `per-suite`, `per-test`).             | `"per-test"`                      |
| `validationRules`   | Object        | Rules to validate fixture data before use.                                  | `{ "users.required": true }`      |

**Example Fixture (`user_fixtures.json`):**
```json
{
  "users": [
    { "id": "1", "name": "Alice", "role": "admin" },
    { "id": "2", "name": "Bob", "role": "user" }
  ]
}
```

---

### **2. Setup Hook Schema**
| Field               | Type          | Description                                                                 | Example Value                     |
|---------------------|---------------|-----------------------------------------------------------------------------|-----------------------------------|
| `type`              | Enum          | Hook type (`beforeAll`, `beforeEach`, `afterEach`, `afterAll`).           | `"beforeAll"`                     |
| `order`             | Integer       | Execution priority (lower numbers run first).                             | `1`                               |
| `implementation`    | Function      | Code block to execute.                                                      | `async (context) => { ... }`      |
| `requires`          | Array         | Dependencies (e.g., fixtures, services).                                  | `[{ "fixture": "user_fixtures" }]`|

**Example Hook (JavaScript):**
```javascript
{
  "type": "beforeEach",
  "order": 2,
  "implementation": async (context) => {
    await context.db.seed("users", context.fixtures.user_fixtures.users);
  }
}
```

---

### **3. Test Container Schema**
| Field               | Type          | Description                                                                 | Example Value                     |
|---------------------|---------------|-----------------------------------------------------------------------------|-----------------------------------|
| `image`             | String        | Docker image name (e.g., `postgres:14`).                                    | `"mongo:6"`                       |
| `ports`             | Object        | Mapped ports (`host:container`).                                            | `{ "27017": 27018 }`              |
| `environment`       | Object        | Environment variables (e.g., `MONGODB_USER`).                              | `{ "ROOT_PASSWORD": "test" }`     |
| `volumeMounts`      | Array         | Persistent storage paths.                                                    | `[{ "host": "/data", "container": "/data/db" }]` |
| `cleanup`           | Boolean       | Whether to delete the container after tests.                                 | `true`                            |

**Example Container Definition:**
```yaml
image: redis:7
ports:
  6379:6379
environment:
  REDIS_PASSWORD: test123
```

---

## **Query Examples**

### **1. Loading a Fixture in a Test**
**Language**: Python (using `pytest` + `pytest-fixtures`)
```python
import pytest
from my_app.fixtures import user_fixtures

@pytest.fixture
def db_connection():
    return DatabaseConnection(user_fixtures["users"])

def test_user_creation(db_connection):
    user = db_connection.create_user("Charlie", "editor")
    assert user.role == "editor"
```

**Language**: JavaScript (using Jest)
```javascript
describe("User tests", () => {
  beforeEach(async () => {
    await loadFixture("user_fixtures");
  });

  test("user roles are enforced", async () => {
    const user = await getUser("Alice");
    expect(user.role).toBe("admin");
  });
});
```

---

### **2. Managing Test Containers**
**Tool**: [Testcontainers](https://www.testcontainers.org/) (Java)
```java
@Testcontainers
public class DatabaseTest {
    @Container
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:13");

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
    }

    @Test
    void test_migration() {
        // Runs against the containerized database
        assertDoesNotThrow(() -> new MigrationExecutor().execute());
    }
}
```

**Tool**: [Docker Compose](https://docs.docker.com/compose/)
```yaml
# docker-compose.yml
version: "3"
services:
  app:
    build: .
    depends_on:
      - redis
      - postgres
  redis:
    image: redis:7
  postgres:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: test
```

Run tests with:
```bash
docker-compose -f tests/docker-compose.yml up --abort-on-container-exit
```

---

### **3. Resetting Test State**
**Database (Transaction Rollback)**
```python
# SQLAlchemy (Python)
def test_with_rollback(session):
    session.begin_nested()  # Start a transaction
    session.add(User(name="Test User"))
    session.flush()
    assert session.query(User).count() == 1
    session.rollback()  # Reverts changes
```

**File System**
```javascript
// Node.js
const fs = require("fs");
const path = require("path");

async function test_file_operations() {
  const tempFile = path.join(__dirname, "test.txt");
  fs.writeFileSync(tempFile, "Hello");
  // Test logic here...
  fs.unlinkSync(tempFile);  // Cleanup
}
```

---

## **Related Patterns**

| Pattern Name               | Purpose                                                                 | When to Pair With Testing Setup |
|----------------------------|-------------------------------------------------------------------------|----------------------------------|
| **[Mocking](mocking-pattern.md)**       | Isolate units by replacing dependencies with simulators.               | Use mocks for unit tests in `Testing Setup`. |
| **[Factories](factory-pattern.md)**     | Programmatically generate test data.                                    | Generate dynamic fixtures.        |
| **[Isolation](isolation-pattern.md)**    | Prevent test interference (e.g., separate processes).                  | Critical for stateful tests.       |
| **[Parameterized Tests](parameterized-tests.md)** | Run the same test with different inputs.                              | Combine with `Testing Setup` for data-driven tests. |
| **[Teardown](teardown-pattern.md)**      | Clean up resources after tests.                                      | Pair with `beforeEach`/`afterEach` hooks. |

---

## **Best Practices**
1. **Modularize Fixtures**: Group related data (e.g., `users.json`, `products.json`).
2. **Version Control**: Track fixture versions if data changes over time.
3. **Performance**: Pre-load fixtures in `beforeAll` instead of `beforeEach`.
4. **Document Dependencies**: Clearly define fixture/service requirements.
5. **Parallelization**: Ensure setup hooks are thread-safe for parallel test suites.

---
**Example Workflow**:
1. Define fixtures (`users.json`, `products.json`).
2. Write setup hooks (`beforeAll` to seed DB, `beforeEach` to reset state).
3. Run tests with isolated containers (PostgreSQL, Redis).
4. Teardown hooks clean up resources.