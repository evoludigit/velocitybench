# **Debugging Custom Scalar Types in GraphQL: A Troubleshooting Guide**

---

## **Table of Contents**
1. [Introduction](#introduction)
2. [Symptom Checklist](#symptom-checklist)
3. [Common Issues and Fixes](#common-issues-and-fixes)
   - [3.1 Scalar Not Resolving in Queries](#31-scalar-not-resolving-in-queries)
   - [3.2 Type Coercion Errors](#32-type-coercion-errors)
   - [3.3 Serialization/Deserialization Failures](#33-serializationdeserialization-failures)
   - [3.4 Performance Issues with Complex Scalars](#34-performance-issues-with-complex-scalars)
4. [Debugging Tools and Techniques](#debugging-tools-and-techniques)
   - [4.1 GraphQL Playground / Apollo Sandbox](#41-graphql-playground--apollo-sandbox)
   - [4.2 Logging and Tracing](#42-logging-and-tracing)
   - [4.3 Schema Validation](#43-schema-validation)
   - [4.4 Unit & Integration Testing](#44-unit--integration-testing)
   - [4.5 Database & API Inspection](#45-database--api-inspection)
5. [Prevention Strategies](#prevention-strategies)
6. [Conclusion](#conclusion)

---

## **Introduction**
Custom scalar types in GraphQL (e.g., `Date`, `JSON`, `UUID`) allow developers to define non-standard data types beyond GraphQL’s built-in scalar types (`String`, `Int`, `Float`, `Boolean`). While useful, they can introduce subtle bugs if not implemented correctly.

This guide provides a structured approach to diagnosing and resolving issues with custom scalar types.

---

## **Symptom Checklist**
Before deep-diving, verify these symptoms:
✅ **Error in Playground/Sandbox**:
   - `Cannot return non-scalar from scalar field` or `Invalid scalar type`
   - `Expected scalar type but received <type>`

✅ **Unexpected Behavior in Queries**:
   - Custom scalars return `null` or invalid values (e.g., `"2024-01-01"` → `null` when expected as `Date`).
   - Type coercion fails (e.g., JSON string is parsed incorrectly).

✅ **Server Crashes or Timeouts**:
   - The resolver for a custom scalar hangs or throws errors.
   - GraphQL server crashes with `TypeError` or `JSON.parse` failures.

✅ **Performance Issues**:
   - Queries with custom scalars are slow (e.g., complex JSON parsing in resolvers).

✅ **Schema Validation Errors**:
   - GraphQL tools (e.g., `graphql-tools`, `graphql-validation`) flag scalar definitions as invalid.

---

## **Common Issues and Fixes**

### **3.1 Scalar Not Resolving in Queries**
**Symptoms**:
- Querying a custom scalar (e.g., `{ date: userCreatedAt }`) returns `null` or an invalid value.
- The GraphQL server does not recognize the scalar type.

**Root Causes**:
- Scalar not properly registered in the schema.
- Incorrect resolver implementation.
- Missing `parseValue`/`parseLiteral` methods.

**Fixes**:

#### **Code Example: Registering a `Date` Scalar**
```javascript
const { GraphQLScalarType } = require('graphql');
const { Kind } = require('graphql/language');

const DateScalar = new GraphQLScalarType({
  name: 'Date',
  description: 'Custom Date type',
  parseValue: (value) => {
    // Parse from string (e.g., "2024-01-01" → Date object)
    return new Date(value);
  },
  serialize: (value) => {
    // Convert Date object → ISO string
    return value.toISOString();
  },
  parseLiteral: (ast) => {
    // Parse from GraphQL AST (e.g., string literals)
    if (ast.kind === Kind.STRING) {
      return new Date(ast.value);
    }
    return null;
  },
});

// Register in schema
const schema = new GraphQLSchema({
  query: new GraphQLObjectType({ /* ... */ }),
  scalarTypes: [DateScalar], // <-- Add scalar to schema
});
```

**Debugging Steps**:
1. Check if `DateScalar` is listed in `schema.getScalarType('Date')`.
2. Verify the resolver receives the correct input (e.g., `req.body` vs. `req.query`).
3. Test with hardcoded values in the resolver:
   ```javascript
   resolve: (_, { date }) => new Date(date) // Should log "Invalid Date" if failing
   ```

---

### **3.2 Type Coercion Errors**
**Symptoms**:
- Query variables are not parsed correctly (e.g., `{"date": "2024-01-01"}` returns error).
- GraphQL Playground shows `Variable "$date" has incorrect type`.

**Root Causes**:
- Missing `parseValue`/`parseLiteral` methods.
- Incorrect type in query variables (e.g., passing `Int` instead of `String`).

**Fixes**:

#### **Code Example: Proper `JSON` Scalar**
```javascript
const JSONScalar = new GraphQLScalarType({
  name: 'JSON',
  description: 'Custom JSON type',
  parseValue: (value) => {
    if (typeof value === 'string') {
      try { return JSON.parse(value); } catch (e) { throw new Error('Invalid JSON'); }
    }
    return null;
  },
  serialize: (value) => JSON.stringify(value),
  parseLiteral: (ast) => {
    if (ast.kind === Kind.STRING) {
      try { return JSON.parse(ast.value); } catch (e) { return null; }
    }
    return null;
  },
});
```

**Debugging Steps**:
1. Validate query variables match the scalar’s expected input (e.g., `{"date": "2024-01-01"}`).
2. Use `console.log(ast)` in `parseLiteral` to inspect GraphQL AST input.
3. Test with raw JSON:
   ```graphql
   query { jsonField }  # Instead of passing a variable
   ```

---

### **3.3 Serialization/Deserialization Failures**
**Symptoms**:
- Server returns `null` or `{"errors":["Cannot return null for non-nullable field"]}`.
- API clients receive malformed data (e.g., `{"date":"Invalid Date"}`).

**Root Causes**:
- `serialize` method throws without proper fallbacks.
- `parseValue` rejects valid input (e.g., empty string).

**Fixes**:

#### **Code Example: Robust `Date` Scalar**
```javascript
const DateScalar = new GraphQLScalarType({
  name: 'Date',
  serialize: (value) => {
    if (value instanceof Date && !isNaN(value.getTime())) {
      return value.toISOString();
    }
    throw new Error('Invalid Date object');
  },
  parseValue: (value) => {
    const date = new Date(value);
    return isNaN(date.getTime()) ? null : date;
  },
});
```

**Debugging Steps**:
1. Log `serialize` and `parseValue` outputs:
   ```javascript
   console.log('Serialize:', value, JSON.stringify(value));
   console.log('Parse:', rawValue, typeof rawValue);
   ```
2. Use tools like Postman to inspect raw API responses.
3. Test edge cases (e.g., `null`, `""`, `NaN`).

---

### **3.4 Performance Issues with Complex Scalars**
**Symptoms**:
- Slow query execution (e.g., JSON parsing in resolvers).
- High latency when returning large custom scalars.

**Root Causes**:
- Recursive JSON/Object resolution.
- Unoptimized `parseValue`/`serialize` logic.

**Fixes**:

#### **Optimize JSON Scalar for Performance**
```javascript
// Avoid deep parsing if only top-level access is needed
const JSONScalar = new GraphQLScalarType({
  name: 'JSON',
  description: 'Optimized JSON scalar',
  parseValue: (value) => {
    if (typeof value === 'string' && value.startsWith('{') && value.endsWith('}')) {
      return JSON.parse(value); // Fast path for JSON strings
    }
    return null;
  },
  serialize: (value) => {
    if (typeof value === 'object' && !Array.isArray(value)) {
      return JSON.stringify(value); // Avoid circular refs
    }
    throw new Error('Invalid JSON');
  },
});
```

**Debugging Steps**:
1. Profile with Chrome DevTools or K6 to find bottlenecks.
2. Use `performance.now()` in resolvers:
   ```javascript
   console.time('parseValue');
   const result = JSON.parse(value);
   console.timeEnd('parseValue');
   ```
3. Caching: Store parsed JSON results in Redis/Memcached.

---

## **Debugging Tools and Techniques**

### **4.1 GraphQL Playground / Apollo Sandbox**
- **Why?** Interactive testing of queries with custom scalars.
- **How?**
  ```graphql
  query {
    user(id: "1") {
      createdAt  # Test Date scalar
      metadata   # Test JSON scalar
    }
  }
  ```
- **Debugging Tip**: Use the "Variables" tab to test `parseValue`/`parseLiteral`.

---

### **4.2 Logging and Tracing**
- **Tools**: Winston, Pino, `console.trace()`.
- **Example**:
  ```javascript
  console.trace('Scalar parseValue:', value, new Error().stack);
  ```
- **Debugging Tip**: Log AST in `parseLiteral`:
  ```javascript
  console.log('AST node:', ast.kind, ast.value);
  ```

---

### **4.3 Schema Validation**
- **Tools**: `graphql-validation`, `graphql-tools`.
- **Example**:
  ```javascript
  const { validateSchema } = require('graphql-validation');
  const errors = validateSchema(schema);
  if (errors.length > 0) console.error(errors);
  ```
- **Debugging Tip**: Check for undefined scalars:
  ```javascript
  console.log('Schema scalars:', schema.getTypeMap());
  ```

---

### **4.4 Unit & Integration Testing**
- **Unit Test Example (Jest)**:
  ```javascript
  test('DateScalar serialization', () => {
    const date = new Date('2024-01-01');
    expect(dateScalar.serialize(date)).toBe('2024-01-01T00:00:00.000Z');
  });
  ```
- **Integration Test Example (MSW)**:
  ```javascript
  import { setupWorker, rest } from 'msw';

  const worker = setupWorker(
    rest.post('/graphql', (req, res, ctx) => {
      return res(
        ctx.json({
          data: {
            dateField: '2024-01-01',
          },
        })
      );
    })
  );
  ```

---

### **4.5 Database & API Inspection**
- **Debug Raw Data**: Query the database directly to verify custom scalar values.
- **API Inspection**: Use curl or Postman to inspect raw GraphQL responses:
  ```bash
  curl -X POST http://localhost:4000/graphql \
    -H "Content-Type: application/json" \
    -d '{"query": "{ user { createdAt } }"}'
  ```

---

## **Prevention Strategies**

1. **Schema First**: Define scalars in `.graphql` files and use codegen (e.g., `graphql-codegen`).
2. **Type Safety**:
   - Use Zod or Joi to validate scalar inputs.
   - Example with Zod:
     ```javascript
     import { z } from 'zod';
     const DateSchema = z.string().datetime();
     ```
3. **Testing**:
   - Write unit tests for all scalars.
   - Use integration tests to verify schema behavior.
4. **Documentation**:
   - Add scalar descriptions (e.g., `description: "ISO 8601 date string"`).
5. **Performance**:
   - Avoid deep deserialization unless needed.
   - Use indexedDB for large JSON data.

---

## **Conclusion**
Custom scalars in GraphQL can simplify data handling but require careful implementation. This guide covers:
- **Symptom identification** (e.g., null returns, type errors).
- **Common fixes** (e.g., `parseValue`, `serialize`).
- **Debugging tools** (logging, schema validation, testing).
- **Prevention strategies** (schema-first, type safety, testing).

**Next Steps**:
1. Audit your custom scalars using the checklist above.
2. Implement the fixes for failing cases.
3. Set up automated tests for new scalars.

By following this guide, you can resolve scalar-related issues efficiently and prevent future bugs.