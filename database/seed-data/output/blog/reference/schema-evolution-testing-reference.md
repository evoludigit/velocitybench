# **[Pattern] Schema Evolution Testing – Reference Guide**

---
## **Overview**
Schema Evolution Testing ensures that applications handle schema changes gracefully without breaking existing functionality. As databases or data formats evolve—through new fields, renamed columns, dropped attributes, or schema migrations—this pattern validates that applications can **read, write, and query** the data correctly across different schema versions. This prevents runtime errors (e.g., `NULL` column references, missing fields) and maintains data integrity during transitions.

Key use cases:
- Database schema migrations (e.g., PostgreSQL `ALTER TABLE`).
- API-backed data models (e.g., GraphQL, REST, or gRPC schemas).
- Serialization formats (e.g., JSON, Avro, Protobuf).
- Big data pipelines (e.g., Kafka, Spark).

This guide covers **testing strategies**, **tooling**, and **best practices** for validating schema evolution.

---

## **Implementation Details**

### **Core Principles**
1. **Backward Compatibility**: Newer versions must support older data structures.
2. **Forward Compatibility**: Older versions must handle new fields gracefully (e.g., ignore unknown fields).
3. **Data Migration Validation**: Test data transformations during upgrades (e.g., renaming `user_age` → `age`).
4. **Rollback Support**: Ensure schema downgrades don’t corrupt data.

### **Key Components**
| Component               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Schema Registry**     | Tracks versions (e.g., Avro, Protobuf, or database schema diffs).          |
| **Test Data Generator** | Creates synthetic data matching old/new schemas (e.g., Faker, mock APIs). |
| **Query/Write Simulator** | Validates reads/writes against schema constraints (e.g., SQL queries, API calls). |
| **Validation Layer**    | Checks data consistency (e.g., schema validators, ORM constraints).        |
| **Deployment Pipeline** | Automates schema changes with rollback tests (e.g., CI/CD hooks).         |

---

## **Schema Reference**
Use this table to document schema changes for testing. Example for a `User` table in PostgreSQL:

| Version | Change Type       | Field Name   | Old Type       | New Type       | Default Value | Notes                                  |
|---------|-------------------|--------------|----------------|----------------|---------------|----------------------------------------|
| 1.0     | Initial           | user_id      | `VARCHAR(36)`  | `VARCHAR(36)`  | Auto-generated | UUID v4                                |
|         |                   | email        | `VARCHAR(255)` | `VARCHAR(255)` | NULL          | Required in v1.1                       |
| 2.0     | Add Column        | phone        | -              | `VARCHAR(20)`  | NULL          | Optional; format: `+1 (123) 456-7890` |
| 3.0     | Rename Column     | user_age     | `INTEGER`      | `age`          | NULL          | Alias `user_age` → `age` (deprecated) |
| 3.1     | Drop Column       | legacy_tag   | `VARCHAR(50)`  | -              | -             | Removed in v4.0                       |
| 4.0     | Type Change       | registration_date | `TIMESTAMP` | `TIMESTAMPTZ` | NOW()          | Timezone-aware                         |

**Notes:**
- Use **semantic versioning** (e.g., `1.0.0` → `1.1.0`) for schema tags.
- Document **deprecated fields** (e.g., `legacy_tag`) to avoid runtime warnings.
- For APIs, include **query parameters** or **headers** that trigger schema checks.

---

## **Query Examples**

### **1. Testing Backward Compatibility (Read)**
**Scenario**: Query a table with a new column (`phone`) added in v2.0.
**Goal**: Ensure v1.0 clients can still read `user_id` and `email`.

```sql
-- Query in v1.0 (ignores unknown columns)
SELECT user_id, email FROM users WHERE user_id = '123e4567-e89b-12d3-a456-426614174000';

-- Query in v3.0 (includes new fields)
SELECT user_id, email, phone, age
FROM users
WHERE user_id = '123e4567-e89b-12d3-a456-426614174000';
```

**Test Case**:
- **Input**: User record from v1.0 schema.
- **Expected**: Query succeeds; `phone` and `age` are `NULL`.
- **Tool**: Use a **schema validator** (e.g., [SQLFluff](https://www.sqlfluff.com/)) to detect unsupported queries.

---

### **2. Testing Forward Compatibility (Write)**
**Scenario**: Insert a record with a new field (`phone`) into v4.0 schema.
**Goal**: Ensure the database handles unknown fields gracefully.

```sql
-- Insert with new field (v4.0 schema)
INSERT INTO users (user_id, email, phone, age, registration_date)
VALUES (
    '789e4567-e89b-12d3-a456-426614174001',
    'test@example.com',
    '+1 (555) 123-4567',
    30,
    NOW()
);

-- Insert with legacy field (should fail or warn)
-- INSERT INTO users (user_id, email, legacy_tag)
-- VALUES ('123e4567-e89b-12d3-a456-426614174000', 'test@example.com', 'premium');
```

**Test Case**:
- **Input**: Record with `phone` (new in v3.0).
- **Expected**: Insert succeeds; `legacy_tag` is rejected (if not nullable).
- **Tool**: Use **database constraints** (e.g., `UNIQUE`, `NOT NULL`) or **application logic** to enforce rules.

---

### **3. Testing Data Migration**
**Scenario**: Rename `user_age` → `age` in v3.0.
**Goal**: Validate the migration script preserves data.

**Migration Script (PostgreSQL)**:
```sql
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN age INTEGER;

-- Step 2: Copy data (with validation)
UPDATE users SET age = user_age WHERE user_age IS NOT NULL;

-- Step 3: Drop old column (after testing)
ALTER TABLE users DROP COLUMN user_age;
```

**Test Case**:
- **Input**: 100 users with `user_age` populated.
- **Expected**:
  - After Step 2: All 100 users have `age` populated; `user_age` unchanged.
  - After Step 3: `user_age` is `NULL` for all users.
- **Tool**: Use **transaction rollback** to revert if validation fails.

---

### **4. Testing API Schema Evolution (REST/GraphQL)**
**Scenario**: Add a `premium` boolean field to a GraphQL schema.
**Old Schema (`v1.0`)**:
```graphql
type User {
  id: ID!
  email: String!
}
```

**New Schema (`v2.0`)**:
```graphql
type User {
  id: ID!
  email: String!
  premium: Boolean  # New field (optional)
}
```

**Test Case**:
```bash
# Query v1.0 client (no `premium`)
curl -X GET "http://api/users?id=123" -H "Accept: application/json"

# Expected: Returns { "id": "123", "email": "test@example.com" }

# Query v2.0 client (with `premium`)
curl -X GET "http://api/users?id=123" -H "Accept: application/json" \
  -H "X-Schema-Version: 2.0"

# Expected: Returns { "id": "123", "email": "test@example.com", "premium": false }
```

**Tooling**:
- **GraphQL**: Use [GraphQL Schema Stitching](https://www.apollographql.com/docs/apollo-server/schema/schema-stitching/) to test backward compatibility.
- **REST**: Use [Postman Collection Runner](https://learning.postman.com/docs/running-tests/collections/) with schema-aware assertions.

---

## **Requirements for Implementation**
### **1. Schema Versioning**
- Use **semantic tags** (e.g., database comments, schema registry metadata).
- Example for PostgreSQL:
  ```sql
  COMMENT ON TABLE users IS 'Schema Version: 3.0';
  ```

### **2. Test Data Generation**
- **Faker Library**: Generate synthetic data for old/new schemas.
  ```python
  from faker import Faker
  fake = Faker()
  user_v1 = {"user_id": "123e4567", "email": fake.email()}
  user_v3 = {"user_id": "456e7890", "email": fake.email(), "phone": fake.phone_number()}
  ```
- **Mock APIs**: Use tools like [Mockoon](https://mockoon.com/) or [Postman Mock Servers](https://learning.postman.com/docs/designing-and-developing-your-api/mocking-data/) to simulate API responses.

### **3. Validation Rules**
| Rule               | Description                                                                 | Example                                  |
|--------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **Backward Read**  | Older clients must read newer schemas.                                     | Query `SELECT * FROM users` in v1.0.     |
| **Forward Write**  | Newer clients must write to older schemas.                                  | Insert into `users` (v1.0 columns only). |
| **Data Migration** | Transforms must preserve data integrity.                                   | `UPDATE users SET age = user_age`.       |
| **Rollback**       | Schema downgrades must not corrupt data.                                   | Test `ROLLBACK` after failed migration. |

### **4. Automated Testing**
- **CI/CD Integration**: Run tests on schema changes (e.g., GitHub Actions, Jenkins).
  ```yaml
  # Example GitHub Actions workflow
  name: Schema Evolution Test
  on: [push]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: python ./test_schema_evolution.py
  ```
- **Test Framework**: Use [Pytest](https://docs.pytest.org/) or [JUnit](https://junit.org/) for schema tests.
  ```python
  # Example pytest test
  def test_backward_read():
      db = DatabaseConnection("v3.0_schema")
      user = db.query("SELECT user_id, email FROM users WHERE id = '123'")
      assert user["age"] is None  # New field ignored
  ```

---

## **Related Patterns**
| Pattern                     | Description                                                                 | When to Use                          |
|-----------------------------|-----------------------------------------------------------------------------|--------------------------------------|
| **Canary Deployment**       | Gradually roll out schema changes to a subset of users.                     | High-risk migrations (e.g., production DB). |
| **Feature Flags**           | Toggle schema compatibility via feature flags.                              | Gradual schema adoption.              |
| **Event Sourcing**          | Track schema changes as immutable events for replay.                        | Audit schema history.                |
| **Schema Registry**         | Centralized repository for schema versions (e.g., Confluent Schema Registry). | Kafka/Avro-based systems.             |
| **Data Validation Layer**   | Middleware to validate incoming data against schema rules.                  | APIs with loose schema constraints.  |
| **Blue-Green Deployment**   | Deploy new schema version alongside old one; switch traffic.               | Zero-downtime migrations.             |

---

## **Tools & Libraries**
| Tool/Library               | Purpose                                                                 | Link                                  |
|----------------------------|-------------------------------------------------------------------------|----------------------------------------|
| **Database**               | Schema migration tools.                                                 |                                        |
| PostgreSQL `pg_migrate`     | Schema change migration tool.                                           | [pg_migrate](https://github.com/rhysd/pg_migrate) |
| Flyway/Liquibase           | Database version control.                                               | [Flyway](https://flywaydb.org/), [Liquibase](https://www.liquibase.org/) |
| **ORM/ODM**                | Schema validation during reads/writes.                                   |                                        |
| SQLAlchemy                 | Python ORM with schema reflection.                                       | [SQLAlchemy](https://www.sqlalchemy.org/) |
| TypeORM                    | TypeScript ORM with schema migration.                                   | [TypeORM](https://typeorm.io/)         |
| **API Testing**            | Schema-aware API validation.                                             |                                        |
| Postman                    | Mock servers and schema testing.                                         | [Postman](https://www.postman.com/)    |
| GraphQL Playground         | Test GraphQL schema evolution.                                           | [GraphQL Playground](https://www.graphqlbin.com/) |
| **Big Data**               | Schema evolution for Avro/Protobuf.                                       |                                        |
| Confluent Schema Registry   | Centralized schema governance for Kafka.                                 | [Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html) |
| Apache Avro                | Schema evolution for binary-serialized data.                             | [Avro](https://avro.apache.org/)      |

---

## **Best Practices**
1. **Test Incrementally**: Validate schema changes in a staging environment before production.
2. **Use Transactions**: Wrap migrations in transactions to allow rollback.
   ```sql
   BEGIN;
   ALTER TABLE users ADD COLUMN phone VARCHAR(20);
   -- Test data integrity here
   COMMIT; -- or ROLLBACK on failure
   ```
3. **Document Breaking Changes**: Clearly mark fields that will be removed in future versions.
4. **Monitor Usage**: Track queries that fail due to schema mismatches (e.g., database error logs).
5. **Automate Rollback**: Define a rollback script for each migration.
6. **Limit Downtime**: Use **blue-green deployment** or **canary releases** for critical schemas.
7. **Leverage ORM Features**: Use ORM tools to handle schema evolution (e.g., Django’s `db_migrations`, Rails’ `ActiveRecord`).