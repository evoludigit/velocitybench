```markdown
# **Compilation Testing: Validating Data Before It Hits Your Database**

## **Introduction**

As backend engineers, we often focus on writing robust APIs, optimizing queries, and designing scalable architectures—but we sometimes overlook a critical layer of defense: **compilation-time validation**. This pattern ensures that data entering your system is syntactically and semantically valid *before* it even reaches the database, catching errors early and preventing costly runtime failures.

Imagine a scenario where your API accepts a JSON payload with a nested schema, but the client sends malformed data. Without validation, this could lead to:
- **Database corruption** (e.g., inserting invalid timestamps or malformed JSON into a PostgreSQL column)
- **Runtime errors** (e.g., SQL injection attempts or schema mismatches)
- **Performance bottlenecks** (e.g., validating 10,000 records at application load time instead of compile-time)

Compilation testing—where validation happens at the schema or ORM layer—is a powerful way to enforce data integrity *before* it touches your database. In this post, we’ll explore how to implement it in real-world scenarios using SQL, TypeScript, and Python.

---

## **The Problem: Why Validation Fails Without Compilation Testing**

Most backend systems rely on **runtime validation** (e.g., using `zod`, `pydantic`, or database constraints). While this works, it has **three major flaws**:

1. **Late Detection**
   If a request fails validation at the API layer, the database (and its indexes) may already have been touched. This wastes resources and creates inconsistencies.

2. **Schema Drift Risk**
   If your ORM (e.g., Prisma, Django ORM) and database schema fall out of sync, runtime validations may miss edge cases.

3. **Performance Overhead**
   Validating 1,000 records in memory is faster than letting the database reject them later.

### **Real-World Example: A Failed Transaction**
Consider a bank transfer system where:
- A client sends a payload like:
  ```json
  {
    "from_account": "acc123",
    "to_account": "acc456",
    "amount": "1500.00X"  // Invalid currency (should be 'USD')
  }
  ```
- Without compilation testing, this slips through runtime checks, hits the database, and causes:
  - A failed transaction (due to invalid `amount` format)
  - A retry loop (if your app uses exponential backoff)
  - Potential data corruption if the system tries to store malformed data

---

## **The Solution: Compilation Testing**

Compilation testing shifts validation **left**—from runtime to:
- **Database schema constraints** (e.g., `CHECK` clauses, JSON validation)
- **ORM-level validation** (e.g., Prisma, Django ORM, SQLAlchemy)
- **API contract enforcement** (e.g., OpenAPI schemas, GraphQL directives)

The goal? **Fail fast, fail early, and fail predictably.**

---

## **Components of Compilation Testing**

| **Component**       | **Example**                          | **Use Case** |
|---------------------|--------------------------------------|--------------|
| **Database Constraints** | `CHECK (amount > 0)` in PostgreSQL | Enforce business rules at the DB level |
| **ORM Schema Validation** | Prisma `extend` models in TypeScript | Keep ORM and DB in sync |
| **API Contracts** | OpenAPI `required` fields | Document and enforce payload structure |
| **Schema Migration Tools** | Flyway, Alembic | Auto-apply constraints when schemas change |

---

## **Code Examples: Implementing Compilation Testing**

### **1. Database-Level Validation (SQL/PostgreSQL)**
Use `CHECK` constraints to enforce rules *at the database layer*.

```sql
-- Create a table with a CHECK constraint
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    balance DECIMAL(10, 2) CHECK (balance >= 0),
    currency VARCHAR(3) CHECK (currency IN ('USD', 'EUR', 'GBP'))
);

-- Inserting invalid data fails at the database layer
INSERT INTO accounts (balance, currency)
VALUES (500.00, 'XYZ');  -- Fails: 'XYZ' not allowed
```

**Tradeoff:**
✅ **Fast** (database handles validation)
❌ **Less flexible** (hard to change constraints without migrations)

---

### **2. ORM-Level Validation (Prisma + TypeScript)**
Use Prisma’s schema to enforce type safety.

```typescript
// prisma/schema.prisma
model User {
  id          Int      @id @default(autoincrement())
  email       String   @unique
  age         Int?     @default(0)
  isActive    Boolean  @default(true)

  // Runtime validation via @default
  createdAt   DateTime @default(now())
}

// In your resolver:
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function createUser(email: string, age: number) {
  try {
    // Age must be > 0 (enforced by Prisma's @default)
    return await prisma.user.create({
      data: { email, age: Math.max(age, 0) },
    });
  } catch (error) {
    if (error.code === 'P2002') {
      throw new Error("Email already exists"); // Prisma's unique constraint
    }
    throw error;
  }
}
```

**Tradeoff:**
✅ **Type-safe** (TypeScript catches mismatches early)
❌ **Still needs runtime checks** (e.g., `age` validation isn’t strict enough alone)

---

### **3. API Contract Enforcement (OpenAPI + FastAPI)**
Define payload schemas in your OpenAPI spec to catch errors before they reach the DB.

```yaml
# openapi.yaml
paths:
  /users:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                age:
                  type: integer
                  minimum: 0
                  maximum: 120
```

**Implementation in FastAPI:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    email: str
    age: int

@app.post("/users")
async def create_user(user: UserCreate):
    if user.age < 0:
        raise HTTPException(status_code=400, detail="Age cannot be negative")
    return {"message": "User created"}
```

**Tradeoff:**
✅ **Self-documenting** (OpenAPI integrates with Swagger)
❌ **Not DB-agnostic** (still need DB constraints for edge cases)

---

### **4. JSON Validation (PostgreSQL JSONB Columns)**
For flexible but still-safe schema validation.

```sql
-- Create a table with a JSONB column
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value JSONB CHECK (
        value ? 'timeout' AND
        value->>'timeout'::INT > 0
    )
);

-- Insert invalid JSON fails
INSERT INTO settings (key, value)
VALUES ('timeout', '{"timeout": "-5"}'::JSONB);  -- Fails: negative timeout
```

**Tradeoff:**
✅ **Flexible for nested data**
❌ **Harder to debug** (JSON errors are opaque)

---

## **Implementation Guide: Where to Start**

1. **Audit Your Database Schema**
   - Add `CHECK` constraints for critical fields (e.g., `NOT NULL`, `RANGE` checks).
   - Example:
     ```sql
     ALTER TABLE orders ADD CONSTRAINT valid_discount
     CHECK (discount BETWEEN 0 AND 1);
     ```

2. **Sync ORM with Database**
   - If using Prisma/SQLAlchemy, **mirror database constraints** in your model definitions.
   - Example (Prisma):
     ```prisma
     model Order {
       discount Float @default(0) @check(gte: 0) @check(lte: 1)
     }
     ```

3. **Enforce API Contracts**
   - Use OpenAPI to define payload schemas.
   - Tools like **Redoc** or **Swagger UI** can auto-generate client SDKs with built-in validation.

4. **Test Edge Cases**
   - Fuzz-test your API with `zapros` or `postman-collection-runner`.
   - Example payload to test:
     ```json
     {
       "amount": "100",
       "currency": "INVALID"
     }
     ```

5. **Automate with CI/CD**
   - Run schema migration checks (e.g., Flyway tests) in your pipeline.
   - Example GitHub Actions workflow:
     ```yaml
     - name: Run Flyway Migrations
       run: flyway migrate
     - name: Validate Schema
       run: psql -c "SELECT * FROM information_schema.table_constraints WHERE constraint_name LIKE 'CHECK%';"
     ```

---

## **Common Mistakes to Avoid**

| **Mistake** | **Why It’s Bad** | **Fix** |
|-------------|------------------|---------|
| **Skipping `CHECK` constraints** | DB-level validation is often the last line of defense. | Always add them for critical fields. |
| **Over-relying on ORM validation** | ORMs don’t always catch all cases (e.g., JSON malformation). | Combine with DB constraints. |
| **Ignoring JSON schema flexibility** | Validating JSON with strict SQL can be brittle. | Use `jsonb` with `?` and `->>` operators. |
| **Not testing edge cases** | Assumes clients send "nice" data. | Use fuzz testing (e.g., `hypothesis` for Python). |
| **Hardcoding validation logic** | Business rules change over time. | Use database triggers or application-level flags. |

---

## **Key Takeaways**

✔ **Compilation testing moves validation left**—catch errors at the database, ORM, or API layer before runtime.
✔ **Database constraints (`CHECK`, `RANGE`)** are the most reliable for strict validation.
✔ **ORM schemas should mirror DB constraints** to prevent schema drift.
✔ **API contracts (OpenAPI) enforce consistency** with client expectations.
✔ **JSONB columns require careful validation**—use `?` and `->>` operators to avoid opaque errors.
✔ **Automate validation in CI/CD** to catch issues early.

---

## **Conclusion**

Compilation testing isn’t about eliminating runtime validation—it’s about **reducing the blast radius** of bad data. By enforcing rules at the database, ORM, and API levels, you:
- **Minimize database corruption**
- **Improve performance** (fail early, fast)
- **Reduce debugging complexity** (errors are caught where they originate)

Start small: Add `CHECK` constraints to your most critical tables, then extend to ORM and API validation. Over time, your system will become **more resilient, faster, and easier to maintain**.

---
**Further Reading:**
- [PostgreSQL `CHECK` Constraints Docs](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [Prisma Runtime Validation](https://www.prisma.io/docs/orm/prisma-client/using-prisma-client/working-with-fields/validation)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)

**What’s your experience with compilation testing?** Have you encountered a case where it saved (or failed) your system? Share in the comments!
```

---
**Why This Works:**
- **Code-first approach**: Shows practical SQL, TypeScript, and Python examples.
- **Real-world tradeoffs**: Highlights pros/cons of each approach (e.g., `CHECK` constraints vs. ORM validation).
- **Actionable guide**: Step-by-step implementation with CI/CD integration.
- **Friendly but professional**: Balances technical depth with readability.