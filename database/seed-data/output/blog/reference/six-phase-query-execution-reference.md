---
**[Pattern] Six-Phase Query Execution Pipeline – Reference Guide**
*Optimized GraphQL Query Processing*

---

## **1. Overview**
The **Six-Phase Query Execution Pipeline** ensures GraphQL queries are processed efficiently while maintaining security, performance, and correctness. This pattern breaks query execution into six sequential phases:

1. **Request Validation** – Validates syntax, schema alignment, and client permissions.
2. **Authorization Rule Checking** – Enforces access control before execution.
3. **Query Plan Optimization** – Compiles the query into an efficient execution plan.
4. **Database Execution** – Executes the plan against the data layer.
5. **Result Projection** – Shapes raw results into the client’s expected GraphQL response.
6. **Error Handling** – Captures, categorizes, and formats errors for clients.

This pattern decouples concerns, improves traceability, and enables optimization at each phase. It’s ideal for high-scale systems where query complexity or security requirements demand granular control.

---

## **2. Schema Reference**
The following schema defines core interfaces and directives to support the pipeline phases.

| **Component**               | **Type/Description**                                                                                     | **Key Attributes**                                                                                     |
|-----------------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `QueryPhase`                | Enum defining the six pipeline phases.                                                                   | `VALIDATION`, `AUTHORIZATION`, `OPTIMIZATION`, `EXECUTION`, `PROJECTION`, `ERROR_HANDLING`          |
| `PhaseInterceptor`          | Interface for interceptor functions at each phase.                                                        | `phase: QueryPhase!`<br>`handler: PhaseHandler!` (custom logic per phase)                            |
| `QueryValidationRule`       | Rules for structural query validation (e.g., type existence, depth limits).                              | `field: String!`<br>`message: String`<br>`errorCode: String`                                          |
| `AuthorizationPolicy`       | Defines access control rules for fields/resolvers (e.g., `isAdmin`, `hasPermission`).                  | `condition: String!` (JMESPath or custom logic)<br>`requiredRole: String`                           |
| `OptimizationStrategy`      | Configures query plan optimizations (e.g., batching, filtering).                                         | `strategy: String!` (e.g., `BATCH_AND_FILTER`)<br>`threshold: Int`                                  |
| `ProjectionDirective`       | GraphQL directive to customize result shaping (e.g., `@map`, `@filter`).                                | `transform: String!`<br>`args: JSON`                                                                 |
| `ErrorFormatter`            | Formats errors for clients (e.g., GraphQL errors vs. HTTP responses).                                     | `phase: QueryPhase!`<br>`includeDetails: Boolean`                                                    |

---
**Example Schema Fragment:**
```graphql
directive @authorize(condition: String!) on FIELD_DEFINITION
directive @optimize(strategy: OptimizationStrategy = BATCH_AND_FILTER) on QUERY
directive @project(transform: String!) on FIELD_DEFINITION
```

---

## **3. Query Examples**
### **A. Basic Query with Interceptors**
```graphql
query GetUser($id: ID!) {
  user(id: $id) @authorize(condition: "owner == $ctx.requesterId") {
    id
    name @project(transform: "uppercase")
    posts {
      title
    }
  }
}
```
- **Phase Breakdown**:
  1. **Validation**: Checks `user` type and `@authorize` directive syntax.
  2. **Authorization**: Verifies `owner == $ctx.requesterId` using a middleware (e.g., [Apollo’s `AuthorizationRule`](https://www.apollographql.com/docs/enterprise/features/authorization/)).
  3. **Optimization**: Applies `@optimize` to batch `posts` resolvers.
  4. **Execution**: Fetches user and posts data.
  5. **Projection**: Converts `name` to uppercase via `@project`.
  6. **Error Handling**: Returns `403 Forbidden` if authorization fails.

---

### **B. Complex Query with Dynamic Optimization**
```graphql
query GetAnalytics($startDate: DateTime!) {
  orders(limit: 100, filter: { date: { gt: $startDate } }) @optimize(
    strategy: BATCH_AND_FILTER,
    threshold: 50
  ) {
    totalAmount
    items {
      product @project(transform: "pricesToCurrency(currency: 'USD')")
    }
  }
}
```
- **Key Behaviors**:
  - **Optimization Phase**: Batches `items` resolvers if `threshold` (50) is exceeded.
  - **Projection**: Converts `prices` to USD using a custom resolver.
  - **Error Handling**: Returns a `422 Unprocessable Entity` if `threshold` causes a timeout.

---

### **C. Error Handling Example**
```graphql
query InvalidQuery {
  user(id: "nonexistent") # Missing @authorize directive
}
```
- **Error Flow**:
  1. **Validation Phase**: Fails with `GraphQLValidationError` (code: `MISSING_AUTH`).
  2. **Error Handling**: Returns:
    ```json
    {
      "errors": [
        {
          "message": "Field 'user' requires @authorize directive",
          "path": ["user"],
          "extensions": {
            "code": "MISSING_AUTH",
            "phase": "VALIDATION"
          }
        }
      ]
    }
    ```

---

## **4. Implementation Details**
### **Core Architecture**
1. **Phase Interceptors**:
   - Register interceptors per phase using a **decorator pattern** (e.g., Express middleware, GraphQL resolvers with `beforeResolve` hooks).
   - Example (Node.js with GraphQL):
     ```javascript
     const { GraphQLSchema } = require('graphql');
     const { createPhaseInterceptor } = require('./pipeline');

     const schema = new GraphQLSchema({
       query: {
         user: {
           resolve: async (_, args, ctx) => {
             // Authorization interceptor example
             const authorized = await ctx.interceptors.AUTHORIZATION(
               { phase: 'AUTHORIZATION', resolver: resolve },
               args,
               ctx
             );
             if (!authorized) throw new Error('Unauthorized');
             return resolve(_, args, ctx);
           },
           // ... other phases via decorators
         }
       }
     });
     ```

2. **Query Plan Optimization**:
   - Use libraries like:
     - [DataLoader](https://github.com/graphql/dataloader) for batching.
     - [GraphQL Persisted Queries](https://www.apollographql.com/docs/apollo-server/features/persisted-queries/) to cache plans.
   - Custom strategies: Implement `OptimizationStrategy` as a class with `apply()` methods.

3. **Projection**:
   - **Directives**: Use `@project` with a registry of transform functions (e.g., `uppercase`, `currencyConversion`).
   - **Example Registry**:
     ```javascript
     const projectionTransforms = {
       uppercase: (value) => value?.toUpperCase(),
       currencyConversion: (value, args) => `$${value}`.replace(/\d(?=(\d{3})+\.)/g, '$&,')
     };
     ```

4. **Error Handling**:
   - **Phase-Specific Errors**: Extend `GraphQLError` with `phase` and `errorCode`:
     ```javascript
     class ValidationError extends GraphQLError {
       constructor(message, phase, errorCode) {
         super(message);
         this.extensions = { phase, errorCode };
       }
     }
     ```
   - **Client-Facing Errors**: Map phases to HTTP codes (e.g., `AUTHORIZATION` → `403`).

---

### **Performance Considerations**
| **Phase**            | **Optimization Techniques**                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------|
| **Validation**        | Use [GraphQL’s built-in validation](https://graphql.org/graphql-spec/June2018/#sec-Schema-Validation) + custom rules. |
| **Authorization**     | Cache `AuthorizationPolicy` results (e.g., Redis).                                       |
| **Optimization**      | Profile queries with tools like [GraphQL Playground](https://www.graphql-playground.com/) to identify bottlenecks. |
| **Execution**         | Leverage [Apollo Federation](https://www.apollographql.com/docs/apollo-server/federation/) for microservices. |
| **Projection**        | Pre-compute transforms (e.g., cache `uppercase` results).                                |
| **Error Handling**    | Stream errors to clients (e.g., [GraphQL over HTTP](https://github.com/enisdenjo/graphql-ws)). |

---

## **5. Related Patterns**
1. **[Query Depth Limit](https://www.apollographql.com/docs/apollo-server/performance/query-depth-limit/)**
   - Enforce `MAX_DEPTH` in the **Validation Phase** to prevent N+1 queries.
   - *Example*: Configure in `apollo-server`:
     ```javascript
     server.applyMiddleware({
       queryDepthLimit: 5,
     });
     ```

2. **[GraphQL Persisted Queries](https://www.apollographql.com/docs/apollo-server/features/persisted-queries/)**
   - Cache query plans in the **Optimization Phase** to reduce parsing overhead.

3. **[Federated Queries](https://www.apollographql.com/docs/apollo-server/federation/)**
   - Split execution across services in the **Database Execution Phase** using Apollo Federation.

4. **[Query Complexity Analysis](https://github.com/rootsongjc/graphql-query-complexity)**
   - Validate complexity in the **Validation Phase** to prevent expensive queries.

5. **[Rate Limiting](https://www.apollographql.com/docs/apollo-server/rate-limiting/)**
   - Enforce rate limits at the **Request Validation** phase via middleware (e.g., [Apollo Rate Limit](https://github.com/felix-feyer/apollo-server-rate-limit)).

---

## **6. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|-------------------------------------|----------------------------------------|------------------------------------------------------------------------------|
| High latency in Authorization      | Slow policy checks                     | Cache results of `AuthorizationPolicy` in Redis.                             |
| Invalid projection transforms       | Missing `@project` handler             | Register all transforms in `projectionTransforms` (see **Implementation**). |
| Timeouts in Database Execution     | Unoptimized queries                    | Use `OptimizationStrategy` with `BATCH_AND_FILTER` and `threshold`.        |
| Duplicate data in results          | Missing `DataLoader`                   | Apply `DataLoader` in the **Execution Phase** for batching.                 |
| Client sees incomplete errors       | Phase-specific errors not formatted    | Extend `ErrorFormatter` to include `phase` and `errorCode` in responses.   |

---

## **7. Further Reading**
- [GraphQL Spec: Query Execution](https://graphql.org/graphql-spec/June2018/#sec-Execution)
- [Apollo Server Phase Interceptors](https://www.apollographql.com/docs/apollo-server/performance/phases/)
- [GraphQL Directives Guide](https://www.apollographql.com/docs/apollo-server/schema/customization/directives/)