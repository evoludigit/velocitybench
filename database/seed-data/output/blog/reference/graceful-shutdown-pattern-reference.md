---
# **[Pattern] Graceful Shutdown Reference Guide**

---

## **Overview**
The **Graceful Shutdown Pattern** ensures that applications (e.g., FraiseQL) exit cleanly by minimizing disruptions during deployments or failures. When triggered by a **`SIGTERM`** signal (or equivalent), the service adheres to a structured timeline:
1. **Rejects new requests** → Prevents accumulation of pending workload.
2. **Drains active connections** → Allows existing requests to complete.
3. **Completes in-flight operations** → Respects configured timeouts.
4. **Closes database/cache connections** → Avoids resource leaks.
5. **Terminates processes** → Ensures clean exit.

This pattern is critical for **zero-downtime deployments**, ensuring no data loss or service degradation. Below are core concepts, implementation details, and practical examples.

---

## **Key Concepts & Schema Reference**
### **1. Graceful Shutdown Lifecycle**
| **Phase**               | **Action**                                                                 | **Timeout (Default)** | **Signal Handling**          |
|-------------------------|---------------------------------------------------------------------------|-----------------------|-------------------------------|
| **Pre-Shutdown**        | Rejects new requests via HTTP/307 (Temporary Redirect) or graceful rejection. | `45s` (configurable) | Blocking (`SIGTERM` received) |
| **Drain Connections**   | Closes idle connections; waits for active connections to complete.       | `120s` (configurable) | Non-blocking                  |
| **Finalize Operations** | Completes transactions/writes; logs pending operations.                   | `30s` (configurable) | Non-blocking                  |
| **Cleanup**             | Closes database/cache connections; releases locks.                      | `15s` (configurable) | Non-blocking                  |
| **Termination**         | Exits processes after cleanup completes.                                  | —                     | `SIGTERM` (final trigger)     |

**Timeouts**: Adjustable via environment variables (`FRAISEQ_SHUTDOWN_*_TIMEOUT`). Example:
```sh
export FRAISEQ_SHUTDOWN_DRAIN_CONNECTIONS_TIMEOUT=90s
```

---

### **2. Error Handling & Edge Cases**
| **Scenario**            | **Behavior**                                                                                     | **Mitigation**                                                                 |
|-------------------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Connection Timeouts** | In-flight requests fail with `503 Service Unavailable` after timeout expires.                | Ensure timeouts align with database connection retries.                       |
| **Lock Contention**     | Database locks held during shutdown may block other instances.                                   | Use short-lived locks (e.g., Redis `SETNX` with TTL).                        |
| **Long-Running Queries**| Queries exceeding `shutdown_finalize_timeout` may abort.                                      | Optimize slow queries; use async batching for writes.                        |
| **Signal Interruptions**| `SIGTERM` received mid-drain; forces abrupt termination.                                       | Implement a watchdog (e.g., Kubernetes liveness probes) to retry gracefully. |

---

## **Implementation Details**
### **1. Signal Handling**
FraiseQL uses a **reactive shutdown manager** (`shutdown_manager`) to:
- Catch `SIGTERM` via `os.signal()` (or custom signal handlers in other languages).
- Trigger a **non-blocking** phase transition chain (see table above).
- Log progress:
  ```log
  [2024-05-20 14:30:00] INFO: Graceful shutdown initiated. Phase: Draining connections (120s/120s)
  [2024-05-20 14:31:30] WARN: 5 active connections remain (timeout in 30s).
  ```

### **2. Database Connection Pooling**
- **Idle Connections**: Closed immediately after `SIGTERM`.
- **Active Connections**:
  - Wait for queries to complete (configurable `drain_timeout`).
  - Fail with `sql: conn reset by peer` if timeout expires.
- **Example Pool Config** (SQLAlchemy-inspired):
  ```python
  db_pool = create_engine(
      "postgresql+psycopg2://user:pass@host/db",
      pool_pre_ping=True,  # Ensures liveness checks
      pool_recycle=300,    # Recycle stale connections
      pool_timeout=30      # Reject new connections after 30s if drained
  )
  ```

### **3. HTTP Layer Graceful Rejection**
- **New Requests**: Return `HTTP/307 Temp Redirect` to a "shutting down" status page:
  ```http
  HTTP/1.1 307 Temporary Redirect
  Location: https://example.com/maintenance
  Retry-After: 120
  ```
- **In-Flight Requests**: Allow completion; log warnings for slow queries:
  ```go
  if shutdownManager.IsShuttingDown() {
      http.Error(w, "Service unavailable (draining connections)", http.StatusServiceUnavailable)
      return
  }
  ```

---

## **Query Examples**
### **1. Querying Shutdown Status**
FraiseQL exposes a **health check endpoint** (`/healthz`):
```http
GET /healthz HTTP/1.1
Host: api.example.com
```

**Responses**:
- **Healthy**:
  ```json
  {"status": "healthy", "shutdown": "not_initiated"}
  ```
- **Shutting Down**:
  ```json
  {"status": "draining", "phase": "connections", "remaining_time": 45}
  ```
- **Failed**:
  ```json
  {"status": "error", "message": "db_connection_timeout"}
  ```

### **2. Forcing a Shutdown (Admin Only)**
Admin API to trigger shutdown (useful for tests):
```http
POST /admin/shutdown HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

**Response**:
```json
{"status": "shutdown_initiated", "phases": ["reject_new_requests", "drain_connections"]}
```

---

## **Configuration**
| **Variable**                          | **Type**    | **Default** | **Description**                                                                 |
|---------------------------------------|-------------|-------------|---------------------------------------------------------------------------------|
| `FRAISEQ_SHUTDOWN_REJECT_TIMEOUT`     | Duration    | `45s`       | Time to reject new requests before draining.                                    |
| `FRAISEQ_SHUTDOWN_DRAIN_TIMEOUT`      | Duration    | `120s`      | Max time to wait for active connections to complete.                           |
| `FRAISEQ_SHUTDOWN_FINALIZE_TIMEOUT`   | Duration    | `30s`       | Time to finalize transactions/writes.                                          |
| `FRAISEQ_SHUTDOWN_CLEANUP_TIMEOUT`    | Duration    | `15s`       | Time to close DB/cache connections.                                             |
| `FRAISEQ_SHUTDOWN_FORCE_AFTER`        | Duration    | `180s`      | Force kill processes if shutdown hangs beyond this time.                         |

**Example `.env`**:
```env
FRAISEQ_SHUTDOWN_REJECT_TIMEOUT=60s
FRAISEQ_SHUTDOWN_DRAIN_TIMEOUT=90s
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Circuit Breaker**       | Temporarily stops requests to unhealthy services during shutdown.                | If database is slow/unresponsive during drain.                                  |
| **Bulkhead Pattern**      | Limits concurrent operations to prevent resource exhaustion.                    | High-concurrency apps where many connections drain simultaneously.              |
| **Idempotent Operations** | Ensures retries during shutdown don’t cause duplicate side effects.             | Writes to databases/caches must be replay-safe.                                 |
| **Zero-Downtime Deployments** | Combines graceful shutdown with blue-green deployments.                          | Production upgrades requiring no user impact.                                  |
| **Retry with Backoff**    | Retries failed operations (e.g., DB commits) after shutdown completes.          | Async tasks that depend on the service.                                         |

---

## **Best Practices**
1. **Monitor Shutdown Progress**:
   - Use Prometheus metrics (`fraise_shutdown_phase`, `fraise_shutdown_remaining_time`).
   - Example query:
     ```promql
     fraise_shutdown_phase{phase="draining"} > 0
     ```

2. **Test Shutdown Scenarios**:
   - Simulate `SIGTERM` in CI/CD:
     ```bash
     kill -TERM $(pidof fraiseql)  # Trigger graceful shutdown
     ```
   - Verify:
     - No new requests accepted.
     - In-flight requests complete within timeouts.
     - DB connections closed (check `pg_stat_activity`).

3. **Database-Specific Tips**:
   - **PostgreSQL**: Use `pg_terminate_backend` only after `drain_timeout` expires.
   - **Redis**: Use `CLUSTER FAILOVER` if clustering is enabled.

4. **Logging**:
   - Tag logs with `shutdown=true` to filter shutdown-related events:
     ```log
     {"level":"info","message":"Shutdown phase: draining","shutdown":"true"}
     ```

---

## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                     |
|------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Stuck in "Draining" Phase**      | Too many long-running queries.                                                | Increase `drain_timeout` or optimize slow queries.                                |
| **Database Errors on Shutdown**    | Active transactions locked DB resources.                                     | Use `SET TRANSACTION ISOLATION LEVEL READ COMMITTED`.                              |
| **HTTP 503 Errors After Timeout**   | Timeout expired; new requests rejected.                                      | Adjust `reject_timeout` or scale horizontally.                                   |
| **Connection Leaks**               | DB pool not drained; connections linger.                                     | Enable `pool_pre_ping` and validate connections before reuse.                     |

---