```markdown
# **Custom Scalar Taxonomy in APIs: Beyond Strings for True Type Safety**

## **Introduction**

Imagine you’re building an e-commerce API where product IDs are UUIDs, prices are formatted in USD with two decimal places, and shipping addresses are validated as GeoJSON objects. Your team uses TypeScript (or Python, Go, or Java), but your backend database and API serialization layer still treats everything as plain strings.

This isn’t just a design oversight—it’s a type safety nightmare. When IDs are accidentally passed as `string` instead of UUID, when prices slip through as floats instead of fixed-point USD, or when malformed GeoJSON breaks your application, you’re left debugging serialization issues instead of core business logic. Worse, clients might send data in formats you never anticipated (e.g., an ISO date string instead of Unix timestamp), exposing your API to subtle bugs.

In this post, we’ll explore a **Custom Scalar Taxonomy pattern**, where we define strict, domain-specific types at the API boundary and enforce them with validation. We’ll use **FraiseQL** as our tool for automatic serialization/deserialization, but you can adapt the concepts to OpenAPI, GraphQL, or custom parsers.

---

## **The Problem: Why "String" Is the Worst Default Type**

Strings are the Swiss Army knife of data—versatile, but only because they’re a crutch. Here’s why they fail in production APIs:

1. **No Validation** – A string `"ABC123"` is identical to `"user-abc123"`, yet one might represent a UUID and the other a username. Without rules, you’re flying blind.
2. **Ambiguity in Concatenation** – Joining strings (e.g., `"order-" + id`) can silently introduce errors if `id` isn’t a string (e.g., a UUID object).
3. **Serialization Pitfalls** – JSON serialization loses type information entirely. A `100.00` price might round-trip as `100` (integer), losing critical precision.
4. **Client-Driven Chaos** – Clients might send data in formats you never considered (e.g., a date as `YYYYMMDD` instead of ISO8601). Your API has no way to reject it gracefully unless you explicitly define rules.

### A Real-World Example: The Faulty Order API

```json
// Request (malformed but valid JSON)
{
  "order_id": "123e4567-e89b-12d3-a456-426614174000",
  "price": "99.99",
  "shipping_address": { "type": "Point", "coordinates": "invalid" }
}

// Response (crash or data corruption)
{
  "error": "TypeError: Invalid UUID format"  // Or worse: silently fails
}
```

The root issue? **No type system** at the API boundary. This forces you to write validation logic everywhere, bloating your code and introducing redundancy.

---

## **The Solution: Custom Scalar Taxonomy**

A **Custom Scalar Taxonomy** is a way to define domain-specific types (e.g., `UUID`, `USD`, `GeoJSON`) and enforce them at serialization boundaries. The key principles:

1. **Automatic Validation** – Reject invalid data at the API layer, not in the database.
2. **Type Safety** – Treat `order_id` as a `UUID` type, not a string, so type errors catch early.
3. **Domain Alignment** – Use types that match your business logic (e.g., `Currency` instead of `float`).
4. **Flexible Parsing** – Accept multiple valid formats (e.g., `"2023-10-01"` or `1696121600000` for dates).

### How FraiseQL Implements This

FraiseQL provides **56 custom scalar types** across 18 domains, with automatic serialization/deserialization. Example types:

| Domain          | Type                   | Example                          |
|-----------------|------------------------|----------------------------------|
| **Temporal**    | `ISO8601Date`, `UnixTime` | `"2023-10-01"`, `1696121600`     |
| **Geographic**  | `GeoJSON`, `LatLng`     | `{"type": "Point", "coordinates": [-122.08, 47.65]}` |
| **Financial**   | `USD`, `EUR`           | `"$100.00"` (validates decimal)  |
| **Identifiers** | `UUID`, `Slug`         | `"123e4567-e89b-12d3-a456-426614174000"` |
| **Network**     | `IPv4`, `Domain`       | `"192.168.1.1"`, `"example.com"` |

### Key Benefits:
- **No Manual Parsing**: FraiseQL handles conversion automatically.
- **Early Rejection**: Invalid data is caught at the API layer, not in the database.
- **Extensible**: Add custom types (e.g., `ProductID`) with minimal effort.

---

## **Implementation Guide: Step-by-Step**

### 1. Define Your Types

FraiseQL types are used like this:

```typescript
// In your API schema (e.g., OpenAPI/Swagger)
{
  "order": {
    "type": "object",
    "properties": {
      "id": { "type": "uuid" },      // FraiseQL's UUID type
      "price": { "type": "usd" },     // USD with 2 decimal places
      "shipping": { "type": "geojson" } // Validates GeoJSON
    }
  }
}
```

### 2. Validate Data at the API Boundary

FraiseQL’s `fraise` CLI or runtime libraries enforce these types. Example with Node.js:

```javascript
const { fraise } = require('fraise');

// Define a schema with custom scalars
const orderSchema = {
  type: 'object',
  properties: {
    id: { type: 'uuid' },
    price: { type: 'usd' },
    shipping: { type: 'geojson' }
  },
  required: ['id', 'price']
};

// Validate input (rejects invalid data)
const input = { id: 'invalid-uuid', price: '99.99', shipping: { type: 'Invalid' } };
const result = fraise.validate(orderSchema, input);

if (result.errors) {
  throw new Error(`Invalid input: ${result.errors.join(', ')}`);
  // Errors: ["id must be a valid UUID", "shipping must be a valid GeoJSON"]
}
```

### 3. Serialize/Deserialize Automatically

FraiseQL converts between your types and JSON/DB formats:

```json
// Input (valid)
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "price": "$100.00",
  "shipping": { "type": "Point", "coordinates": [-122.08, 47.65] }
}

// Output (FraiseQL ensures correct types)
{
  "id": "UUID('123e4567-e89b-12d3-a456-426614174000')",
  "price": 100.00, // USD type normalizes to number
  "shipping": { ... } // GeoJSON remains intact
}
```

### 4. (Optional) Extend with Custom Types

Need a `ProductID` type? Inherit from FraiseQL’s base types:

```javascript
const { Scalar } = require('fraise');
const ProductID = Scalar.extend({
  name: 'product_id',
  validate: (value) => {
    return /^PROD-\d{8}$/.test(value);
  },
  serialize: (value) => value,
  deserialize: (value) => value
});

// Usage in schema:
{
  "product": {
    "type": "product_id"
  }
}
```

---

## **Common Mistakes to Avoid**

1. **Overusing Strings**
   - ❌ `"price": "$100"` (no validation)
   - ✅ `"price": { "type": "usd", "value": 100.00 }`

2. **Ignoring Edge Cases**
   - Validate floats vs. integers (e.g., `inventory: { type: "int" }`).
   - Reject empty strings where required (e.g., `email: { type: "email", minLength: 1 }`).

3. **Mismatched Schemas**
   - If your frontend sends `ISO8601Date` but your backend expects `UnixTime`, clarify expectations early.

4. **Bloating Schemas**
   - Don’t define 50 custom types if 90% of fields are `string`. Use FraiseQL’s built-ins where possible.

5. **Silent Failures**
   - Always validate at the API boundary, not just in the database. Example:
     ```sql
     -- BAD: Let the DB fail with "invalid UUID" (hard to debug)
     INSERT INTO orders (id) VALUES ('not-a-uuid');

     -- GOOD: Reject early with FraiseQL
     fraise.validate({ id: { type: 'uuid' } }, { id: 'not-a-uuid' });
     ```

---

## **Key Takeaways**

✅ **Type Safety at the API Layer** – Reject invalid data before it reaches your database.
✅ **Automatic Validation** – FraiseQL handles parsing/serialization without boilerplate.
✅ **Domain Alignment** – Use `USD`, `UUID`, and `GeoJSON` instead of loose `string`/`number` types.
✅ **Extensible** – Add custom types (e.g., `ProductID`) with minimal effort.
❌ **Avoid Strings** – They’re a code smell for lack of type safety.
❌ **Don’t Trust Clients** – Always validate, even if the client "knows" the format.

---

## **Conclusion**

A **Custom Scalar Taxonomy** transforms APIs from fragile string-based endpoints into robust, type-safe systems. By leveraging tools like FraiseQL, you:
1. Reduce bugs from malformed data.
2. Simplify validation logic (no more regex spaghetti).
3. Align your API types with your business domain.

Start small—validate critical fields (e.g., `UUID` IDs, `USD` prices) first. Over time, you’ll find that loose strings are the exception, not the rule.

**Need to try it?** [FraiseQL’s docs](https://fraiseql.com) include full type reference and SDKs for Node.js, Python, and Go.

---
```

### **Why This Works for Your Audience:**
1. **Practical Focus**: Code-first examples show immediate value.
2. **No Silver Bullets**: Acknowledges tradeoffs (e.g., custom type overhead).
3. **Actionable**: Step-by-step guide with clear "do/don’t" examples.
4. **Scalable**: Starts with built-in types but shows how to extend.

Would you like a follow-up post diving deeper into custom type implementation?