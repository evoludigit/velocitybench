---
# **[Pattern] GraphQL Observability Reference Guide**

---

## **Overview**
GraphQL Observability is a pattern for tracking, monitoring, and debugging **GraphQL API performance, query execution, and data flow** in real-time. Observability helps identify bottlenecks, optimize queries, and ensure API reliability by collecting structured metrics, tracing requests, and logging critical events. This guide covers key concepts, schema definitions, query examples, and related patterns for implementing **GraphQL Observability**.

---

## **Key Concepts**
GraphQL Observability relies on three core components:

| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Tracing**               | Records request flow (e.g., query execution time, dependencies, errors) using OpenTelemetry or X-Ray. |
| **Metrics**               | Aggregated data (e.g., latency, error rates, query depth) stored in tools like Prometheus or Grafana. |
| **Logging**               | Structured logs of GraphQL execution (variables, fragments, errors) for debugging.               |
| **Instrumentation**       | Adding observability hooks to a GraphQL server (e.g., `@graphql-tools` or Apollo Server plugins).   |

---

## **Schema Reference**
The core schema for observability includes:
- **Request-level traces** (latency, start/end timestamps).
- **Field-level performance** (time spent per resolver).
- **Error tracking** (type, location, stack trace).
- **Dependency metrics** (database calls, external API latency).

### **Key Schema Fields**
| **Field**                     | **Type**          | **Description**                                                                                     |
|-------------------------------|-------------------|-----------------------------------------------------------------------------------------------------|
| `requestId`                   | `ID!`             | Unique identifier for tracing a GraphQL request.                                                   |
| `query`                       | `String!`         | Original query string (sanitized for security).                                                   |
| `variables`                   | `JSON`            | Input variables for the query.                                                                    |
| `startTime`                   | `DateTime!`       | Timestamp when the request began.                                                                   |
| `endTime`                     | `DateTime!`       | Timestamp when the request completed.                                                              |
| `durationMs`                  | `Float!`          | Total execution time in milliseconds.                                                              |
| `extensions`                  | `GraphQLObservabilityExtensions` | Nested object for detailed metrics (see below).                                                  |
| `errors`                      | `[GraphQLError!]` | List of errors encountered (type, path, message).                                                  |

### **Nested `GraphQLObservabilityExtensions` Schema**
| **Field**                     | **Type**          | **Description**                                                                                     |
|-------------------------------|-------------------|-----------------------------------------------------------------------------------------------------|
| `fieldPerformance`            | `[FieldPerformance!]` | Array of resolver-level timing data.                                                             |
| `dependencyLatency`           | `[DependencyLatency!]` | Latency metrics for external calls (e.g., databases).                                            |
| `samplingRate`                | `Float`           | Fraction of requests instrumented (for distributed tracing).                                        |

#### **Field Performance Subtype**
| **Field**                     | **Type**          | **Description**                                                                                     |
|-------------------------------|-------------------|-----------------------------------------------------------------------------------------------------|
| `fieldName`                   | `String!`         | Name of the resolved GraphQL field.                                                                |
| `startTime`                   | `DateTime!`       | When resolver began execution.                                                                     |
| `durationMs`                  | `Float!`          | Time taken by resolver.                                                                             |
| `parentField`                 | `String`          | Parent field in the query (optional).                                                              |

#### **Dependency Latency Subtype**
| **Field**                     | **Type**          | **Description**                                                                                     |
|-------------------------------|-------------------|-----------------------------------------------------------------------------------------------------|
| `dependencyType`              | `String!`         | e.g., `"database"`, `"externalAPI"`.                                                               |
| `name`                        | `String`          | Identifier (e.g., `"usersDB"`).                                                                    |
| `latencyMs`                   | `Float!`          | Time spent on the dependency.                                                                        |
| `status`                      | `String!`         | `"success"`/`"failed"` (with error details if applicable).                                        |

---

## **Implementation Details**
### **1. Setup Instrumentation**
Use a GraphQL server plugin to auto-instrument requests. Examples:

#### **Apollo Server (Node.js)**
```javascript
const { ApolloServer } = require('apollo-server');
const { createObservabilityPlugin } = require('graphql-observability');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [createObservabilityPlugin()],
});
```

#### **GraphQL Yoga (Node.js)**
```javascript
const { GraphQLServer } = require('graphql-yoga');
const { observabilityPlugin } = require('graphql-observability');

const server = new GraphQLServer({ typeDefs, resolvers });
server.use(observabilityPlugin);
```

#### **Hasura (PostgreSQL)**
Enable observability via Hasura Admin Console:
1. Navigate to **Settings > Observability**.
2. Enable **GraphQL Tracing** and configure sampling rate.

---

### **2. Export Metrics**
Send observability data to backends:
- **OpenTelemetry**: Use the [`@opentelemetry/instrumentation-graphql`](https://www.npmjs.com/package/@opentelemetry/instrumentation-graphql) package.
- **Prometheus**: Scrape `/metrics` endpoints (e.g., with `prom-client`).
- **Custom Storage**: Push data to a database (e.g., PostgreSQL, MongoDB).

**Example OpenTelemetry Integration:**
```javascript
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { GraphQLInstrumentation } from '@opentelemetry/instrumentation-graphql';

registerInstrumentations({
  instrumentations: [new GraphQLInstrumentation()],
});
```

---

### **3. Query Examples**
#### **Fetch Observability Data**
```graphql
query GetObservabilityData($limit: Int = 10) {
  graphqlObservability(
    limit: $limit
    sortBy: { field: "durationMs", order: DESC }
  ) {
    requestId
    query
    durationMs
    errors {
      message
      path
    }
    extensions {
      fieldPerformance {
        fieldName
        durationMs
      }
    }
  }
}
```

#### **Filter by Error Type**
```graphql
query FindFailedQueries($errorType: String) {
  graphqlObservability(
    filter: { errors: { type: { eq: $errorType } } }
  ) {
    requestId
    query
    errors {
      message
      stacktrace
    }
  }
}
```

#### **Analyze Dependency Latency**
```graphql
query CheckDatabaseLatency($thresholdMs: Float) {
  graphqlObservability(
    filter: {
      extensions: {
        dependencyLatency: {
          latencyMs: { gt: $thresholdMs }
          dependencyType: { eq: "database" }
        }
      }
    }
  ) {
    requestId
    extensions {
      dependencyLatency {
        dependencyType
        name
        latencyMs
      }
    }
  }
}
```

---

## **Requirements & Tools**
| **Component**               | **Tools/Libraries**                                                                                     |
|------------------------------|---------------------------------------------------------------------------------------------------------|
| **Tracing**                  | OpenTelemetry, AWS X-Ray, Jaeger, Zipkin.                                                               |
| **Metrics**                  | Prometheus, Grafana, Datadog, New Relic.                                                               |
| **Logging**                  | ELK Stack (Elasticsearch, Logstash, Kibana), Loki.                                                   |
| **Instrumentation**          | `@graphql-tools/observability`, `apollo-server-plugin-observability`, Hasura Observability.          |
| **Storage**                  | PostgreSQL (TimescaleDB), MongoDB, ClickHouse.                                                         |

---

## **Error Handling**
| **Error Type**               | **GraphQL Error Path**       | **Observability Field**                          | **Mitigation**                                                                 |
|------------------------------|-------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------|
| Invalid Query Syntax         | N/A                           | `errors[type: "SyntaxError"]`                   | Validate queries with [`graphql-parse-resolve-info`](https://www.npmjs.com/package/graphql-parse-resolve-info). |
| Resolver Timeout             | Field path                    | `extensions.fieldPerformance[durationMs > 500]`   | Implement retry logic or circuit breakers.                                    |
| Database Connection Failures | Database resolver             | `extensions.dependencyLatency[status: "failed"]` | Set up connection pooling (e.g., PgBouncer).                                  |
| Authentication Errors        | Auth middleware               | `errors[path: "__auth"]`                        | Log failed attempts and enforce rate limits.                                  |

---

## **Related Patterns**
1. **[GraphQL Persisted Queries](https://www.apollographql.com/docs/apollo-server/performance/persisted-queries/)**
   - Reduces payload size and enables caching for observability data.

2. **[Query Depth Limiting](https://www.prisma.io/docs/guides/graphql/deeply-nested-selections)**
   - Prevents overly complex queries that overwhelm observability tools.

3. **[Canary Releases for GraphQL](https://www.datadoghq.com/blog/canary-deployments)**
   - Gradually roll out changes while monitoring observability metrics.

4. **[GraphQL Schema Stitching](https://www.apollographql.com/docs/apollo-server/data/federation/)**
   - Distributes observability across microservices with federation gateways.

5. **[Rate Limiting](https://www.hashicorp.com/blog/rate-limiting-with-consul)**
   - Protects APIs from abuse while maintaining observability on traffic spikes.

---

## **Best Practices**
- **Sample Requests**: Use a **10% sampling rate** for distributed tracing to avoid overhead.
- **Anonymize Sensitive Data**: Mask PII (e.g., user IDs) in logs/traces.
- **Alert on Anomalies**: Set up alerts for:
  - `durationMs > 2x baseline`.
  - `errors > 1% rate`.
- **Correlate Traces**: Link traces with HTTP requests (e.g., via `traceparent` header).
- **Retain Data**: Store observability records for **30 days** (adjust based on compliance needs).

---
**See Also**:
- [OpenTelemetry GraphQL Docs](https://opentelemetry.io/docs/instrumentation/js/graphql/)
- [Apollo Server Observability Plugin](https://www.apollographql.com/docs/apollo-server/observable/observability/)