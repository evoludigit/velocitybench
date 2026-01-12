# **Debugging Custom Scalar Taxonomy: A Troubleshooting Guide**
*Ensuring Type Safety Across 56 Scalars in 18 Domains*

This guide provides a structured approach to diagnosing and resolving issues with your **Custom Scalar Taxonomy** pattern. By following these steps, you can quickly identify why invalid data passes through APIs, validate domain-specific rules, and prevent runtime errors.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue with this checklist:

| Symptom | Likely Cause |
|---------|-------------|
| ✅ **Client receives no validation errors** for malformed inputs | Missing server-side validation |
| ✅ **API returns incorrect data types** (e.g., `string` where `UUID` was expected) | Scalar definition mismatch |
| ✅ **Client-side tooling (e.g., GraphQL Playground) doesn’t auto-complete** | Missing scalar descriptions or `possibleTypes` |
| ✅ **Runtime errors like `TypeError` or `InvalidScalar`** | Incorrect scalar implementation |
| ✅ **Multiple scalars share similar logic** but have inconsistent behavior | Duplicate or misconfigured scalar handlers |
| ✅ **New scalars break existing queries** | Backward compatibility not maintained |

If most symptoms checked apply, proceed to **Common Issues & Fixes**.

---

## **2. Common Issues & Fixes**

### **Issue 1: Invalid Data Passes Through API (No Validation)**
**Symptoms:**
- `200 OK` responses for clearly invalid inputs (e.g., `id: "not-a-uuid"`).
- Frontend assumes data is validated but encounters runtime failures.

**Root Cause:**
Missing or improper scalar validation logic.

**Fix:**
#### **For GraphQL (Using TypeScript/Node.js):**
```javascript
// Before (No validation)
const scalarRegistry = new ScalarRegistry();
scalarRegistry.register('UUID', GraphQLScalarType);

// After (Strict validation)
const UUIDScalar = new GraphQLScalarType({
  name: 'UUID',
  description: 'A RFC-4122 UUID',
  parseValue: (value) => {
    if (!uuidv4 validate(value)) throw new Error(`Invalid UUID`);
    return value;
  },
  serialize: (value) => {
    if (!uuidv4.validate(value)) throw new Error(`Invalid UUID`);
    return value;
  },
});
```

#### **For Protocol Buffers (gRPC):**
```proto
// Before (No type constraints)
message User { string id = 1; }

// After (Strict type enforcement)
scalar UUID = "type.googleapis.com/google.type.UUID";
// Then enforce in client/server logic.
```

**Prevention:**
- **Unit Test Scalar Parsing:** Always test edge cases (empty strings, invalid formats).
- **Input Sanitization:** Add middleware (e.g., NestJS `@Validate()` decorators) for API layers.

---

### **Issue 2: No Domain-Specific Validation**
**Symptoms:**
- `currency` scalar accepts `"abc"` instead of `123.45` or `"$50"`.
- `Timestamp` accepts `"invalid date string"`.

**Root Cause:**
Generic scalar implementations lack domain knowledge.

**Fix:**
#### **Custom Currency Scalar (Example):**
```javascript
const CurrencyScalar = new GraphQLScalarType({
  name: 'Currency',
  description: 'Amount in USD (e.g., "100.00" or "-5.99")',
  parseValue: (value) => {
    const match = /^-?\d{1,3}(?:,\d{3})*(?:\.\d+)?$/.test(String(value));
    if (!match) throw new Error('Invalid currency format');
    return parseFloat(value);
  },
});
```

#### **Debugging Tip:**
- **Log parsed values** to check if they meet expectations:
  ```javascript
  parseValue(value) {
    const parsed = /* ... */;
    console.log(`Parsed "${value}" →`, parsed);
    return parsed;
  }
  ```

**Prevention:**
- **Domain-specific regex/validators** (e.g., use `validator.js` for emails/URLs).
- **Document expected formats** in scalar descriptions.

---

### **Issue 3: Client Can’t Infer Expected Format**
**Symptoms:**
- IDE autocompletion suggests wrong types.
- GraphQL clients show vague type hints.

**Root Cause:**
Missing or unclear scalar definitions.

**Fix:**
#### **Improve Scalar Metadata:**
```javascript
const UUIDScalar = new GraphQLScalarType({
  name: 'UUID',
  description: |
    A globally unique identifier (UUIDv4).
    Must match regex: `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`.
  },
  // ... validation logic
});
```

#### **For gRPC:**
```proto
syntax = "proto3";
import "google/protobuf/struct.proto";

message Currency {
  string amount = 1;  // Must be "$123.45" or "123.45"
  string currency_code = 2;  // ISO code (e.g., "USD")
}
```

**Prevention:**
- **Update GraphQL schema tooling** (e.g., GraphQL Code Generator) to reflect new scalars.
- **Use `possibleTypes`** (GraphQL) or `oneof` (Protobuf) for discriminated unions.

---

### **Issue 4: Runtime Errors from Malformed Data**
**Symptoms:**
- `TypeError: Cannot read property 'x' of undefined` in resolvers.
- Database queries fail with `Cast to text from buffer failed`.

**Root Cause:**
Scalar deserialization fails, but errors propagate silently.

**Fix:**
#### **Add Error Boundaries in Resolvers:**
```javascript
async function getUser(root, { id }) {
  try {
    const user = await UserModel.findById(id);
    return user || null;
  } catch (err) {
    if (err.code === 11000) { // MongoDB duplicate key
      throw new GraphQLError('ID already exists');
    }
    throw new GraphQLError(`Failed to fetch user: ${err.message}`);
  }
}
```

#### **Debugging Tools:**
- **GraphQL Error Tracking:** Use Sentry/LogRocket to catch unhandled scalar errors.
- **Logging Middleware:** Log all scalar parse/serialize calls:
  ```javascript
  ScalarRegistry.prototype.register = (name, scalar) => {
    const originalParse = scalar.parseValue;
    scalar.parseValue = (value) => {
      console.trace(`[${name}] Parsing "${value}"`);
      return originalParse(value);
    };
    // ... similarly for serialize
  };
  ```

**Prevention:**
- **Validate at all layers** (API → DB → Client).
- **Use ORM validators** (e.g., Sequelize `validate()`).

---

## **3. Debugging Tools & Techniques**
| Tool/Technique | Purpose |
|----------------|---------|
| **GraphQL Playground/Apollo Studio** | Test scalars interactively with `query { scalarField } { __typename }`. |
| **Postman/gRPCurl** | Send malformed requests to isolate scalar issues. |
| **Logging Middleware** | Log scalar parse/serialize calls (as shown above). |
| **Static Analysis** | Tools like `graphql-codegen` to validate schema consistency. |
| **Breakpoints** | Set in scalar handlers to inspect `value` before processing. |
| **Error Injection Tests** | Fuzz-test with `invalid-date`, `empty-string`, etc. |

**Example Debugging Workflow:**
1. **Reproduce**: Send `{"id": "invalid-uuid"}` to API.
2. **Inspect**: Check server logs for silent failures.
3. **Isolate**: Add `console.log` in the `UUID` scalar’s `parseValue`.
4. **Fix**: Update regex or add `try/catch`.

---

## **4. Prevention Strategies**
### **A. Design-Time Safeguards**
1. **Scalar Registry Pattern:**
   Centralize scalars in a module to enforce consistency:
   ```javascript
   // src/scalars/index.ts
   export const scalars = {
     UUID: UUIDScalar,
     Currency: CurrencyScalar,
   };
   ```
2. **Schema Validation:**
   - Use `graphql-compose` or `nexus` to auto-generate scalars from interfaces.
   - Example:
     ```javascript
     const DateTimeScalar = new NexusScalar({
       type: Nexus.InputObjectType,
       name: 'DateTime',
       description: 'ISO 8601 format (e.g., "2023-12-01T00:00:00Z")',
       // ... validation
     });
     ```

### **B. Runtime Safeguards**
1. **Input Sanitization Layer:**
   Wrap API routes with validators (e.g., `express-validator`):
   ```javascript
   const { validate } = require('express-validator');
   app.post('/user', [
     validate('id').isUUID(),
   ], userController.create);
   ```
2. **Schema Stitching (Advanced):**
   - Use `graphql-tools` to merge schemas with strict type-checking:
     ```javascript
     const { mergeSchemas } = require('@graphql-tools/schema');
     const combinedSchema = mergeSchemas([schema1, schema2]);
     ```

### **C. Testing Strategies**
1. **Unit Tests for Scalars:**
   ```javascript
   test('UUID scalar rejects invalid input', () => {
     expect(() => UUIDScalar.parseValue('not-a-uuid')).toThrow();
   });
   ```
2. **Integration Tests:**
   - Mock the scalar in resolvers and verify behavior:
     ```javascript
     jest.mock('../scalars', () => ({
       UUIDScalar: {
         parseValue: jest.fn((v) => v === 'valid-uuid-123' ? v : null),
       },
     }));
     ```

### **D. Documentation & Onboarding**
1. **Scalar Handbook:**
   Maintain a **README** in your repo with:
   - Expected formats for each scalar.
   - Example queries/mutations.
   - Common pitfalls.
2. **Client SDK Type Safety:**
   - Generate TypeScript types from your GraphQL schema:
     ```bash
     graphql-codegen --schema ./schema.graphql --generates ./types.ts
     ```

---

## **5. Example Fix: Full UUID Scalar Implementation**
```javascript
// src/scalars/UUID.ts
import { GraphQLScalarType } from 'graphql';
import { UUID } from 'uuidv4';

export const UUIDScalar = new GraphQLScalarType({
  name: 'UUID',
  description: 'A RFC-4122 UUID',
  serialize(value) {
    if (!UUID.validate(value)) {
      throw new Error(`Invalid UUID: ${value}`);
    }
    return value;
  },
  parseValue(value) {
    if (!UUID.validate(value)) {
      throw new Error(`Invalid UUID: ${value}`);
    }
    return value;
  },
  parseLiteral(ast) {
    if (!ast.kind === Kind.STRING) return null;
    if (!UUID.validate(ast.value)) {
      throw new Error(`Invalid UUID literal: ${ast.value}`);
    }
    return ast.value;
  },
});
```

**Usage in Schema:**
```graphql
type User @model {
  id: UUID! @id @unique
  name: String!
}
```

---

## **Summary of Key Takeaways**
| Area | Action Item |
|------|-------------|
| **Validation** | Implement `parseValue`/`serialize` + unit tests. |
| **Documentation** | Add clear descriptions and examples. |
| **Debugging** | Log scalar inputs/outputs; use breakpoints. |
| **Prevention** | Centralize scalars, use input sanitization, and test edge cases. |
| **Tooling** | GraphQL Playground, logging middleware, and static analysis. |

By following this guide, you can systematically address issues in your **Custom Scalar Taxonomy**, ensuring type safety and reducing runtime errors. Start with the **Symptom Checklist**, then apply fixes from **Common Issues**, and reinforce with **Prevention Strategies**.

---
**Final Tip:** For large-scale systems, consider a **scalar factory** pattern to dynamically register/validate scalars at runtime. Example:
```javascript
const createScalar = (name, validator) => ({
  name,
  parseValue: (v) => validator(v) || null,
  serialize: (v) => validator(v) ? v : null,
});
```