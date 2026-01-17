# **[Pattern] GraphQL Debugging Reference Guide**

---

## **Overview**
GraphQL Debugging is a structured approach to identifying, isolating, and resolving issues in GraphQL schemas, queries, and resolvers. Unlike traditional debugging, GraphQL debugging leverages its introspection capabilities, error handling, and tooling to trace execution flow, validate data, and diagnose performance bottlenecks. This guide covers key debugging techniques, common pitfalls, and reference tools, with a focus on schema validation, query execution tracing, resolver debugging, and performance optimization.

---

## **Key Concepts & Implementation Details**

### **1. GraphQL Debugging Patterns**
| Pattern               | Description                                                                                     | Use Case                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Schema Validation** | Verify schema syntax, types, and directives before execution.                                    | Pre-flight schema checks to prevent runtime errors.                                        |
| **Query Tracing**     | Log execution paths of queries to identify bottlenecks or unexpected resolver calls.           | Diagnose slow queries or resolver logic misbehavior.                                        |
| **Error Handling**    | Capture and analyze GraphQL errors (e.g., `400 Bad Request`, `Validation Error`).               | Debug client-side syntax issues or server-side resolver failures.                           |
| **Data Validation**   | Verify returned data against expected GraphQL types and directives (e.g., `@deprecated`).        | Ensure backward compatibility or flag deprecated fields.                                    |
| **Performance Profiling** | Measure query execution time, resolver latencies, and memory usage.                           | Optimize slow queries or reshape resolver performance.                                      |
| **Mocking & Testing** | Simulate resolvers or mock external dependencies for isolated testing.                           | Unit-test complex resolver logic without live backend calls.                               |

---

### **2. Debugging Tools & Integrations**
| Tool/Feature          | Description                                                                                     | Example Use Case                                                                             |
|-----------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **GraphQL Playground** | Interactive IDE for querying, tracing, and inspecting GraphQL schemas.                          | Test queries directly against a live schema with execution insights.                        |
| **Apollo Studio**     | Schema exploration, query tracing, and error tracking.                                         | Visualize query execution paths in a dashboard.                                            |
| **Hot Chocolate (ASP.NET)** | .NET library for GraphQL with built-in debugging middleware.                                   | Log resolver inputs/outputs for .NET-based APIs.                                            |
| **GraphQL Server Extensions** (e.g., `debugger`) | Attach debuggers to GraphQL servers (e.g., via `graphql-debugger`).                          | Step through resolver code in real-time during development.                                |
| **Postman/Newman**    | GraphQL support with execution tracing for REST/GraphQL hybrids.                              | Debug GraphQL endpoints embedded in REST APIs.                                              |
| **Introspection Queries** | Query the schema’s `__schema`, `__type`, and `__executionStats` for metadata.               | Inspect schema structure or query performance stats dynamically.                           |

---

## **Schema Reference**
### **Debugging Schema Directives**
| Directive          | Purpose                                                                                     | Example                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `@debug`           | Temporarily include/exclude fields from queries during debugging.                          | ```graphql: { user { id @debug(if: true) name } }```                                         |
| `@deprecated`      | Mark fields for debugging to flag removal in future versions.                              | ```type User { id: ID! @deprecated(reason: "Use userId instead") }```                       |
| `@skip`/`@include` | Conditionally exclude/include fields based on debug variables.                            | ```query { user { ... @skip(if: $debugMode) { oldField } } ```                            |

### **Introspection Queries**
```graphql
# Fetch schema metadata
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      fields {
        name
        type {
          name
          kind
        }
      }
    }
  }
}

# Fetch execution stats (if supported)
query {
  __executionStats {
    query {
      startTime
      endTime
      totalDuration
    }
  }
}
```

---

## **Query Examples**

### **1. Basic Query with Debugging**
```graphql
# Query to fetch user data with debugging annotations
query DebugUser($debug: Boolean!) {
  user(id: "123") {
    id
    name
    email @debug(if: $debug)  # Only include if debug flag is true
    posts {
      title
      # @include skips this field unless `debugMode` is true
      draft @include(if: $debugMode)
    }
  }
}
```

### **2. Error Handling & Validation**
```graphql
# Query that triggers a validation error (missing required field)
query InvalidQuery {
  user {
    # Missing required `id` argument
    name
  }
}
```
**Expected Error Response:**
```json
{
  "errors": [
    {
      "message": "Variable '$query' has an invalid value.",
      "path": ["user"],
      "extensions": {
        "code": "GRAPHQL_VARIABLE_VALUE_INVALID"
      }
    }
  ]
}
```

### **3. Query Tracing (Apollo Studio)**
```graphql
# Enable tracing in Apollo Playground
query {
  user(id: "123") {
    name
  }
}
```
**Tracing Output (simplified):**
```json
{
  "data": { "user": { "name": "Alice" } },
  "extensions": {
    "tracing": {
      "version": 1,
      "startTime": "2023-10-01T12:00:00Z",
      "endTime": "2023-10-01T12:00:01Z",
      "duration": 1000,
      "resolvers": [
        {
          "path": ["user"],
          "variableValues": { "id": "123" },
          "startTime": "2023-10-01T12:00:00.5Z",
          "endTime": "2023-10-01T12:00:00.8Z"
        }
      ]
    }
  }
}
```

### **4. Performance Debugging**
```graphql
# Slow query with excessive nesting
query PerformanceDebug {
  user(id: "123") {
    name
    posts {
      title
      comments {
        text
        # N+1 query anti-pattern (debug: uncomment to see the issue)
        # author { name }  # Requires N+1 resolver calls
      }
    }
  }
}
```
**Optimized Version:**
```graphql
# Batch-loaded with `@defer`/@stream (GraphQL Subscriptions)
query OptimizedUser {
  user(id: "123") {
    name
    posts {
      title
      comments {
        text
      }
    }
    # Defer author data to avoid blocking
    author @defer {
      name
    }
  }
}
```

---

## **Resolver Debugging**
### **Logging Middleware (Hot Chocolate Example)**
```csharp
// Add debugger middleware to a Hot Chocolate server
services.AddGraphQLServer()
    .AddDebugger() // Enables resolver logging
    .AddQueryType<Query>();
```
**Resolver Log Output:**
```
[DEBUG] Resolver 'UserResolver.GetUser' started (Input: { "id": "123" })
[DEBUG] Resolver 'UserResolver.GetUser' completed (Duration: 5ms)
[DEBUG] Resolver 'PostResolver.GetPosts' started (Input: { "authorId": "123" })
```

### **Debugging Resolver Failures**
```graphql
# Query that fails in a resolver
query {
  user(id: "nonexistent") {
    name
  }
}
```
**Resolver Error Handling (Node.js Example):**
```javascript
const resolvers = {
  Query: {
    user: (_, { id }, context) => {
      if (!id) throw new Error("ID is required!");
      try {
        const user = db.findUser(id);
        if (!user) throw new Error("User not found");
        return user;
      } catch (error) {
        context.errorLogger.log(error); // Custom logging
        throw new CustomError("User fetch failed", 500);
      }
    }
  }
};
```

---

## **Common Debugging Scenarios & Fixes**

| Scenario                          | Debugging Steps                                                                                     | Tools/Queries to Use                                                                         |
|-----------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| **400 Bad Request**               | Validate query syntax, variables, and schema compliance.                                          | `graphql validate` (CLI), Playground introspection.                                         |
| **Slow Queries**                  | Trace execution paths, identify N+1 queries, or expensive resolvers.                               | Query tracing (Apollo Studio), `EXPLAIN ANALYZE` (PostgreSQL-like tools).                     |
| **Resolver Crashes**              | Add logging or debugger middleware to catch exceptions.                                           | Hot Chocolate/Apollo debuggers, custom error logging.                                      |
| **Deprecated Fields**             | Use `@deprecated` directive to warn users of removed fields.                                      | Introspection query for `__type` metadata.                                                  |
| **Data Mismatch**                 | Compare graphql type definitions with database schemas.                                             | Manual schema inspection or `graphql-schema-printer` CLI tool.                               |
| **CORS/Network Issues**           | Check server configuration for CORS headers.                                                       | Browser DevTools `Network` tab, `curl` for direct API calls.                                |

---

## **Related Patterns**
1. **[GraphQL Schema Design](https://graphql.org/learn/schema/)**
   - Best practices for defining scalable, maintainable schemas (e.g., composition, unions, interfaces).

2. **[GraphQL Query Optimization](https://www.apollographql.com/docs/graphql/performance/)**
   - Techniques to avoid over-fetching (e.g., `@defer`, `@stream`, pagination).

3. **[GraphQL Subscriptions](https://www.apollographql.com/docs/graphql/subscriptions/)**
   - Real-time debugging with WebSockets (e.g., monitoring subscription errors).

4. **[GraphQL Testing](https://www.apollographql.com/docs/devtools/testing/)**
   - Unit testing resolvers and end-to-end query validation (e.g., Jest + `@graphql-testing`).

5. **[GraphQL Federation](https://www.apollographql.com/docs/federation/)**
   - Debugging multi-service schemas (e.g., entity resolution, `@extends` directives).

6. **[OpenTelemetry for GraphQL](https://opentelemetry.io/docs/)**
   - Distributed tracing for GraphQL APIs integrated with microservices.

---

## **Best Practices**
- **Enable Debug Mode in Development**: Use `@debug` directives or server-side debugging flags.
- **Validate Schemas Pre-Launch**: Use tools like `graphql-schema-validation` or `graphql-cli`.
- **Log Resolver Input/Output**: Add logging middleware for critical resolvers.
- **Leverage Introspection**: Query `__schema` to inspect available types/fields dynamically.
- **Test Queries with Mock Data**: Use `graphql-mock` or Apollo’s mocking to isolate issues.
- **Monitor Performance**: Set up alerts for slow queries (e.g., >500ms) using Apollo Studio.
- **Document Deprecations**: Clearly mark deprecated fields with `@deprecated` and provide alternatives.

---
**Key Takeaway**: GraphQL debugging combines schema introspection, query tracing, and resolver-level inspection to quickly identify issues. Start with validation, then trace execution, and finally optimize performance. Use tools like Apollo Studio, Playground, or Hot Chocolate to streamline the process.