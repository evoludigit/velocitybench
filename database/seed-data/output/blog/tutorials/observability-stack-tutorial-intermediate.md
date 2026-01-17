```markdown
# **Observability: Metrics, Logs, and Traces – The Full Picture of Your System**

Your microservices might be running, but how do you *know* they’re working as expected? How do you diagnose failures when they happen? Or, worse—how do you *predict* they might fail before users notice?

That’s where **observability** comes in.

Observability combines **metrics** (quantifiable system health), **logs** (raw event data), and **traces** (end-to-end request flows) to give you a complete picture of your system’s behavior. Without all three, you’re flying blind—missing performance bottlenecks, undetected errors, and inefficient resource usage.

In this guide, we’ll:
- Explain why observability is more than just monitoring
- Break down how metrics, logs, and traces work together
- Show you practical implementations in Go, Python, and Java
- Warn you about common pitfalls

By the end, you’ll have the tools to build a robust observability stack that helps you debug faster, optimize performance, and prevent outages.

---

## **The Problem: When Observability Is Broken**

Most modern systems rely on a mix of monitoring, tracing, and logging—but too often, these systems are **fragmented**.

- **No metrics?** You can’t measure latency, error rates, or resource usage. You might think your service is "working," but without numbers, you’re guessing.
- **Only logs?** You can see what happened, but not *why* or *where* it happened. Logs are like a crime scene photo—useful, but incomplete.
- **No traces?** You can’t follow a request across services. A 500 error might be in App A, but you don’t know it’s triggered by a slow call to App B.
- **Tools acting alone?** Alerts on metrics don’t correlate with logs. Traces don’t show the bigger picture. You end up switching between dashboards, losing context.

### **A Real-World Example: The Mysterious 504 Gateway Timeout**
Let’s say your users report slow API responses.

- **Metrics** might show a spike in `http_server_request_duration` for `/users`.
- **Logs** could reveal `waiting for DB query` or `timeout after 3s`.
- **Traces** would show the request bouncing between services, with one call taking 4 seconds while others complete in milliseconds.

Without traces, you’d assume the issue is in `/users`. Without logs, you’d just see a timeout. Without metrics, you’d never know it was even happening.

---

## **The Solution: Metrics + Logs + Traces = Full Observability**

Observability isn’t about *collecting* data—it’s about **understanding** your system’s behavior. Here’s how each piece fits:

| **Tool**       | **Purpose**                          | **Example Use Case**                          |
|----------------|--------------------------------------|-----------------------------------------------|
| **Metrics**    | Quantitative system health           | Alert when `http_server_request_duration > 1s` |
| **Logs**       | Detailed event data                  | Debug why a DB query failed                   |
| **Traces**     | End-to-end request flow              | Find latency in a microservice call           |

### **How They Work Together**
1. **Metrics** flag anomalies (e.g., high latency).
2. **Traces** show *where* the latency is happening.
3. **Logs** give *why* it’s happening.

---

## **Implementation Guide: Building Observability in Practice**

Let’s implement a minimal observability stack in **Go, Python, and Java**, using:
- **Prometheus** (metrics)
- **OpenTelemetry** (traces & logs)
- **Jaeger** (trace visualization)

---

### **1. Metrics: Prometheus + Go (or Python/Java)**
Metrics help you track key performance indicators (KPIs) like latency, error rates, and throughput.

#### **Example: Go HTTP Server Metrics**
```go
package main

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"log"
	"net/http"
)

var (
	requestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "Duration of HTTP requests in seconds",
			Buckets: []float64{.1, .5, 1, 2, 5},
		},
		[]string{"method", "path", "status"},
	)
)

func init() {
	prometheus.MustRegister(requestDuration)
}

func main() {
	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		requestDuration.WithLabelValues(
			r.Method,
			r.URL.Path,
			"200",
		).Observe(float64(time.Since(r.Context().Deadline()).Seconds()))
	})

	log.Println("Server running on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```
**Run it:**
```sh
go run main.go
```
**Check metrics:**
```sh
curl http://localhost:8080/metrics
```
You’ll see Prometheus-compatible histograms tracking request durations.

#### **Python (FastAPI) Example**
```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
import time

app = FastAPI()

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests',
    ['method', 'path', 'status']
)

@app.get("/health")
async def health(request: Request):
    start = time.time()
    REQUEST_DURATION.labels(
        request.method,
        request.url.path,
        "200"
    ).observe(time.time() - start)
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type="text/plain")
```
**Run with:**
```sh
uvicorn main:app --reload
```

---

### **2. Traces: OpenTelemetry + Jaeger**
Traces follow requests across services, showing dependencies and bottlenecks.

#### **Go Example (OpenTelemetry + Jaeger)**
```go
package main

import (
	"context"
	"github.com/opentelemetry/go-otel"
	"github.com/opentelemetry/go-otel/exporters/jaeger"
	"github.com/opentelemetry/go-otel/propagation"
	"github.com/opentelemetry/go-otel/sdk/resource"
	sdktrace "github.com/opentelemetry/go-otel/sdk/trace"
	semconv "github.com/opentelemetry/semconv/v1.4.0"
	"io"
	"log"
	"net/http"
)

func initTracer() (*sdktrace.TracerProvider, io.Closer) {
	exp, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint("http://jaeger:14268/api/traces")))
	if err != nil {
		log.Fatal(err)
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exp),
		sdktrace.WithResource(resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName("example-service"),
		)),
	)
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))
	return tp, exp
}

func main() {
	tp, closer := initTracer()
	defer closer.Close()

	http.HandleFunc("/trace", func(w http.ResponseWriter, r *http.Request) {
		ctx := otel.GetTextMapPropagator().Extract(r.Context(), propagation.HeaderCarrier(r.Header))
		tracer := otel.Tracer("example")
		ctx, span := tracer.Start(ctx, "http.request")
		defer span.End()

		span.AddEvent("handling request")
		w.WriteHeader(http.StatusOK)
	})
	http.ListenAndServe(":8080", nil)
}
```
**Run with:**
```sh
docker run -d --name jaeger -p 16686:16686 jaegertracing/all-in-one
go run main.go
```
Visit `http://localhost:16686` to see traces in Jaeger.

#### **Python (FastAPI) Example**
```python
from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()
instrumentation = FastAPIInstrumentor(
    should_intercept=["/*"],
    tracer_provider=TracerProvider(),
    should_batch=True,
)

@app.get("/trace")
async def trace_request(request: Request):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("example-span"):
        return {"status": "ok"}

# Initialize Jaeger exporter
exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
processor = BatchSpanProcessor(exporter)
tracer_provider = trace.TracerProvider()
tracer_provider.add_span_processor(processor)
trace.set_tracer_provider(tracer_provider)
```
**Run with:**
```sh
uvicorn main:app --reload
```

---

### **3. Logs: Structured Logging + OpenTelemetry**
Logs should be **structured** (JSON) and **correlated** with traces.

#### **Go Example (Structured Logging + Traces)**
```go
package main

import (
	"context"
	"github.com/opentelemetry/go-otel"
	"log"
)

func logWithTrace(ctx context.Context, message string, args ...interface{}) {
	span := otel.TraceContextFromContext(ctx).Span()
	if span.IsRecording() {
		log.Printf("%s [trace_id=%x, span_id=%x] %s", message, span.SpanContext().TraceID(), span.SpanContext().SpanID(), args...)
	} else {
		log.Printf(message, args...)
	}
}

func main() {
	ctx := context.Background()
	logWithTrace(ctx, "Starting request")
}
```

#### **Python Example (Structured Logging)**
```python
import json
import logging
from opentelemetry import trace
from opentelemetry.trace import Span

def log_with_trace(ctx: Span, message: str):
    trace_id = ctx.span_context.trace_id
    span_id = ctx.span_context.span_id
    log_data = {
        "message": message,
        "trace_id": trace_id,
        "span_id": span_id,
    }
    logging.info(json.dumps(log_data))

# Example usage
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("example"):
    log_with_trace(tracer.current_span(), "Request started")
```

---

## **Common Mistakes to Avoid**

### **1. Treating Observability as an Afterthought**
- **Bad:** Add metrics/logs after development is done.
- **Good:** Design observability from day one (e.g., instrument every function).

### **2. Over-Instrumenting**
- **Problem:** Too many metrics/logs slow down the system.
- **Solution:** Focus on **key metrics** (e.g., latencies, error rates) and **debugging logs**.

### **3. Ignoring Correlation IDs**
- **Problem:** Logs and traces don’t link.
- **Solution:** Always propagate **trace IDs** between services.

### **4. Not Setting Up Alerts**
- **Problem:** Metrics collect dust.
- **Solution:** Use **Prometheus Alertmanager** or **Grafana Alerts** to notify on failures.

### **5. Using Proprietary Tools Too Early**
- **Problem:** Vendor lock-in in observability stacks.
- **Solution:** Start with **OpenTelemetry**, then choose your exporters (Jaeger, Zipkin, etc.).

---

## **Key Takeaways**
✅ **Observability ≠ Monitoring**
   - Monitoring tells you *what* is wrong.
   - Observability tells you *why* and *how to fix it*.

✅ **Metrics + Logs + Traces = Full Picture**
   - **Metrics** → "Something is wrong."
   - **Traces** → "It’s happening here."
   - **Logs** → "Because of this error."

✅ **Start Small, Scale Smart**
   - Begin with **one service**, then expand.
   - Use **OpenTelemetry** for instrumentation.

✅ **Automate Alerts**
   - Don’t just collect data—**act on it**.

✅ **Avoid Vendor Lock-In**
   - Stick with **standards** (Prometheus, OpenTelemetry).

---

## **Conclusion: Build a System You Can Trust**

Observability isn’t just for large-scale systems—it’s for **any** backend service that matters. Without it, you’re flying blind, reacting to outages instead of preventing them.

By combining:
- **Metrics** (quantitative health)
- **Traces** (request flows)
- **Logs** (debugging context)

You’ll gain the ability to:
✔ **Detect issues faster** (before users do).
✔ **Debug efficiently** (no more blind guessing).
✔ **Optimize performance** (find bottlenecks early).

Start small—instrument one service, set up Jaeger for traces, and Prometheus for metrics. Then expand. Your future self (and your users) will thank you.

---
**Next Steps:**
- Try **OpenTelemetry** in your language of choice.
- Set up **Jaeger** for trace visualization.
- Experiment with **Grafana** for dashboards.

Happy monitoring!
```

---
**P.S.** Want to dive deeper? Check out:
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Jaeger Tutorial](https://www.jaegertracing.io/docs/latest/getting-started/)