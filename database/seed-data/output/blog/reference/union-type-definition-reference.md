# **[Pattern] Union Type Definition – Reference Guide**

---

## **Overview**
Union types in data modeling allow a field to accept multiple distinct types while enforcing type-specific properties at runtime. This pattern is particularly useful when working with **polymorphic data** (e.g., a JSON field that can represent either a `User`, `Product`, or `Order`). Unlike traditional types, a union type does not enforce a single schema—it instead aggregates multiple schemas under one field, often requiring additional logic (e.g., discrimination) to differentiate valid types.

Common use cases include:
- **API responses** that may vary by endpoint or payload variant.
- **Database records** with polymorphic relationships (e.g., `content` fields like text, images, or videos).
- **Event-driven systems** where an event type is unknown until runtime.

---

## **Implementation Details**

### **Key Concepts**
1. **Discriminator Field**
   A required field (e.g., `"__type"`) that identifies the concrete type of a union value. Example:
   ```json
   {
     "__type": "User",
     "id": "123",
     "username": "devuser"
   }
   ```

2. **Schema Composition**
   Each possible type in the union must define its own sub-schema. The union schema aggregates these sub-schemas.

3. **Validation**
   Tools like JSON Schema (`$union`) or GraphQL unions enforce type-specific rules (e.g., validating `User.email` only when `__type` is `"User"`).

4. **Field Overrides**
   Some fields (e.g., `__type`) may be **optional** or **read-only**, requiring custom logic in client libraries.

### **Supported Formats**
| Format       | Implementation Notes                                                                 |
|--------------|--------------------------------------------------------------------------------------|
| **JSON Schema** | Uses `$defs` and `$union`; discriminator fields are typically string literals.      |
| **GraphQL**   | Uses `union` types and interfaces with `@type` directives.                          |
| **Protobuf**  | Requires manual discrimination via `oneof` or a type field (e.g., `string type = 1`). |
| **OpenAPI 3.0** | Uses `oneOf` or `anyOf` with discriminator logic in the server.                       |

---

## **Schema Reference**

### **Example Union Schema (JSON Schema)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "__type": {
      "type": "string",
      "enum": ["User", "Product", "Order"],
      "description": "Discriminator field for the union type."
    },
    "commonField": {
      "description": "Shared property across all union types."
    }
  },
  "required": ["__type"],
  "oneOf": [
    {
      "properties": { "__type": { "const": "User" } },
      "required": ["__type"],
      "properties": {
        "id": { "type": "string" },
        "username": { "type": "string" }
      }
    },
    {
      "properties": { "__type": { "const": "Product" } },
      "required": ["__type"],
      "properties": {
        "sku": { "type": "string" },
        "price": { "type": "number" }
      }
    },
    {
      "properties": { "__type": { "const": "Order" } },
      "required": ["__type"],
      "properties": {
        "orderId": { "type": "string" },
        "items": { "type": "array" }
      }
    }
  ]
}
```

### **GraphQL Union Example**
```graphql
type User {
  id: ID!
  username: String!
}

type Product {
  sku: ID!
  price: Float!
}

union Item = User | Product;

type Query {
  getItem(id: ID!): Item
}
```

### **Protobuf Example**
```protobuf
syntax = "proto3";

message User {
  string id = 1;
  string username = 2;
}

message Product {
  string sku = 1;
  float price = 2;
}

message Item {
  oneof type {
    User user = 1;
    Product product = 2;
  }
}
```

---

## **Query Examples**

### **1. Validate a Union Type (JSON Schema)**
**Input:**
```json
{
  "__type": "User",
  "id": "123",
  "username": "valid_user"
}
```
**Validation:**
- Passes (`__type` matches `User`, all required fields present).

**Invalid Input:**
```json
{
  "__type": "User",
  "price": 9.99  // Invalid for "User" type
}
```
**Error:** `Additional property "price" not allowed` (assuming schema restricts it).

---

### **2. GraphQL Query**
```graphql
query {
  getItem(id: "user_456") {
    ... on User {
      username
    }
    ... on Product {
      sku
    }
  }
}
```
**Response:**
```json
{
  "data": {
    "getItem": {
      "username": "devuser"  // Fields are resolved based on actual type
    }
  }
}
```

---

### **3. Protobuf Decode (Python)**
```python
from generated_pb2 import Item

def deserialize(item_proto):
    if item_proto.HasField("user"):
        return item_proto.user
    if item_proto.HasField("product"):
        return item_proto.product
    raise ValueError("Unknown type")
```

---

## **Related Patterns**

| Pattern               | Description                                                                                     | When to Use                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Polymorphic Records** | Extends union types with dynamic field validation (e.g., for nested polymorphic data).        | When a field’s structure depends on a parent’s type (e.g., `Event` with `User`/`Product` payloads). |
| **Discriminated Unions** (TS/JS) | TypeScript-style discriminated unions with type guards.                                         | When using strongly-typed languages like TypeScript/JavaScript.             |
| **Schema Registry**   | Centralized version control for evolving union schemas.                                          | In microservices where schemas evolve independently.                          |
| **Type Safety Wrappers** | Encapsulates unions in a generic wrapper (e.g., `Result<T>`).                                   | For error handling in APIs where success/failure payloads differ.          |

---

## **Best Practices**

1. **Explicit Discriminator**
   Always use a clear discriminator field (e.g., `__type`, `_kind`) to avoid runtime ambiguity.

2. **Document Constraints**
   Clearly specify which fields are required for each union type (e.g., "Product.price is mandatory").

3. **Versioning**
   For backward compatibility, add optional fields (e.g., `"version": "2.0"`) to transition schemas.

4. **Error Handling**
   Validate discriminators server-side to prevent malformed payloads.

5. **Tooling**
   Use tools like:
   - **JSON Schema:** [`ajv`](https://ajv.js.org/) for validation.
   - **GraphQL:** [`graphql-codegen`](https://graphql-codegen.com/) for type safety.
   - **Protobuf:** [`protoc`](https://developers.google.com/protocol-buffers) with plugins.

---
**Length:** ~1,000 words | **Scannable Sections:** Key concepts, schema snippets, query examples.