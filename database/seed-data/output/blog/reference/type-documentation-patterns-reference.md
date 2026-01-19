**[Pattern] Type Documentation Reference Guide**

---

### **1. Overview**
The **Type Documentation** pattern provides a structured way to document data types, their fields, constraints, and usage examples within an API or system. It ensures consistency by defining schemas (e.g., JSON Schema, OpenAPI) while offering clear, consumable explanations for developers. This pattern is especially useful for:
- **APIs** (REST, GraphQL) requiring consistent request/response validation.
- **Microservices** with interdependent data contracts.
- **Internal systems** where developer onboarding relies on shared type definitions.

Key benefits:
- **Self-documenting APIs**: Reduces reliance on external docs.
- **Validation**: Enforces data integrity via schema constraints.
- **Tooling**: Integrates with IDEs, testing frameworks, and OpenAPI clients.

---

### **2. Schema Reference**
Below is a standardized schema table for documenting types. Use this template to define types with metadata and examples.

| **Field**               | **Description**                                                                                     | **Example Values**                                                                                     | **Constraints (Optional)** | **Default** |
|--------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|----------------------------|-------------|
| `type`                   | Data type (e.g., `object`, `array`, `string`).                                                     | `integer`, `boolean`, `null`                                                                          | Valid types only          | —           |
| `name`                   | Human-readable name (e.g., `UserProfile`, `OrderItem`).                                             | `PaymentDetails`                                                                                      | Max 100 chars              | —           |
| `description`            | Clear explanation of purpose/usage.                                                                | `"User’s contact information for notifications."`                                                     | —                          | —           |
| `fields`                 | Nested objects or arrays (recursively documented).                                                 | `{ "id": { "type": "string", "description": "Unique identifier" } }`                                  | —                          | —           |
| `required`               | Array of field names that must be provided.                                                         | `["email", "createdAt"]`                                                                             | —                          | `[]`        |
| `examples`               | Real-world usage examples (valid/invalid).                                                         | JSON snippets                                                                                          | —                          | `{}`        |
| `constraints`            | Custom rules (e.g., `minLength: 5`, `enum: ["active", "inactive"]`).                              | `{ "minItems": 1, "pattern": "^[A-Z]{3}$" }`                                                          | —                          | `{}`        |
| `version`                | Schema version for backward compatibility.                                                          | `1.0`                                                                                                  | SemVer format              | `1.0`       |
| `tags`                   | Categorization (e.g., `auth`, `payment`).                                                          | `["finance", "user"]`                                                                                 | —                          | `[]`        |
| `deprecated`             | Boolean or date indicating if this type is obsolete.                                               | `true` or `"2023-12-01"`                                                                               | —                          | `false`     |

---
#### **Example Schema Table (User Type)**
| **Field**    | **Description**                          | **Example Values**                          | **Constraints**       | **Default** |
|--------------|------------------------------------------|---------------------------------------------|-----------------------|-------------|
| `type`       | `object`                                 | —                                           | —                     | —           |
| `name`       | `User`                                   | —                                           | —                     | —           |
| `description`| `"Core user entity with authentication."` | —                                           | —                     | —           |
| `fields`     |                                         | `{ "id": { "type": "string", "required": true }, "email": { "type": "string", "constraints": { "format": "email" } } }` | —           | —           |
| `required`   | `["id", "email"]`                        | —                                           | —                     | —           |
| `examples`   |                                         | `{"id": "u123", "email": "user@example.com", "roles": ["admin"]}` | —           | `{}`        |
| `version`    | `2.1`                                    | —                                           | —                     | `1.0`       |

---

### **3. Query Examples**
#### **A. Defining a Type (JSON Schema)**
```json
{
  "type": "object",
  "name": "PaymentTransaction",
  "description": "Audit log for financial transactions.",
  "fields": {
    "transactionId": { "type": "string", "required": true },
    "amount": { "type": "number", "constraints": { "minimum": 0.01 } },
    "status": {
      "type": "string",
      "constraints": {
        "enum": ["pending", "completed", "failed"]
      }
    }
  },
  "examples": [
    {
      "transactionId": "txn_abc123",
      "amount": 99.99,
      "status": "completed"
    },
    {
      "transactionId": "txn_def456",
      "amount": -50,  // ← Invalid (violates `minimum` constraint)
      "status": "completed"
    }
  ]
}
```

#### **B. Using Type Documentation in OpenAPI**
```yaml
openapi: 3.0.0
components:
  schemas:
    Order:
      type: object
      name: "Order"
      description: "Customer order with itemized details."
      required:
        - orderId
        - customerId
      properties:
        orderId:
          type: string
          description: "UUIDv4 identifier."
        items:
          type: array
          items:
            $ref: '#/components/schemas/OrderItem'
        status:
          type: string
          enum: ["draft", "paid", "shipped"]
components:
  schemas:
    OrderItem:
      type: object
      description: "Line-item in an order."
      properties:
        productId:
          type: string
          format: uuid
        quantity:
          type: integer
          minimum: 1
```

#### **C. Validating Requests with Type Documentation**
Use tools like:
- **JSON Schema Validator** (e.g., [Ajv](https://ajv.js.org/)):
  ```javascript
  const schema = { ... }; // From Type Documentation
  const Ajv = require('ajv');
  const validate = new Ajv().compile(schema);
  const isValid = validate({ id: "u123", email: "invalid" }); // Returns false.
  ```
- **OpenAPI Clients** (e.g., [Swagger UI](https://swagger.io/tools/swagger-ui/)) to auto-generate and validate requests.

---

### **4. Implementation Details**
#### **Key Concepts**
1. **Schema Inheritance**:
   Use `$ref` in JSON Schema/OpenAPI to avoid duplication (e.g., `User` and `Admin` sharing a base `User` type).
   ```json
   {
     "$ref": "#/components/schemas/User"
   }
   ```

2. **Versioning**:
   - **Backward Compatibility**: Add optional fields or change `type` from `required` to `nullable`.
   - **Breaking Changes**: Increment major version (e.g., `1.0` → `2.0`) and document deprecation timelines.

3. **Tooling Integration**:
   - **IDE Support**: Generate code stubs (e.g., TypeScript interfaces from JSON Schema with tools like [json-schema-to-typescript](https://github.com/vega/json-schema-to-typescript)).
   - **Testing**: Use schemas to mock API responses (e.g., [Postman’s Schema Validation](https://learning.postman.com/docs/designing-and-developing-your-api/validating-your-api/)).

4. **Examples Best Practices**:
   - Include **valid** and **invalid** examples to highlight constraints.
   - Use real-world data where possible (e.g., email formats, UUIDs).

#### **Common Pitfalls**
- **Over-constraining**: Avoid overly restrictive fields (e.g., `maxLength: 1` for `description`).
- **Ignoring Versioning**: Skipping versioning can lead to breaking changes without notice.
- **Poor Examples**: Vague examples (e.g., `{ "id": "1" }`) don’t help developers.

---

### **5. Related Patterns**
1. **[API Versioning](https://github.com/grpc/grpc-java/blob/master/documentation/versioning.md)**
   - Combine with Type Documentation to manage schema evolution across versions.

2. **[OpenAPI/Swagger](https://swagger.io/specification/)**
   - Extend your type documentation with OpenAPI for API contract management.

3. **[GraphQL Schema Stitching](https://www.apollographql.com/docs/guides/schema-stitching/)**
   - Useful for federating types across microservices with GraphQL.

4. **[Event-Driven Data Contracts](https://www.eventstore.com/blog/event-driven-data-contracts/)**
   - Document types for event schemas (e.g., `OrderCreated`, `PaymentProcessed`).

5. **[Postman/Newman for API Testing](https://learning.postman.com/docs/writing-scripts/script-reusable-components/)**
   - Validate types in Postman collections using schema definitions.

---
### **6. Further Reading**
- [JSON Schema Specification](https://json-schema.org/understanding-json-schema/)
- [OpenAPI 3.0 Spec](https://spec.openapis.org/oas/v3.0.3)
- [TypeScript Interfaces from JSON Schema](https://medium.com/@solomonjohnson1/using-json-schema-to-generate-typescript-interfaces-617bfb9f26a6)