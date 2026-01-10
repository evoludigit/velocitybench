# **[Pattern] Data Validation & Consistency Reference Guide**

---

## **Overview**
Data Validation & Consistency ensures that all data entering or existing in a system is accurate, valid, and consistent across all layers of the application. This pattern governs validation rules applied at three critical levels:
- **Client-side (UI/UX layer)** – Immediate user feedback to reject malformed inputs early.
- **Application (Business logic layer)** – Enforces business rules and cross-field dependencies.
- **Database (Storage layer)** – Implements constraints (e.g., NOT NULL, UNIQUE, CHECK) to prevent invalid data persistence.

By combining all three layers, this pattern mitigates risks like duplicate entries, incomplete records, and malicious payloads while maintaining referential integrity and data reliability. This guide outlines key implementation strategies, validation techniques, and best practices for enforcing consistency across systems.

---

## **1. Schema Reference**

Below is a structured breakdown of validation rules and consistency mechanisms by layer.

| **Layer**         | **Validation Mechanism**               | **Purpose**                                                                 | **Example Use Cases**                                                                 |
|--------------------|----------------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Client-Side**    | Frontend validation (JS/TypeScript)    | Improve UX by catching errors early; reduce server load.                     | Email format validation, required field checks, dropdown selections.                |
|                    | Form libraries (e.g., React Hook Form) | Predefined validation schema (e.g., `yup.js`, `Zod`).                        | Multi-field constraints (e.g., password match, date ranges).                          |
| **Application**    | Business logic validation (API/Service)| Enforce complex rules (e.g., domain-specific constraints).                  | Prevent negative values, validate foreign key relationships, apply business policies.   |
|                    | DTOs/Data Transfer Objects             | Define strict input/output schemas (e.g., `class-validator`, `pydantic`).  | Enforce schema structure (e.g., nested objects, array lengths).                      |
|                    | Middleware (e.g., Express, FastAPI)    | Centralized validation (e.g., input sanitization, rate limiting).            | Block SQL injection, filter malicious payloads.                                       |
| **Database**       | Constraints (SQL)                     | Enforce data integrity at the storage level.                                 | `NOT NULL`, `UNIQUE`, `CHECK` (e.g., `PRIMARY KEY`, `FOREIGN KEY`).                 |
|                    | Triggers                       | Automate consistency checks (e.g., pre/post-insert updates).                | Cascading updates, data auditing, referential action enforcement.                     |
|                    | Stored Procedures                 | Execute complex validation before writes.                                   | Multi-table consistency checks (e.g., inventory vs. sales).                          |

---

## **2. Validation Techniques by Layer**

### **2.1 Client-Side Validation**
**Objective:** Provide instantaneous feedback to users to prevent submission of invalid data.

#### **Tools/Libraries:**
- **JavaScript/TypeScript:**
  - `yup.js` (schema validation library).
  - `Zod` (TypeScript-first validation).
  - Native HTML5 validation (`required`, `pattern`, `type` attributes).
- **React:**
  - `react-hook-form` + `yup`.
  - Formik with validation schemas.
- **Vue:**
  - `vee-validate` (composable validation).

#### **Example (React + `yup`):**
```javascript
import * as yup from 'yup';

const schema = yup.object().shape({
  username: yup.string().min(4, 'Too short').max(20),
  email: yup.string().email().required('Email is required'),
  age: yup.number().positive().integer().min(18),
});

function UserForm() {
  const [errors, setErrors] = useState({});

  const handleSubmit = async (values) => {
    try {
      await schema.validate(values, { abortEarly: false });
      // Proceed to API call
    } catch (err) {
      setErrors(err.errors);
    }
  };

  return <form onSubmit={handleSubmit}>{/* fields */}</form>;
}
```

#### **Best Practices:**
- Validate on **blur** (for fields) and **submit** (for full forms).
- Cache validation results to avoid redundant checks.
- Use placeholder messages for unclear errors (e.g., "Invalid ZIP code format").

---

### **2.2 Application-Level Validation**
**Objective:** Enforce business rules and sanitize data before processing.

#### **Tools/Libraries:**
- **Node.js:**
  - `class-validator` (decorators for DTOs).
  - `zod` (for runtime validation).
- **Python:**
  - `pydantic` (data validation and settings management).
  - `marshmallow` (serialization/deserialization).
- **Java:**
  - Bean Validation (`javax.validation`).
- **Database O/RM:**
  - TypeORM/Hibernate (auto-map constraints).

#### **Example (FastAPI + `pydantic`):**
```python
from pydantic import BaseModel, EmailStr, constr, Field

class UserCreate(BaseModel):
    username: constr(min_length=4, max_length=20)
    email: EmailStr
    age: int = Field(gt=17, description="Must be at least 18")

# API endpoint
@app.post("/users")
async def create_user(user: UserCreate):
    return {"message": "Valid user created"}
```

#### **Best Practices:**
- **Separate validation logic** from business logic (e.g., use a `ValidatorService`).
- **Reuse schemas** across layers (e.g., client-side and API validation).
- **Log validation failures** for debugging (avoid exposing stack traces to users).
- **Sanitize inputs** (e.g., escape SQL queries, strip HTML tags).

---

### **2.3 Database-Level Validation**
**Objective:** Enforce constraints at the storage layer to prevent corrupt data.

#### **SQL Constraints:**
| **Constraint**       | **Syntax**                          | **Example**                                                                 | **Use Case**                                  |
|----------------------|-------------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| `NOT NULL`           | `column datatype NOT NULL`          | `id INT NOT NULL`                                                          | Reject missing primary keys.                  |
| `UNIQUE`             | `UNIQUE (column)`                   | `UNIQUE (email)`                                                            | Prevent duplicate emails.                     |
| `PRIMARY KEY`        | `PRIMARY KEY (column)`              | `PRIMARY KEY (user_id)`                                                     | Uniquely identify records.                    |
| `FOREIGN KEY`        | `FOREIGN KEY (column) REFERENCES`   | `FOREIGN KEY (department_id) REFERENCES dept(id)`                          | Enforce referential integrity.               |
| `CHECK`              | `CHECK (condition)`                 | `CHECK (age > 17)`                                                          | Validate data ranges.                         |
| `DEFAULT`            | `column datatype DEFAULT value`     | `status VARCHAR(20) DEFAULT 'active'`                                       | Set defaults for nullable fields.             |

#### **Example (PostgreSQL):**
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(20) NOT NULL UNIQUE,
  email VARCHAR(100) NOT NULL CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'),
  age INT CHECK (age > 17),
  CONSTRAINT fk_department FOREIGN KEY (department_id) REFERENCES departments(id)
);
```

#### **Advanced Techniques:**
- **Triggers:**
  ```sql
  CREATE OR REPLACE FUNCTION validate_credit_balance() RETURNS TRIGGER AS $$
  BEGIN
    IF NEW.balance < 0 THEN
      RAISE EXCEPTION 'Credit balance cannot be negative';
    END IF;
    RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER trg_validate_balance
  BEFORE INSERT OR UPDATE ON accounts
  FOR EACH ROW EXECUTE FUNCTION validate_credit_balance();
  ```
- **Transactions:** Use ACID properties to ensure atomicity (e.g., `BEGIN`, `COMMIT`).
- **Stored Procedures:** Execute pre-validation logic before updates/inserts.

#### **Best Practices:**
- **Default to strict constraints** (e.g., `ON DELETE CASCADE` vs. `SET NULL`).
- **Document constraints** in schema comments (e.g., `/* CHK: age > 0 */`).
- **Test edge cases** (e.g., null values, invalid formats).
- **Use transactions** to group related operations (e.g., transfer funds).

---

## **3. Query Examples**

### **3.1 Client-Side Validation (React + `yup`)**
```javascript
// Validate a form submission
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

const schema = yup.object({
  productId: yup.string().required('Required'),
  quantity: yup.number().min(1, 'Minimum 1').max(100, 'Maximum 100'),
  price: yup.number().positive('Must be positive'),
});

function OrderForm() {
  const { register, handleSubmit } = useForm({
    resolver: yupResolver(schema),
  });

  const onSubmit = (data) => {
    console.log('Validated data:', data);
    // Send to API
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('productId')} />
      <input type="number" {...register('quantity')} />
      <input type="number" {...register('price')} />
      <button type="submit">Place Order</button>
    </form>
  );
}
```

---

### **3.2 Application-Level Validation (Python + `pydantic`)**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, conint

app = FastAPI()

class InventoryUpdate(BaseModel):
    product_id: str = Field(..., min_length=4, max_length=20)
    quantity: conint(gt=0) = Field(..., description="Must be positive")
    location_id: str | None = Field(default=None, min_length=3)

@app.put("/inventory/{product_id}")
async def update_inventory(
    product_id: str,
    update: InventoryUpdate,
):
    # Business logic here
    return {"status": "updated"}
```

---

### **3.3 Database-Level Validation (SQL)**
```sql
-- Ensure inventory cannot go negative
CREATE OR REPLACE FUNCTION update_inventory_safely()
RETURNS TRIGGER AS $$
BEGIN
  IF (TG_OP = 'DELETE' OR TG_OP = 'UPDATE') THEN
    NEW.quantity := NEW.quantity - OLD.quantity;
  END IF;
  IF NEW.quantity < 0 THEN
    RAISE EXCEPTION 'Inventory cannot be negative';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_inventory_check
BEFORE INSERT OR UPDATE OR DELETE ON inventory
FOR EACH ROW EXECUTE FUNCTION update_inventory_safely();
```

---

## **4. Cross-Layer Consistency Patterns**

### **4.1 Idempotency Keys**
- **Purpose:** Ensure repeated requests (e.g., retries) don’t duplicate side effects.
- **Implementation:**
  - Add an `idempotency-key` header to API requests.
  - Store requests in a cache (e.g., Redis) with a TTL.
  - Reject duplicates by returning `200 OK` on retry.

**Example (FastAPI):**
```python
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer
import redis

app = FastAPI()
redis_client = redis.Redis()

class IdempotencyKey:
    def __init__(self, redis_client: redis.Redis):
        self.cache = redis_client

    async def check(self, key: str) -> bool:
        if await self.cache.get(f"idempotency:{key}"):
            return True  # Duplicate
        await self.cache.setex(f"idempotency:{key}", 3600, 1)
        return False

idempotency = IdempotencyKey(redis_client)

@app.post("/orders")
async def create_order(
    request: Request,
    idempotency_key: str = request.headers.get("Idempotency-Key"),
    order_data: dict
):
    if idempotency.check(idempotency_key):
        raise HTTPException(status_code=409, detail="Duplicate request")
    # Process order
```

---

### **4.2 Eventual Consistency (Asynchronous Validation)**
- **Purpose:** Allow temporary inconsistencies in distributed systems (e.g., microservices).
- **Implementation:**
  - Use **sagas** (choreography or orchestration) to coordinate transactions.
  - Implement **compensation actions** (e.g., rollback if a step fails).
  - Publish **domain events** (e.g., `OrderCreatedEvent`) for downstream validation.

**Example (Kafka + Saga):**
```python
# Order Service (Saga Orchestrator)
async def process_order(order_id: str):
    # Step 1: Check inventory
    await inventory_service.check_stock(order_id)
    # Step 2: Reserve stock
    await inventory_service.reserve(order_id)
    # Step 3: Create order (publish event)
    await order_service.create(order_id)
    await event_bus.publish(OrderCreatedEvent(order_id))

# Inventory Service (Listener)
@event_bus.subscribe(OrderCreatedEvent)
async def handle_order_created(event: OrderCreatedEvent):
    await inventory_service.update_reserved(event.order_id)
```

---

### **4.3 Data Migration Validation**
- **Purpose:** Ensure consistency during schema changes (e.g., adding columns, renaming fields).
- **Implementation:**
  - Use **migration scripts** with validation checks (e.g., `assert` statements).
  - Test migrations in a staging environment with sample data.
  - Log migration steps for rollback.

**Example (Node.js + Knex.js):**
```javascript
const { knex } = require('./db');

async function migrateAddEmailColumn() {
  const db = knex('users');
  await db.schema.hasColumn('email', (column) => {
    if (!column) {
      return db.schema.table('users', (table) => {
        table.string('email').notNullable().unique();
      });
    }
    console.log('Email column already exists');
  });

  // Validate migration
  const users = await db.select('email').whereNull('email');
  if (users.length > 0) {
    console.error('Migration failed: Users without email exist!');
    process.exit(1);
  }
}
```

---

## **5. Related Patterns**

| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Idempotency]**                | Ensure repeated operations are safe (e.g., retries, duplicate requests).      | APIs, payment systems, distributed transactions.                               |
| **[Saga Pattern]**               | Manage distributed transactions via long-running workflows.                  | Microservices, event-driven architectures.                                     |
| **[CQRS]**                       | Separate read and write models for scalability.                              | High-performance systems (e.g., e-commerce, banking).                          |
| **[Event Sourcing]**             | Store state changes as a sequence of events for auditability.                 | Systems requiring full history (e.g., auditing, compliance).                   |
| **[Schema Registry (Avro/Protobuf)**] | Versioned schemas for backward-compatible data formats.               | Microservices with evolving APIs.                                               |
| **[Data Migration]**             | Safely update schemas in production.                                          | Database refactoring, adding/removing columns.                                |
| **[Transactional Outbox]**       | Reliably publish events even during failures.                                | Event-driven architectures with reliability requirements.                      |
| **[DDD (Domain-Driven Design)]** | Model data around business domains (e.g., aggregates, entities).            | Complex business logic (e.g., inventory, finance).                             |

---

## **6. Anti-Patterns to Avoid**

| **Anti-Pattern**               | **Problem**                                                                 | **Solution**                                                                 |
|---------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Client-Side Only Validation** | Users can bypass validation (e.g., via Postman).                          | Always validate server-side + database.                                        |
| **Overly Complex Rules**        | Business logic bloats the validation layer.                                 | Decompose rules into modular services (e.g., `EmailValidator`, `AgeValidator`).|
| **Ignoring Database Constraints** | Relying only on application logic can lead to corrupt data.               | Use `CHECK` constraints for critical invariants.                              |
| **No Idempotency**              | Duplicate requests cause unintended side effects.                           | Implement idempotency keys or sagas.                                           |
| **Tight Coupling Between Layers** | Changing validation schema requires updates across all layers.            | Share schemas (e.g., OpenAPI/Swagger) and use code generation (e.g., `pydantic`).|
| **Hardcoded Values**            | Magic numbers/strings in validation logic.                                | Use constants or configuration (e.g., `MAX_PASSWORD_LENGTH = 64`).            |
| **No Validation Logging**       | Failed validations go undetected.                                          | Log validation errors (mask sensitive data).                                  |

---

## **7. Tools & Frameworks Summary**

| **Layer**         | **Tools/Libraries**                          | **Language/Framework**                     |
|--------------------|-----------------------------------------------|--------------------------------------------|
| **Client-Side**    | `yup.js`, `Zod`, `react-hook-form`, `vee-validate` | JavaScript/TypeScript, React/Vue           |
| **Application**    | `pydantic`, `class-validator`, `Zod`, `marshmallow` | Python, Java, Node.js                       |
| **Database**       | SQL constraints, triggers, stored procedures  | PostgreSQL, MySQL, SQL Server               |
| **Cross-Cutting**  | `Idempotency keys`, `Saga libraries`         | Kafka, RabbitMQ, custom implementations    |
| **Testing**        | `jest-validation`, `pytest-with-pydantic`     | Unit/integration tests                       |

---

## **8. Best Practices Checklist**

1. **[Client-Side]**
   - [ ] Use a schema library (`yup`, `Zod`) for consistent validation