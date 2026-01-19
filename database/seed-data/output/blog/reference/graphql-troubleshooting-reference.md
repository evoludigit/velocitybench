# **[Pattern] GraphQL Troubleshooting Reference Guide**

---

## **Overview**
GraphQL troubleshooting requires systematic debugging to identify issues in queries, resolvers, schema design, or network layers. This guide provides structured methodologies—**query inspection, schema validation, resolver debugging, caching issues, and client-server alignment**—to resolve common GraphQL errors efficiently. Follow this pattern to diagnose performance bottlenecks, malformed responses, or client-server inconsistencies while ensuring compliance with best practices like schema-first development and proper error handling.

---

## **Key Concepts & Implementation Details**

### **1. Schema Validation**
Ensure your GraphQL schema aligns with client expectations. Common validation steps:
- **Check for `undefined` types**: Resolvers return `null` or `undefined` if a field is missing in parent data.
- **Type mismatch**: Resolver returns a scoped type (e.g., `Int` instead of `String`).
- **Deprecated fields**: Deprecated fields may still resolve but log warnings.

**Tooling**:
- Use GraphQL Schema Validator (`graphql-tools`) or Apollo’s `schema` CLI.
- Verify with:
  ```bash
  graphql validate schema.graphql
  ```

---

### **2. Query Parsing & Syntax Errors**
GraphQL errors occur at parsing (syntax) or execution (runtime) phases.

| **Error Type**       | **Cause**                          | **Solution**                                  |
|-----------------------|-------------------------------------|-----------------------------------------------|
| **SyntaxError**       | Malformed query (e.g., unclosed `}`)| Fix brackets/quotes via IDE linting.          |
| **Not Found Error**   | Invalid field/path in schema        | Validate schema with `graphql-inspector`.     |
| **Validation Error**  | Missing required args (e.g., `ID!`) | Add default values or update client queries.  |

**Example Query (Correct & Invalid)**:
```graphql
# ✅ Valid Query
query GetUser { user(id: "1") { name } }

# ❌ Invalid Query (missing required arg)
query GetUser { user { name } }  # Error: Cannot query field "user" on type "Query"
```

---

### **3. Resolver Debugging**
Resolvers are the core of GraphQL execution. Common pitfalls:
- **Improper return types**: Returning `Promise` directly instead of resolving it.
- **Missing async/await**: Unhandled race conditions in async resolvers.
- **Over-fetching**: Resolvers retrieving data beyond required fields.

**Debugging Steps**:
1. **Log resolver context**:
   ```javascript
   resolve: async (parent, args, context) => {
     console.log("Resolver input:", { parent, args, context });
     return await fetchData(args.id);
   }
   ```
2. **Use `graphql-playground`** to inspect resolver inputs/outputs via the `"debug"` tab.

---

### **4. Network & Caching Issues**
GraphQL relies on efficient data fetching. Common issues:
- **Slow queries**: Excessive nested fields or unresolved promises.
- **Caching misconfigurations**: Stale data in Apollo Cache or Relay.
- **Connection timeouts**: Unoptimized resolver calls.

**Optimization Techniques**:
| **Issue**               | **Fix**                                      |
|--------------------------|-----------------------------------------------|
| Deep nesting             | Use `dataLoader` for batching.                |
| Missing `persistedQuery` | Enable in Apollo Server (`persistedQueries: true`). |
| Cache stale reads        | Configure cache invalidation policies.       |

---

### **5. Client-Server Mismatches**
Clients and servers must agree on:
- **Schema evolution**: Backward compatibility via `!` and `@deprecated`.
- **Field selections**: Clients should only request necessary fields (avoid over-fetching).
- **Error serialization**: Standardized error formats (e.g., `errors: [ { message: "..." } ]`).

**Example Client-Server Conflict**:
```graphql
# Server schema defines `user { name, age }` but client requests:
query GetUser { user { secretData } }  # ❌ Fails with "Cannot query field 'secretData' on type 'User'"
```

---

## **Schema Reference Table**
| **Component**          | **Best Practices**                          | **Tools/Extensions**               |
|------------------------|---------------------------------------------|-------------------------------------|
| **Schema Design**      | Avoid over-fetching; use interfaces.        | GraphQL Code Generator, Prisma      |
| **Query Parsing**      | Use `graphql-js` for parsing.               | Apollo Studio, Skaffolder          |
| **Resolver Logic**     | Async/await + error handling.               | debug=*"resolver"* in Apollo Logs   |
| **Caching**            | Persisted queries, cache policies.          | Apollo Cache, Relay Modern          |
| **Error Handling**     | Standardized error shapes.                  | @graphql-tools/error-list          |

---

## **Query Examples**

### **✅ Valid Query (Optimized)**
```graphql
query GetOptimizedUser {
  user(id: "1") {
    name
    profile { avatar }  # Only fetch necessary nested fields
  }
}
```

### **❌ Suboptimal Query (Over-fetching)**
```graphql
query GetOverFetchedUser {
  user(id: "1") {
    name
    ...  # Unused fields included
    address { city, country }
    posts { title, comments { content } }
  }
}
```

### **Debugging a Failed Query**
```graphql
# ️ Error: "Cannot return null for non-nullable field"
query FindUser {
  user(id: "2") @skip(if: $userIdMissing)
  { name }
}
```

**Debugging Steps**:
1. Check if `userIdMissing` is `true` in variables.
2. Validate resolver for `user(id: 2)` to ensure it returns `{ name: "..." }`.

---

## **Related Patterns**
| **Pattern**                  | **Use Case**                                  | **Reference**                          |
|------------------------------|-----------------------------------------------|-----------------------------------------|
| **Schema Composition**       | Modular schema design (e.g., codegen).       | [GraphQL Schema Composition Guide](https://www.apollographql.com/docs/guides/schema-composition) |
| **Performance Optimization** | Pagination, data skipping.                   | [Apollo Performance Best Practices](https://www.apollographql.com/blog/performance/) |
| **Authentication**           | JWT/Role-based access control.               | [GraphQL Authentication](https://www.howtographql.com/basics/2-authentication/) |
| **Subscriptions**           | Real-time updates (e.g., WebSockets).        | [GraphQL Subscriptions](https://graphql.org/learn/subscriptions/) |

---

## **Troubleshooting Checklist**
1. **Parse errors?** Validate syntax via `graphql-parse`.
2. **Resolver failures?** Add `console.log` to debug context/args.
3. **Slow responses?** Profile with Chrome DevTools or Apollo Studio.
4. **Schema drift?** Compare client queries with `graphql-server` schema.
5. **Client mismatches?** Verify field types in GraphQL Playground.

---
**End of Guide** (~950 words).
*For deeper dives, reference the [GraphQL Spec](https://spec.graphql.org/) and [Apollo Docs](https://www.apollographql.com/docs).*