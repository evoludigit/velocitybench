```markdown
# **Trace Collection Patterns: Structuring and Processing Logs Like a Pro**

Ever wondered how Netflix, Uber, or Stripe track millions of user requests and debug issues across distributed systems? The secret lies in **trace collection patterns**—a systematic way to capture, aggregate, and analyze request flows across services.

In this guide, we’ll explore:
- Why trace collection matters in modern distributed systems.
- Common challenges with traditional log-based debugging.
- A **practical pattern** for collecting traces efficiently.
- **Real-world code examples** in Go, Python, and Java.
- **Implementation best practices** and anti-patterns.

By the end, you’ll know how to design robust tracing systems that scale.

---

## **Introduction: The Need for Trace Collection**

Modern applications are rarely monolithic. Instead, they’re composed of microservices, serverless functions, and third-party APIs, all communicating via HTTP, gRPC, or messaging queues. When something breaks, logs alone often aren’t enough:

- **Logs are flat**: They don’t show how one service’s error cascades into another.
- **Correlation is manual**: You might need to stitch together logs from multiple services to debug a workflow.
- **Performance impact**: Writing logs for every request slows down your system.

**Trace collection** solves these problems by capturing structured, correlated request flows. Instead of scattering logs, you get a **single timeline** of a user request journey, making debugging faster and more reliable.

---

## **The Problem: Why Traditional Logs Fall Short**

### **Problem #1: Logs Are Hard to Correlate**
Consider a user booking a flight:
1. **Frontend** sends a request to `/book`.
2. `/book` calls a **payment service**.
3. The payment service **rejects the transaction**.
4. The frontend **shows an error**, but logs are scattered across three services.

Without traces, debugging requires:
```bash
# Manual log filtering
grep PaymentFailed logs/payment-service*
grep "Error processing" logs/frontend*
```
This is **error-prone and slow**.

### **Problem #2: Distributed Tracing is Complex**
The OpenTelemetry (OTel) spec defines four key components:
- **Traces**: A timeline of spans (operations) in a request.
- **Spans**: Individual units of work (e.g., `/book` API call).
- **Attributes**: Key-value pairs (e.g., `user_id`, `status_code`).
- **Links**: References to other traces (e.g., downstream API calls).

But setting this up from scratch is tedious. You need:
✅ A tracing library
✅ A collector (e.g., Jaeger, Zipkin)
✅ A backend storage (e.g., Elasticsearch, Prometheus)
✅ Alerting rules

### **Problem #3: Performance Overhead**
Every HTTP request that spawns a trace adds latency:
```go
// Example: Adding a span in Go (OpenTelemetry)
ctx, span := otel.Tracer("example").Start(ctx, "book_flight")
defer span.End()

// Simulate slow downstream call
time.Sleep(1 * time.Second)
```
If traces are **overly verbose**, they can **bottleneck** your system.

---

## **The Solution: Trace Collection Patterns**

To avoid these pitfalls, we’ll use a **modular trace collection pattern** with:
1. **Lightweight tracing** (minimal overhead).
2. **Smart sampling** (not every trace goes to storage).
3. **Distributed correlation** (linking traces across services).

### **Key Components**
| Component           | Purpose                                                                 |
|---------------------|-------------------------------------------------------------------------|
| **Tracing Library** | Injects spans into code (e.g., OpenTelemetry, Jaeger Client).           |
| **Sampler**         | Decides which traces to record (e.g., always sample payment failures).  |
| **Collector**       | Aggregates traces from all services (e.g., Jaeger, Zipkin).             |
| **Storage**         | Stores traces for analysis (e.g., Elasticsearch, Prometheus).           |
| **Exporter**        | Sends traces to the collector (e.g., HTTP, gRPC).                      |

### **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Service A  │───▶│  Collector  │───▶│  Storage    │
└─────────────┘    └─────────────┘    └─────────────┘
    ↑                     ↑                     ↑
    │                     │                     │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Service B  │───▶│  Service A  │───▶│  Service C  │
└─────────────┘    └─────────────┘    └─────────────┘
```
Each service **propagates a trace ID** (`X-Trace-ID`) for correlation.

---

## **Code Examples: Implementing Traces**

### **1. Basic Trace Setup (Go)**
We’ll use **[OpenTelemetry Go](https://pkg.go.dev/go.opentelemetry.io/otel)** to instrument a simple HTTP server.

#### **Install OpenTelemetry**
```bash
go get go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp
```

#### **Example: Book Flight Endpoint**
```go
package main

import (
	"context"
	"log"
	"net/http"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/jaeger"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

func main() {
	// 1. Set up Jaeger exporter
	exp, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint("http://localhost:14268/api/traces")))
	if err != nil {
		log.Fatal(err)
	}

	// 2. Create a trace provider
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exp),
		sdktrace.WithResource(resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName("flight-booking"),
		)),
	)
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	// 3. Start HTTP server with tracing
	http.HandleFunc("/book", bookFlightHandler)
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func bookFlightHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// 1. Extract trace context (propagated by previous calls)
	ctx, span := otel.Tracer("flight").Start(ctx, "book_flight")
	defer span.End()

	// 2. Simulate a slow downstream call (e.g., payment service)
	downstreamCtx, downstreamSpan := otel.Tracer("payment").Start(ctx, "process_payment")
	downstreamSpan.SetAttributes(
		attribute.String("user_id", "123"),
		attribute.String("amount", "$199.99"),
	)
	downstreamSpan.End()

	// 3. Simulate error
	if r.URL.Query().Get("fail") == "true" {
		span.RecordError(errors.New("payment declined"))
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("Payment failed"))
		return
	}

	// 4. Success
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Flight booked!"))
}
```

#### **Test It**
```bash
# Start Jaeger locally (Docker)
docker run -d --name jaeger -p 16686:16686 jaegertracing/all-in-one

# Call with tracing enabled
curl -H "X-Trace-ID: abc123" http://localhost:8080/book?fail=true
```
Visit `http://localhost:16686` to see the trace in Jaeger.

---

### **2. Smart Sampling (Python - OpenTelemetry)**
Not all traces need full detail. We’ll implement **probabilistic sampling** (e.g., only 1% of traces).

#### **Install OpenTelemetry Python**
```bash
pip install opentelemetry-sdk opentelemetry-exporter-jaeger
```

#### **Example: Sampler in Flask**
```python
from flask import Flask, request
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.sampling import ProbabilitySampler

app = Flask(__name__)

# 1. Configure trace provider with sampler
resource = Resource.create(attributes={"service.name": "flight-python"})
provider = TracerProvider(resource=resource)
sampler = ProbabilitySampler(0.01)  # 1% sampling rate
provider.add_span_processor(
    BatchSpanProcessor(
        JaegerExporter(
            endpoint="http://localhost:14268/api/traces",
            # Optional: Set sampling strategy
            sampling_strategy="otel.sampling.strategy.always_sample_if_parent_in_span_context",
        )
    )
)
trace.set_tracer_provider(provider)

# 2. Tracer
tracer = trace.get_tracer(__name__)

@app.route("/book")
def book_flight():
    with tracer.start_as_current_span("book_flight") as span:
        span.set_attributes({"user_id": request.args.get("user_id", "unknown")})

        # Simulate downstream call
        with tracer.start_as_current_span("process_payment") as downstream_span:
            downstream_span.set_attributes({
                "amount": "$199.99",
                "status": "declined" if request.args.get("fail") else "approved"
            })

        if request.args.get("fail"):
            span.record_exception(Exception("Payment declined"))
            return {"error": "Payment failed"}, 400
        return {"status": "Booked!"}, 200

if __name__ == "__main__":
    app.run(port=5000)
```

#### **Test It**
```bash
# Call with sampling
curl http://localhost:5000/book?user_id=456&fail=true
```
Check Jaeger—only **1% of traces** will appear.

---

### **3. Distributed Correlation (Java - Spring Boot)**
Link traces across services using **trace IDs** and **baggage** (custom key-value pairs).

#### **Dependencies (`pom.xml`)**
```xml
<dependency>
    <groupId>io.opentelemetry</groupId>
    <artifactId>opentelemetry-sdk</artifactId>
    <version>1.24.0</version>
</dependency>
<dependency>
    <groupId>io.opentelemetry</groupId>
    <artifactId>opentelemetry-exporter-jaeger</artifactId>
    <version>1.24.0</version>
</dependency>
```

#### **Example: Spring Boot Trace Correlation**
```java
import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.trace.*;
import io.opentelemetry.sdk.OpenTelemetrySdk;
import io.opentelemetry.sdk.trace.export.BatchSpanProcessor;
import io.opentelemetry.sdk.trace.export.SimpleSpanProcessor;
import io.opentelemetry.sdk.trace.sampling.SamplingDecision;
import io.opentelemetry.sdk.trace.sampling.SamplingResult;
import io.opentelemetry.sdk.trace.sampling.Sampler;
import io.opentelemetry.sdk.trace.sampling.parentbased.ParentBasedSampler;
import io.opentelemetry.sdk.trace.export.JaegerSpanExporter;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.CompletableFuture;

@SpringBootApplication
public class FlightBookingApp {

    public static void main(String[] args) {
        // 1. Configure OpenTelemetry
        JaegerSpanExporter exporter = JaegerSpanExporter.builder()
                .setEndpoint("http://localhost:14268/api/traces")
                .build();

        TracerProvider tracerProvider = OpenTelemetrySdk.builder()
                .setSampler(ParentBasedSampler.create(ParentBasedSampler.alwaysSample()))
                .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
                .buildTracerProvider();

        GlobalOpenTelemetry.set(tracerProvider);

        SpringApplication.run(FlightBookingApp.class, args);
    }

    @RestController
    static class FlightController {

        @PostMapping("/book")
        public CompletableFuture<String> bookFlight(@RequestBody FlightRequest request) {
            Tracer tracer = GlobalOpenTelemetry.getTracer("flight");
            Span span = tracer.spanBuilder("book_flight")
                    .setAttribute("user_id", request.getUserId())
                    .startSpan();

            try (SpanContext context = span.makeCurrent()) {
                // 2. Call downstream service with propagated context
                CompletableFuture<String> result = CompletableFuture.supplyAsync(() ->
                    callPaymentService(request, context));

                return result.thenApply(response ->
                    span.addEvent("Flight booked: " + response));
            } finally {
                span.end();
            }
        }

        private String callPaymentService(FlightRequest request, SpanContext context) {
            Tracer tracer = GlobalOpenTelemetry.getTracer("payment");
            Span span = tracer.spanBuilder("process_payment")
                    .setParent(context)
                    .startSpan();

            try (SpanContext _ = span.makeCurrent()) {
                span.setAttribute("amount", "$199.99");
                if ("fail".equals(request.getPaymentStatus())) {
                    throw new RuntimeException("Payment declined");
                }
                return "Payment approved";
            } finally {
                span.end();
            }
        }

        static class FlightRequest {
            private String userId;
            private String paymentStatus;

            // Getters & setters
        }
    }
}
```

#### **Test It**
```bash
curl -X POST http://localhost:8080/book \
  -H "Content-Type: application/json" \
  -d '{"userId": "789", "paymentStatus": "fail"}'
```
Check Jaeger—**linked spans** will appear.

---

## **Implementation Guide**

### **Step 1: Choose a Tracing Library**
| Language | Library               | Notes                                  |
|----------|-----------------------|----------------------------------------|
| Go       | OpenTelemetry Go      | Mature, integrates with Jaeger/Zipkin  |
| Python   | OpenTelemetry Python  | Works with Jaeger, Prometheus          |
| Java     | Spring Boot + OTel    | Auto-instrumentation with `@RestController` |
| Node.js  | `@opentelemetry/auto` | Lightweight, supports AWS X-Ray        |

### **Step 2: Propagate Trace Context**
Always **inject and extract** trace IDs in:
- **HTTP headers** (`X-Trace-ID`, `X-B3-TraceId`)
- **Message queues** (Kafka, RabbitMQ)
- **Database calls** (PostgreSQL, MongoDB)

Example (Python):
```python
from opentelemetry.propagators import TextMapPropagator
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Enable HTTP header propagation
propagator = TextMapPropagator()
RequestsInstrumentor().instrument(span_context=propagator)
```

### **Step 3: Implement Sampling**
- **Always sample** when debugging.
- **Probabilistic sampling** (e.g., 1-5%) for production.
- **Error-based sampling**: Always trace failed requests.

Example (Go):
```go
// Always sample for errors
if err != nil {
    span.RecordError(err)
    // Force export (bypass sampler)
    span.End(sdktrace.WithExportToCollector())
}
```

### **Step 4: Store and Visualize**
| Tool          | Use Case                          | Setup Cost |
|---------------|-----------------------------------|------------|
| Jaeger        | Interactive trace exploration      | Medium     |
| Zipkin        | Lightweight, HTTP-based           | Low        |
| Elasticsearch | Full-text search + dashboards      | High       |
| Prometheus    | Metrics + traces (OTLP exporter)   | Medium     |

### **Step 5: Monitor Trace Volume**
- **Alert if trace volume spikes** (could indicate a DoS).
- **Set retries with backoff** for collector failures.

Example (Terraform + Prometheus):
```hcl
resource "prometheus_alert_rule" "high_trace_volume" {
  name     = "HighTraceVolume"
  rule     = <<EOF
    ALERT HighTraceVolume
    IF rate(otel_traces_exported_total{job="otel-collector"}[1m]) > 1000
    FOR 5m
    LABELS{severity="warning"}
    ANNOTATIONS {
      summary = "Trace volume increased by 10x"
    }
    EOF
}
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Over-Tracing**
- **Problem**: Every function call creates a span → **high latency**.
- **Fix**: Use **span batching** and **sampling**.

### **❌ Mistake 2: Ignoring Trace Context Propagation**
- **Problem**: Trace IDs are lost when calling external services.
- **Fix**: Always **propagate `SpanContext`** (e.g., in HTTP headers).

### **❌ Mistake 3: No Error Handling in Traces**
- **Problem**: Errors are logged but not linked to traces.
- **Fix**: Always call `span.RecordError(err)` on failures.

### **❌ Mistake 4: Storing Too Much Data**
- **Problem**: Full traces for every request consume **GBs of storage**.
- **Fix**: Use **sampling** and **attribute filtering** (e.g., exclude PII).

### **❌ Mistake 5: Not Testing Locally**
- **Problem**: Traces fail in production due to missing dependencies.
- **Fix**: Run