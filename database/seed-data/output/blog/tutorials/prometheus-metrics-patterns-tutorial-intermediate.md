```markdown
---
title: "Prometheus Metrics Patterns: Observability for Your GraphQL Server"
date: 2023-09-20
tags: ["observability", "prometheus", "graphql", "metrics", "backend", "monitoring"]
draft: false
---

# **Prometheus Metrics Patterns: Observability for Your GraphQL Server**

As backend engineers, we know observability isn’t an afterthought—it’s the foundation of reliable systems. But what happens when your GraphQL API runs silently in the background, collecting requests but emitting no insights into performance, errors, or bottlenecks? This is the **black-box GraphQL server problem**, where operational visibility is missing, and outages or degradations go undetected until users complain.

In this post, we’ll explore **Prometheus Metrics Patterns**, a practical approach to instrumenting GraphQL servers with meaningful metrics. We’ll cover:

- Why your GraphQL API needs observability upfront
- How to capture key metrics (latency, errors, cache hits, etc.)
- Real-world examples using **Prometheus clients** (including Go, JavaScript, and Python)
- Common pitfalls and how to avoid them

By the end, you’ll have a replicable pattern to turn your GraphQL API into an observable, self-healing system.

---

## **The Problem: The Black-Box GraphQL Server**

GraphQL’s declarative nature is powerful, but it introduces complexity in monitoring. Unlike REST endpoints with predictable paths, GraphQL serves dynamic datasets with nested queries and mutations. Without proper instrumentation:

1. **Latency is invisible**: A slow query might return in 5 seconds, but you don’t know until the user reports it.
2. **Errors are silent**: GraphQL errors are often wrapped in generic responses, and logs may not correlate them with business impacts.
3. **Cache inefficiencies go unnoticed**: You might cache aggressively, but are you hitting cache or hitting the database every time?
4. **Alert fatigue**: Alerts on raw request counts are noisy; you need context (e.g., "This mutation fails 90% of the time for user role 'admin'").

### **A Real-World Example**
Imagine `FraiseQL`, a GraphQL API powering a content management system (CMS). Without metrics, you’d only know:

- Total requests: ✅
- 500 errors: ❌ (but are they critical?)
- Latency spikes: ❌ (but when?)

With metrics, you could track:
✅ Query latencies per resolver (e.g., `posts:query` takes 300ms)
✅ Mutation error rates by field (e.g., `publishPost` fails 5% of the time)
✅ Cache hit ratios (e.g., `users:fetch` hits the cache 90% of the time)

---

## **The Solution: Prometheus Metrics Patterns**

Prometheus is a time-series database designed for observability. Its strengths lie in:

- **Pull-based metrics**: No need to instrument every client.
- **Label dimensions**: Contextualize metrics (e.g., `http_requests_total{method="POST", route="/api/posts"}`).
- **Alerting**: Integrate with Grafana or Alertmanager for proactive monitoring.

For GraphQL, we need metrics that expose **latency, errors, cache behavior, and business logic bottlenecks**. Here’s how:

### **Core Metrics to Instrument**
| Metric Type          | Example                          | Purpose                                                                 |
|----------------------|----------------------------------|--------------------------------------------------------------------------|
| **Latency Histograms** | `query_latency_seconds`          | Track distribution of query execution time (e.g., P50, P90).             |
| **Counter Errors**    | `graphql_errors_total`           | Count total errors, with labels for field/operation.                     |
| **Gauge Active Requests** | `graphql_active_requests` | Monitor concurrent requests (for rate limiting).                        |
| **Cache Metrics**     | `cache_hits_total`, `cache_misses_total` | Evaluate cache efficiency.                             |
| **Mutation Counters** | `mutation_create_user_total`     | Track business operations (e.g., how many users were created today?).   |

---
## **Implementation Guide**

### **1. Choose a Prometheus Client**
Prometheus provides SDKs for multiple languages. Here’s how to set up metrics in **Go**, **JavaScript (Node.js)**, and **Python**.

#### **Go Example (Using `prometheus` Go SDK)**
```go
// metrics.go
package main

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"net/http"
)

var (
	queryLatency = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "graphql_query_latency_seconds",
			Help:    "Time taken to execute GraphQL queries in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"operation", "operation_type"},
	)

	errorsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "graphql_errors_total",
			Help: "Total GraphQL errors encountered",
		},
		[]string{"operation", "error_type", "field"},
	)
)

func init() {
	prometheus.MustRegister(queryLatency, errorsTotal)
}

func handleQuery(req *http.Request, op string, opType string, latency time.Duration) {
	queryLatency.WithLabelValues(op, opType).Observe(latency.Seconds())
}

func handleError(op, errorType, field string) {
	errorsTotal.WithLabelValues(op, errorType, field).Inc()
}
```

#### **JavaScript (Node.js) Example (Using `prom-client`)**
```javascript
// server.js
const client = require('prom-client');
const { startHTTPServer } = require('./metrics');

const queryLatency = new client.Histogram({
  name: 'graphql_query_latency_seconds',
  help: 'Time taken to execute GraphQL queries in seconds',
  buckets: [0.1, 0.5, 1, 2.5, 5, 10], // Custom buckets for GraphQL
  labelNames: ['operation', 'operation_type'],
});

const errorsTotal = new client.Counter({
  name: 'graphql_errors_total',
  help: 'Total GraphQL errors encountered',
  labelNames: ['operation', 'error_type', 'field'],
});

async function handleQuery(req, op, opType, latency) {
  queryLatency
    .labels(op, opType)
    .observe(latency / 1000); // Convert ms to seconds
}

async function handleError(op, errorType, field) {
  errorsTotal.labels(op, errorType, field).inc();
}

// Expose metrics endpoint
startHTTPServer(8000, './metrics');
```

#### **Python Example (Using `prometheus-client`)**
```python
# metrics.py
from prometheus_client import (
    Histogram, Counter,
    REGISTRY, start_http_server
)
from graphql import GraphQLField

QUERY_LATENCY = Histogram(
    'graphql_query_latency_seconds',
    'Time taken to execute GraphQL queries in seconds',
    labelnames=['operation', 'operation_type'],
    buckets=[0.1, 0.5, 1, 2.5, 5, 10]
)

ERRORS_TOTAL = Counter(
    'graphql_errors_total',
    'Total GraphQL errors encountered',
    labelnames=['operation', 'error_type', 'field']
)

def measure_query(q_name, q_type, latency):
    QUERY_LATENCY.labels(q_name, q_type).observe(latency)

def record_error(op, error_type, field):
    ERRORS_TOTAL.labels(op, error_type, field).inc()
```

---

### **2. Instrument Your GraphQL Server**
#### **Example: Apollo Server (JavaScript)**
```javascript
const { ApolloServer } = require('apollo-server');
const { handleQuery, handleError } = require('./metrics');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: ({ req }) => {
    const start = Date.now();
    return {
      req,
      start,
      async onQuery({ operationName, operationType }) {
        const latency = Date.now() - this.start;
        await handleQuery(this.req, operationName, operationType, latency);
      },
      async onError(err) {
        const field = err.path.join('->');
        await handleError(`graphql_${operationName}`, err.extensions.errorType, field);
      }
    };
  }
});
```

#### **Example: Graphene (Python)**
```python
from graphene import ObjectType, Field, String
from metrics import measure_query, record_error

class Query(ObjectType):
    hello = String(name=String())

    async def resolve_hello(self, info, name):
        start = time.time()
        result = 'Hello, ' + name
        measure_query('hello', 'query', time.time() - start)
        return result

schema = graphene.Schema(query=Query)

async def app():
    app = Flask(__name__)
    app.add_url_rule('/metrics', 'metrics', generate_live_view(REGISTRY))
    app.add_url_rule('/query', 'graphql', lambda: schema.execute_sync(info=graphene_info()))
    return app
```

---

### **3. Configure Prometheus to Scrape Metrics**
In your `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'graphql_server'
    static_configs:
      - targets: ['localhost:8000']  # Metrics endpoint
```

---

## **Common Mistakes to Avoid**

1. **Overlabeling Metrics**
   - ❌ Label every resolver with `field1, field2` → high cardinality → Grafana slows down.
   - ✅ Use meaningful labels like `operation_name`, `field_type`.

2. **Ignoring Histograms for Latency**
   - ❌ Tracking only mean latency → misses outliers.
   - ✅ Use histograms with buckets (e.g., `[0.1, 0.5, 1, 2.5, 5]`).

3. **Not Correlating with Business Logic**
   - ❌ Alerting on raw `errors_total` without context.
   - ✅ Add labels like `user_role`, `query_depth`.

4. **Skipping Error Context**
   - ❌ `graphql_errors_total` without `error_type`.
   - ✅ Track `validation_error`, `database_error`, etc.

5. **Not Testing Metrics**
   - ❌ Assumes metrics work until they fail.
   - ✅ Load-test with tools like `k6` and verify Prometheus scrapes.

---

## **Key Takeaways**

- **Instrument early**: Metrics are easier to add during development than retrofitting later.
- **Focus on business metrics**: Track what matters (e.g., failed mutations) over vanity metrics.
- **Use histograms for latency**: Captures distribution, not just averages.
- **Label strategically**: Too few labels → lack of context; too many → high cardinality.
- **Test your metrics**: Verify Prometheus scrapes data during load tests.

---

## **Conclusion**

Prometheus metrics patterns transform black-box GraphQL servers into observable systems. By capturing **latency, errors, cache usage, and business operations**, you gain visibility into performance bottlenecks, error trends, and usage patterns.

Start small: instrument one query or mutation, then expand. Use **histograms** for latency, **counters** for errors, and **gauges** for active requests. Correlate metrics with business logic (e.g., "Admin mutations fail 3x more than user mutations") to turn data into actionable insights.

Want to go deeper? Explore:
- **Grafana dashboards** for visualizing GraphQL metrics.
- **Alertmanager rules** to notify on anomalies (e.g., "Mutation error rate > 1%").

Happy monitoring!
```

---
**TL;DR**: This post covers how to instrument GraphQL servers with Prometheus metrics to gain observability into latency, errors, cache usage, and business logic. Code examples for Go, JavaScript, and Python are provided, along with best practices and common pitfalls. 🚀