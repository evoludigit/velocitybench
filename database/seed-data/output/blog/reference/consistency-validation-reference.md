---
# **[Pattern] Consistency Validation Reference Guide**

---

## **Overview**
The **Consistency Validation** pattern ensures that data across distributed systems remains logically consistent by enforcing constraints on record interactions at the application or service boundary. Unlike traditional database constraints, this pattern validates consistency across microservices, event-driven systems, or multi-database setups by applying business rules at critical touchpoints—such as API calls, event processing, or transaction boundaries.

Key use cases include:
- **Eventual consistency systems**: Validating that a command (e.g., `update_user`) aligns with all downstream updates (e.g., `refresh_cache`, `notify_subscribers`).
- **Saga workflows**: Ensuring steps in a distributed transaction (e.g., `place_order`, `reserve_inventory`, `update_account`) don’t violate invariants.
- **Multi-service transactions**: Confirming that cross-service updates (e.g., `create_order` → `log_delivery`) don’t conflict with existing states.
- **Idempotency checks**: Preventing duplicate operations (e.g., retries) from corrupting data.

The pattern acts as a **safety net** when multi-step processes span multiple services or databases, reducing the need for centralized coordination while maintaining data integrity.

---

## **Implementation Details**
### **Core Concepts**
1. **Consistency Boundary**
   The scope where validation occurs (e.g., a single API endpoint, event handler, or transactional unit).
   Example: Validating that an `order_total` matches calculated item sums *before* updating the database.

2. **Validation Rules**
   Predefined constraints enforced at the boundary. Rules can be:
   - **Structural**: Schema compliance (e.g., `optional: true` for fields).
   - **Temporal**: Ordering constraints (e.g., "A payment must precede shipping").
   - **Semantic**: Business logic (e.g., "Inventory <= 0 → reject order").
   - **Referential**: Cross-record integrity (e.g., "User ID must exist in `users` table").

3. **Validation Points**
   Where checks are applied:
   - **Request Validation**: Frontend/API layer (e.g., validate `order_items` sum matches `total`).
   - **Command Validation**: Before processing a sagas step (e.g., "Inventory reserve > 0").
   - **Event Validation**: After receiving an event (e.g., "Duplicate `order_created` event ignored").
   - **Post-Processing**: After updates (e.g., validate cache coherence).

4. **Failure Modes**
   - **Reject**: Fail fast (e.g., return `400 Bad Request` for invalid input).
   - **Retry**: For transient errors (e.g., retry if a referenced record is temporarily unavailable).
   - **Compensate**: Undo prior steps (e.g., rollback inventory reservation if payment fails).
   - **Notify**: Log/warn without blocking (e.g., "Data skew detected").

5. **Tools & Libraries**
   | Category               | Tools/Libraries                          | Purpose                                  |
   |------------------------|------------------------------------------|------------------------------------------|
   | **Validation Frames**  | Zod, Joi, JSON Schema                    | Schema validation at API boundaries.     |
   | **Workflow Engines**   | Camunda, Temporal, Apache Beam           | Validate saga steps.                     |
   | **Event Stores**       | Kafka, NATS, AWS EventBridge             | Detect duplicate/events.                 |
   | **Query Validation**   | DQL (Domain Query Language), GraphQL     | Validate queries against invariants.     |
   | **Testing**            | Pact, Contract Tests                     | Validate cross-service interactions.     |

---

## **Schema Reference**
Below are common validation schemas for the pattern. Use these as templates or extend them for domain-specific rules.

### **1. Request Validation Schema (JSON)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "order_id": { "type": "string", "format": "uuid" },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "product_id": { "type": "string", "pattern": "^prod-[0-9a-f]{8}$" },
          "quantity": { "type": "integer", "minimum": 1 },
          "price": { "type": "number", "minimum": 0.01 }
        },
        "required": ["product_id", "quantity", "price"],
        "additionalProperties": false
      }
    },
    "total": {
      "type": "number",
      "minimum": 0.01,
      "description": "Must equal sum of `items[*].quantity * items[*].price`."
    }
  },
  "required": ["items", "total"],
  "additionalProperties": false,
  "$validate": {
    "total": {
      "type": "function",
      "args": ["$", "data"],
      "description": "Custom: Validate total matches item sum.",
      "fn": (schema, data) => {
        const sum = data.items.reduce(
          (acc, item) => acc + (item.quantity * item.price), 0
        );
        return sum === data.total;
      }
    }
  }
}
```

### **2. Event Validation Schema (Envelope)**
```json
{
  "schema": "http://example.com/schemas/event-validation/v1",
  "type": "object",
  "properties": {
    "event_id": { "type": "string", "format": "uuid" },
    "event_type": {
      "enum": ["order_created", "order_updated", "order_cancelled"],
      "description": "Must match predefined types."
    },
    "timestamp": { "type": "string", "format": "date-time" },
    "payload": {
      "anyOf": [
        { "$ref": "#/definitions/order_created_payload" },
        { "$ref": "#/definitions/order_updated_payload" }
      ]
    },
    "idempotency_key": { "type": "string", "description": "Prevent duplicates." }
  },
  "required": ["event_type", "timestamp", "payload"],
  "additionalProperties": false,
  "$validate": {
    "unique_idempotency_key": {
      "type": "function",
      "args": ["$", "data", "context"],
      "fn": (schema, data, context) => {
        // Check if idempotency_key exists in store (context.event_store)
        return !context.event_store.has(data.idempotency_key);
      }
    }
  },
  "definitions": {
    "order_created_payload": { /* ... */ },
    "order_updated_payload": { /* ... */ }
  }
}
```

### **3. Saga Validation Rules (YAML)**
```yaml
# validate-saga.yaml
saga: order_fulfillment
steps:
  - name: reserve_inventory
    validate:
      - rule: "inventory >= quantity"
        description: "Sufficient stock available."
        query: |
          SELECT SUM(quantity) FROM inventory_items
          WHERE product_id = ? AND status = 'available'
      - rule: "reservation_expiration > NOW()"
        description: "Inventory reserved for <= 24h."
        query: |
          SELECT expiration FROM reservations
          WHERE order_id = ? AND status = 'pending'
  - name: update_account
    validate:
      - rule: "account_balance >= order_total"
        description: "Funds available for payment."
        query: |
          SELECT balance FROM accounts WHERE user_id = ?
```

---

## **Query Examples**
### **1. Validate Cross-Service Referential Integrity**
**Scenario**: Ensure a `user_id` in the `orders` table exists in `users`.
**SQL**:
```sql
-- Pre-insert validation
SELECT 1 FROM users
WHERE id = :user_id AND active = true;
```
**Result**:
- If row exists → Proceed with `INSERT INTO orders`.
- If not → Reject with `404 User Not Found`.

**GraphQL**:
```graphql
query CheckUserExists($userId: ID!) {
  user(id: $userId) {
    id
    active
  }
}
```
**Resolver Logic**:
```javascript
if (!user.active) throw new Error("User is inactive");
```

### **2. Validate Eventual Consistency (Post-Update)**
**Scenario**: After updating `user_email`, ensure the `preferences` table syncs.
**Python (FastAPI)**:
```python
from fastapi import APIRouter, HTTPException
from db import async_session

router = APIRouter()

@router.patch("/users/{user_id}/email")
async def update_email(user_id: str, email: str):
    # 1. Check email uniqueness
    async with async_session() as session:
        existing = await session.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        )
        if existing.fetchone():
            raise HTTPException(status_code=400, detail="Email taken")

    # 2. Update user
    await session.execute(
        "UPDATE users SET email = ? WHERE id = ?", (email, user_id)
    )

    # 3. Sync preferences (eventual consistency)
    await session.execute(
        "UPDATE preferences SET email = ? WHERE user_id = ?",
        (email, user_id)
    )
```

### **3. Validate Temporal Order (Saga Step)**
**Scenario**: Payment must precede shipping in a saga.
**Java (Temporal Workflow)**:
```java
@Workflow
public class OrderFulfillmentWorkflow {
    public CompletableFuture<String> start(Order order) {
        return workflow.executeSync(() ->
            workflow.continueAsNew(
                new OrderFulfillmentActivity(order)
                    .validateStep("payment", order.getPaymentId())
                    .validateStep("shipping", order.getShippingId())
            )
        );
    }
}

public class OrderFulfillmentActivity {
    private final Order order;

    public OrderFulfillmentActivity(Order order) { this.order = order; }

    public void validateStep(String step, String stepId) {
        // Check if step is in correct order
        if (step.equals("shipping") && !order.getSteps().contains("payment")) {
            throw new WorkflowFailureException("Payment required before shipping.");
        }
    }
}
```

---

## **Related Patterns**
| Pattern                          | Relationship to Consistency Validation                          | When to Use                                                                 |
|----------------------------------|----------------------------------------------------------------|----------------------------------------------------------------------------|
| **Saga Pattern**                 | Validation occurs at each saga step boundary.                 | Distributed transactions requiring step-by-step consistency checks.          |
| **Event Sourcing**               | Events are validated before being appended to the store.       | Audit logs and replayable event histories with strict ordering.              |
| **Command Query Responsibility Segregation (CQRS)** | Queries validate against read models; commands validate writes. | Separate read/write models with distinct validation rules.                   |
| **Idempotency Keys**             | Validation ensures unique operations (e.g., retries).         | APIs susceptible to duplicate requests (e.g., payments, orders).              |
| **Distributed Locks**            | Locks prevent race conditions during validation.             | High-concurrency scenarios (e.g., inventory updates).                       |
| **Schema Registry**              | Validates data schemas across services.                       | Multi-team environments with evolving schemas.                               |
| **Compensation Transactions**    | Validation triggers compensating actions (e.g., undo).         | Rolling back steps in long-running transactions (e.g., payments → cancellations). |
| **Eventual Consistency (EC)**    | Validation defines acceptable "slack" in EC systems.          | Systems where 100% consistency isn’t critical (e.g., user profiles).         |

---

## **Anti-Patterns to Avoid**
1. **Over-Validation**
   - *Problem*: Excessive checks slow down performance.
   - *Solution*: Validate at the least granular boundary (e.g., API layer > service layer).

2. **Cascading Rollbacks**
   - *Problem*: Undoing all steps in a saga can fail midway, leaving partial states.
   - *Solution*: Use compensating transactions or event replay.

3. **Tight Coupling**
   - *Problem*: Validating against another service’s DB schema increases coupling.
   - *Solution*: Use event-driven validation (e.g., validate on events, not direct DB calls).

4. **Ignoring Idempotency**
   - *Problem*: Retries of non-idempotent operations corrupt data.
   - *Solution*: Apply idempotency keys to all writes.

5. **Validation as a Black Box**
   - *Problem*: Untested validation rules cause silent failures.
   - *Solution*: Instrument validation with logs/metrics (e.g., OpenTelemetry).