# **[Pattern] Response Formatting and Serialization Reference Guide**

---

## **Overview**
The **Response Formatting and Serialization** pattern ensures that database query results are consistently transformed into structured JSON responses adhering to a **GraphQL schema** and standardized response format. This pattern standardizes output, reduces inconsistency in API responses, and ensures backward compatibility when schema changes occur. It bridges raw database responses (e.g., SQL tables, ORM objects, or denormalized data) with GraphQL’s type system, handling edge cases like missing fields, nested relationships, and conditional formatting while maintaining performance and security.

### **Key Objectives**
- **Schema Alignment**: Map database models to GraphQL types with explicit field mappings.
- **Consistent Formatting**: Enforce a standardized response structure (e.g., pagination, error handling, metadata).
- **Efficient Serialization**: Optimize object-to-JSON conversion to avoid redundant processing.
- **Relationship Handling**: Resolve nested queries (e.g., `@hasMany`, `@belongsTo`) or eager-load data where required.
- **Edge Case Handling**: Null values, default values, and conditional formatting (e.g., timestamps, currency).
- **Performance**: Minimize database round-trips by batching queries or using GraphQL’s `include`/`exclude` directives.

---

## **Schema Reference**
The following table defines the core structure of serialized responses, including required and optional fields.

| **Field**               | **Type**          | **Description**                                                                                     | **Example**                          | **Notes**                                  |
|-------------------------|-------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|--------------------------------------------|
| **`data`**              | Object            | Root payload containing response data.                                                               | `{ user: { ... }, products: [...] }`   | Required. Contains schema-defined types.   |
| **`errors`**            | Array[Error]      | Array of error objects (if any).                                                                     | `[{ message: "Field missing", code: 400 }]` | Optional; omitted if no errors.          |
| **`extensions`**        | Object            | Metadata (e.g., performance metrics, tracing IDs).                                                 | `{ executionTime: "5ms" }`           | Optional; vendor-specific.                |
| **`pagination`**        | Object            | Pagination metadata (for list queries).                                                              | `{ offset: 0, limit: 10, total: 50 }` | Optional; populated when applicable.       |
| **`metadata`**          | Object            | Custom context (e.g., `isAnonymous`, `currency`).                                                  | `{ currency: "USD", lastUpdated: "2024-01-01" }` | Optional. |

### **Schema-Specific Types**
Each GraphQL type in the schema maps to a structured JSON object. Below are examples for common types:

| **GraphQL Type** | **Serialized JSON Structure**                                                                 | **Notes**                                  |
|------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------|
| **`User`**       | `{ id: "123", name: "Alice", email: "alice@example.com", createdAt: "2024-01-01T00:00:00Z" }` | Required fields: `id`, `name`.             |
| **`Product`**    | `{ sku: "P100", price: 9.99, attributes: { color: "blue", weight: 500 } }`                     | Nested objects are flattened in JSON.      |
| **`Order`**      | `{ orderId: "ORD456", items: [{ product: { sku: "P100" }, quantity: 2 }], total: 19.98 }`       | Arrays are serialized as JSON arrays.      |
| **Scalar Types** | See [GraphQL Scalar Handling](#scalar-types) below.                                                   |                                 |

---

## **Scalar Type Handling**
GraphQL scalars (e.g., `ID`, `String`, `Int`, `Float`, `Boolean`) are serialized as-is, but custom scalars (e.g., `DateTime`, `Currency`) require special handling:

| **Scalar**     | **Database Format** | **JSON Output**               | **Transformation Rules**                          |
|----------------|---------------------|--------------------------------|--------------------------------------------------|
| `DateTime`     | `YYYY-MM-DD HH:MM:SS` | `"2024-01-01T12:00:00.000Z"`   | ISO-8601 with timezone (UTC).                   |
| `Currency`     | `9.99` (float)      | `"$9.99"`                      | Format as locale-specific string with symbol.     |
| `JSON`         | Raw JSON string     | Parsed object/array            | Decode if stored as string; else pass through.   |

---

## **Query Examples**

### **1. Basic Query (Single Object)**
**GraphQL Query:**
```graphql
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
    createdAt
  }
}
```

**Variables:**
```json
{ "id": "123" }
```

**Response:**
```json
{
  "data": {
    "user": {
      "id": "123",
      "name": "Alice",
      "email": "alice@example.com",
      "createdAt": "2024-01-01T00:00:00Z"
    }
  },
  "extensions": {
    "executionTime": "3ms"
  }
}
```

---

### **2. List Query with Pagination**
**GraphQL Query:**
```graphql
query GetProducts($limit: Int = 10, $offset: Int = 0) {
  products(limit: $limit, offset: $offset) {
    edges {
      node {
        sku
        name
        price
      }
    }
    pagination {
      offset
      limit
      total
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "products": {
      "edges": [
        { "node": { "sku": "P100", "name": "Widget", "price": 9.99 } },
        { "node": { "sku": "P101", "name": "Gadget", "price": 19.99 } }
      ],
      "pagination": {
        "offset": 0,
        "limit": 10,
        "total": 50
      }
    }
  }
}
```

---

### **3. Nested Query (Relations)**
**GraphQL Query:**
```graphql
query GetUserWithOrders($id: ID!) {
  user(id: $id) {
    id
    name
    orders(limit: 5) {
      orderId
      total
      items {
        product {
          sku
          name
        }
        quantity
      }
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "user": {
      "id": "123",
      "name": "Alice",
      "orders": [
        {
          "orderId": "ORD456",
          "total": 19.98,
          "items": [
            { "product": { "sku": "P100", "name": "Widget" }, "quantity": 2 }
          ]
        }
      ]
    }
  }
}
```

---

### **4. Error Handling**
**GraphQL Query:**
```graphql
query InvalidQuery {
  user(id: "invalid-id") {
    name
  }
}
```

**Response (with errors):**
```json
{
  "errors": [
    {
      "message": "User with ID invalid-id not found",
      "code": 404,
      "extensions": {
        "query": "user(id: \"invalid-id\") { name }"
      }
    }
  ],
  "data": {
    "user": null
  }
}
```

---

## **Implementation Details**

### **1. Database-to-GraphQL Mapping**
- **ORM/ActiveRecord Models**: Map model attributes to GraphQL fields (e.g., `user.name` → `name`).
- **Denormalized Data**: Flatten nested relations if performance-critical (e.g., `user.address.city`).
- **Dynamic Fields**: Use GraphQL’s `JSON` scalar for flexible fields (e.g., `metadata: { key: value }`).

**Example (ORM to GraphQL):**
```python
# Pseudo-code: ActiveRecord -> GraphQL
class UserSerializer:
    def serialize(self, user):
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email.strftime("%Y-%m-%dT%H:%M:%SZ")  # DateTime
        }
```

---

### **2. Handling Relationships**
| **GraphQL Directive** | **Serialization Behavior**                                                                 | **Example**                                  |
|-----------------------|-------------------------------------------------------------------------------------------|----------------------------------------------|
| `@hasMany`            | Eager-load related records; serialize as array.                                           | `orders: [{ orderId: "123", total: 9.99 }]`  |
| `@belongsTo`          | Include foreign-key fields in parent object.                                              | `user: { id: "123", name: "Alice" }`         |
| `include`/`exclude`   | Conditionally include/exclude fields in the response.                                     | Exclude sensitive fields like `password`.    |
| `@connection`         | Paginated cursor-based pagination (e.g., Relay-style).                                   | `{ edges: [...], pageInfo: { ... } }`        |

---

### **3. Performance Optimization**
- **Batching**: Use tools like `data-loader` or Django’s `collect_related` to reduce N+1 queries.
- **Fragment Caching**: Reuse serialized fragments for repeated fields (e.g., `Product` in multiple queries).
- **Lazy Loading**: Load nested data only if requested (e.g., `user.orders` only if `orders` is queried).

---

### **4. Edge Cases**
| **Scenario**               | **Solution**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Missing Fields**         | Return `null` or default value (e.g., `email: null`).                       |
| **Circular References**    | Break cycles (e.g., `user: { id: "123", ... }` without `address.user`).     |
| **Timezone Handling**      | Serialize timestamps in UTC (RFC 3339).                                      |
| **Large Objects**          | Truncate or paginate (e.g., `text: "Truncated..."`).                       |
| **Validation Errors**      | Return structured errors (e.g., `{ field: "email", message: "Invalid format" }`). |

---

## **Related Patterns**
1. **[GraphQL Schema Design](link)**
   - Defines the type system and directives used in this pattern.
2. **[Data Loading and Caching](link)**
   - Provides strategies to optimize database queries (e.g., batching, caching).
3. **[Error Handling](link)**
   - Standardizes error response structures across APIs.
4. **[Authentication and Authorization](link)**
   - Ensures serialized responses respect access controls (e.g., hide `user.password`).
5. **[Pagination](link)**
   - Details cursor-based or offset-based pagination for list queries.

---

## **Best Practices**
- **Idempotency**: Ensure repeated queries return identical responses for the same input.
- **Immutable Types**: Avoid modifying serialized objects after creation (e.g., use `frozenset` for IDs).
- **Schema Validation**: Use tools like `graphql-codegen` to generate type-safe serializers.
- **Testing**: Mock database responses and validate serialized output against schema expectations.
- **Documentation**: Include examples of serialized responses in the GraphQL schema comments.

---

## **Troubleshooting**
| **Issue**                     | **Diagnosis**                                                                 | **Solution**                                  |
|-------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Schema Mismatch**           | Serialized field does not match GraphQL type.                                 | Update serializer or schema.                  |
| **Performance Bottlenecks**   | Slow queries due to N+1 problems.                                             | Use batching or eager loading.                |
| ** Circular References**      | Infinite loops in nested serialization.                                      | Implement cycle detection (e.g., `seen` set). |
| **Timezone Errors**           | Incorrect timestamp formatting.                                               | Enforce UTC in serializers.                   |
| **Large Payloads**            | Response size exceeds client limits.                                          | Paginate or truncate fields.                  |

---

## **Example Code Snippets**
### **Python (FastAPI + SQLAlchemy)**
```python
from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

class UserOut(BaseModel):
    id: str
    name: str
    email: Optional[str] = None

@app.get("/user/{id}", response_model=UserOut)
def get_user(id: str):
    user = db.session.execute("SELECT id, name, email FROM users WHERE id = :id", {"id": id}).fetchone()
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email or None
    }
```

### **JavaScript (Node.js + TypeORM)**
```javascript
import { serialize } from "./serializers.js";

@Controller("users")
export class UserController {
  @Get(":id")
  async getUser(@Param("id") id: string) {
    const user = await this.userRepository.findOneOrFail({ where: { id } });
    return { data: serialize.user(user) };
  }
}

// serializers.js
export const serialize = {
  user: (user) => ({
    id: user.id,
    name: user.firstName + " " + user.lastName,
    email: user.email,
    createdAt: user.createdAt.toISOString(),
  }),
};
```

---
**Last Updated:** [YYYY-MM-DD]
**Version:** 1.0