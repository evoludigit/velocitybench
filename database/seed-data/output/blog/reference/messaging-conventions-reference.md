# **[Pattern] Messaging Conventions Reference Guide**

---

## **Overview**
The **Messaging Conventions** pattern defines a structured way to format messages exchanged between services, APIs, or internal systems to ensure consistency, interoperability, and ease of parsing. By enforcing standardized schemas, naming conventions, and metadata rules, this pattern reduces ambiguity, minimizes errors, and simplifies integration efforts.

Key benefits include:
- **Predictability**: Clear structure for field names, data types, and message formats.
- **Interoperability**: Compatible across languages, tools, or platforms.
- **Maintainability**: Easier debugging and versioning with standardized metadata.
- **Tooling Support**: Better integration with event-driven architectures (e.g., Kafka, RabbitMQ) and data processing pipelines.

This guide covers core conventions, schema design, and best practices for implementation.

---

## **Implementation Details**

### **1. Core Components of Messaging Conventions**
| **Component**          | **Description**                                                                 | **Example**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Message Type**       | Defines the purpose of the message (e.g., `OrderCreated`, `PaymentFailed`). | `event_type: "OrderCreated"`                                                 |
| **Versioning**         | Ensures backward/forward compatibility.                                       | `version: "1.0"`                                                              |
| **Timestamp**          | Standardized time format for event ordering.                                  | `timestamp: "2024-05-15T14:30:00Z"` (ISO 8601)                               |
| **ID**                 | Unique identifier for traceability.                                           | `id: "ord_12345"`                                                            |
| **Payload**            | Structured data (JSON, Avro, etc.) with key-value pairs.                     | `{ "customer_id": "cust_789", "amount": 99.99 }`                             |
| **Headers/Metafields** | Additional metadata (e.g., `source_service`, `correlation_id`).                | `source_service: "ecommerce_frontend"`, `correlation_id: "req_678"`        |
| **Error Handling**     | Standardized fields for errors (e.g., `error_code`, `error_message`).        | `error_code: "INVALID_PAYMENT"`, `error_message: "Card declined"`          |
| **Idempotency Key**    | Prevents duplicate processing.                                                | `idempotency_key: "order_pay_987"`                                           |

---

### **2. Schema Design Principles**
#### **A. Field Naming Conventions**
- Use **snake_case** for all fields (e.g., `user_email`, `order_status`).
- Avoid spaces, special characters, or camelCase (unless legacy systems require it).
- Prefix domain-specific fields (e.g., `payment_` for payment-related fields).

#### **B. Data Types**
| **Type**       | **Use Case**                          | **Example**               |
|----------------|---------------------------------------|---------------------------|
| `string`       | Text, IDs, or identifiers.             | `"user_email"`            |
| `number`       | Numeric values (use `float`/`int`).    | `100.50` (price), `42` (ID)|
| `boolean`      | True/false flags.                      | `is_shipped: true`        |
| `timestamp`    | Event occurrence time (ISO 8601).      | `"2024-05-15T14:30:00Z"` |
| `array`        | Collections of items.                  | `["item1", "item2"]`      |
| `object`       | Nested structures (e.g., `address`).  | `{ "street": "123 Main" }` |
| `enum`         | Predefined values (e.g., `status`).    | `status: "PENDING"`       |

#### **C. Optional vs. Required Fields**
- Mark required fields with `*` in schemas.
- Document optional fields with `[ ]` (e.g., `[address]`).

#### **D. Versioning Strategy**
- Increment minor version for **backward-compatible** changes (new fields).
- Use major version for **breaking changes** (renamed fields, deleted fields).
- Example:
  ```json
  {
    "version": "2.1",
    "fields": {
      "required": ["user_id*", "amount*"],
      "optional": ["discount[optional]"]
    }
  }
  ```

#### **E. Error Handling**
- Include a dedicated `error` object with:
  - `error_code` (e.g., `VALIDATION_FAILED_400`).
  - `error_message` (human-readable).
  - `details` (debugging info, optional).
- Example:
  ```json
  {
    "error": {
      "error_code": "INVALID_CREDENTIALS_401",
      "error_message": "Authentication failed",
      "details": { "field": "password" }
    }
  }
  ```

---

### **3. Message Structures**
#### **A. Event Message (Asynchronous)**
```json
{
  "message_type": "OrderCreated",
  "version": "1.0",
  "id": "ord_12345",
  "timestamp": "2024-05-15T14:30:00Z",
  "source_service": "ecommerce",
  "payload": {
    "order_id": "ord_12345",
    "customer_id": "cust_789",
    "items": [
      { "product_id": "prod_001", "quantity": 2 }
    ]
  }
}
```

#### **B. Request/Response (Synchronous)**
```json
// Request
{
  "request_type": "CreateUser",
  "version": "1.0",
  "id": "req_678",
  "payload": {
    "username": "john_doe",
    "email": "john@example.com"
  }
}

// Response (Success)
{
  "response_type": "CreateUserResponse",
  "version": "1.0",
  "id": "req_678",
  "status": "SUCCESS",
  "payload": {
    "user_id": "user_1001"
  }
}

// Response (Error)
{
  "response_type": "CreateUserResponse",
  "version": "1.0",
  "id": "req_678",
  "status": "ERROR",
  "error": {
    "error_code": "DUPLICATE_EMAIL_409",
    "error_message": "Email already exists"
  }
}
```

---

## **Schema Reference**
Below is a **tabular schema** for a `PaymentProcessed` event. Customize fields as needed.

| **Field**               | **Type**   | **Required** | **Description**                          | **Example Value**                     |
|-------------------------|------------|--------------|------------------------------------------|----------------------------------------|
| `message_type`          | `string`   | ✅           | Event type (e.g., "PaymentProcessed").    | `"PaymentProcessed"`                   |
| `version`               | `string`   | ✅           | Schema version.                          | `"1.0"`                               |
| `id`                    | `string`   | ✅           | Unique event ID.                         | `"pay_54321"`                         |
| `timestamp`             | `timestamp`| ✅           | Event time (ISO 8601).                   | `"2024-05-15T14:30:00Z"`              |
| `source_service`        | `string`   | ❌           | Service that emitted the event.          | `"payment_gateway"`                   |
| `payload.transaction_id`| `string`   | ✅           | Unique transaction ID.                   | `"txn_98765"`                         |
| `payload.amount`        | `number`   | ✅           | Transaction amount.                      | `99.99`                               |
| `payload.currency`      | `string`   | ✅           | Currency code (ISO 4217).                | `"USD"`                               |
| `payload.status`        | `enum`     | ✅           | Payment status (`PENDING`, `COMPLETED`). | `"COMPLETED"`                         |
| `payload.payment_method`| `string`   | ❌           | Payment method (e.g., `credit_card`).    | `"credit_card"`                       |
| `metadata.correlation_id`| `string`   | ❌           | Links to parent request.                | `"req_123"`                           |
| `error.error_code`      | `string`   | ❌           | Error code (if applicable).              | `null` or `"FRAUD_DETECTED_400"`      |

---

## **Query Examples**
### **1. Filtering Events by Message Type**
**Tool:** Kafka (SQL-like syntax)
```sql
SELECT *
FROM payment_events
WHERE message_type = 'PaymentProcessed'
  AND timestamp > '2024-05-15T00:00:00Z'
  AND payload.status = 'COMPLETED';
```

**Tool:** Elasticsearch (DSL)
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "message_type": "PaymentProcessed" } },
        { "range": { "timestamp": { "gte": "2024-05-15T00:00:00Z" } } }
      ]
    }
  }
}
```

---

### **2. Aggregating Payment Data**
**Tool:** Spark (PySpark)
```python
from pyspark.sql.functions import col, avg

# Load data
df = spark.read.json("path/to/payments")

# Filter and aggregate
result = df.filter(
    (col("message_type") == "PaymentProcessed") &
    (col("payload.status") == "COMPLETED")
).groupBy("payload.currency").agg(
    avg("payload.amount").alias("avg_amount")
).orderBy("avg_amount", ascending=False)
```

---

### **3. Handling Errors**
**Tool:** Python (Pandas)
```python
import pandas as pd

# Load error events
errors = pd.read_json("path/to/errors.json")

# Find common error codes
common_errors = errors.groupby("error.error_code").size().sort_values(ascending=False)
print(common_errors.head(5))
```

---

## **Related Patterns**
| **Pattern**                  | **Description**                                                                 | **When to Use**                                                                 |
|------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Schema Registry](https://www.confluent.io/schema-registry/)** | Centralized repository for message schemas (Avro, Protobuf, JSON Schema).       | When versioning schemas across microservices.                                   |
| **[Idempotent Producer](https://docs.confluent.io/kafka/ecosystem/idempotent-producer.html)** | Ensures exactly-once delivery for message consumers.                          | For critical transactions (e.g., payments).                                     |
| **[Event Sourcing](https://martinfowler.com/eaaT.html)**         | Persist state changes as a sequence of events.                                  | When auditing or replaying state is required.                                    |
| **[CQRS](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)**    | Separates read and write models.                                               | High-throughput read-heavy systems.                                             |
| **[API Gateway Patterns](https://www.apigee.com/about/what-is-an-api-gateway)** | Routes and transforms messages between services.                                | When integrating multiple heterogeneous services.                                |

---

## **Best Practices**
1. **Document Schema Changes**:
   - Maintain a `CHANGELOG.md` file with version updates.
   - Example:
     ```
     ## v1.1 (2024-05-16)
     - Added `payload.payment_method` field.
     - Deprecated `legacy_payment_type`.
     ```

2. **Use Tools**:
   - **Schema Validation**: Schema Registry, JSON Schema Validator.
   - **Monitoring**: Track message volume, latency, and error rates.

3. **Testing**:
   - Unit test message serialization/deserialization.
   - Validate against schemas in CI/CD pipelines.

4. **Security**:
   - Encrypt sensitive fields (e.g., `payload.cc_number`).
   - Use TLS for message transport.

5. **Performance**:
   - Optimize payload size (avoid large arrays/nested objects).
   - Compress messages (e.g., Avro with Snappy compression).

6. **Deprecation**:
   - Mark fields as deprecated with a `deprecated_since` field.
   - Example:
     ```json
     {
       "legacy_payment_type": "deprecated_since: v2.0",
       "payment_method": "required since v2.0"
     }
     ```