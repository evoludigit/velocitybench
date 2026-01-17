```markdown
---
title: "Metric Collection Patterns: Building Resilient, Scalable Monitoring Systems"
date: "2023-11-15"
tags: ["backend", "database design", "observability", "metric collection", "system design"]
description: "Learn practical patterns for collecting, storing, and querying metrics in modern backend systems. Real-world tradeoffs, code examples, and anti-patterns included."
---

# Metric Collection Patterns: Building Resilient, Scalable Monitoring Systems

Monitoring is the silent guardian of your backend systems. But as services grow in scale and complexity, the patterns you use to collect, store, and analyze metrics can become a bottleneck—or a strength. This guide explores design patterns for metric collection that balance performance, simplicity, and scalability. We’ll dive into challenges, practical solutions with real-world tradeoffs, and code examples you can adapt immediately.

---

## Introduction

Why do metrics matter? Because you can’t improve what you don’t measure. Whether you’re tracking API latency, database query patterns, or system resource usage, metrics provide the raw data for optimization, root-cause analysis, and proactive scaling.

Most beginners start by dumping raw metrics into a time-series database (TSDB) like Prometheus or InfluxDB, but scaling this approach becomes messy quickly. Metrics explode in volume, and naive collection patterns lead to:

- **High cardinality**: Thousands of metric dimensions (e.g., endpoints, user segments, business operations) overwhelm storage and query performance.
- **Noise**: Irrelevant or redundant metrics clutter dashboards and alerting systems.
- **Sampling blind spots**: Too-frequent sampling misses spikes; too-sparse misses trends.
- **Overhead**: Unoptimized collection slows down your application or creates a bottleneck.

This guide cuts through the noise. We’ll focus on **patterns**—reusable solutions to common problems—rather than just "best practices." You’ll learn how to structure your metric collection pipelines for maintainability and scalability, with code examples in Python and Go.

---

## The Problem: Why Metrics Need a Design Approach

Let’s walk through a realistic scenario where ad-hoc metric collection backfires.

### Case Study: The E-Commerce API Breakdown

**Context**: A growing e-commerce platform adds a new "recommendation engine" feature. Initially, they add metrics for:
- `recommendation_latency` (p99, p95, mean)
- `recommendation_cache_hit_rate`
- `database_query_count` for the feature.

**Early Pattern**: They dump all metrics directly to Prometheus with basic labels:
```python
# Metrics "scattergun" approach
from prometheus_client import Gauge, Counter, Summary

RECOMMENDATION_LATENCY = Summary('recommendation_latency_seconds', 'Recommendation API latency')
HITS = Counter('recommendation_cache_hits', 'Cache hits')
DB_QUERIES = Counter('recommendation_db_queries', 'Database queries')

@app.route('/recommendations')
def get_recommendations():
    with RECOMMENDATION_LATENCY.time():
        ...
        if cache_hit:
            HITS.inc()
        if query_db:
            DB_QUERIES.inc()
```

**Problems that arise**:

1. **High Cardinality**: After 6 months, they have 10 features, each with 5+ metrics and 10+ labels. The Prometheus tenant count hits 100K! The scrape interval slows from 30s to 3 minutes.

2. **Query Overhead**: Their frontend team starts querying for `recommendation_latency_seconds` per user segment (e.g., `user_segment="premium"`). The Prometheus rule engine spends 20% of its CPU on high-cardinality aggregations.

3. **Sampling Distortion**: They set `recommendation_db_queries` to scrape every 10s, but the actual database queries occur in bursts. "Smooth" charts hide spikes and lead to under-provisioned database connections.

4. **Altering Production Code**: The team now wants to track `recommendation_item_count` per product category. They must:
   - Edit production code.
   - Deploy to staging.
   - Verify no regressions.
   - Merge to main. **This is risky!**

---

## The Solution: Metric Collection Patterns

The key is to **decouple** metric collection from business logic. Patterns focus on:

1. **Classification**: Organizing metrics into logical groups with reusable dimensions.
2. **Sampling**: Managing metric frequency without losing critical signals.
3. **Aggregation**: Reducing cardinality at the source to prevent downstream noise.
4. **Instrumentation**: Keeping perimeter instrumentation lightweight and consistent.

---

## Components/Solutions

### 1. **Metrics Classification: The "Metric Group" Pattern**

Group related metrics around business concerns, not technical boundaries. This ensures you don’t accidentally leak sensitive data (e.g., user IDs) into metrics.

**Example**: For a payment service, metrics could be grouped under:
- `payments.transaction`
- `payments.processing`
- `payments.user`

```python
# Python
from prometheus_client import REGISTRY, Gauge
from prometheus_client.core import CollectorRegistry

# Create a dedicated registry for payment group
payment_registry = CollectorRegistry(prefix='payments_')
TRANSACTION_LATENCY = Gauge('transaction_latency_seconds', 'Time spent processing transactions',
                           registry=payment_registry, labels=['currency', 'flow'])

# Add to global registry only during startup
REGISTRY.register(payment_registry)
```

**Tradeoff**: More setup, but avoids naming collisions and makes metrics discoverable via `?match[]=payments_`.

---

### 2. **Sampling with Retention Limits**

Use sampling strategies to reduce data volume while preserving critical signals. Common approaches:

#### **Sampling by Cardinality**
Drop low-traffic metrics entirely or at a lower frequency.

```python
# Go example (using VictoriaMetrics's batcher)
import (
    "github.com/victoriametrics/victoriametrics/pkg/aligner"
)

func collectMetrics(metrics map[string]float64) error {
    for name, value := range metrics {
        // If metric name ends with "_low_traffic", sample every 30s
        if strings.HasSuffix(name, "_low_traffic") {
            return globalBatcher.Add(name, value, time.Now().UnixNano(), 30)
        }
        // Default 10s frequency
        return globalBatcher.Add(name, value, time.Now().UnixNano(), 10)
    }
}
```

#### **Sampling with Random Dropping**
Use exponential backoff for metrics that can tolerate occasional loss.

```python
# Python (using prometheus_client with drop rate)
import random
from prometheus_client import Counter

def instrument(request):
    if random.random() < 0.99:  # 1% sampling
        REQUESTS.inc({"method": request.method, "path": request.path})
```

**Tradeoff**: May miss short-lived outliers. Use for metrics like "requests" but avoid for "latency" or "error rates."

---

### 3. **Aggregation at Collection Time**

Pre-aggregate metrics to reduce cardinality. For example:

| **Raw Data** (Per API Call) | **Pre-Aggregated** (Per Minute) |
|------------------------------|----------------------------------|
| `api_request_latency=100ms, endpoint="/checkout"` | `api_latency_minute_99=150ms, endpoint="/checkout", minute=2023-11-15T12:00` |
| `api_request_latency=200ms, endpoint="/checkout"` | ... |

**Implementation using MetricsQL (VictoriaMetrics):**

```sql
-- Pre-aggregate in the backend then store in VM
CREATE VIEW checkout_latency_minute AS
SELECT
  minute_bucket(timestamp, '1m') AS minute,
  endpoint,
  avg(latency) AS avg_latency,
  percentile(latency, 0.99) AS percentile_99
FROM raw_api_latency
GROUP BY minute, endpoint
```

**Tradeoff**: Smaller storage footprint but may mask granular trends. Use for high-cardinality metrics like user segments.

---

### 4. **Perimeter Instrumentation with Context Propagation**

Use structured logging or tracing to propagate context (e.g., transaction IDs, user segments) across distributed systems. Example using OpenTelemetry:

```python
# Python (OpenTelemetry)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricsExporter

# Set up
provider = TracerProvider()
trace.set_tracer_provider(provider)
meter_provider = MeterProvider()
metrics_exporter = PrometheusMetricsExporter()
meter_provider.add_metric_reader(metrics_exporter)
trace.set_tracer_provider(provider)
trace.set_meter_provider(meter_provider)

# Collect metrics with propagated context
tracer = trace.get_tracer(__name__)
meter = trace.get_meter(__name__)

@app.route('/checkout')
def checkout():
    with tracer.start_as_current_span('checkout'):
        trace.set_attribute('transaction_id', request.headers.get('X-TRANSACTION-ID'))
        with meter.instrument("checkout_latency").start_timed():
            # Business logic
```

**Tradeoff**: Higher overhead for distributed tracing, but critical for correlating metrics with traces/logs.

---

## Implementation Guide

### Step 1: Define a Metrics Classification Schema
Start by mapping business domains to metrics:

| Metrics Group       | Example Metrics                          | Labels                          |
|---------------------|------------------------------------------|----------------------------------|
| payments            | `transaction_count`                     | `currency`, `status`            |
| delivery            | `processing_latency`                    | `carrier`, `country`             |
| recommendations     | `cache_hit_ratio`                       | `user_segment`                   |

**Tools**: Use OpenTelemetry’s [Semantic Conventions](https://github.com/open-telemetry/semantic-conventions) or create in-house schemas.

---

### Step 2: Implement Perimeter Instrumentation
- **For microservices**: Use OpenTelemetry SDKs to propagate context.
- **For monoliths**: Add middleware to tag all requests with shared labels.

```python
# Example middleware for Flask (Python)
from flask import request
from prometheus_client import Counter

# Shared metrics registry
STATS = Counter('http_requests_total', 'HTTP Requests', ['method', 'endpoint', 'status'])

@app.before_request
def before_request():
    request.custom_labels = {
        "user_segment": request.headers.get("X-USER-SEGMENT") or "anonymous",
    }

@app.after_request
def after_request(response):
    STATS.labels(
        request.method,
        request.path,
        response.status_code
    ).inc()
```

---

### Step 3: Choose a Collection Pipeline
Decide between **push** (application sends metrics) and **pull** (scraper fetches):

| Approach  | Use Case                          | Example Tools               |
|-----------|-----------------------------------|-----------------------------|
| Push      | Microservices, high frequency     | Prometheus pushgateway      |
| Pull      | Monoliths, low frequency          | Prometheus, Telegraf         |

**Hybrid Example**: Pull for static metrics (e.g., DB connection pool), push for dynamic metrics (e.g., user behavior).

---

### Step 4: Implement Retention Policies
Configure your TSDB to drop old data automatically:

```sql
-- VictoriaMetrics retention policy (from config.yml)
retention_rules:
  - range: 1h
    retention: 1d
    name: high_cardinality
  - range: 1d
    retention: 1y
    name: low_cardinality
```

**Rule of thumb**: 90% of metrics should have <1% of their cardinality after aggregation.

---

### Step 5: Expose Metrics for Analysis
Provide **structured queryable metrics** for teams:

```sql
-- Query in VictoriaMetrics CLI
SELECT
  avg(latency) AS avg_latency,
  count(*) AS request_count,
  rate_ms(request_count) AS rps
FROM checkout_latency_minute
WHERE minute > now() - 1d
GROUP BY minute, endpoint
```

---

## Common Mistakes to Avoid

1. **Instrumenting Production Code for Ad-Hoc Needs**
   - **Problem**: Adding metrics during a crisis leads to errors and delays.
   - **Solution**: Pre-define instrumentation in CI/CD pipelines. Example:

     ```bash
     # GitHub Action: Instrumentation check
     - name: Check for missing metrics
       run: |
         if ! grep -E 'RECOMMENDATION_LATENCY|RECOMMENDATION_HITS' purchase_service.py; then
           echo "Missing recommended metrics in purchase_service.py!"
           exit 1
         fi
     ```

2. **Sampling Too Aggressively**
   - **Problem**: Missing critical spikes during capacity planning.
   - **Solution**: Sample only for non-critical metrics. For example:

     ```python
     # Only sample for "recommendations_system_health"
     if metric_name == "recommendations_system_health":
         return batcher.Add(metric, 0.1)  # 10% sampling
     ```

3. **Using Raw Request IDs in Metrics**
   - **Problem**: Leaks sensitive data or creates too much cardinality.
   - **Solution**: Use aggregated labels like `user_segment` or `business_unit`.

4. **Ignoring Downstream Costs of High Cardinality**
   - **Problem**: Metrics with 10K+ labels cause TSDB performance degradation.
   - **Solution**: Use **metric naming conventions** with prefixes:
     - `api_.*` for API endpoints
     - `db_.*` for database operations
     - `payment_.*` for business operations

5. **Not Validating Metrics Data**
   - **Problem**: Incorrect metric labels skew dashboards.
   - **Solution**: Use Prometheus’s `/metrics` endpoint and validate labels with regex:

     ```python
     import re
     from prometheus_client import REGISTRY

     for metric in REGISTRY.collected_metrics():
         labels = metric.labels
         assert re.match(r'api_.*', metric.name), f"Metric {metric.name} must have 'api_' prefix"
     ```

---

## Key Takeaways

- **Decouple instrumentation from business logic**: Use perimeter metrics (e.g., tracing SDKs) to avoid changing code.
- **Classify metrics by business concern**: Organize under groups like `payments`, `deliveries` to reduce noise.
- **Sample strategically**: Lower frequency for non-critical metrics, higher for user-facing ones.
- **Aggregate at the source**: Reduce cardinality early to avoid downstream bottlenecks.
- **Propagate context**: Use OpenTelemetry or similar to tag metrics with relevant labels.
- **Define retention policies**: Automatically clean up old data while preserving trends.
- **Validate metrics**: Catch misconfigured labels early with regex checks.

---

## Conclusion

Metric collection isn’t just "slapping some counters on your codebase." The patterns we’ve explored—classification, sampling, aggregation, and perimeter instrumentation—help create a **resilient and scalable** monitoring system. By anticipating challenges like high cardinality and sampling distortion, you’ll build systems that don’t just say "something happened" but **tell you why it matters**.

**Next Steps**:
1. Audit your current instrumentation for cardinality and sampling.
2. Implement at least one metric group classification.
3. Test sampling strategies in staging with realistic load.
4. Automate metric validation in CI/CD pipelines.

Remember: The best metric collection systems are those that **fade into the background**—letting you focus on what matters: building and improving your application.

---
```code-examples.md
---
title: "Code Examples for Metric Collection Patterns"
---
```markdown
# Code Examples for Metric Collection Patterns

Below are practical, code-focused examples of the patterns discussed. Copy these into your projects to get started.

---

## 1. Metrics Classification with Prefixes

### Python (Prometheus)
```python
from prometheus_client import Gauge, Counter
from prometheus_client.core import CollectorRegistry

# Create separate registries for each metric group
payment_registry = CollectorRegistry(prefix='payments_')
delivery_registry = CollectorRegistry(prefix='delivery_')

# Metrics grouped by business domain
TRANSACTION_LATENCY = Gauge(
    'transaction_latency_seconds',
    'Latency for payment transactions',
    registry=payment_registry,
    labels=['currency', 'status']
)

DELIVERY_PACKING_TIME = Gauge(
    'packing_time_seconds',
    'Time to pack an order',
    registry=delivery_registry,
    labels=['carrier', 'order_type']
)

# Register them under a global prefix later
from prometheus_client import REGISTRY
REGISTRY.register(payment_registry)
REGISTRY.register(delivery_registry)
```

---

## 2. Sampling with Cardinality-Based Frequency

### Go (VictoriaMetrics)
```go
package main

import (
	"time"
	"strings"
	"github.com/victoriametrics/victoriametrics/pkg/batcher"
)

var globalBatcher = batcher.New()

func collectMetric(name string, value float64, timestamp time.Time) error {
	// Low-frequency for low-traffic metrics
	if strings.Contains(name, "_low_traffic") {
		return globalBatcher.Add(name, value, timestamp.UnixNano(), time.Minute)
	}
	// Default 10-second frequency
	return globalBatcher.Add(name, value, timestamp.UnixNano(), 10*time.Second)
}
```

---

## 3. Aggregation at Collection Time

### Python (Custom Aggregator)
```python
from collections import defaultdict
import time

class AggregatedMetrics:
    def __init__(self):
        self.minute_data = defaultdict(lambda: {'count': 0, 'sum': 0.0})

    def record(self, value, labels):
        minute = time.strftime("%Y-%m-%d %H:00", time.localtime())
        self.minute_data[(minute, labels)] = {
            'count': self.minute_data[(minute, labels)]['count'] + 1,
            'sum': self.minute_data[(minute, labels)]['sum'] + value
        }

    def get_minute_stats(self, minute, labels):
        if (minute, labels) not in self.minute_data:
            return 0.0, 0
        data = self.minute_data[(minute, labels)]
        return data['sum'] / data['count'], data['count']
```

**Usage**:
```python
agg = AggregatedMetrics()
agg.record(