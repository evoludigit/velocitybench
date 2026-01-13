# **[Pattern] Execution Phase Instrumentation Reference Guide**

---

## **Overview**
The **Execution Phase Instrumentation** pattern captures timing metrics for discrete phases of an application execution flow (e.g., pre-processing, business logic, post-processing, or external calls). This enables performance monitoring, troubleshooting, and optimization by isolating slow or inconsistent phases. Commonly used in distributed systems, microservices, and high-throughput applications, the pattern includes timestamps for phase boundaries, duration calculations, and optional correlated context (e.g., transaction IDs, request headers).

---

## **Key Concepts**
1. **Phase Boundaries**:
   - Clearly defined segments of execution (e.g., `startProcessing`, `processData`, `persistResults`).
   - Must be consistent across all instrumentation points to avoid misaligned timing data.

2. **Timestamps**:
   - Use high-precision timestamps (nanoseconds) to measure phase durations with minimal overhead.
   - Example formats:
     - Unix epoch (milliseconds/seconds).
     - ISO 8601 timestamps (e.g., `"2023-10-15T14:30:00.123Z"`).

3. **Phase Metadata**:
   - Optional fields to enrich analysis:
     - `phaseName`: Human-readable label (e.g., `"DataValidation"`).
     - `phaseType`: Categorization (e.g., `"ExternalAPICall"`).
     - `correlationId`: Links phases to a specific execution context (e.g., a request ID).

4. **Aggregation Strategies**:
   - **Absolute Timings**: Raw start/end timestamps for detailed replay (e.g., `"phaseStart": 1697324600123`).
   - **Relative Durations**: Pre-computed durations (e.g., `"durationMs": 45`).
   - **Percentiles**: Statistical summaries (e.g., P90 latency) for large-scale systems.

5. **Context Propagation**:
   - Correlate phase data across services using headers/attributes (e.g., `X-Correlation-ID`).
   - Avoid redundant metadata by reusing context from earlier phases.

---

## **Schema Reference**
Below is the **Event-Driven** schema for instrumentation (adaptable to logging/telemetry systems).

| **Field**               | **Type**       | **Description**                                                                                     | **Example**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `eventType`             | `string`       | Fixed value: `"ExecutionPhaseEvent"`.                                                                    | `"ExecutionPhaseEvent"`         |
| `timestamp`             | `long`         | Unix epoch in milliseconds (nanosecond precision if supported).                                      | `1697324600000`                 |
| `phase`                 | `object`       | Phase-specific metadata.                                                                             | `{}`                            |
| `phase.name`            | `string`       | Human-readable phase identifier (e.g., `"UserAuth"`).                                                | `"PaymentProcessing"`           |
| `phase.type`            | `string`       | Categorization (e.g., `"APICall"`, `"LocalOp"`).                                                     | `"ExternalAPICall"`             |
| `phase.startTimestamp`  | `long`         | Start timestamp of the phase.                                                                          | `1697324600123`                  |
| `phase.endTimestamp`    | `long`         | End timestamp of the phase.                                                                           | `1697324600576`                  |
| `phase.durationMs`      | `long`         | Pre-calculated duration (milliseconds).                                                              | `453`                           |
| `context`               | `object`       | Correlated metadata (e.g., request ID, service name).                                                | `{}`                            |
| `context.correlationId` | `string`       | Unique identifier for tracing execution flows (e.g., UUID).                                          | `"73a1e6b7-9bcd-4321-8f0a-1234"` |
| `context.service`       | `string`       | Name of the service emitting the event.                                                              | `"OrderService"`                |

---

## **Query Examples**
### **1. Find Phases with Long Durations**
**Use Case**: Identify slow phases in a service (e.g., `PaymentService`).
**Query (SQL-like pseudocode):**
```sql
SELECT phase.name, AVG(phase.durationMs) AS avgDuration
FROM execution_phase_events
WHERE context.service = 'PaymentService'
  AND phase.durationMs > 500  -- Filter >500ms
GROUP BY phase.name
ORDER BY avgDuration DESC
LIMIT 10;
```

**Expected Output**:
| `phase.name`          | `avgDuration` |
|-----------------------|---------------|
| `"PaymentValidation"` | `680`         |
| `"ThirdPartyCall`     | `520`         |

---

### **2. Trace a Specific Execution Flow**
**Use Case**: Reconstruct the timeline for a failing request (`correlationId`).
**Query (Log Aggregator e.g., ELK):**
```json
{
  "query": {
    "match": {
      "context.correlationId": "73a1e6b7-9bcd-4321-8f0a-1234"
    }
  },
  "_source": ["phase.name", "timestamp", "phase.durationMs"]
}
```
**Sample Output**:
```json
[
  { "phase.name": "AuthCheck", "timestamp": 1697324600000, "durationMs": 20 },
  { "phase.name": "PaymentProcessing", "timestamp": 1697324600123, "durationMs": 680 }
]
```

---

### **3. Calculate Phase Contribution to Total Latency**
**Use Case**: Decompose end-to-end latency by phase (e.g., for a web request).
**Query (Time-Series DB e.g., Prometheus):**
```promql
# Total duration of "processOrder" flow.
sum by(service) (
  max(execution_phase_end[5m]) -
  max(execution_phase_start[5m])
) by (service)

# Duration breakdown (sum of all phases).
sum by(phase_name) (
  execution_phase_duration[5m]
) by (phase_name, service)
```
**Metrics**:
| Metric               | Value (ms) |
|----------------------|------------|
| `total_latency`      | `1200`     |
| `phase_name="Auth"`  | `50`       |
| `phase_name="DBCall"`| `900`      |

---

## **Implementation Considerations**
### **1. Instrumentation Overhead**
- **Trade-offs**:
  - High-precision timestamps add minimal overhead (~1–5% CPU).
  - Avoid logging every micro-phase if not critical for observability.
- **Optimization**:
  - Batch instrumentation for bulk phases (e.g., loop iterations).
  - Use lightweight formats (e.g., JSON for logs, Protobuf for telemetry).

### **2. Correlation Across Services**
- **Header Propagation**:
  ```http
  POST /order HTTP/1.1
  X-Correlation-ID: 73a1e6b7-9bcd-4321-8f0a-1234
  ```
- **Distributed Tracing**:
  Integrate with OpenTelemetry or Jaeger to extend phase data to downstream services.

### **3. Schema Evolution**
- **Backward Compatibility**:
  - Add new fields (e.g., `phase.subPhase`) without breaking readers.
  - Use optional fields or version tags (e.g., `"schemaVersion": "1.2"`).
- **Example Schema Update**:
  ```json
  {
    "phase": {
      "name": "LegacyPhase",
      "subPhase": "NewSubPhase"  // Optional field
    }
  }
  ```

---

## **Related Patterns**
1. **[Distributed Tracing]**
   - Extends `Execution Phase Instrumentation` across service boundaries by correlating traces using headers/IDs.
   - *Use when*: Diagnosing cross-service latency.

2. **[Sampling for High Cardinality]**
   - Reduces instrumentation volume by sampling phases (e.g., 1% of requests) to manage costs in large-scale systems.
   - *Use when*: Monitoring millions of concurrent flows.

3. **[Phase-Based Throttling]**
   - Uses phase durations to enforce rate limits (e.g., "No phase may exceed 300ms").
   - *Use when*: Preventing spikes in resource consumption.

4. **[Circuit Breaker]**
   - Combines with instrumentation to trigger fallbacks if a phase (e.g., `"ExternalAPICall"`) fails repeatedly.
   - *Use when*: Handling downstream service failures.

5. **[Logical Time Clocks (Lamport Timestamps)]**
   - For asynchronous systems where event ordering matters across services.
   - *Use when*: Debugging out-of-order phase execution.

---

## **Example Implementations**
### **1. Java (Spring Boot)**
```java
@Slf4j
public class PaymentService {
    private static final String CORRELATION_ID = "X-Correlation-ID";

    public String processPayment() {
        String correlationId = request.getHeader(CORRELATION_ID);
        long start = System.nanoTime();

        // Phase 1: Validation
        long phase1Start = System.nanoTime();
        validatePayment();
        long phase1End = System.nanoTime();

        // Log phase
        log.info("Phase Event: name={}, duration={}ms, correlationId={}",
                 "PaymentValidation", Duration.ofNanos(phase1End - phase1Start).toMillis(),
                 correlationId);

        // Phase 2: Persist
        long phase2Start = System.nanoTime();
        persistPayment();
        long phase2End = System.nanoTime();

        return "Success";
    }
}
```

### **2. Python (Asyncio)**
```python
import asyncio
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def track_phase(phase_name, correlation_id):
    start = time.perf_counter_ns()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter_ns() - start) / 1_000_000
        print(f'Phase Event: name={phase_name}, duration={duration_ms:.2f}ms, correlationId={correlation_id}')

async def process_order():
    correlation_id = "order-123"
    async with track_phase("OrderProcessing", correlation_id):
        await asyncio.sleep(0.5)
        # Business logic...
```

### **3. Observability Pipeline (ELK Stack)**
1. **Log Shipping**: Forward phase events to a log collector (e.g., Filebeat).
2. **Indexing**: Store in Elasticsearch with a `phase` field mapped as `nested` for flexible queries.
3. **Visualization**: Use Kibana to build dashboards like:
   - "Phases by Latency Percentiles."
   - "Error Rates by Phase Type."

---
## **Troubleshooting**
| **Issue**                          | **Cause**                                  | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------|------------------------------------------------------------------------------|
| Missing phase events                | Instrumentation skipped in code.           | Add logging for `track_phase()` entry/exit.                                   |
| Incorrect durations                 | Timestamp skew in distributed systems.     | Use synchronized clocks (e.g., NTP) or logical clocks (Lamport).             |
| High cardinality of correlation IDs | Too many unique IDs overwhelm storage.     | Implement sampling or bucketing (e.g., hash correlation IDs).                |
| Phase names missing metadata        | Dynamic phases not categorized.            | Enforce a phase taxonomy (e.g., enum values).                                |

---
## **Key Takeaways**
- **Instrument phases explicitly** to isolate bottlenecks.
- **Correlate with context** (e.g., request IDs) for end-to-end tracing.
- **Balance granularity**—avoid overloading systems with too many events.
- **Integrate with tracing** for distributed systems.