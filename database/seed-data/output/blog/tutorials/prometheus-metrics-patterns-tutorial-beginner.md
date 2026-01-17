```markdown
# **Prometheus Metrics Patterns: Observability for Your GraphQL API**

*How to instrument your backend like a metric-driven superhero*

---

## **Introduction**

Ever wondered how production teams reliably spot issues before they impact users? Most backend systems today rely on *metrics*—quantitative measurements of system behavior—to monitor health, performance, and anomalies. But metrics aren’t just for large-scale platforms; even small codebases benefit from structured observability.

This post dives into **Prometheus Metrics Patterns**, a practical approach to exposing meaningful monitoring data for APIs (especially GraphQL). We’ll cover:

- How metrics differ from logs/logging (and why they’re not interchangeable)
- A beginner-friendly guide to Prometheus
- Real-world examples for GraphQL (like FraiseQL’s 15+ metrics)
- Pitfalls to avoid (and how to fix them)

By the end, you’ll know how to design instrumented APIs—without overcomplicating things.

---

## **The Problem: A Black-Box GraphQL Server**

GraphQL’s flexibility is its strength—but it comes with blind spots:

- **No default telemetry**: Unlike REST, GraphQL APIs don’t inherently expose latency or error metrics.
- **Complex queries**: A single request might fetch 10+ relations; tracing these manually is error-prone.
- **Latency isn’t uniform**: A "fast" query might perform poorly under load.

**Example**: A FraiseQL API handles mutations and queries, but without metrics, you don’t know:
- Which mutations fail under 500ms?
- When cache hit rates drop below 80%?
- Where database bottlenecks appear?

Without answers, your team resorts to:
- 🔍 Manual debugging (slow)
- 📊 Guessing (risky)
- 🚨 Firefighting (reactive)

---

## **The Solution: Prometheus + Metrics**

Prometheus is a *time-series database* for metrics, but it’s only as powerful as the patterns you use. Here’s the approach:

1. **Expose high-cardinality metrics** (e.g., `graphql_operation_latency{query="add_user"}`).
2. **Use histograms for distributions**, counters for counts, and gauges for volatility.
3. **Label judiciously**—avoid cardinality explosions (we’ll cover this).

---

## **Components/Solutions**

### 1. Prometheus Primer
Prometheus scrapes `/metrics` endpoints every 15–60 seconds. Your API simply exposes:

```promql
# Example PromQL query: Latency > 500ms
sum(rate(graphql_operation_latency_sum[5m])) by (query, status)
  > quantile(0.99, rate(graphql_operation_latency_bucket[5m]))
```

### 2. Key Metric Types
| **Type**      | **Use Case**                          | **Example**                          |
|---------------|---------------------------------------|---------------------------------------|
| **Counter**   | Count events (e.g., "cache misses")  | `cache_misses_total`                  |
| **Histogram** | Track latency distributions           | `graphql_latency_seconds_bucket`      |
| **Gauge**     | Measure current state (e.g., "active users") | `db_connection_pool_size` |

### 3. FraiseQL’s Metrics (15+ Examples)
FraiseQL instruments:
- Query latency (histogram)
- Mutation errors (counter)
- Cache hit rates (gauge)
- Database call counts (counter)

---

## **Implementation Guide**

### **Step 1: Add Prometheus Client**
Use the Prometheus Go client (or equivalent for your language). Example in Go:

```go
// go.mod: github.com/prometheus/client_golang/prometheus v0.12.0
package main

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"net/http"
)

var (
	graphQLQueryLatency = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "graphql_query_latency_seconds",
			Help:    "Latency of GraphQL queries in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"query", "operation"},
	)
)

func init() {
	prometheus.MustRegister(graphQLQueryLatency)
}

func handler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer graphQLQueryLatency.WithLabelValues("add_user", "mutation").
		Observe(time.Since(start).Seconds())

	// ... GraphQL logic ...
}
```

### **Step 2: Expose Metrics Endpoint**
Mount a `/metrics` handler:

```go
http.Handle("/metrics", promhttp.Handler())
go func() {
	log.Fatal(http.ListenAndServe(":8080", nil))
}()
```

### **Step 3: Configure Prometheus**
Add your service to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "graphql"
    static_configs:
      - targets: ["localhost:8080"]
```

### **Step 4: PromQL Alerts**
Example for high latency:
```
ALERT HighQueryLatency {
  expr: histogram_quantile(0.95, rate(graphql_query_latency_seconds_bucket[5m])) > 0.5
  for: 5m
  labels: {severity="warning"}
}
```

---

## **Common Mistakes to Avoid**

### **❌ Over-labeling → Cardinality Explosion**
Avoid labels like `label1="value1", label2="value2"` if they explode cardinality (e.g., `query="GET /users/123"`). Instead:
- Use `query="users"` if it’s an aggregate metric.
- Pre-aggregate or hash high-cardinal labels.

### **❌ No Context for Metrics**
Prometheus lacks context—metrics alone don’t explain "why" a spike occurred. Pair with structured logs or traces.

### **❌ Ignoring Histograms**
Counters are for counts; histograms capture *distributions*. Without them, you miss slow-tail cases.

---

## **Key Takeaways**
✅ **Use Prometheus for metrics**, not logs.
✅ **Instrument key operations** (queries, mutations, cache).
✅ **Prefer histograms over counters** for latency.
✅ **Label wisely** to avoid cardinality bloat.
✅ **Alert on meaningful thresholds** (e.g., "99th percentile > 500ms").

---

## **Conclusion**

Prometheus Metrics Patterns turn your GraphQL API into a self-monitoring system. Start with:
1. A histogram for latency.
2. Counters for errors.
3. Gauges for critical state.

Combine this with logs (e.g., OpenTelemetry) and traces for a complete observability stack. The goal? **Proactive debugging**—not reactive firefighting.

Want to go deeper? Check out:
- [Prometheus History](https://prometheus.io/docs/introduction/overview/)
- [GraphQL Metrics Guide](https://www.graphql-metrics.com/)

Now go instrument your API like a hero. 🚀
```