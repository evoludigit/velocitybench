# **[Pattern] Sumo Logic APM Integration Reference Guide**

---

## **Overview**
This guide outlines **Sumo Logic’s APM (Application Performance Monitoring) Integration Patterns**, detailing how to ingest, analyze, and correlate APM telemetry with infrastructure, logs, and custom metrics. APM integrations enable end-to-end visibility into application performance, latency, errors, and dependencies. This reference covers **OpenTelemetry (OTel), Sumo Logic’s native APM collectors, and third-party APM tool integrations**, including implementation steps, configuration best practices, and common challenges with sample queries for correlating data.

---

## **Key Concepts**
| Concept                     | Description                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| **Trace Data**              | End-to-end request flows captured via trace IDs, spans, and context propagation.                |
| **Metric Aggregation**      | Collecting performance metrics (e.g., latency, errors) for aggregations and dashboards.       |
| **Log Correlation**         | Associating APM traces with logs using trace IDs or custom fields.                            |
| **Service Map**             | Visualizing dependencies between microservices and infrastructure components.                 |
| **OpenTelemetry (OTel) SDK**| Standardized SDKs for instrumentation of applications (Java, Node.js, Python, etc.).          |
| **Custom Attributes**       | Extending APM data with business-specific metadata (e.g., `user_id`, `order_id`).              |
| **Sampling**                | Reducing volume by sampling traces at ingestion or application level (e.g., `trace_id` hashing).|
| **Retention Policies**      | Configuring trace/metric retention (default: 90 days; adjust based on compliance needs).        |

---

## **Implementation Details**

### **1. Native Sumo Logic APM Integration (Collector-Based)**
Sumo Logic provides **APM collectors** (Lightweight Collectors or Distributed Tracing Collectors) for extracting APM data from:
- **Agent-based tools**: Datadog, New Relic, AppDynamics.
- **Otel-compatible APMs**: Jaeger, Zipkin, OpenTelemetry Collector.

#### **Steps**
1. **Deploy Collector**:
   - Download the [Sumo Logic Distributed Collector](https://help.sumologic.com/03Send-Data/Send-Data-to-Sumo-Logic/Configure-the-APM-Collector).
   - Configure `config.yml` with Sumo Logic’s APM endpoint:
     ```yaml
     apm:
       receiver: apmreceiver
       otlp:
         protocols:
           grpc:
             endpoint: "otelcol.sumologic.com:4317"
     ```

2. **Instrument Applications** (Otel SDK):
   - Add the Otel SDK to your app (e.g., Java, Python):
     ```java
     // Maven dependency
     <dependency>
       <groupId>io.opentelemetry</groupId>
       <artifactId>opentelemetry-sdk</artifactId>
       <version>1.30.0</version>
     </dependency>
     ```
   - Configure exporter to send to the collector:
     ```java
     OtlpGrpcSpanExporter exporter = OtlpGrpcSpanExporter.builder()
         .setEndpoint("otelcol:4317")
         .build();
     SdkTracerProvider.builder()
         .addSpanProcessor(SimpleSpanProcessor.create(exporter))
         .buildAndRegister();
     ```

3. **Verify Ingestion**:
   - Check **Sumo Logic > APM > Traces** for ingested data.
   - Validate **Service Map** visibility.

---

### **2. Third-Party APM Integrations**
| APM Tool       | Integration Method                          | Schema Mapping                          |
|----------------|--------------------------------------------|-----------------------------------------|
| **Datadog**    | Forward traces via Otel/HTTP API            | `dd.trace_id` → `trace_id`              |
| **New Relic**  | Use NR’s Otel plugin or APM collector       | `newrelic.trace_id` → `trace_id`        |
| **AppDynamics**| Export traces via AppDynamics OTel plugin  | `ad.trace` → `trace_id`                 |
| **AWS X-Ray**  | Use X-Ray’s OpenTelemetry plugin           | `X-Ray Trace ID` → `trace_id`           |

#### **Example: New Relic → Sumo Logic**
1. **Configure New Relic APM**:
   - Enable **OpenTelemetry** in New Relic UI:
     ```
     nrel-otel-collector.newrelic.com:4318
     ```
2. **Forward to Sumo Logic Collector**:
   Modify collector’s `config.yml`:
   ```yaml
   receivers:
     otlp:
       protocols:
         grpc:
           endpoint: "nrel-otel-collector.newrelic.com:4318"
   ```

---

### **3. Log Correlation with APM**
Correlate APM traces with logs using **trace IDs** or custom fields in log sources.

#### **Schema Reference**
| Field Name          | Type    | Description                                      | Example Value                     |
|---------------------|---------|--------------------------------------------------|-----------------------------------|
| `trace_id`          | String  | Unique identifier for a trace.                    | `"a1b2c3d4e5f6"`                  |
| `span_id`           | String  | Identifies a specific operation within a trace.   | `"x1y2z3"`                        |
| `service.name`      | String  | Name of the service generating the span.         | `"order-service"`                 |
| `http.url`          | String  | Endpoint for HTTP spans.                          | `"/api/orders"`                   |
| `http.status_code`  | Integer | HTTP response status.                            | `500`                             |
| `error.message`     | String  | Error details (if any).                          | `"Database connection failed"`    |

---

## **Query Examples**
### **1. Trace Analysis**
Find slow API endpoints:
```sql
_trace id="*" | timeslice 30m
| stats avg(duration), count(*) by http.url
| where avg(duration) > 500
| sort -avg(duration)
```

### **2. Error Rate by Service**
```sql
_trace id="*" error=true
| timeslice 1h
| stats count(*) by service.name
| sort -count
```

### **3. Log-APM Correlation**
Join logs with APM traces using `trace_id`:
```sql
_logs
| join _trace (trace_id)
| parse regex ".*ERROR.*: (?<error_msg>.*)" multiline=5
| timeslice 5m
| stats count(*) by error_msg, service.name
```

### **4. Service Dependency Map**
Visualize dependencies in **Sumo Logic Service Map**:
- Ensure `service.name` and `peers.service` fields are populated.
- View in **APM > Service Map**.

---

## **Best Practices**
1. **Sampling Strategy**:
   - Use **adaptive sampling** (e.g., sample 10% of high-latency traces).
   - Avoid overloading collectors with `trace_id` hashing:
     ```yaml
     processors:
       batch/traces:
         timeout: 1s
         send_batch_size: 1000
     ```

2. **Trace Context Propagation**:
   - Ensure `trace_id` and `span_id` are propagated across services (e.g., via HTTP headers):
     ```
     X-B3-TraceId: <trace_id>
     X-B3-SpanId: <span_id>
     ```

3. **Schema Consistency**:
   - Standardize field names (e.g., `http.url` vs. `url`).
   - Use Sumo Logic’s **Field Extraction** to map legacy APM schemas.

4. **Retention**:
   - Reduce storage costs by setting shorter retention for raw traces (e.g., 30 days):
     ```
     admin > Search > Retention Policies > Edit
     ```

5. **Alerting**:
   - Create **APM-based alerts** for:
     - High error rates (`error=true`).
     - Latency spikes (`duration > threshold`).
     - Dependency failures (`peers.service` errors).

---

## **Common Pitfalls & Solutions**
| Pitfall                          | Solution                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| **High trace volume**             | Implement sampling or increase collector batch size.                     |
| **Missing service.name**          | Add auto-instrumentation or manual annotation in Otel SDK.               |
| **Correlation failures**          | Verify `trace_id` propagation across microservices.                      |
| **Schema mismatch**               | Use Sumo Logic’s **Field Extraction** or transform third-party schemas. |
| **Collector crashes**             | Monitor collector logs; increase resources or adjust `config.yml`.       |

---

## **Related Patterns**
1. **[Log Correlation with APM](https://help.sumologic.com/03Send-Data/04Sources/05Hosted/03Log-Sources/Sumologic-Log-Source/Log-Correlation)**
   - Deep dive into correlating logs with APM traces using `trace_id`.

2. **[OpenTelemetry Instrumentation Guide](https://help.sumologic.com/03Send-Data/Send-Data-to-Sumo-Logic/OpenTelemetry/Instrument-your-Applications)**
   - Step-by-step Otel SDK setup for Java, Python, Node.js.

3. **[Sumo Logic Metrics Integration](https://help.sumologic.com/03Send-Data/Send-Data-to-Sumo-Logic/Metrics-Monitoring)**
   - Combine APM metrics with infrastructure metrics (e.g., CPU, memory).

4. **[Distributed Tracing for Microservices](https://help.sumologic.com/03Send-Data/Send-Data-to-Sumo-Logic/OpenTelemetry/Distributed-Tracing)**
   - Advanced patterns for cross-service tracing.

5. **[Alerting on APM Data](https://help.sumologic.com/04Analytics/Alerting/Alerting-Basics)**
   - Build alerts for APM anomalies (errors, latency, dependencies).

---
**Last Updated**: [Insert Date]
**Version**: 1.2

---
*For further assistance, refer to [Sumo Logic APM Documentation](https://help.sumologic.com/03Send-Data/Send-Data-to-Sumo-Logic/OpenTelemetry).*