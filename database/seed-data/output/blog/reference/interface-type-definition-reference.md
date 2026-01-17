# **[Pattern] Interface Type Definition: Reference Guide**

---

## **1. Overview**
The **Interface Type Definition** pattern standardizes shared data schemas across microservices and APIs by defining reusable **interface types** that abstract common fields, reducing duplication and ensuring consistency. This pattern is ideal for scenarios where multiple entities or services share similar attributes (e.g., user roles, addresses, or product metadata).

Key benefits:
- **Reduces redundancy** by enforcing a shared contract for fields.
- **Improves maintainability**—updates to interface schema propagate automatically.
- **Enhances interoperability** between services via standardized data contracts.
- **Validates early** through schema enforcement (OpenAPI/Swagger, GraphQL interfaces, or Protobuf).

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Definition**
An **interface type** is a **non-instantiable schema** defining:
- **Required/mandatory fields** (e.g., `email` in a `User` interface).
- **Optional fields** (e.g., `phone` with a default value).
- **Data types** (e.g., `string`, `number`, `boolean`).
- **Constraints** (e.g., regex patterns, min/max lengths).

Interfaces **do not** include implementation logic (e.g., methods) but focus purely on **data structure**.

---

### **2.2 Schema Enforcement Options**
| **Technology**       | **How to Use**                                                                 | **Example**                                  |
|----------------------|-------------------------------------------------------------------------------|----------------------------------------------|
| **OpenAPI/Swagger**  | Define interfaces in `$ref` or separate schema files.                          | `type: object`, `properties: { email: { type: string } }` |
| **GraphQL**          | Use `interface` keyword with implementing types.                              | `interface User { id: ID!, email: String! }`  |
| **Protocol Buffers** | Define `.proto` messages as interfaces (via `syntax = "proto3"`).             | `message User { required string email = 1; }`|
| **JSON Schema**      | Use `$defs` for reusable interface schemas.                                    | `"$defs": { "Address": { "type": "object", ... }}` |

---

### **2.3 Design Principles**
1. **Granularity**:
   - Prefer smaller interfaces (e.g., `BaseUser`, `Address`) over monolithic ones.
   - Example:
     ```json
     // Avoid:
     { "User": { "id", "name", "email", "address" } }
     // Prefer:
     { "BaseUser": { "id", "email" }, "Address": { "street", "city" } }
     ```

2. **Backward Compatibility**:
   - Add optional fields (not required) to avoid breaking changes.
   - Example:
     ```json
     // Old: email (required)
     // New: email (required), phone (optional)
     ```

3. **Versioning**:
   - Tag interfaces with semantic versions (e.g., `v1/user.interface.json`).
   - Use branch strategies (e.g., `feature/address-v2`) for major updates.

4. **Tooling Integration**:
   - **Validation**: Use tools like [JSON Schema Validator](https://www.jsonschemavalidator.net/) or [GraphQL Syntax](https://astexplorer.net/).
   - **Codegen**: Generate TypeScript/Java clients from OpenAPI specs (e.g., `openapi-generator`).

---

## **3. Schema Reference Table**
Below are common interface types and their fields. Customize based on your domain.

| **Interface Name** | **Required Fields**               | **Optional Fields**               | **Data Type**       | **Description**                          |
|--------------------|------------------------------------|------------------------------------|---------------------|------------------------------------------|
| `BaseUser`         | `id`, `email`                     | `createdAt`, `lastLogin`           | `string`, `date`    | Core user attributes.                    |
| `Address`          | `street`, `city`                  | `state`, `postalCode`, `country`   | `string`            | Physical address.                        |
| `Role`             | `name`                             | `permissions`, `isAdmin`           | `string`, `boolean` | User permissions.                        |
| `Product`          | `sku`, `price`, `category`         | `description`, `stock`             | `string`, `number`  | E-commerce product.                     |
| `PaymentMethod`    | `type`                             | `cardLast4`, `expiryDate`          | `string`, `date`    | Payment details (masked).                |

---
**Note**: Replace placeholders with your actual field names/types. Use tools like [Swagger Editor](https://editor.swagger.io/) to visualize interfaces.

---

## **4. Query Examples**

### **4.1 OpenAPI Example (REST API)**
```yaml
paths:
  /users:
    get:
      summary: Retrieve users with shared interfaces
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      allOf:
        - $ref: '#/components/schemas/BaseUser'
        - type: object
          properties:
            phone:
              type: string
              pattern: "^\\+?[0-9]{10,15}$"
```

**Request**:
```bash
GET /users
```

**Response**:
```json
[
  {
    "id": "u123",
    "email": "user@example.com",
    "createdAt": "2023-01-01",
    "phone": "+1234567890"
  }
]
```

---

### **4.2 GraphQL Example**
```graphql
type Query {
  users: [User!]!
}

interface User @extends {
  id: ID!
  email: String!
}

type RegularUser implements User {
  id: ID!
  email: String!
  phone: String
}

type AdminUser implements User {
  id: ID!
  email: String!
  permissions: [String!]!
}
```

**Query**:
```graphql
query {
  users {
    id
    ... on AdminUser {
      permissions
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "users": [
      { "id": "u123", "email": "user@example.com" },
      { "id": "u456", "email": "admin@example.com", "permissions": ["edit", "delete"] }
    ]
  }
}
```

---

### **4.3 Protocol Buffers Example**
```proto
syntax = "proto3";

message BaseUser {
  string id = 1;
  string email = 2;
}

message User extends BaseUser {
  string phone = 3;
}

service UserService {
  rpc GetUsers (GetUsersRequest) returns (UserList);
}
```

**Compile & Use**:
```bash
protoc --go_out=. user.proto
```

---

## **5. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                          |
|---------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **DTO (Data Transfer Object)** | Encapsulates data for API requests/responses.                            | When interfaces need extension for API contracts. |
| **Event Sourcing**        | Logs state changes as events with shared schemas.                          | For audit trails with consistent event formats. |
| **Schema Registry (Confluent)** | Centralized schema management (Avro/Protobuf).                           | When multiple teams collaborate on schemas. |
| **Entity-Attribute-Value (EAV)** | Flexible schema for dynamic attributes (e.g., user preferences).          | When attributes are highly variable.     |
| **API Gateway**           | Routes requests/responses with standardized interfaces.                   | To unify heterogeneous microservices.    |

---

## **6. Best Practices & Anti-Patterns**

### **Best Practices**
✅ **Use interfaces for commonality**:
   - Example: Reuse `Address` across `User`, `Order`, and `Shipment`.

✅ **Document changes**:
   - Maintain a `CHANGELOG.md` for interface updates (e.g., `v2: Added zipCode`).

✅ **Leverage tooling**:
   - Automate validation with CI/CD (e.g., GitHub Actions for JSON Schema checks).

✅ **Start small**:
   - Begin with 2–3 core interfaces (e.g., `User`, `Product`) before scaling.

### **Anti-Patterns**
❌ **Over-engineering**:
   - Avoid creating 50+ tiny interfaces for trivial fields (e.g., `UserName`).

❌ **Circular dependencies**:
   - Example: `User` depends on `Address`, which depends on `User` (breaks backward compatibility).

❌ **Ignoring versioning**:
   - Force-breaking changes (e.g., renaming `email` to `userEmail`) without deprecation.

---

## **7. Tools & Libraries**
| **Tool/Library**          | **Purpose**                                      | **Link**                                  |
|---------------------------|--------------------------------------------------|-------------------------------------------|
| OpenAPI Generator         | Codegen clients from OpenAPI specs.              | [https://openapi-generator.tech/](https)   |
| JSON Schema Validator     | Validate JSON against interface schemas.         | [https://www.jsonschemavalidator.net/](https)|
| Protobuf Compiler         | Compile `.proto` files to language bindings.    | [https://developers.google.com/protocol-buffers](https)|
| GraphQL Code Generator    | Generate types from GraphQL schemas.             | [https://graphql-code-generator.com/](https) |
| Swagger UI                | Visualize and test OpenAPI interfaces.           | [https://swagger.io/tools/swagger-ui/](https)|

---
## **8. Example Workflow**
1. **Define Interface**:
   ```json
   // shared/interfaces/user.json
   {
     "$id": "user.interface.json",
     "type": "object",
     "properties": {
       "id": { "type": "string", "format": "uuid" },
       "email": { "type": "string", "format": "email" }
     },
     "required": ["id", "email"]
   }
   ```
2. **Reference in Service**:
   ```yaml
   # serviceA/openapi.yml
   components:
     schemas:
       User: $ref: ../shared/interfaces/user.json
   ```
3. **Validate**:
   ```bash
   npm install @apidevtools/swagger-cli
   swagger-cli validate serviceA/openapi.yml
   ```

---
**Next Steps**:
- [ ] Audit existing APIs for shared fields.
- [ ] Create a shared schema repository (e.g., GitHub/GitLab).
- [ ] Train teams on interface versioning.