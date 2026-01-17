**[Pattern] Projection Null Handling: Reference Guide**

---

### **1. Overview**
In GraphQL, projections transform server-side data models into client-specific response shapes. However, real-world data often contains **nulls, missing fields, or incompatible types**, which can break responses or degrade performance if mishandled. This pattern defines a **consistent, predictable approach to null handling** in projections, ensuring robust GraphQL responses while minimizing client-side validation and fallback logic.

Key goals:
- **Graceful null handling**: Replace or omit null/missing fields without breaking the GraphQL schema.
- **Type safety**: Enforce expected types and provide sensible defaults or conversions.
- **Performance**: Avoid N+1 queries or excessive compute by handling nulls at the projection layer.
- **Client compatibility**: Deliver predictable responses that align with client assumptions.

---

### **2. Schema Reference**

| **Field**               | **Type**               | **Description**                                                                                     | **Null Handling Behavior**                                                                                     | **Example Value**               |
|-------------------------|------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|----------------------------------|
| `user.id`               | `ID!`                  | Unique identifier for a user.                                                                       | Omits the field entirely if null.                                                                              | `123`                           |
| `user.name`             | `String!`              | User’s full name.                                                                                 | Returns `null` if missing (not nullable in schema).                                                       | `"John Doe"`                      |
| `user.email`            | `String`               | User’s email (optional).                                                                         | Returns `null` if missing or empty.                                                                        | `null`                          |
| `order.items`           | `[OrderItem!]!`        | List of items in an order.                                                                            | Returns empty array `[]` if null/missing.                                                                     | `[]`                             |
| `product.sku`           | `String`               | Product stock-keeping unit.                                                                       | Returns `"UNKNOWN"` if null/missing.                                                                           | `"UNKNOWN"`                      |
| `user.lastLogin`        | `DateTime`             | Last login timestamp (UTC).                                                                        | Returns `"1970-01-01T00:00:00Z"` (epoch) if null/missing.                                               | `"1970-01-01T00:00:00Z"`        |
| `user.preferences`      | `PreferencesInput`     | User preferences object.                                                                          | Returns a default `PreferencesInput` if null (e.g., `{ theme: "light" }`).                                  | `{ theme: "light" }`             |

**Key Annotations:**
- `!` (Non-nullable): Fields with this suffix **must** be provided by the projection or throw an error.
- Arrays (`[Type]!`): Empty arrays (`[]`) are returned for null/missing values.
- Defaults: Custom defaults (e.g., `"UNKNOWN"`, `{ theme: "light" }`) enforce type safety.

---

### **3. Query Examples**

#### **3.1 Handling Null Fields**
```graphql
query GetUserWithNulls {
  user(id: "123") {
    id
    name
    email
    preferences {
      theme
      notifications
    }
  }
}
```
**Response (if `preferences` is null):**
```json
{
  "user": {
    "id": "123",
    "name": "John Doe",
    "email": null,
    "preferences": { "theme": "light", "notifications": false }
  }
}
```
**Notes:**
- `email` returns `null` (matches schema).
- `preferences` uses a default object (defined in projection logic).

---

#### **3.2 Handling Missing Arrays**
```graphql
query GetOrderWithEmptyItems {
  order(id: "456") {
    id
    total
    items {
      id
      name
    }
  }
}
```
**Response (if `items` is null):**
```json
{
  "order": {
    "id": "456",
    "total": 99.99,
    "items": []
  }
}
```
**Key Behavior:**
- Empty array (`[]`) is returned for `null` or missing `items`.

---

#### **3.3 Type Conversion and Fallbacks**
```graphql
query GetProductWithDefaults {
  product(sku: "XYZ") {
    sku
    name
    price
    category
  }
}
```
**Response (if `category` is null):**
```json
{
  "product": {
    "sku": "UNKNOWN",
    "name": "Widget",
    "price": 19.99,
    "category": "Miscellaneous"
  }
}
```
**Projection Logic (Pseudocode):**
```javascript
return {
  sku: product?.sku ?? "UNKNOWN",
  name: product?.name ?? "Unnamed Product",
  price: convertToCurrency(product?.price), // Type conversion
  category: product?.category ?? "Miscellaneous"
};
```

---

### **4. Implementation Techniques**

#### **4.1 Default Values**
Use **ternary operators** or **object destructuring** to assign defaults:
```javascript
const userProjections = {
  preferences: (user) => ({
    theme: user.preferences?.theme ?? "light",
    notifications: user.preferences?.notifications ?? false
  })
};
```

#### **4.2 Array Handling**
Convert null/undefined arrays to empty arrays:
```javascript
const orderItems = Array.isArray(order.items) ? order.items : [];
```

#### **4.3 Type Conversion**
Ensure numeric/date fields match GraphQL types:
```javascript
const formattedDate = new Date(1672531200000).toISOString(); // "1970-01-01T00:00:00Z"
```

#### **4.4 Schema Integration**
Define nullable fields with defaults in the resolver:
```javascript
const resolvers = {
  Query: {
    user: (_, { id }) => {
      const user = db.getUser(id);
      return {
        ...user,
        email: user.email ?? null, // Explicit null (schema allows it)
        preferences: user.preferences || { theme: "light" } // Default object
      };
    }
  }
};
```

---

### **5. Performance Considerations**
- **Avoid N+1 Queries**: Load related data (e.g., `preferences`) in a single query or pre-fetch.
- **Lazy Defaults**: Compute defaults only if needed (e.g., deferred to resolver execution).
- **Caching**: Cache projection results for repeated requests (e.g., with `Redis`).

---

### **6. Related Patterns**
| **Pattern**                  | **Description**                                                                                     | **Use Case**                                                                                     |
|------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **DataLoader**               | Batch and cache database queries to avoid N+1 problems.                                               | Optimize projections with nested relationships.                                                 |
| **Type Conversion Middleware** | Validate and convert types (e.g., strings → numbers) before projection.                           | Ensure GraphQL fields match expected types.                                                      |
| **Error Handling in Projections** | Define fallback responses for critical errors (e.g., database failures).                          | Provide graceful degradation when data is unavailable.                                           |
| **Fragment Reuse**           | Share projection logic across multiple queries using fragments.                                     | Reduce code duplication in complex projections.                                                  |

---

### **7. Anti-Patterns to Avoid**
| **Anti-Pattern**                     | **Risk**                                                                                             | **Solution**                                                                                     |
|--------------------------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| Returning `null` for non-nullable fields | Breaks GraphQL validation and crashes resolvers.                                                   | Use defaults or throw errors (per schema requirements).                                           |
| Empty objects for missing fields    | Confuses clients expecting `null` or `undefined`.                                                  | Use empty arrays (`[]`) or defaults (e.g., `{}`) consistently.                                    |
| Silent type conversion failures    | Silent failures can lead to client-side bugs.                                                      | Log warnings or validate types early.                                                            |
| Projection logic in client-side code | Makes client code brittle to schema changes.                                                      | Keep projection logic server-side only.                                                          |

---
**License**: [MIT](https://opensource.org/licenses/MIT) | **Last Updated**: `YYYY-MM-DD`