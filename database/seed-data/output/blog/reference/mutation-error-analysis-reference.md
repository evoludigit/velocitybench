---

# **[Pattern] Mutation Error Analysis – Reference Guide**

---

## **Overview**
Mutation error analysis is a **testing and debugging pattern** designed to systematically identify, categorize, and resolve failures occurring in GraphQL mutations. This pattern helps developers:
- **Pinpoint** why mutations fail (e.g., validation errors, schema conflicts, runtime exceptions).
- **Classify** errors by severity (e.g., client-side vs. server-side) and impact (e.g., partial failures).
- **Automate** error reporting and recovery via logs, alerts, or retry mechanisms.
- **Validate** error handling logic against test cases (e.g., mocking failures for edge cases).

It is especially critical for **state-changing operations** (e.g., `createUser`, `updateOrder`) where failures may propagate unintended side effects. This pattern integrates with **GraphQL execution pipelines**, error handlers, and monitoring tools (e.g., OpenTelemetry, Sentry).

---

## **Schema Reference**
Below are key components of the pattern, represented in a **simplified schema** for implementation consistency.

| **Component**               | **Description**                                                                                     | **Example Fields**                                                                                     | **Data Type**                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------|
| **ErrorContext**            | Metadata attached to mutation failures to enable analysis.                                          | `mutationName`, `timestamp`, `correlationId`, `source` (client/server)                               | `Object`                          |
| **ErrorCategory**           | Predefined classification of error types (e.g., validation, auth, database).                      | `type` (`VALIDATION_ERROR`, `AUTH_FAILED`, `DB_TIMEOUT`)                                             | `Enum`                            |
| **ErrorDetails**            | Granular breakdown of the failure.                                                                | `message`, `path` (GraphQL field path), `code` (custom error code), `stackTrace` (if applicable)      | `Object`                          |
| **Resolution**              | Suggested fixes or workarounds for the error.                                                     | `steps`, `references` (links to docs/Wiki), `isRecurring`                                            | `Object`                          |
| **ErrorLogEntry**           | Persisted record of mutation failures (for auditing/replay debugging).                              | `errorContext`, `errorDetails`, `severity` (`CRITICAL`, `WARNING`, `INFO`), `resolvedAt`             | `Object`                          |
| **MutationFailureTrigger**  | Patterns that cause frequent failures (e.g., race conditions, inconsistent inputs).                | `triggerType` (`NULL_INPUT`, `CONCURRENCY`), `reproductionSteps`                                    | `Object`                          |

---

## **Implementation Details**

### **1. Core Workflow**
Mutation error analysis follows a **4-phase lifecycle**:
1. **Capture**:
   - Attach `ErrorContext` and `ErrorDetails` to failed mutations using GraphQL’s `onError` middleware.
   - Example middleware:
     ```javascript
     const { GraphQLServer } = require('graphql-yoga');

     const server = new GraphQLServer({
       typeDefs,
       resolvers,
       onError: (error) => {
         // Log and classify the error
         const errorEntry = {
           mutationName: error.path.join('.'),
           errorContext: { source: 'server', timestamp: new Date() },
           errorDetails: { ...error, type: CLASSIFY_ERROR(error) },
         };
         logError(errorEntry);
         return error; // Propagate to client
       },
     });
     ```

2. **Classify**:
   - Use helper functions to **auto-categorize errors** (e.g., check `error.extensions.code` for GraphQL-standard codes like `UNAUTHENTICATED`).
   - Example classification:
     ```javascript
     function CLASSIFY_ERROR(error) {
       switch (error.extensions?.code) {
         case 'UNAUTHENTICATED': return { type: 'AUTH_FAILED', path: error.path };
         case 'BAD_USER_INPUT': return { type: 'VALIDATION_ERROR', details: error.extensions?.invalidArgs };
         default: return { type: 'UNKNOWN', stackTrace: error.extensions?.stacktrace };
       }
     }
     ```

3. **Analyze**:
   - Query persisted `ErrorLogEntry` aggregates (e.g., top 5 recurring errors by `ErrorCategory`).
   - Enrich analysis with **business context** (e.g., user ID, mutation frequency).

4. **Resolve**:
   - Trigger alerts for **critical errors** (e.g., `DB_TIMEOUT`).
   - Suggest fixes via `Resolution` field (e.g., "Retry with exponential backoff for timeout errors").
   - Escalate to a **dedicated error dashboard** (e.g., Grafana + Prometheus).

---

### **2. Key Components**
#### **A. ErrorContext**
- **Purpose**: Correlate errors across microservices (e.g., track a failed `createOrder` mutation’s cascading effects).
- **Implementation**:
  - Inject `correlationId` into the `ErrorContext` during mutation execution (e.g., via middleware or tracing headers).
  - Example:
    ```typescript
    middleware((ctx, next) => {
      ctx.correlationId = uuidv4();
      return next();
    });
    ```

#### **B. ErrorCategory**
- **Purpose**: Standardize error handling (e.g., group all `403 Forbidden` as `AUTH_FAILED`).
- **Enumeration**:
  ```typescript
  enum ErrorCategory {
    VALIDATION_ERROR = 'VALIDATION_ERROR',
    AUTH_FAILED = 'AUTH_FAILED',
    DB_ERROR = 'DB_ERROR',
    RATE_LIMITED = 'RATE_LIMITED',
    UNKNOWN = 'UNKNOWN',
  }
  ```

#### **C. ErrorLogEntry**
- **Storage**: Log entries to a database (e.g., PostgreSQL) or time-series DB (e.g., InfluxDB) for performance.
- **Schema Example**:
  ```sql
  CREATE TABLE error_logs (
    id UUID PRIMARY KEY,
    mutation_name VARCHAR(255),
    error_category VARCHAR(50),
    severity VARCHAR(20),
    details JSONB,
    resolved_at TIMESTAMP,
    correlation_id UUID,
    tags VARCHAR[]  -- e.g., ["inventory", "payment"]
  );
  ```

#### **D. MutationFailureTrigger**
- **Purpose**: Detect systemic issues (e.g., "90% of `updateUser` failures occur during peak hours").
- **Implementation**:
  - Use **time-series analysis** (e.g., Prometheus metrics) to correlate `ErrorLogEntry` timestamps with system metrics (e.g., CPU load).
  - Example query:
    ```graphql
    query TriggersForErrorCategory($category: String!) {
      errorTriggers(category: $category) {
        pattern { type: String, frequency: Float }
        affectedMutations { name: String, failureRate: Float }
      }
    }
    ```

---

### **3. Error Handling Strategies**
| **Strategy**               | **When to Use**                                  | **Implementation**                                                                                     |
|----------------------------|--------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Client-Side Retry**      | Idempotent mutations (e.g., `fetchUserProfile`).   | Use exponential backoff with `retryIf` (e.g., `error.extensions.code === 'NETWORK_ERROR'`).         |
| **Server-Side Recovery**   | Critical failures (e.g., `createOrder`).        | Implement compensating transactions (e.g., rollback partial updates).                                  |
| **Dead Letter Queue (DLQ)**| Non-recoverable errors.                          | Route failed mutations to a queue (e.g., Kafka) for manual review.                                      |
| **Fallback Values**        | Partial failures (e.g., `updateUser` fails for `email` but succeeds for `name`). | Return a subset of successful fields (e.g., `{ user: { name: "Alice" } }`).                           |

---

## **Query Examples**
### **1. Retrieve Error Logs by Category**
```graphql
query GetAuthFailures {
  errorLogs(category: "AUTH_FAILED", limit: 10) {
    mutationName
    errorDetails { message }
    correlationId
    resolvedAt
  }
}
```

### **2. Find Recurring Triggers**
```graphql
query FindRateLimitTriggers {
  errorTriggers(category: "RATE_LIMITED") {
    pattern { type: String, frequency: Float }
    affectedMutations { name: String, avgLatencyMs: Float }
  }
}
```

### **3. Check Mutation-Specific Failures**
```graphql
query MutationFailureRate($mutation: String!) {
  errorLogs(mutationName: $mutation) {
    count
    failureRate: count / totalInvocations
    topErrors { errorDetails { message } }
  }
}
```

---

## **Related Patterns**
1. **[Error Handling Integration Pattern](https://example.com/error-handling)**
   - Extends this pattern with **centralized error policies** (e.g., retry logic, fallback responses).
   - *Use Case*: Shared error handling across GraphQL and REST APIs.

2. **[Distributed Tracing Pattern](https://example.com/distributed-tracing)**
   - Correlates mutation errors with **cross-service traces** (e.g., link a failed `checkout` mutation to a downstream payment failure).
   - *Tools*: OpenTelemetry, Jaeger.

3. **[Idempotency Pattern](https://example.com/idempotency)**
   - Ensures mutations can be safely retried (critical for error recovery).
   - *Example*: Use `Idempotency-Key` headers to deduplicate requests.

4. **[Schema Evolution Testing](https://example.com/schema-evolution)**
   - Validates mutations against **schema drift** (e.g., a deprecated field causing failures).
   - *Tool*: GraphQL Playground + schema validators.

5. **[Circuit Breaker Pattern](https://example.com/circuit-breaker)**
   - Temporarily **blocks** failing mutations to prevent cascading failures (e.g., during DB outages).
   - *Implementation*: Hystrix or custom middleware.

---

## **Best Practices**
1. **Standardize Error Messages**:
   - Avoid vague errors (e.g., "Internal Server Error"). Use **machine-readable codes** (e.g., `INVALID_ARGUMENT_AGE`).

2. **Instrument Critical Mutations**:
   - Add tracing to **high-risk operations** (e.g., `transferFunds`) using OpenTelemetry.

3. **Automate Alerts**:
   - Set up dashboards (e.g., Grafana) for:
     - Spikes in `DB_ERROR` frequency.
     - Recurring `AUTH_FAILED` for specific users.

4. **Test Error Scenarios**:
   - Include **mutation failure tests** in your CI/CD pipeline (e.g., mock `403 Forbidden` responses).

5. **Document Resolutions**:
   - Keep the `Resolution` field updated with **known fixes** (e.g., "Apply patch to auth service").

---
**See Also**:
- [GraphQL Error Handling Spec](https://spec.graphql.org/draft/#sec-Errors)
- [Error Classification Taxonomy](https://example.com/error-taxonomy)