# **[Pattern] Connection Pool Strategies Reference Guide**

---

## **Overview**
Connection pooling optimizes database performance by reusing established connections instead of opening new ones for each query. This pattern reduces overhead from connection handshakes, improves throughput, and minimizes resource exhaustion. FraiseQL implements configurable connection pool strategies with dynamic sizing (CPU-core and workload-based), lifecycle management (idle timeouts, max lifetime), health checks, and automatic failover/reconnection to ensure resilient database interactions.

Key benefits:
- **Performance**: Reduces repeated TCP/IP handshakes and auth overhead.
- **Scalability**: Adjusts pool size dynamically per core/load.
- **Reliability**: Detects and repairs unhealthy connections transparently.
- **Cost Efficiency**: Limits idle connections to avoid server resource waste.

---

## **Key Concepts**
### **1. Pool Sizing Strategies**
| **Metric**               | **Description**                                                                                     | **Formula**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Default Pool Size**    | Base size based on CPU cores (default: 4×cores with min/max bounds).                                | `min(4×Cores, 20)` / `max(1×Core, 50)`                                                          |
| **Workload Scaling**     | Adjusts size based on active queries (e.g., 1.5× queries per connection under peak load).           | `PoolSize = Clamp(1.5 × ActiveQueries / UtilizationRatio, Min, Max)`                           |
| **Core-Based Adjustment**| Adapts to thread contention (e.g., per-core pool on multi-threaded apps).                            | `PoolPerCore = Clamp(Cores / Threads, 1, 4)`                                                   |
| **Concurrency Throttle** | Limits concurrent operations per connection to avoid overload (default: 50).                        | `Concurrency = min(MaxConcurrent, ActiveQueries × LatencyFactor)`                              |

### **2. Connection Lifecycle**
| **Parameter**            | **Purpose**                                                                                          | **Default**      |
|--------------------------|-----------------------------------------------------------------------------------------------------|------------------|
| `idleTimeoutMs`          | Timeout for unused connections (prevents stale connections).                                         | `60000` (1 min)  |
| `maxLifetimeMs`          | Maximum time a connection can exist before replacement.                                               | `3600000` (1 hr) |
| `maxRetries`             | Retry count for failed connections before marking as unhealthy.                                      | `3`              |
| `retryIntervalMs`        | Delay between retries (exponential backoff).                                                         | `1000` (1 sec)   |

### **3. Health Checks**
- **Ping Interval**: Validates connections periodically (`healthCheckIntervalMs`, default: `30000` ms).
- **Failure Threshold**: Closes connection if `n` consecutive pings fail (`healthCheckFailureThreshold = 3`).
- **Reconnection**: Automatically reopens connections post-failure.

### **4. Reconnection Logic**
- **Transient Failures**: Retries on network errors (e.g., `SQLTransientError`), timeouts.
- **Permanent Failures**: Logs error and retries with exponential backoff (max: 10s delay).
- **Graceful Degradation**: Reduces pool size by 50% if reconnection fails.

---
## **Configuration Schema**

| **Section**       | **Parameter**               | **Type**      | **Description**                                                                                     | **Default**      | **Example Values**                     |
|-------------------|-----------------------------|---------------|-----------------------------------------------------------------------------------------------------|------------------|------------------------------------------|
| `pool`           | `size`                      | `int`         | Base pool size (overridden by scaling formulas).                                                    | `20`             | `8` (low-traffic), `100` (high-traffic) |
|                   | `maxSize`                   | `int`         | Absolute upper size limit.                                                                          | `50`             | `200`                                    |
|                   | `coreFactor`               | `float`       | Multiplier for core-based sizing (`coreFactor × Cores`).                                            | `4`              | `3` (conservative), `6` (aggressive)   |
|                   | `workloadFactor`           | `float`       | Scales pool by active queries (`workloadFactor × ActiveQueries`).                                  | `1.5`            | `2.0`                                    |
| `lifecycle`      | `idleTimeoutMs`             | `int`         | Timeout for idle connections (ms).                                                                 | `60000`          | `30000`                                  |
|                   | `maxLifetimeMs`             | `int`         | Max connection age before replacement (ms).                                                        | `3600000`        | `1800000`                                |
| `health`         | `checkIntervalMs`           | `int`         | Ping interval (ms).                                                                               | `30000`          | `10000`                                  |
|                   | `failureThreshold`          | `int`         | Consecutive failures to close connection.                                                          | `3`              | `5`                                      |
| `retry`          | `maxRetries`                | `int`         | Max retries for transient failures.                                                               | `3`              | `5`                                      |
|                   | `retryDelayMs`              | `int`         | Initial retry delay (ms).                                                                         | `1000`           | `500`, `2000` (exponential backoff)     |
|                   | `concurrency`               | `int`         | Max concurrent operations per connection.                                                        | `50`             | `100`                                    |

**Example Configuration (YAML):**
```yaml
pool:
  size: 20
  maxSize: 100
  coreFactor: 3
  workloadFactor: 2.0
lifecycle:
  idleTimeoutMs: 30000
health:
  checkIntervalMs: 10000
retry:
  maxRetries: 5
  retryDelayMs: [1000, 2000, 5000]  # Exponential delays
```

---

## **Query Examples**

### **1. Static Pool Configuration**
```csharp
// Initialize with fixed pool size (30 connections)
var pool = new ConnectionPoolBuilder()
    .SetPoolSize(30)
    .Build();
```

### **2. Dynamic Core-Based Sizing**
```csharp
// Auto-scale based on CPU cores (factor=3)
var pool = new ConnectionPoolBuilder()
    .SetCoreFactor(3)
    .Build();
```
*Result*: `PoolSize = min(max(3 × Cores, 1), 50)`.

### **3. Workload-Driven Scaling**
```csharp
// Scale pool by active queries (factor=1.8)
var pool = new ConnectionPoolBuilder()
    .SetWorkloadFactor(1.8)
    .Build();
```
*Logic*: `PoolSize = Clamp(1.8 × ActiveQueries, 10, 200)`.

### **4. Custom Lifecycle Policies**
```csharp
// Short-lived connections (30s idle timeout)
var pool = new ConnectionPoolBuilder()
    .SetIdleTimeoutMs(30000)
    .SetMaxLifetimeMs(900000)  // 15 mins
    .Build();
```

### **5. Health Check Tuning**
```csharp
// Aggressive health checks (2s interval, 2 failures to close)
var pool = new ConnectionPoolBuilder()
    .SetHealthCheckIntervalMs(2000)
    .SetFailureThreshold(2)
    .Build();
```

### **6. Reconnection with Exponential Backoff**
```csharp
// Retry transient errors with delays: [500ms, 1s, 2s]
var pool = new ConnectionPoolBuilder()
    .SetMaxRetries(3)
    .SetRetryDelaysMilliseconds(new[] { 500, 1000, 2000 })
    .Build();
```

### **7. Concurrency Limits**
```csharp
// Limit 100 concurrent operations per connection
var pool = new ConnectionPoolBuilder()
    .SetConcurrencyLimit(100)
    .Build();
```

---

## **Monitoring Metrics**
Track these metrics for optimization:
| **Metric**               | **Description**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|
| `pool.activeConnections`  | Current connections in use.                                                                      |
| `pool.idleConnections`   | Connections available for reuse.                                                                |
| `pool.pendingQueries`    | Queries waiting due to pool exhaustion.                                                          |
| `pool.failures`          | Reconnection failures (threshold: warn if >10% of queries).                                       |
| `pool.pingErrors`        | Health check failures (trigger alerts if >3/minute).                                             |
| `pool.avgLatencyMs`      | Connection acquisition time (target: <10ms).                                                     |

**Example Query (Prometheus):**
```sql
# Slow connection acquisitions
histogram_quantile(0.95, rate(pool_acquire_duration_seconds_bucket[5m])) > 0.05
```

---

## **Related Patterns**
1. **[Connection Resiliency]**
   - Complements this pattern with circuit breakers for database outages (e.g., [FraiseQL Circuit Breaker](link)).
   - *Use Case*: Gracefully handle server restarts or network partitions.

2. **[Query Batch Optimization]**
   - Reduces connection churn by batching queries (e.g., `BATCH_SIZES = [100, 500]`).
   - *Use Case*: Bulk inserts/updates with low-latency requirements.

3. **[Dynamic Scaling with Autoscaling Groups]**
   - Pair with auto-scaling to adjust pool size based on load (e.g., AWS Auto Scaling).
   - *Use Case*: Cloud deployments with variable traffic.

4. **[Connection Leak Detection]**
   - Integrate with tools like [FraiseQL Debug](link) to log unclosed connections.
   - *Use Case*: Debug "connection leak" issues in long-running transactions.

5. **[Read/Write Splitting]**
   - Combine with master-slave replication for read-heavy workloads.
   - *Use Case*: E-commerce platforms with high read-to-write ratios.

---
## **Best Practices**
1. **Benchmark First**: Use `fraiseql benchmark --pool` to tune `coreFactor`/`workloadFactor`.
2. **Avoid Over-Provisioning**: Set `maxSize` to prevent thrashing (e.g., `maxSize = 2 × coreFactor × Cores`).
3. **Monitor Idle Connections**: High `idleConnections` may indicate over-provisioning.
4. **Handle Failures Gracefully**: Use `OnConnectionFailed` callbacks for custom retries.
5. **Test Failover**: Simulate database outages to validate reconnection logic.

---
**See Also**:
- [FraiseQL Connection Pool API Docs](link)
- [Database Connection Lifecycle Guide](link)