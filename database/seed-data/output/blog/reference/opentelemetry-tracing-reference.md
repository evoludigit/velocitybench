# **[Pattern] OpenTelemetry Tracing Reference Guide**

---

## **Overview**
OpenTelemetry (OTel) tracing in FraiseQL enables **distributed tracing** for complex query execution across microservices, databases, and external dependencies. This pattern integrates OpenTelemetry’s **standardized instrumentation** to capture detailed **spans** (timeline records) for every stage of query processing, including:
- **Query parsing & optimization** (e.g., plan generation)
- **External API calls** (e.g., REST, gRPC)
- **Database interactions** (e.g., SQL execution, connection pooling)
- **Context propagation** (e.g., headers, W3C TraceContext)

FraiseQL supports **OTLP (OpenTelemetry Protocol)**, **Jaeger**, and **Zipkin** as exporters, allowing ingestion into observability backends like **Prometheus**, **Grafana**, or **OpenTelemetry Collector**.

---

## **Key Concepts**
| **Term**               | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Trace**              | A sequence of spans representing a single request’s journey across services.                                                                                                                                | A user clicking a button → API call → Database query → Rendering response.                     |
| **Span**               | A single operation (e.g., `parse_query`, `execute_sql`, `fetch_row`). Includes:<br>- **Name**: Operation type (e.g., `QueryParser`).<br>- **Attributes**: Key-value metadata (e.g., `db.system=Postgres`).<br>- **Timestamps**: Start/end/errors. | `span = tracer.start_span("parse_query", attributes={"query": "SELECT * FROM users"})` |
| **Trace Context**      | Headers (e.g., `traceparent`) to correlate spans across services.                                                                                                                                              | `traceparent: 00-1234abcd567890...` (W3C standard).                                                |
| **Instrumentation**    | OpenTelemetry SDK hooks (e.g., interceptors, auto-instrumentation) to add spans to code paths.                                                                                                                  | Auto-instrumenting HTTP clients or database drivers.                                             |
| **Span Links**         | References to related traces/spans for cross-service context.                                                                                                                                              | Linking a `QueryPlan` span to a `ExecuteSQL` span.                                               |
| **Sampling**           | Controls trace volume (e.g., `always_on`, `probabilistic`, or `parent-based`).                                                                                                                                     | Sample every 10th request, or follow parent traces from upstream.                              |

---

## **Schema Reference**
### **1. Trace Structure**
| **Field**          | **Type**       | **Description**                                                                                     | **Example Value**                          |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `trace_id`         | Hex String     | Globally unique identifier for the trace.                                                          | `00-a1b2c3d4e5f67890`                     |
| `spans`            | Array[Span]    | List of spans in chronological order.                                                              | `[span1, span2, ...]`                     |
| `resources`        | Object         | Metadata about the service (e.g., `service.name`, `telemetry.sdk`).                               | `{"service.name": "fraiseql-query-service"}` |

### **2. Span Attributes**
| **Attribute**       | **Type**       | **Description**                                                                                     | **Example**                                |
|---------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `name`              | String         | Operation name (e.g., `QueryParser`, `ExecuteSQL`).                                                 | `"parse_query"`                             |
| `start_time`        | Unix Timestamp | Span start time (nanoseconds since epoch).                                                          | `1672531200000000000`                     |
| `end_time`          | Unix Timestamp | Span end time.                                                                                     | `1672531200100000000`                     |
| `duration`          | Duration       | Time elapsed (e.g., `10ms`).                                                                         | `10000000` (10ms)                          |
| `attributes`        | Key-Value Pairs | Query-specific metadata (e.g., `db.system`, `query.text`).                                           | `{"db.system": "Postgres", "query.text": "SELECT ..."}` |
| `status`            | Object         | Success/failure state (`{code: "OK"|"ERROR", message: "..."}`).                                  | `{"code": "ERROR", "message": "Syntax error"}` |
| `links`             | Array[Link]    | References to parent/child traces (e.g., `trace_id`, `span_id`).                                    | `[{trace_id: "xyz", span_id: "123"}]`       |

### **3. Query-Specific Attributes**
| **Attribute**       | **Type**       | **Description**                                                                                     | **Example**                                |
|---------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `query.text`        | String         | Raw query string.                                                                                   | `"WITH r AS (SELECT * FROM users) ... "`   |
| `query.plan`        | String         | Execution plan (e.g., `HashJoin`, `SeqScan`).                                                       | `"SeqScan on users"`                       |
| `db.system`         | String         | Database vendor (e.g., `Postgres`, `MySQL`).                                                         | `"Postgres"`                               |
| `db.query_time`     | Duration       | Time spent in database (from `EXPLAIN ANALYZE`).                                                     | `50000000` (50ms)                          |
| `fraiseql.version`  | String         | FraiseQL runtime version.                                                                          | `"v2.1.0"`                                 |

---
## **Query Execution Trace Flow**
Below is a **typical trace** for a query executed via FraiseQL, showing key spans and context propagation:

```
Trace ID: 00-a1b2c3d4e5f67890
└─ Span 1: "receive_query" (name: "query_receiver")
    │  Attributes: {http.method="POST", http.path="/run_query"}
    │  Links: [] (new trace)
└─ Span 2: "parse_query" (name: "QueryParser")
    │  Attributes: {query.text="SELECT * FROM users", parse.duration=2ms}
    │  Parent Span: Span 1
└─ Span 3: "generate_plan" (name: "QueryPlanner")
    │  Attributes: {plan="HashJoin(users, orders)", optimize.duration=3ms}
    │  Parent Span: Span 2
└─ Span 4: "execute_sql" (name: "PostgresDriver")
    │  Attributes: {db.system="Postgres", query_time=45ms}
    │  Parent Span: Span 3
    │  Links: [] (embedded in traceparent header if calling external service)
└─ Span 5: "render_result" (name: "ResultFormat")
    │  Attributes: {format="JSON", serialize.duration=1ms}
    │  Parent Span: Span 4
```

---
## **Query Examples**
### **1. Basic Tracing Setup (Python)**
Enable OpenTelemetry auto-instrumentation for HTTP and database calls:
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configure exporter (OTLP endpoint)
exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")
processor = BatchSpanProcessor(exporter)
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(processor)

# Auto-instrument HTTP client (e.g., `requests`)
trace.set_tracer_provider(trace.get_tracer_provider())

# Execute a query (auto-instrumented)
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("execute_fraiseql_query") as span:
    query_result = fraiseql.execute("SELECT * FROM users WHERE age > 25")
```

### **2. Manual Span Instrumentation**
Add custom spans for business logic:
```python
from opentelemetry.trace import get_current_span

def validate_user(user_id: str) -> bool:
    span = get_current_span()
    with tracer.start_as_child_span(
        span_context=span.get_span_context(),
        name="validate_user",
        attributes={"user.id": user_id}
    ) as child_span:
        # Simulate API call
        response = requests.get(f"https://api.users.com/{user_id}")
        child_span.set_attribute("api.response_time", response.elapsed.total_seconds())
        return response.status_code == 200
```

### **3. Sampling Configuration**
Limit trace volume with probabilistic sampling:
```python
from opentelemetry.sdk.trace.sampling import ProbabilitySampler

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="..."),
        sampling_strategy=ProbabilitySampler(0.1)  # 10% of traces
    )
)
```

### **4. Exporting to Jaeger**
Configure Jaeger as the exporter:
```python
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-collector",
    agent_port=6831
)
processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(processor)
```

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Span Context Propagation]** | Ensures trace IDs are carried via headers (e.g., `traceparent`) in HTTP/rPC calls.                                                                                                                 | Cross-service tracing (e.g., FraiseQL → API Gateway → Database).                                     |
| **[Structured Logging]**    | Correlates logs with traces using `trace_id`/`span_id` in log entries.                                                                                                                               | Debugging issues in distributed systems with logs + traces.                                         |
| **[Query Optimization Tracing]** | Adds spans for plan analysis (e.g., `EXPLAIN ANALYZE`) to identify bottlenecks.                                                                                                                  | Performance tuning of slow queries.                                                                 |
| **[OTLP Ingestion]**       | Standardized protocol for sending traces to backends (e.g., Prometheus, Grafana).                                                                                                                    | Centralized observability with OTel Collector.                                                      |
| **[Error Tracking]**       | Attaches span attributes (e.g., `error.message`) to failed queries.                                                                                                                                         | Post-mortem analysis of query failures.                                                              |

---
## **Troubleshooting**
| **Issue**                          | **Solution**                                                                                                                                                                                                 |
|------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Traces not appearing in Jaeger** | Verify `traceparent` headers are propagated. Check `OTEL_SERVICE_NAME` and exporter endpoint in config.                                                                                        |
| **High cardinality in attributes** | Limit dynamic attributes (e.g., `query.text`) to reduce storage costs. Use aggregations (e.g., `query.type=SELECT`).                                                                           |
| **Missing spans for DB calls**     | Enable auto-instrumentation for your DB driver (e.g., `opentelemetry-instrumentation-psycopg2`).                                                                                                   |
| **Sampling missing critical traces**| Use `parent-based` sampling to ensure root traces are sampled.                                                                                                                                         |

---
## **Best Practices**
1. **Tag Queries Meaningfully**:
   Use consistent attributes for `query.text`, `db.system`, and `fraiseql.version` to filter traces.
   ```python
   span.set_attribute("query.type", "analytical")  # Categorize queries
   ```

2. **Avoid Overhead**:
   Sample aggressively (e.g., 10%) to balance debuggability and performance.

3. **Correlate Logs**:
   Include `trace_id` in logs for end-to-end debugging:
   ```python
   logging.info("Processing query", extra={"trace_id": get_current_span().get_span_context().trace_id})
   ```

4. **Monitor Span Durations**:
   Set up alerts for long-running spans (e.g., `execute_sql > 500ms`).

5. **Compliance**:
   Redact PII in attributes (e.g., `user.email`) before exporting.

---
## **References**
- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/latest/)
- [OTLP Protocol Spec](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/trace/v1/trace_proto.md)
- [FraiseQL GitHub](https://github.com/fraise-ai/fraiseql) (for SDK integration details).