# **[Pattern] Input Type Definition (ITD) Reference Guide**

---
## **Overview**
The **Input Type Definition (ITD)** pattern defines standardized, reusable input schemas for APIs, microservices, or event-driven systems. ITDs ensure consistent data contracts across services by enforcing structure, validation, and metadata for input payloads (e.g., API requests, database schemas, or message payloads). This pattern is critical for systems requiring tight data cohesion, such as **REST APIs, GraphQL APIs, event sourcing, or data pipelines**.

ITDs deliver:
- **Schema validation**: Enforces constraints (e.g., field types, required fields) to prevent malformed data.
- **Reusability**: Centralizes input definitions, avoiding duplication across services.
- **Documentation**: Acts as self-documenting contracts for developers and consumers.
- **Tooling support**: Integrates with OpenAPI/Swagger, JSON Schema, Protocol Buffers, or Avro for validation and serialization.

Common use cases include:
- API gateway input validation.
- Event-driven systems (e.g., Kafka, RabbitMQ).
- Microservices communication.
- Database migrations (e.g., Prisma, TypeORM).

---

## **Schema Reference**
Below is a standardized schema for defining ITDs, using **JSON Schema 2020-12** as the underlying format. Key fields are highlighted for clarity.

| **Field**               | **Type**       | **Description**                                                                                     | **Required?** | **Example Value**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|----------------|---------------------------------------------|
| `@context`              | `string[]`     | JSON-LD or OpenAPI/Swagger context references (for tooling integration).                            | Optional       | `["https://schema.org"]`                     |
| `title`                 | `string`       | Human-readable name of the input type.                                                             | **Yes**        | `"CreateUserRequest"`                       |
| `description`           | `string`       | Free-form documentation (markdown supported).                                                     | Optional       | `"Input for user registration API."`         |
| `version`               | `string`       | Semantic version of the ITD (e.g., `v1.0.0`).                                                      | Optional       | `"1.0.0"`                                    |
| `type`                  | `string`       | `"object"` (default) or `"array"` for collections.                                                  | Optional       | `"object"`                                   |
| `properties`            | `object`       | Nested schema definition (key: field name, value: sub-schema).                                     | Optional       | `{ "email": { "type": "string", "format": "email" } }` |
| `required`              | `string[]`     | List of mandatory fields.                                                                           | Optional       | `["email", "password"]`                     |
| `examples`              | `any[]`        | Example payloads (validates against the schema).                                                    | Optional       | `[{ "email": "test@example.com" }]`         |
| `additionalProperties`  | `boolean`      | Enforce closure: `false` (strict schema) or `true` (allow extra fields).                         | Optional       | `false`                                      |
| `allOf`/`anyOf`/`oneOf` | `object[]`     | Combines schemas (e.g., `allOf` for intersection types).                                            | Optional       | `[{ "type": "object" }, { "properties": {...} }]` |
| `deprecated`            | `boolean`      | Marks the ITD as obsolete.                                                                          | Optional       | `true`                                       |
| `extends`               | `string`       | References another ITD (e.g., `"extends": "#/definitions/UserBase"`).                             | Optional       | `"#/definitions/BasePayload"`                |
| `securitySchemes`       | `object`       | OpenAPI security schemes (if used with API gateways).                                              | Optional       | `{ "bearerAuth": { ... } }`                  |

---

### **Field-Specific Validation Rules**
| **Field**               | **Constraints**                                                                                     | **Notes**                                  |
|-------------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `type: string`          | Must be `"string"`, `"number"`, `"integer"`, `"boolean"`, `"array"`, or `"object"`.                  | `"null"` is also valid.                     |
| `format`                | For strings: `"email"`, `"uuid"`, `"date"`, etc. (see [IANA formats](https://www.iana.org/assignments/media-types/media-types.xhtml)). | Custom formats can be defined via `pattern`.|
| `enum`                  | Limits values to a closed list (e.g., `["active", "inactive"]`).                                   | Conflicts with `default`.                   |
| `default`               | Provides a fallback value if the field is omitted.                                                   | Can be `null`.                              |
| `pattern`               | Regex for string validation (e.g., ` "^[A-Za-z]+$"`).                                               | Requires `type: "string"`.                  |
| `minimum`/`maximum`     | For numbers: enforces bounds (e.g., `minimum: 18`).                                                  | Exclusive bounds: `exclusiveMinimum: true`. |
| `minLength`/`maxLength` | For strings: enforces length constraints.                                                          | Example: `minLength: 8`.                   |

---

## **Query Examples**
### **1. Defining an ITD for an API Request**
Below is a complete ITD for a `CreateUserRequest` payload, using JSON Schema syntax with ITD conventions.

```json
{
  "@context": ["https://json-schema.org/draft/2020-12/schema"],
  "title": "CreateUserRequest",
  "description": "Input for creating a new user in the system. Supports email, password, and optional metadata.",
  "version": "1.0.0",
  "type": "object",
  "required": ["email", "password"],
  "properties": {
    "email": {
      "type": "string",
      "format": "email",
      "description": "User's email address."
    },
    "password": {
      "type": "string",
      "minLength": 8,
      "pattern": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,}$",
      "description": "Password must include letters and numbers."
    },
    "metadata": {
      "type": "object",
      "properties": {
        "preferences": {
          "type": "object",
          "default": { "theme": "light" }
        }
      },
      "additionalProperties": false
    }
  },
  "examples": [
    {
      "email": "user@example.com",
      "password": "SecurePass123"
    }
  ]
}
```

### **2. Extending an ITD**
Reuse an existing schema by extending it:

```json
{
  "title": "CreatePremiumUserRequest",
  "extends": "#/definitions/CreateUserRequest",
  "properties": {
    "tier": {
      "type": "string",
      "enum": ["basic", "premium", "enterprise"]
    }
  },
  "required": ["tier"]
}
```

### **3. Validating an Input Payload**
Use tools like:
- **Ajv** (JavaScript): `ajv.validate(schema, payload)`
- **JSON Schema Validator (JS)**: `jsonschema.validate(payload, schema)`
- **OpenAPI Generator**: For API gateway validation.

**Example Validation (Python):**
```python
from jsonschema import validate, ValidationError

schema = {...}  # ITD from above
payload = {
  "email": "user@example.com",
  "password": "Secure123",
  "metadata": {"preferences": {"theme": "dark"}}
}

try:
  validate(instance=payload, schema=schema)
  print("Valid!")
except ValidationError as e:
  print(f"Invalid: {e.message}")
```

---

## **Implementation Details**
### **Key Concepts**
1. **Versioning**:
   - Use semantic versioning (`MAJOR.MINOR.PATCH`) for ITDs.
   - Document breaking changes in the `CHANGELOG.md`.
   - Example: `v2.0.0` breaks backward compatibility; `v1.1.0` adds optional fields.

2. **Tooling Integration**:
   - **OpenAPI/Swagger**: Map ITDs to `requestBody` schemas.
     ```yaml
     components:
       schemas:
         CreateUserRequest:  # <-- ITD reference
           $ref: "#/definitions/CreateUserRequest"
     ```
   - **GraphQL**: Use ITDs to define input objects.
     ```graphql
     input CreateUserInput {
       email: String! @validate(email: true)
       password: String! @validate(minLength: 8)
     }
     ```
   - **Event Systems**: Serialize ITDs to **Avro** or **Protocol Buffers** for efficiency.
     ```avro
     {
       "name": "CreateUserRequest",
       "type": "record",
       "fields": [
         {"name": "email", "type": "string"}
       ]
     }
     ```

3. **Performance Considerations**:
   - **Caching**: Cache compiled schemas (e.g., AJV’s `compile` method).
   - **Inline vs. External**: Embed small ITDs in code; reference large ones externally (e.g., Git submodules).

4. **Error Handling**:
   - Provide **human-readable errors** (e.g., `"Missing required field: password"`).
   - Log validation failures with timestamps and request IDs for debugging.

---

### **Best Practices**
| **Practice**               | **Guideline**                                                                                     |
|-----------------------------|---------------------------------------------------------------------------------------------------|
| **Naming Conventions**      | Use `PascalCase` for ITDs (e.g., `CreateOrderRequest`).                                           |
| **Documentation**           | Include examples, constraints, and real-world usage in the ITD’s `description`.                    |
| **Tooling**                | Automate validation in CI/CD (e.g., GitHub Actions with `ajv-cli`).                               |
| **Deprecation**             | Mark deprecated ITDs with `deprecated: true` and redirect to newer versions.                       |
| **Security**               | Avoid exposing sensitive fields (e.g., `password`) in examples.                                   |
| **Testing**                | Write unit tests for edge cases (e.g., empty strings, malformed JSON).                            |

---

## **Query Examples: Advanced**
### **1. Union Types (GraphQL-like)**
Combine multiple ITDs into a single input:
```json
{
  "$schema": "http://json-schema.org/draft/2019-09/schema",
  "oneOf": [
    { "$ref": "#/definitions/CreateUserRequest" },
    { "$ref": "#/definitions/UpdateUserRequest" }
  ]
}
```

### **2. Conditional Fields**
Use `if`/`then`/`else` (JSON Schema 2020-12):
```json
{
  "properties": {
    "userType": {
      "type": "string",
      "enum": ["admin", "user"]
    },
    "role": {
      "if": { "properties": { "userType": { "const": "admin" } } },
      "then": { "type": "string" }
    }
  }
}
```

### **3. Referencing External ITDs**
Link to ITDs stored in a central registry (e.g., GitHub):
```json
{
  "$ref": "https://raw.githubusercontent.com/org/itd-repo/main/definitions/UserBase.json#/definitions/UserBase"
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                  |
|---------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **[Output Type Definition](output-type-definition.md)** | Mirrors ITD for output payloads (responses/events).                                                  | For consistent return types across services.     |
| **[Data Migration Pattern](data-migration.md)**          | Uses ITDs to validate schema changes in databases.                                                   | When migrating from SQL to NoSQL or vice versa. |
| **[API Gateway Pattern](api-gateway.md)**                | Validates ITDs at the gateway layer before routing.                                                  | For centralized request validation.             |
| **[Event Sourcing](event-sourcing.md)**                  | ITDs define event payload schemas (e.g., `UserCreatedEvent`).                                      | For audit logs and CQRS.                       |
| **[Schema Registry](schema-registry.md)**               | Central repository for ITDs (e.g., Confluent Schema Registry).                                      | For event-driven systems with Avro/Protobuf.    |
| **[OpenAPI Specification](openapi.md)**                   | Extends ITDs with API-specific metadata (paths, security).                                          | For RESTful APIs.                               |
| **[GraphQL Input Types](graphql-input-types.md)**         | Maps ITDs to GraphQL `input` types.                                                                | For GraphQL APIs.                               |

---

## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                                     | **Solution**                                      |
|-------------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **Validation fails**                | Schema mismatch between ITD and payload.                                                          | Check `required` fields and `type` constraints.    |
| **Performance bottleneck**          | Schema compilation overhead in runtime.                                                          | Pre-compile schemas (e.g., AJV).                  |
| **Tooling conflicts**               | Incompatible JSON Schema versions (e.g., Draft 7 vs. 2020-12).                                   | Standardize on Draft 2020-12.                     |
| **Large payloads**                  | ITD defines unnecessary fields.                                                                   | Use `additionalProperties: false` and split ITDs.|
| **Deprecated ITD in production**    | Legacy code still uses old schemas.                                                                | Gracefully deprecate with `deprecated: true`.     |

---

## **Further Reading**
1. **[JSON Schema Specification](https://json-schema.org/)** – Core syntax and features.
2. **[OpenAPI 3.0 Spec](https://swagger.io/specification/)** – API schema integration.
3. **[Protocol Buffers](https://developers.google.com/protocol-buffers)** – Efficient serialization.
4. **[Avro Schema](https://avro.apache.org/docs/current/spec.html)** – Event-driven data formats.