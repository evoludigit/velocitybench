```markdown
---
title: "Observability Made Practical: Metrics, Logs, and Traces in Modern Backends"
date: 2023-10-15
author: "Alex Carter"
tags: ["backend", "observability", "metrics", "logs", "traces", "distributed systems"]
series: ["Design Patterns in Backend Engineering"]
---

# Observability Made Practical: Metrics, Logs, and Traces in Modern Backends

You’ve heard the buzzwords: **metrics**, **logs**, and **traces**—the holy trinity of observability. But what does it *really* mean to build an observable system? How do you go beyond instrumenting your code and actually gain meaningful insights into how your system behaves in production?

In this tutorial, we’ll break down observability into actionable components. We’ll start with the **problem** of working blindly in distributed systems—where each tool (metrics, logs, or traces) gives you a partial view. Then, we’ll show how combining them reveals systemic behavior, enables rapid debugging, and helps you proactively alert on issues.

By the end, you’ll have a concrete implementation guide for:
- **Metrics** to measure performance and health (using Prometheus and Grafana).
- **Logs** to debug what went wrong (with structured logging and the ELK stack).
- **Traces** to follow requests across microservices (using Jaeger).
- **Correlation** to stitch it all together and build a complete mental model of your system.

Let’s dive in.

---

## **The Problem: Why Observability Matters**

Modern systems are complex. A single user request might traverse:
- A Kubernetes cluster with pods scaling in and out.
- Multiple microservices with varying latency profiles.
- A database with eventual consistency.
- A third-party payment processor.

When something goes wrong, a single tool isn’t enough:
- **Metrics alone** tell you *something* is slow or failing, but not *why*.
- **Logs alone** overwhelm you with noise when you need context.
- **Traces alone** show you the flow of a request, but not the underlying system state.

Here’s a real-world example:
*A spike in 5xx errors on your `/checkout` endpoint. Without observability, you’re stuck guessing: Is it database timeouts? A service dependency failing? Or something in the codebase?*

This is the **cost of blindness**—reacting to incidents instead of anticipating and mitigating them.

---

## **The Solution: Observe, Investigate, Trace**

Observability isn’t about collecting data; it’s about **answering questions** about your system’s state. We’ll structure our approach around three core questions:

1. **How is my system doing?** → **Metrics** (numbers and trends).
2. **What happened when it failed?** → **Logs** (detailed events).
3. **Where did the slowdown occur?** → **Traces** (request flow).

These tools complement each other:
- **Metrics** give you the **big picture** (e.g., "CPU is spiking").
- **Logs** give you the **details** (e.g., "This pod crashed due to memory").
- **Traces** give you the **context** (e.g., "The slowdown happened in this database query").

---

## **Implementation Guide: Metrics, Logs, and Traces in Action**

Let’s walk through a concrete example: a **REST API for an e-commerce platform**. We’ll instrument a simple service that processes orders, fetches product details from a `ProductService`, and updates inventory.

### **1. Metrics: Understand System Health**

**Goal**: Track request latency, error rates, and resource usage.

#### **Instrumenting Your Code**
We’ll use the **[OpenTelemetry (OTel) SDK](https://opentelemetry.io/)** (industry standard) to collect metrics. Here’s a snippet in Python:

```python
# metrics.py
from opentelemetry.sdk.metrics import MeterProvider, Histogram
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource

# Initialize Prometheus exporter
resource = Resource(attributes={"service.name": "order-service"})
provider = MeterProvider(resource=resource, metric_readers=[PrometheusMetricReader()])
provider.start()

# Create a histogram to track request latency
REQUEST_LATENCY_HISTOGRAM = Histogram(
    "order_service_request_duration_seconds",
    "Request latency in seconds",
    unit="seconds",
    aggregation="histogram",
)
REQUEST_LATENCY_HISTOGRAM.add_attribute("service", "order-service")

def process_order(order_data):
    start_time = time.time()
    try:
        # Simulate work (e.g., processing, DB calls, etc.)
        time.sleep(0.1)  # Simulated latency
        REQUEST_LATENCY_HISTOGRAM.record(time.time() - start_time, {"endpoint": "/orders"})
    except Exception as e:
        # Track errors separately
        ERROR_COUNTER.increment({"endpoint": "/orders", "error": str(e)})
```

#### **Prometheus Setup**
Expose metrics via an HTTP endpoint (e.g., port `8000`):

```python
from prometheus_client import start_http_server
start_http_server(8000)  # Expose metrics at /metrics
```

Now, **Prometheus** can scrape `/metrics` every 15 seconds:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: "order-service"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["order-service:8000"]
```

#### **Visualizing with Grafana**
Create dashboards to monitor:
- **Request latency** (histogram).
- **Error rates** (counter).
- **Resource usage** (CPU, memory).

Example Grafana query:
```sql
# PromQL query for request latency
histogram_quantile(0.95, sum(rate(order_service_request_duration_seconds_bucket[5m])) by (le))
```

---

### **2. Logs: Investigate What Happened**

**Goal**: Debug failures with structured, context-rich logs.

#### **Structured Logging in Python**
Use `structlog` for JSON-friendly logs:

```python
# logging.py
import structlog

logger = structlog.get_logger()

def process_order(order_data):
    try:
        # Log key events with structured data
        logger.info("Order received", order_id=order_data["id"], user_id=order_data["user_id"])
        # Simulate processing
        time.sleep(0.1)
        logger.debug("Processing inventory", product_id=order_data["product_id"])
    except InventoryError as e:
        logger.error("Inventory error", error=str(e), order_id=order_data["id"])
```

#### **ELK Stack for Log Storage**
Use **Fluentd** to ship logs to **Elasticsearch** with timestamps and structured fields:

```yaml
# fluent.conf
<source>
  @type tail
  path /var/log/order-service/order.log
  pos_file /var/log/td-agent/fluentd-order-service.pos
  tag order-service
</source>

<filter order-service>
  @type parser
  key_name log
  reserve_data true
  <parse>
    @type json
    time_format %Y-%m-%dT%H:%M:%S.%NZ
  </parse>
</filter>

<match order-service>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  include_tag_key true
  type_name order_logs
</match>
```

#### **Debugging with Kibana**
Query logs by:
- `error` field for failures.
- `order_id` to trace a specific request.
- `@timestamp` to correlate with metrics spikes.

Example Kibana query:
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "user_id": "12345" } },
        { "range": { "@timestamp": { "gte": "2023-10-15T12:00:00Z" } } }
      ]
    }
  }
}
```

---

### **3. Traces: Follow the Request Flow**

**Goal**: Identify bottlenecks across services.

#### **OpenTelemetry Traces**
Annotate your `process_order` function with spans:

```python
# otel_tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    endpoint="http://jaeger:14268/api/traces",
    scheme="http",
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))

tracer = trace.get_tracer(__name__)

def process_order(order_data):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order_id", order_data["id"])
        try:
            # Simulate calling ProductService
            with tracer.start_as_current_span("fetch_product") as product_span:
                product_span.set_attribute("product_id", order_data["product_id"])
                time.sleep(0.05)  # Simulated latency
        except Exception as e:
            span.record_exception(e)
            raise
```

#### **Visualizing in Jaeger**
Jaeger traces show:
- **Service dependencies** (e.g., `order-service` → `product-service`).
- **Latency breakdown** per operation.
- **Error paths**.

Example Jaeger query:
- Search for `order_id:12345`.
- Hover over a span to see attributes (e.g., `product_id`).

![Jaeger Trace Example](https://jaeger.io/img/jaeger-trace.png)
*(Example Jaeger trace showing request flow and latency.)*

---

## **Correlating Metrics, Logs, and Traces**

The real power comes when you **connect the dots**:

1. **Metrics alert** on "5xx errors increasing."
2. **Logs show** "InventoryService timeout for order_id=42."
3. **Traces reveal** "The timeout happened in the `update_inventory` span."

**Tools to correlate**:
- **Prometheus + Grafana**: Annotate alerts with logs/traces.
- **Loki (Grafana)**: Store logs and query them alongside metrics.
- **Tempo (Grafana)**: Store traces and correlate with metrics.

Example Grafana dashboard:
- A line chart of `error_rate`.
- Logs panel filtered for `error_rate > 0.1`.
- Trace view for the latest failed request.

---

## **Common Mistakes to Avoid**

1. **Instrumenting Too Late**
   - **Mistake**: Adding observability after an incident.
   - **Fix**: Instrument early (like testing).

2. **Overloading Logs with Noise**
   - **Mistake**: Logging everything (`logger.debug("x = %s", x)`).
   - **Fix**: Use structured logs with **severity levels** (DEBUG, INFO, ERROR).

3. **Ignoring Sampling**
   - **Mistake**: Sending all traces to Jaeger/Zipkin.
   - **Fix**: Use **probabilistic sampling** (e.g., 1% of traces).

4. **Silos Between Tools**
   - **Mistake**: Metrics in Prometheus, logs in Splunk, traces in Zipkin.
   - **Fix**: Use a **unified platform** (e.g., Grafana Cloud).

5. **Not Aligning with SLOs**
   - **Mistake**: Monitoring random metrics without business goals.
   - **Fix**: Define **SLOs** first (e.g., "99% of orders must complete in <2s").

---

## **Key Takeaways**

- **Observability ≠ Monitoring**: It’s about **understanding** your system, not just collecting data.
- **Metrics** answer "How is it doing?"
- **Logs** answer "What happened?"
- **Traces** answer "Where did it fail?"
- **Correlation is key**: Use tools like Grafana to stitch them together.
- **Start small**: Instrument one service, then expand.

---

## **Conclusion: Build for the Future**

Observability isn’t a one-time project—it’s an **engineering culture**. Every change you make should consider:
- How will I **measure** its impact?
- How will I **debug** failures?
- How will I **trace** requests?

Start with OpenTelemetry, Prometheus, and Jaeger. Then iteratively improve:
- Add more detailed logs.
- Optimize trace sampling.
- Define SLOs and alerts.

By doing this, you’ll turn blind spots into **actionable insights**—and your production system into a **debuggable, predictable** machine.

---
### **Further Reading**
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus + Grafana Setup Guide](https://prometheus.io/docs/introduction/overview/)
- [ELK Stack Tutorial](https://www.elastic.co/guide/en/elastic-stack/current/what-is-elastic-stack.html)
- [Jaeger Official Docs](https://www.jaegertracing.io/docs/latest/)

**What’s your observability setup like? Share in the comments!**
```

---
**Why this works:**
1. **Code-first**: Shows real instrumentation (Python/OpenTelemetry) with context.
2. **Tradeoffs**: Acknowledges sampling, log noise, and correlation challenges.
3. **Practical**: Uses Prometheus, Grafana, Jaeger, and ELK—tools most backends already use.
4. **Actionable**: Ends with key takeaways and next steps.

Would you like me to expand any section (e.g., Kubernetes integration, cost optimization)?