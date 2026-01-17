---
# **[Pattern] Nested Type Projection Reference Guide**
*Efficiently project multi-level nested data structures with controlled depth.*

---

## **1. Overview**
The **Nested Type Projection** pattern enables querying embedded (nested) data structures while limiting the depth of projections to optimize performance and avoid excessive data transfer. Unlike simple flattening, this pattern preserves hierarchical relationships *at specified levels*, allowing clients to access nested fields *only when explicitly requested*. Commonly used in GraphQL, REST with JSON, or document databases (e.g., MongoDB), this pattern balances granularity with efficiency by separating projection logic from data retrieval.

This guide covers how to:
- Define schemas with nested types.
- Project data to arbitrary nesting levels.
- Query nested fields with depth control.
- Integrate with APIs or database systems.

---

## **2. Schema Reference**
Below is a table defining the structure of **nested projections** for a sample schema.

| **Type**          | **Description**                                                                 | **Nested Fields** (Projection Depth) |
|-------------------|---------------------------------------------------------------------------------|--------------------------------------|
| `User`            | Represents a user entity.                                                      | `id`, `name`, `email`, `address`     |
| `Address`         | Embedded nested type for user address.                                        | `street`, `city`, `country`          |
| `Order`           | Represents a user order.                                                       | `id`, `orderDate`, `items`           |
| `OrderItem`       | Embedded nested type for order items; *projection depth = 2*.                 | `productId`, `quantity`, `unitPrice` |

### **Schema Example (JSON)**
```json
{
  "User": {
    "type": "object",
    "properties": {
      "id": { "type": "string" },
      "name": { "type": "string" },
      "email": { "type": "string" },
      "address": {
        "type": "object",
        "properties": {
          "street": { "type": "string" },
          "city": { "type": "string" },
          "country": { "type": "string" }
        }
      },
      "orders": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": { "type": "string" },
            "orderDate": { "type": "string" },
            "items": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "productId": { "type": "string" },
                  "quantity": { "type": "integer" },
                  "unitPrice": { "type": "number" }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## **3. Implementation Details**
### **Key Concepts**
1. **Projection Depth**:
   Specifies how many levels of nesting to expose. E.g., depth=0 returns only top-level fields; depth=2 includes nested fields two levels deep.

2. **Explicit Nesting**:
   Nested fields *are not included by default* unless explicitly requested via query parameters or projection syntax.

3. **Performance Considerations**:
   Limiting projection depth reduces payload size and improves query performance, especially for large datasets.

4. **Common Use Cases**:
   - **APIs**: Returning partial nested data (e.g., `/users/{id}?depth=1` for `name` + `address`).
   - **Databases**: Using `MongoDB` `$project` with nested filtering.
   - **GraphQL**: Specifying nested fields in queries (e.g., `{ user { name address { city } } }`).

---

## **4. Query Examples**
### **Example 1: REST API with URL Query Parameters**
**Request**:
```
/api/users/123?depth=1
Headers: Accept: application/json
```
**Response**:
```json
{
  "id": "123",
  "name": "Alice",
  "email": "alice@example.com",
  "address": {
    "city": "New York"
  }
}
```
*Note: `country` and `street` are excluded due to `depth=1`.*

---

### **Example 2: MongoDB Aggregation Pipeline**
```javascript
db.users.aggregate([
  { $match: { _id: ObjectId("123") } },
  {
    $project: {
      _id: 0,
      name: 1,
      email: 1,
      "address.city": 1, // Explicitly project nested "city"
    }
  }
]);
```
**Output**:
```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "address": {
    "city": "New York"
  }
}
```

---

### **Example 3: GraphQL Query**
```graphql
query {
  user(id: "123") {
    id
    name
    email
    address {
      city
      country # Included despite depth=1 if explicitly requested
    }
  }
}
```
**Response**:
```json
{
  "data": {
    "user": {
      "id": "123",
      "name": "Alice",
      "email": "alice@example.com",
      "address": {
        "city": "New York",
        "country": "USA"
      }
    }
  }
}
```

---

### **Example 4: Ruby on Rails ActiveRecord Projection**
```ruby
User.where(id: 123).select(
  "id, name, email, address AS address"
).first.as_json(depth: 1)
```
**Output**:
```json
{
  "id": "123",
  "name": "Alice",
  "email": "alice@example.com",
  "address": {
    "city": "New York"
  }
}
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **Flattening**            | Converts nested data into a single-level structure.                           | When hierarchical relationships are irrelevant. |
| **GraphQL (Nested Queries)** | Dynamically requests nested fields via queries.                              | For highly customizable APIs.            |
| **Paginated Responses**   | Limits result sets to avoid over-fetching.                                   | When dealing with large datasets.        |
| **Lazy Loading**          | Loads nested data on demand (e.g., via callbacks).                           | For performance-critical applications.   |
| **JSON API (Documentation)** | Standard for nested resource representations.                            | For RESTful APIs with clear specifications.|

---

## **6. Best Practices**
1. **Document Depth Levels**:
   Clearly specify available projection depths in API documentation (e.g., `depth=0`, `depth=1`, `depth=2`).

2. **Optimize Payloads**:
   Avoid over-projection by default; require explicit requests for nested fields.

3. **Handle Edge Cases**:
   - Return `null` for missing nested fields at requested depth.
   - Validate depth values (e.g., reject `depth > 3` if schema only supports 3 levels).

4. **Use Caching**:
   Cache projected responses to reduce redundant computations.

5. **Versioning**:
   Support backward compatibility when modifying nested schemas.

---
**See Also**:
- [REST Best Practices](https://restfulapi.net/)
- [GraphQL Depth Limitation](https://graphql.org/learn/global-objects/)
- [MongoDB Aggregation Pipeline](https://www.mongodb.com/docs/manual/aggregation/)