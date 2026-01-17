# **Debugging Graceful Shutdown Pattern: A Troubleshooting Guide**

---

## **1. Introduction**
The **Graceful Shutdown Pattern** ensures that applications handle termination signals (e.g., `SIGTERM`) properly by:
- **Draining in-flight connections** (preventing new requests)
- **Completing pending operations** (e.g., database transactions, cache writes)
- **Closing resources cleanly** (e.g., DB connections, HTTP clients)

If misconfigured, this can lead to **connection errors, incomplete transactions, or service disruptions** during deployments.

---

## **2. Symptom Checklist**
| **Symptom**                     | **Likely Cause**                          | **Verification Steps** |
|----------------------------------|------------------------------------------|-------------------------|
| Clients report `502 Bad Gateway` | Unclean shutdown during rolling updates   | Check logs for `SIGTERM` uncaught |
| Database transactions incomplete | Uncommitted writes on shutdown            | Query pending transactions |
| Cache corruption                 | Cache evictions during shutdown           | Check cache stats before/after shutdown |
| Open connections remain          | `SIGTERM` handled but connections not drained | Use `lsof -i` to check active connections |
| Slow rollback during deploy      | Long-running operations blocked by shutdown | Monitor `p99` latency during updates |

---

## **3. Common Issues & Fixes**

### **Issue 1: SIGTERM Not Handled Properly**
**Symptoms:**
- Logs show `unhandled SIGTERM`
- Processes crash abruptly on `kill -TERM <pid>`

**Fix:**
Ensure `SIGTERM` is caught and a structured shutdown begins.
```go
package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
)

var shutdownCtx = context.Background()

func main() {
	// Setup signal handling
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)

	// Start graceful shutdown
	go func() {
		<-sigCh
		log.Println("Shutting down gracefully...")
		shutdownCtx, _ = context.WithTimeout(context.Background(), 30*time.Second)
		// Drain connections, close DB pools, etc.
	}()
}
```

**Debugging Check:**
```bash
# Verify SIGTERM was caught
grep -i "shutting down" /var/log/app.log
```

---

### **Issue 2: Connections Not Drained Before Shutdown**
**Symptoms:**
- New connections still being accepted after `SIGTERM`
- Persistent HTTP `502` errors during deploy

**Fix:**
Use **connection pooling with graceful shutdown**:
```javascript
// Node.js (Express example with `express` + `cluster`)
const http = require('http');
const cluster = require('cluster');

function shutdownServer() {
  httpServer.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
}

// Handle SIGTERM
process.on('SIGTERM', () => {
  console.log('SIGTERM received. Draining connections...');
  httpServer.dropAllConnections(); // If using `express` + `http-server`
  setTimeout(shutdownServer, 30000); // 30s timeout
});
```

**Debugging Check:**
```bash
# Check active connections pre-shutdown
netstat -anp | grep <port> | wc -l
```

---

### **Issue 3: Incomplete Database Transactions**
**Symptoms:**
- Database shows `IN_PROGRESS` transactions after shutdown
- Data corruption detected post-deploy

**Fix:**
Ensure all transactions are completed or rolled back:
```python
# Python (SQLAlchemy)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://user:pass@localhost/db")
Session = sessionmaker(bind=engine)

def graceful_shutdown():
    Session.close_all()  # Close all sessions
    engine.dispose()     # Shut down the engine
```

**Debugging Check:**
```sql
-- Check PostgreSQL for pending transactions
SELECT * FROM pg_stat_activity WHERE state = 'active';
```

---

### **Issue 4: Cache Not Flushed on Shutdown**
**Symptoms:**
- Cache inconsistency after redeploy
- Users see stale data

**Fix:**
Use a synchronous cache eviction mechanism:
```go
// Go (Redis + sync.Mutex)
var (
    cacheMu   sync.Mutex
    cache     = make(map[string]string)
    redisConn *redis.Client
)

func shutdown() {
    cacheMu.Lock()
    defer cacheMu.Unlock()
    redisConn.FlushAll() // Ensure sync with Redis
}
```

**Debugging Check:**
```bash
# Verify Redis cache was cleared
redis-cli INFO stats | grep keyspace_hits
```

---

## **4. Debugging Tools & Techniques**

### **A. Log-Based Debugging**
- **Key Log Entries to Check:**
  - `SIGTERM received` (confirm signal handling)
  - `Draining connections...` (verify graceful shutdown started)
  - `All connections closed` (confirm cleanup)
- **Example Command:**
  ```bash
  tail -f /var/log/app.log | grep -E "shutdown|SIGTERM|connection"
  ```

### **B. System-Level Checks**
| **Tool**       | **Use Case**                          | **Command** |
|----------------|---------------------------------------|-------------|
| `lsof`         | Check open files/sockets              | `lsof -i :<port>` |
| `netstat`      | Active connections                    | `netstat -anp` |
| `strace`       | System calls during shutdown          | `strace -p <pid>` |
| `pprof`        | Long-running goroutines (Go)           | `go tool pprof http://localhost:6060/debug/pprof/go` |

### **C. Distributed Tracing**
- Use **OpenTelemetry** or **Jaeger** to trace requests during shutdown.
- **Example Query:**
  ```bash
  jaeger-cli query --span.selector='app.name=YOUR_APP' --duration=60s
  ```

---

## **5. Prevention Strategies**

### **A. Automated Testing**
- **Unit Tests:**
  Mock `SIGTERM` and verify cleanup:
  ```python
  def test_graceful_shutdown():
      import signal
      signal.signal(signal.SIGTERM, graceful_shutdown)
      signal.SIGTERM()  # Simulate signal
      assert not db_pool.is_closed()  # Should close
  ```
- **Integration Tests:**
  - Deploy a test pod with `SIGTERM` and verify no errors.

### **B. Configuration Best Practices**
| **Setting**               | **Recommended Value** | **Why?** |
|---------------------------|-----------------------|----------|
| `timeout` (shutdown)      | 30s–60s               | Balances speed and cleanup |
| `max_connections` (DB)    | Based on workload     | Prevents connection leaks |
| `cache_flush_on_shutdown` | `true`               | Ensures consistency |

### **C. CI/CD Guardrails**
- **Pre-Deployment Check:**
  ```bash
  # Verify graceful_shutdown() exists
  grep -q "signal.SIGTERM" app/main.go || exit 1
  ```
- **Post-Rollout Check:**
  ```bash
  # Ensure no lingering connections
  until nc -zv localhost <port> >/dev/null; do sleep 1; done
  ```

### **D. Alerting**
- Set up alerts for:
  - Unhandled `SIGTERM` (via log monitoring)
  - High connection count during deploy (`netstat` alerts)

---

## **6. Conclusion**
### **Quick Fix Cheat Sheet**
| **Problem**               | **Immediate Fix** |
|---------------------------|-------------------|
| `SIGTERM` ignored         | Add `signal.SIGTERM` handler |
| Connections not draining | Implement `dropAllConnections()` |
| DB transactions stuck     | Call `session.close()` explicitly |
| Cache corruption          | Add `cache.flush()` on shutdown |

### **Final Checklist Before Production**
✅ Signal handler registered for `SIGTERM`
✅ Connections drained before shutdown
✅ All DB transactions committed/rolled back
✅ Cache flushed or backed up
✅ Shutdown timeout set (e.g., 30–60s)

---
**Next Steps:**
- Review logs for suspicious shutdowns
- Test rollback with `kubectl rollout undo` (K8s)
- Monitor latency spikes during deployments

This guide ensures **quick resolution** of graceful shutdown issues while preventing recurrence.