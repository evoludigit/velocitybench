# **[Pattern] Monolith Validation Reference Guide**

---

## **Overview**
**Monolith Validation** is a design pattern used to centrally manage validation logic for an entire application (or "monolith") in a single, authoritative validation service. This pattern decouples validation logic from business logic, ensuring consistency across microservices, APIs, and event-driven workflows. Unlike decentralized validation (where validation rules are scattered across services), Monolith Validation consolidates rules in a defined schema, reducing redundancy and improving enforceability. It is particularly useful in **monolithic architectures**, **polyglot persistence systems**, or any scenario where strict validation consistency is critical (e.g., financial transactions, data pipelines, or API contracts).

This guide covers the **schema design**, **implementation details**, **query examples**, and **integration strategies** for Monolith Validation. It assumes familiarity with **JSON Schema**, **OpenAPI/Swagger**, or similar validation standards.

---

## **Schema Reference**
The Monolith Validation pattern relies on a structured **validation schema** (typically JSON Schema) that defines:
- **Core validation rules** (e.g., required fields, data types, constraints).
- **Domain-specific rules** (e.g., business invariants like "account balance ≥ 0").
- **Dynamic validation** (e.g., conditional rules based on context).

Below is the **core schema structure**:

| **Schema Element**       | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `schemaVersion`           | Version of the validation schema (semantic versioning recommended).                                                                                                                                     | `"2.0.0"`                                                                                      |
| `metadata`                | Non-validating metadata (e.g., schema owner, last updated).                                                                                                                                                | `{ "owner": "finance-team", "lastUpdated": "2023-10-01" }`   |
| `entity`                  | Defines an entity (e.g., `User`, `Order`) and its validation rules.                                                                                                                                         | `"entity": "User"`                                                                              |
| `requiredFields`          | List of mandatory fields.                                                                                                                                                                                   | `[ "id", "email", "createdAt" ]`                                                                |
| `type`                    | Top-level data type (e.g., `object`, `array`).                                                                                                                                                           | `"type": "object"`                                                                             |
| `properties`              | Nested field definitions (type, format, min/max values, custom validators).                                                                                                                             | `{ "age": { "type": "integer", "minimum": 18 } }`                                               |
| `customValidators`        | Domain-specific rules (e.g., regex, business logic via functions).                                                                                                                                          | `{ "email": { "pattern": "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$" } }` |
| `contextualRules`         | Rules that depend on external context (e.g., "if `isPremium` = true, then `discount > 0.2`").                                                                                                      | `{ "rules": [ { "if": { "property": "isPremium", "equal": true }, "then": { "minimum": 0.2 } } ] }` |
| `validationGroups`        | Group rules by use case (e.g., `create`, `update`, `api`).                                                                                                                                               | `{ "groups": { "create": ["email", "password"], "update": ["name"] } }`                      |
| `errorMessages`           | Custom error messages for validation failures.                                                                                                                                                          | `{ "email": "Invalid email format." }`                                                          |
| `dependencies`            | Field dependencies (e.g., `country` requires `taxId`).                                                                                                                                                     | `{ "taxId": { "dependentSchema": { "if": { "property": "country", "equal": "US" }, "then": { "required": ["taxId"] } } }` |

---

### **Example Schema**
```json
{
  "schemaVersion": "2.0.0",
  "metadata": {
    "owner": "accounting",
    "lastUpdated": "2023-10-01"
  },
  "entity": "Invoice",
  "type": "object",
  "requiredFields": ["id", "customerId", "amount", "status"],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "customerId": { "type": "string", "pattern": "^CUST-[0-9]{8}$" },
    "amount": {
      "type": "number",
      "minimum": 0,
      "customValidators": {
        "fn": "validateCurrency",
        "args": ["USD"]
      }
    },
    "status": {
      "type": "string",
      "enum": ["draft", "pending", "paid", "void"],
      "default": "draft"
    }
  },
  "contextualRules": [
    {
      "if": { "property": "amount", "greaterThan": 10000 },
      "then": { "required": ["taxExempt"] }
    }
  ],
  "validationGroups": {
    "api": ["id", "customerId", "status"],
    "internal": ["amount", "taxExempt"]
  },
  "errorMessages": {
    "amount": "Amount must be a positive value in USD.",
    "status": "Invalid status."
  }
}
```

---

## **Implementation Details**
### **1. Core Components**
| **Component**            | **Purpose**                                                                                                                                                                                                 | **Implementation Notes**                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Validation Service**   | Centralized service that enforces the schema. Can be a library (e.g., AJV, Zod), a microservice, or a middleware layer.                                                                                  | - Use **AJV** for JSON Schema validation. <br> - For dynamic rules, embed a script engine (e.g., **Lua**, **JavaScript**). |
| **Schema Registry**      | Stores and version-controls schemas (e.g., Git, Confluent Schema Registry, AWS Glue).                                                                                                                | - Tag schemas by `schemaVersion`. <br> - Enable backward/forward compatibility.                                  |
| **Validator Client**     | Library or SDK that clients use to validate data against the schema.                                                                                                                                     | - Support **async validation** (e.g., for event-driven systems). <br> - Provide **bulk validation** for batches. |
| **Rule Engine Integration** | Optional: Integrate with rule engines (e.g., **Drools**, **Easy Rules**) for complex business logic.                                                                                                | - Use for **stateful validation** (e.g., multi-step approval workflows).                                       |
| **Audit Logging**        | Logs validation events (e.g., failures, schema changes) for compliance.                                                                                                                               | - Store in a **dedicated audit table** or **SIEM system**. <br> - Include `requestId`, `timestamp`, `schemaVersion`. |

---

### **2. Validation Workflow**
1. **Schema Definition**
   - Define the schema in the **Validation Service** or **Schema Registry**.
   - Example: `POST /v1/schemas` to register a new schema.

2. **Client Request**
   - Clients (e.g., APIs, services) include a `validationSchema` header or body parameter.
   - Example request:
     ```http
     POST /invoices
     Headers: X-Validation-Schema: "invoices/v1.json"
     Body: { "customerId": "CUST-12345678", "amount": 99.99 }
     ```

3. **Validation Execution**
   - The **Validator Client** fetches the schema (if not cached) and validates the payload.
   - Returns:
     - `200 OK` if valid.
     - `400 Bad Request` with details if invalid (e.g., `{ "errors": [ { "field": "amount", "message": "Must be ≥ 0" } ] }`).

4. **Error Handling**
   - Provide **granular error responses** (field-level, not just global).
   - Support **retries with corrected data** (e.g., via `Precondition-Fail`).

5. **Schema Evolution**
   - Use **backward-compatible changes** (e.g., adding optional fields).
   - Deprecate schemas via `deprecated: true` and redirect to newer versions.

---

### **3. Integration Strategies**
| **Scenario**               | **Implementation**                                                                                                                                                                                                 | **Example**                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **API Gateway**            | Validate requests/responses at the gateway using the Monolith Validation schema.                                                                                                                              | Use **Kong** or **Apigee** plugin to hook into AJV validation.                                   |
| **Event-Driven Systems**   | Validate events (e.g., Kafka topics) before processing.                                                                                                                                                     | Deploy a **Kafka Connect** validator or use **Debezium**-integrated validation.               |
| **Database Layer**         | Enforce constraints in the DB (e.g., PostgreSQL checks) but validate against the schema for flexibility.                                                                                                | Create triggers or use **JSONB validation** with `CHECK` constraints.                          |
| **Client-Side Validation** | Lightweight validation in UI/apps (e.g., React hooks) to improve UX, but **never trust** client-side validation—always validate server-side.                                                               | Use **Zod** or **Yup** for frontend, but enforce server-side with Monolith Validation.          |
| **CI/CD Pipeline**         | Validate schemas in CI to catch schema drift early.                                                                                                                                                           | Use **GitHub Actions** with AJV to lint schemas on PRs.                                         |

---

## **Query Examples**
### **1. Register a New Schema**
```http
POST /v1/schemas
Content-Type: application/json

{
  "name": "payment/v1",
  "schema": {
    "schemaVersion": "1.0.0",
    "entity": "Payment",
    "requiredFields": ["id", "amount", "currency"],
    "properties": {
      "amount": { "type": "number", "minimum": 0.01 },
      "currency": { "type": "string", "enum": ["USD", "EUR"] }
    }
  }
}
```
**Response:**
```json
{
  "id": "schema:payment:v1",
  "status": "active",
  "version": "1.0.0"
}
```

---

### **2. Validate a Payload**
```http
POST /v1/validate
Headers: X-Validation-Schema: "payment/v1"
Content-Type: application/json

{
  "id": "pay-123",
  "amount": -5.00,
  "currency": "USD"
}
```
**Response (Invalid):**
```json
{
  "errors": [
    {
      "field": "amount",
      "message": "Must be ≥ 0.01"
    }
  ],
  "schemaVersion": "1.0.0"
}
```

---

### **3. Batch Validation**
```http
POST /v1/batch-validate
Headers: X-Validation-Schema: "users/v2"
Content-Type: application/json

{
  "payloads": [
    { "id": "user1", "age": 17 },
    { "id": "user2", "age": 25 }
  ]
}
```
**Response:**
```json
{
  "valid": 1,
  "invalid": 1,
  "errors": [
    {
      "payload": { "id": "user1", "age": 17 },
      "errors": [
        { "field": "age", "message": "Must be ≥ 18" }
      ]
    }
  ]
}
```

---

### **4. List Schemas**
```http
GET /v1/schemas
```
**Response:**
```json
{
  "schemas": [
    { "name": "users/v1", "version": "1.0.0", "lastUpdated": "2023-09-15" },
    { "name": "payments/v1", "version": "1.0.0", "lastUpdated": "2023-10-01" }
  ]
}
```

---

## **Related Patterns**
1. **Schema Registry**
   - **Purpose**: Centralized storage for schemas (e.g., Confluent, AWS Glue).
   - **Relation**: Monolith Validation relies on a Schema Registry to manage schema versions and dependencies.

2. **OpenAPI Validation**
   - **Purpose**: Validate API requests/responses against Swagger/OpenAPI specs.
   - **Relation**: Pair with Monolith Validation for API-specific rules (e.g., query params, headers).

3. **Event Validation**
   - **Purpose**: Validate event messages (e.g., Kafka, RabbitMQ) before processing.
   - **Relation**: Use Monolith Validation to enforce event schemas in real-time.

4. **Canonical Data Model**
   - **Purpose**: Define a single source of truth for data formats across services.
   - **Relation**: Monolith Validation schemas can serve as the canonical model for validation.

5. **Policy as Code**
   - **Purpose**: Embed validation rules in infrastructure-as-code (e.g., Terraform, Ansible).
   - **Relation**: Use Monolith Validation schemas to enforce policies dynamically.

6. **Async Validation**
   - **Purpose**: Validate data asynchronously (e.g., after DB write).
   - **Relation**: Implement with **background workers** or **event listeners** that trigger validation.

---

## **Best Practices**
1. **Minimize Schema Bloat**
   - Split large schemas into **modular entities** (e.g., `User`, `OrderItem`).
   - Use **references** (e.g., `$ref`) to avoid duplication.

2. **Versioning Strategy**
   - Follow **semantic versioning** (`MAJOR.MINOR.PATCH`).
   - Document **breaking changes** clearly.

3. **Performance**
   - Cache schemas client-side to reduce registry calls.
   - Use **incremental validation** for large payloads.

4. **Testing**
   - Write **unit tests** for edge cases (e.g., `null` values, empty strings).
   - Test **schema evolution** (e.g., backward compatibility).

5. **Security**
   - Authenticate **schema registry access** (e.g., OAuth2).
   - Validate schemas **on write** to prevent malicious payloads.

6. **Observability**
   - Monitor **validation failures** (e.g., metrics for `400 Bad Request`).
   - Log **schema changes** for audit trails.

---
**See Also**:
- [JSON Schema Specification](https://json-schema.org/)
- [AJV: Fast JSON Schema Validator](https://ajv.js.org/)
- [OpenAPI Specification](https://spec.openapis.org/)