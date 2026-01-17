# **[Pattern] GraphQL Monitoring Reference Guide**

---

## **Overview**
GraphQL Monitoring is a structured approach to observing, tracking, and improving GraphQL API performance, reliability, and developer experience. Unlike traditional REST monitoring, GraphQL’s nested, query-driven architecture requires specialized metrics—such as query depth, latency, error rates, and schema usage—to identify bottlenecks, optimize queries, and ensure scalability. This pattern outlines key concepts, implementation best practices, and tools/frameworks for implementing GraphQL monitoring effectively.

---

## **Implementation Details**

### **Key Concepts**
1. **Metrics to Monitor**
   - **Query Performance**:
     - Latency (p95, p99 percentiles).
     - Execution time (resolved vs. query time).
     - Request volume (RPS, throughput).
   - **Schema Usage**:
     - Field-level analytics (popular fields, dead code).
     - Federation/relay integration stats (if applicable).
   - **Errors & Failures**:
     - Error types (validation, runtime, network).
     - Persistent vs. transient errors.
   - **Cache Performance**:
     - Cache hit/miss ratios.
     - Cache invalidation patterns.

2. **Monitoring Layers**
   - **Client-Side** (browser/front-end):
     Monitor latency, network errors, and failed requests with tools like **Apollo Client DevTools**, **Relay Network**, or custom instrumentation.
   - **Server-Side** (backend):
     Track execution time, database queries, and error rates via **GraphQL middleware** (e.g., Apollo Server’s `createServer`), **Prometheus**, or **OpenTelemetry**.
   - **Schema Layer**:
     Audit schema complexity, versioning, and usage with tools like **GraphQL Inspector** or **Schema Report**.

3. **Alerting & Anomaly Detection**
   - Set thresholds for:
     - High-latency queries (>500ms p99).
     - Spiky traffic (RPS exceeding baseline by 3σ).
     - Error rates (>1% of requests).
   - Use tools like **Datadog**, **New Relic**, or **Grafana Alerts**.

---

### **Schema Reference**
Below is a core **GraphQL schema** for monitoring purposes. Extend this with your existing schema or integrate via middleware.

| Query Type          | Description                                                                 | Example Fields                                                                 |
|---------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **`monitoringStats`** | Aggregated metrics for a given time range (e.g., last 5 minutes).         | `totalQueries`, `avgLatencyMs`, `errorRate`, `cacheHitRate`, `topFieldsByUsage` |
| **`queryPerformance`** | Details on a specific query (idempotent via `operationName`).            | `executionTimeMs`, `resolvedFields`, `databaseQueries`, `errors`              |
| **`schemaAudit`**     | Schema complexity, field popularity, and potential optimizations.        | `averageDepth`, `unusedFields`, `fieldCount`, `complexityScore`               |
| **`errorLog`**        | Historical error tracking with contextual data.                           | `timestamp`, `errorMessage`, `query`, `stackTrace`, `retryCount`              |
| **`cacheMetrics`**    | Cache performance metrics (e.g., Redis/LocalStore).                        | `hitCount`, `missCount`, `cacheSize`, `ttlDistribution`                      |

**Example Schema Fragment:**
```graphql
type Query {
  monitoringStats(timeWindow: TimeWindow!): MonitoringStats!
  queryPerformance(operationName: String!): QueryPerformance!
  schemaAudit: SchemaAudit!
  errorLog(limit: Int = 100, errorType: String): [ErrorLog!]!
}

type MonitoringStats {
  totalQueries: Float!
  avgLatencyMs: Float!
  errorRate: Float!
  cacheHitRate: Float!
  topFieldsByUsage(limit: Int = 10): [FieldUsage!]!
}

type FieldUsage {
  fieldName: String!
  queryCount: Int!
  depth: Int!
}
```

---

## **Query Examples**

### **1. Fetch Aggregated Monitoring Stats**
```graphql
query GetMonitoringStats {
  monitoringStats(timeWindow: LAST_5_MINUTES) {
    totalQueries
    avgLatencyMs
    errorRate
    topFieldsByUsage(limit: 5) {
      fieldName
      queryCount
    }
  }
}
```
**Response:**
```json
{
  "data": {
    "monitoringStats": {
      "totalQueries": 1245,
      "avgLatencyMs": 187.3,
      "errorRate": 0.008,
      "topFieldsByUsage": [
        { "fieldName": "user.id", "queryCount": 987 },
        { "fieldName": "post.title", "queryCount": 654 }
      ]
    }
  }
}
```

---

### **2. Inspect Query Performance by Operation Name**
```graphql
query GetQueryPerformance {
  queryPerformance(operationName: "getUserWithPosts") {
    executionTimeMs
    resolvedFields
    errors {
      message
      path
    }
  }
}
```
**Response:**
```json
{
  "data": {
    "queryPerformance": {
      "executionTimeMs": 321,
      "resolvedFields": 15,
      "errors": [
        { "message": "Field 'post.comments' not found", "path": ["post", "comments"] }
      ]
    }
  }
}
```

---

### **3. Schema Audit for Optimization**
```graphql
query GetSchemaAudit {
  schemaAudit {
    averageDepth
    unusedFields
    complexityScore
  }
}
```
**Response:**
```json
{
  "data": {
    "schemaAudit": {
      "averageDepth": 4.2,
      "unusedFields": ["old.field.deprecated"],
      "complexityScore": 1250
    }
  }
}
```

---

### **4. Retrieve Error Logs for Debugging**
```graphql
query GetErrorLogs {
  errorLog(limit: 5, errorType: "NEEDS_RETRY") {
    timestamp
    query
    errorMessage
  }
}
```
**Response:**
```json
{
  "data": {
    "errorLog": [
      {
        "timestamp": "2023-10-01T12:00:00Z",
        "query": "query { getUser(id: 1) { name } }",
        "errorMessage": "Database timeout"
      }
    ]
  }
}
```

---

## **Implementation Techniques**

### **1. Middleware-Based Instrumentation (Apollo Server Example)**
Use Apollo Server’s `createServer` to add monitoring hooks:
```javascript
const { ApolloServer } = require('apollo-server');
const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [
    {
      requestDidStart() {
        return {
          willSendResponse({ request, response }) {
            // Log metrics to Prometheus/OpenTelemetry
            const metrics = {
              latencyMs: response.executionTime,
              query: request.query,
              errors: response.errors?.length > 0,
            };
            // Emit to monitoring system
          },
        };
      },
    },
  ],
});
```

### **2. Client-Side Tracking (Apollo Client)**
Enable **auto-capture** with `@apollo/client`:
```javascript
import { ApolloClient, InMemoryCache } from '@apollo/client';
import { createClientSideMonitoring } from './monitoring';

const client = new ApolloClient({
  cache: new InMemoryCache(),
  link: ApolloLink.from([
    createClientSideMonitoring(),
    // Other links...
  ]),
});
```

### **3. Schema Analysis Tools**
- **GraphQL Inspector**: Detect unused fields/dead code.
  ```bash
  npx graphql-inspector schema.graphql
  ```
- **Schema Report**: Generate HTML reports.
  ```bash
  npx graphql-schema-report schema.graphql --output report.html
  ```

### **4. Integration with APM Tools**
- **Prometheus + Grafana**:
  Expose metrics via `/metrics` endpoint (e.g., `http_metrics_server`).
  ```yaml
  # prometheus.yml
  scrape_configs:
    - job_name: 'graphql'
      metrics_path: '/metrics'
      static_configs:
        - targets: ['localhost:4000']
  ```
- **Datadog**:
  Use Datadog’s OpenTelemetry SDK for distributed tracing.

---

## **Related Patterns**

1. **Rate Limiting**
   - Combine with monitoring to detect abusive queries (e.g., `QueryTooDeep` errors).
   - Tools: **Apollo Rate Limiting**, **Dgraph’s Throttling**.

2. **Caching Strategies**
   - Use cache metrics to optimize hits/misses (e.g., Redis vs. in-memory).
   - Pattern: **Persisted Queries** + **DataLoader**.

3. **Federation Monitoring**
   - Track federation-specific metrics (e.g., entity resolution latency).
   - Tools: **Apollo Federation Insights**.

4. **Query Complexity**
   - Enforce `maxComplexity` rules during development (e.g., via `graphql-validation-complexity`).
   - Integrate with monitoring to flag high-complexity queries.

5. **Canary Deployments**
   - Gradually roll out schema changes and monitor usage/errors.
   - Tools: **Flagsmith**, **LaunchDarkly**.

6. **Observability Pipeline**
   - Correlate logs (e.g., ELK Stack) with metrics (Prometheus) and traces (Jaeger).
   - OpenTelemetry: Unified instrumentation for all layers.

---

## **Best Practices**
1. **Instrument Early**: Add monitoring to staging environments during development.
2. **Sample High-Volume Queries**: Avoid overwhelming your monitoring system.
3. **Avoid Query Leaks**: Sanitize client-side logs to prevent exposing sensitive data.
4. **Schema Versioning**: Tag monitoring metrics by schema version (e.g., `v2.1.0`).
5. **Automate Alerts**: Use SLOs (Service Level Objectives) to define acceptable error budgets.
6. **Cost Optimization**: Monitor expensive fields (e.g., `deeply.nested.array`) and optimize.

---
## **Troubleshooting**
| Issue                          | Diagnosis                          | Solution                                  |
|--------------------------------|------------------------------------|-------------------------------------------|
| High latency in `queryPerformance` | Check `databaseQueries` field.   | Optimize joins/indexes or add caching.   |
| 5xx errors spiking             | Review `errorLog` for patterns.   | Implement retry logic or circuit breakers.|
| Unused fields in `schemaAudit` | Deprecated APIs or unused types. | Deprecate fields with `@deprecated` tag.  |
| Cache hit ratio <20%          | Cold starts or stale data.       | Adjust TTL or pre-warm cache.             |

---
**See Also**:
- [GraphQL Depth-First Search (DFS) Optimization](https://www.apollographql.com/blog/graphql/optimizing-graphql-performance/)
- [OpenTelemetry for GraphQL](https://opentelemetry.io/docs/instrumentation/runtimes/graphql/)