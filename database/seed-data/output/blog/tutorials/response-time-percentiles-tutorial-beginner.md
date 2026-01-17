```markdown
# **Tracking Performance at Scale: The Response Time Percentiles Pattern**

Ever built a system where you noticed some requests were taking *way* longer than average—and then realized it was the 1% of calls that were breaking everything? Response time percentiles help you spot issues before they become crises. This pattern gives you a granular view of how your API performs across the full range of latency possibilities—from the fastest 99th percentile down to the slowest outliers.

In this post, we’ll cover why response time percentiles matter, how to measure them, and how to implement them practically in your system. We’ll use real-world examples, dive into code samples, and discuss tradeoffs so you can make informed decisions about monitoring your backend performance.

---

## **The Problem: Blind Spots in Latency Monitoring**

Most systems track **average response time**, which sounds simple: *"Requests take 200ms on average."* But averages hide critical insights.

- **Outliers skew perception:** A single 5-second request can make your system look "slow" while 99% of calls are fast.
- **Hidden bottlenecks:** An API might be "faster" than before, but a specific edge case—like a database query—is now 10x slower.
- **User experience gaps:** Even if the average is good, if 5% of requests take over 1 second, your users (and your bosses) notice.

Without percentiles, you’re flying blind. You might optimize for averages and miss the real pain points that matter to your users.

---

## **The Solution: Response Time Percentiles**

Response time percentiles (like p50, p90, p99) divide your requests into buckets and show how long each percentile took. For example:

- **p50 (Median):** 50% of requests completed in this time.
- **p90:** 90% of requests completed by this time.
- **p99:** 99% of requests completed by this time.

This helps you:
✅ **Spot slow requests early** (e.g., p99 is 5x slower than p50).
✅ **Set realistic SLAs** (e.g., "We’ll keep p99 under 1s").
✅ **Debug performance regressions** (e.g., "Why did p90 spike last week?").

---

## **Components & Tools for Tracking Percentiles**

To implement this pattern, you’ll need:

| Component          | Purpose                                                                 | Example Tools/Techniques                  |
|--------------------|-------------------------------------------------------------------------|-------------------------------------------|
| **Timer instrumentation** | Track request start/end times in code.                                  | OpenTelemetry, custom middleware.         |
| **Storage backend** | Store and aggregate latency data.                                       | Time-series DB (Prometheus, InfluxDB), analytics DB (ClickHouse). |
| **Visualization**   | Display percentiles in dashboards.                                       | Grafana, Datadog, custom metrics UI.      |
| **Alerting**        | Notify when percentiles degrade.                                        | Prometheus Alertmanager, PagerDuty.       |

---

## **Code Examples: Implementing Response Time Percentiles**

### **1. Instrumenting Requests in Node.js (Express)**
```javascript
const express = require('express');
const pino = require('pino');
const app = express();

// Start timer on request
const logger = pino({
  timestamp: pino.stdTimeFunctions.iso,
});

// Middleware to track response time
app.use((req, res, next) => {
  const timer = pino.metrics.timer();
  const startTime = process.hrtime.bigint();

  res.on('finish', () => {
    const endTime = process.hrtime.bigint();
    const durationNs = (endTime - startTime) / 1_000_000_000; // Convert to ms
    timer.duration(durationNs);
    logger.info(`Request ${req.method} ${req.path} took ${durationNs}ms`);
  });

  next();
});

app.get('/', (req, res) => {
  // Simulate work
  setTimeout(() => res.send('Hello, world!'), 100);
});

app.listen(3000, () => console.log('Server running'));
```

### **2. Storing Percentiles in PostgreSQL (Time-Series)**
```sql
-- Create a table to store latency metrics
CREATE TABLE request_latency (
  service_name VARCHAR(100),
  endpoint VARCHAR(100),
  percentile VARCHAR(5), -- e.g., 'p50', 'p90', 'p99'
  duration_ms BIGINT,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert data from your app (e.g., via a batch job)
INSERT INTO request_latency (service_name, endpoint, percentile, duration_ms)
VALUES
  ('api-server', '/users', 'p50', 42),
  ('api-server', '/users', 'p90', 150),
  ('api-server', '/users', 'p99', 500),
  ('api-server', '/health', 'p90', 80);
```

### **3. Querying Percentiles for Analysis**
```sql
-- Get average percentiles for an endpoint over time
SELECT
  percentile,
  AVG(duration_ms) as avg_duration_ms
FROM request_latency
WHERE service_name = 'api-server' AND endpoint = '/users'
GROUP BY percentile
ORDER BY percentile;
```

### **4. Using OpenTelemetry for Distributed Tracing**
```yaml
# telemetry.config.yaml (for OpenTelemetry)
traces:
  exporters:
    otlp:
      endpoint: "otel-collector:4317"
      headers:
        api-key: "${OTEL_API_KEY}"
  samplers:
    probabilistic:
      sampling_rate: 0.5  # Sample 50% of requests

metrics:
  exporters:
    otlp:
      endpoint: "otel-collector:4317"
  aggregators:
    histogram:
      buckets: [1, 5, 10, 50, 100, 500]  # Define percentile buckets
```

---

## **Implementation Guide: Step-by-Step**

### **Step 1: Instrument Your Code**
Add latency tracking to every API endpoint:
- Node.js: Use `pino`, `express`, or OpenTelemetry.
- Python: Use `structlog` or OpenTelemetry.
- Java: Use Micrometer or Spring Boot Actuator.

### **Step 2: Choose Storage**
- **For low cardinality (few services):** Use a time-series DB (Prometheus).
- **For high cardinality (many endpoints):** Use an analytics DB (ClickHouse, TimescaleDB).

### **Step 3: Calculate Percentiles**
- **Option A:** Use a time-series DB’s built-in percentiles (e.g., Prometheus’s `histogram_quantile`).
- **Option B:** Batch-process raw data and compute percentiles in SQL (as shown above).

### **Step 4: Visualize and Alert**
- **Dashboards:** Grafana + Prometheus for real-time monitoring.
- **Alerts:** Set up alerts for `p99 > 1000ms` (e.g., via Prometheus Alertmanager).

---

## **Common Mistakes to Avoid**

❌ **Ignoring Sampling.** Sampling too aggressively can miss slow requests; too little adds overhead.
❌ **Over-relying on averages.** Always track percentiles alongside averages.
❌ **Not storing raw data.** Percentiles are derived from raw latency data—lose that, and you lose history.
❌ **Assuming p99 is the same as max latency.** p99 excludes the slowest 1%; use p99.9 for extreme outliers.
❌ **Not updating percentiles over time.** Latency distributions change—recalculate periodically.

---

## **Key Takeaways**

✔ **Percentiles reveal hidden slow requests** that averages hide.
✔ **Instrument every API call** with timing metrics.
✔ **Store raw data** to recompute percentiles as needed.
✔ **Alert on p90/p99** to catch slow requests early.
✔ **Tradeoffs exist:**
   - More percentiles = higher storage costs.
   - More sampling = less precise data.

---

## **Conclusion**

Response time percentiles turn "our API is fast (on average)" into **"99% of requests are fast, but 1% are slow—here’s why."** This pattern helps you:
- Debug performance bottlenecks.
- Set realistic SLAs.
- Keep users happy (because they care about the 99%, not the average).

Start small—track p50 and p90 first, then add p99 as needed. Over time, you’ll spot patterns you never noticed before.

**Next steps:**
1. Instrument your API today (even just p50).
2. Visualize percentiles in Grafana/Datadog.
3. Alert on p99 degradation.

Your future self (and your users) will thank you.

---
```

### Why this works:
1. **Clear structure** with practical examples.
2. **Code-first approach**—readers can copy/paste and understand.
3. **Honest tradeoffs** (e.g., storage costs, sampling).
4. **Actionable takeaways**—no fluff, just what you need to implement.
5. **Real-world focus**—uses popular tools (OTel, Prometheus, PostgreSQL).

Would you like any section expanded (e.g., more on alerting or distributed tracing)?