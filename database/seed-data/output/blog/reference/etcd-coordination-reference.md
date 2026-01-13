---

# **[Pattern] Etcd Coordination Integration Reference Guide**

## **Overview**
Etcd is a distributed, consistent key-value store designed for coordinating distributed systems. This guide outlines **core integration patterns** for using etcd to manage consensus, leader election, configuration synchronization, and distributed locks. The patterns cover **low-level key-value operations**, **high-level abstractions** (e.g., leases, watchers), and **real-world use cases** like service registration, leader election, and distributed configuration.

Key benefits of etcd coordination:
- **Strong consistency** (linearizability) for critical state.
- **Leaderless operation** for high availability.
- **Built-in TTL (leases) and watchers** for automatic cleanup and reactivity.
- **Scalability** for large-scale distributed systems.

---

## **Schema Reference**
Below is a structured schema table for key etcd integration concepts. All keys follow the convention:
`/{namespace}/{resource}/{resource_id}`

| **Category**               | **Key Path**                          | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|----------------------------|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Configuration Sync**     | `/config/{app_name}/{setting}`        | Stores dynamic or static configurations for applications. Supports nested JSON/YAML via subkeys.                                                                                                          | `/config/webapp/database/url`                                                              |
| **Service Discovery**      | `/services/{service_type}/{instance}` | Registers service endpoints (IP:port, metadata) for client-side discovery. Leases ensure automatic de-registration on failure.                                                                | `/services/api/v1/instance-1` (`{"host": "10.0.0.1", "port": 8080, "lease": "10s"}`)       |
| **Leader Election**        | `/election/{group}/{candidate}`       | Candidates compete for leadership by writing to `/election/{group}/current`. The last successful writer wins. Uses leases to detect failures.                                                          | `/election/pod-manager/current` (`{"leader": "pod-42", "ttl": "30s"}`)                       |
| **Distributed Locks**      | `/locks/{scope}/{lock_key}`           | Atomic lock acquisition via compare-and-swap (CAS). Leases prevent stale locks.                                                                                                                                | `/locks/database/migrations/lock-123` (`{"owner": "app-7", "lease": "60s"}`)                |
| **Workflow Coordination**  | `/workflows/{job_id}/{step}`          | Tracks multi-step workflows (e.g., CI/CD pipelines). Steps are atomic and can block/wait for dependencies.                                                                                                | `/workflows/pipeline-1/step-2` (`{"status": "running", "dependencies": ["step-1"]}`)       |
| **Health Checks**          | `/health/{service_type}/{instance}`   | Clients publish liveness/readiness probes. Etcd detects failures via lease expiration and triggers rebalancing.                                                                                      | `/health/webapi/instance-2` (`{"status": "healthy", "lease": "5s"}`)                         |
| **Rate Limiting**          | `/limits/{resource}/{client}`         | Tracks usage quotas (e.g., API calls) per client to enforce soft/hard limits.                                                                                                                                    | `/limits/api/token-abc123` (`{"remaining": 900, "reset": "2023-12-01T12:00:00Z"}`)       |

---

## **Implementation Details**
### **1. Core Operations**
| **Operation**       | **Method**       | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|---------------------|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Write**           | `PUT`            | Updates a key-value pair. Supports **CAS (compare-and-swap)** for atomic condition checks.                                                                                                                    | `PUT /locks/db/lock-1 value="locked" if:absence` (overwrite if key doesn’t exist)         |
| **Read**            | `GET`            | Retrieves key-value pairs with optional **prefix filtering** (e.g., `GET /config/webapp`).                                                                                                               | `GET /services/api/v1` (returns all API instances)                                              |
| **Delete**          | `DELETE`         | Removes a key. Useful for **lease-based cleanup** (e.g., de-registering failed services).                                                                                                                 | `DELETE /services/api/v1/instance-1`                                                            |
| **Watch**           | `Watch` (stream) | Asynchronous notification for key changes. Supports **prefix watches** (e.g., `/config/*`). Watchers auto-reconnect if disconnected.                                                                 | `WATCH /locks/database` (notifies when `lock-123` is acquired/released)                       |
| **Leases**          | `Lease GRANT`    | Assigns a TTL to a key. Expiring leases trigger **automatic cleanup** (e.g., delete keys or notify watchers).                                                                                          | `LEASE GRANT 30000` → `PUT /health/webapi/instance-1 value="..." lease=lease-123`         |

---

### **2. Advanced Patterns**
#### **A. Leader Election**
**Use Case**: Select a single leader for coordination (e.g., database replication).
**Implementation**:
1. Candidates write to `/election/{group}/current` with a **lease**.
2. If the write succeeds, the candidate is elected; otherwise, retry.
3. Use **watchers** on `/election/{group}` to detect leadership changes.

**Pseudocode**:
```go
func electLeader(group string) {
    lease := etcd.NewLease()
    lease.Grant(30 * time.Second)

    _, err := etcd.Put(
        fmt.Sprintf("/election/%s/current", group),
        fmt.Sprintf("leader-%d", os.Getpid()),
        etcd.WithLease(lease.ID()),
        etcd.With Compare(etcd.CompareAbsent()),
    )
    if err != nil {
        time.Sleep(1 * time.Second) // Retry
        electLeader(group)
    }

    // Watch for election changes
    watchChan := etcd.Watch(fmt.Sprintf("/election/%s", group))
    go func() {
        for watchResp := range watchChan {
            for _, event := range watchResp.Events {
                if event.IsDelete() {
                    // Lost leadership; re-elect
                    electLeader(group)
                }
            }
        }
    }()
}
```

#### **B. Distributed Locks**
**Use Case**: Serialize access to shared resources (e.g., database migrations).
**Implementation**:
1. Acquire lock via **CAS** on `/locks/{scope}/{key}`.
2. Set a **short lease** (e.g., 5–30 seconds) to avoid deadlocks.
3. Release the lock by deleting the key or letting the lease expire.

**Pseudocode**:
```go
func acquireLock(lockPath string) error {
    lease := etcd.NewLease()
    lease.Grant(5 * time.Second)

    _, err := etcd.Put(
        lockPath,
        fmt.Sprintf("locked-by-%d", os.Getpid()),
        etcd.WithLease(lease.ID()),
        etcd.WithCompare(etcd.CompareAbsent()),
    )
    return err
}

func releaseLock(lockPath string) {
    etcd.Delete(lockPath) // Manual release or let lease expire
}
```

#### **C. Config Sync with Watchers**
**Use Case**: Dynamically update application configs without restarts.
**Implementation**:
1. Write config to `/config/{app}/{key}`.
2. Clients **watch** the config path and apply changes on update.

**Pseudocode**:
```go
func syncConfig(app, key string) {
    watchChan := etcd.Watch(fmt.Sprintf("/config/%s/%s", app, key))
    go func() {
        for watchResp := range watchChan {
            for _, event := range watchResp.Events {
                if event.IsPut() {
                    // Apply new config
                    config := event.Kv.Value
                    applyConfig(config)
                }
            }
        }
    }()
}
```

---

### **3. Best Practices**
| **Best Practice**               | **Guidance**                                                                                                                                                                                                 | **Example**                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Use Leases for Ephemeral Data** | Leases automatically clean up keys (e.g., service registrations) on failure. Avoid manual deletes.                                                                                                    | `lease.Grant(30)` → `PUT` with `lease=lease.ID()`                                                |
| **Prefix Watches for Scaling**    | Watch prefixes (`/config/*`) instead of individual keys to decouple clients from key paths.                                                                                                         | `WATCH /config/webapp` (catches `/config/webapp/database` changes)                               |
| **Short Lease durations**        | Balance responsiveness vs. stale locks (e.g., 5–30 seconds for locks, 30–60s for services).                                                                                                               | `LEASE GRANT 30000` (5-minute leases for health checks)                                       |
| **CAS for Atomicity**            | Use `Compare` (e.g., `etcd.CompareAbsent()`, `etcd.CompareVersion()`) to avoid race conditions.                                                                                                    | `PUT` with `Compare(etcd.CompareAbsent())` for idempotent writes                               |
| **Graceful Degradation**         | Clients should retry failed operations (e.g., leader election) with exponential backoff.                                                                                                               | `time.Sleep(time.Duration(rand.Intn(1000)) * time.Millisecond)` on retry                      |
| **Audit Key Naming**            | Follow conventions (e.g., `/services/{type}/{id}`) for maintainability. Avoid wildcard keys in production.                                                                                               | `/services/api/v1/instance-1` (not `/services/*`)                                             |
| **Limit Watcher Load**           | Batch watches (e.g., combine `/config/*` and `/health/*`) to reduce etcd overhead.                                                                                                                 | Single watcher for `/config/* AND /health/*`                                                   |

---

### **4. Common Pitfalls & Solutions**
| **Pitfall**                          | **Cause**                                                                                                                                                                                                 | **Solution**                                                                                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Stale Locks**                     | Lease expires but lock key isn’t deleted (e.g., client crash).                                                                                                                                          | Use **auto-delete on lease expiration** or manual `DELETE` in cleanup.                                                                                               |
| **Watch Flooding**                  | Too many watchers on high-churn paths (e.g., `/health/*`).                                                                                                                                              | Aggregate watches (e.g., `WATCH /health/*`) or use **prefix watches** sparingly.                                                                              |
| **Key-Value Collisions**            | Concurrent writes to the same key without CAS.                                                                                                                                                         | Always use `Compare` (e.g., `etcd.CompareVersion()`) for critical writes.                                                                                          |
| **Leader Election Starvation**      | Too many candidates competing for leadership.                                                                                                                                                          | Limit candidates or use **priority classes** (e.g., prioritize stable nodes).                                                                        |
| **Config Drift**                    | Manual config edits bypass etcd (e.g., restarting with hardcoded values).                                                                                                                              | Enforce etcd as the **source of truth**; validate configs on startup.                                                                                            |
| **Unbounded Retries**               | Clients indefinitely retry failed operations (e.g., lease revocation).                                                                                                                                   | Implement **max retries** (e.g., 5 attempts) or **circuit breakers**.                                                                                             |

---

## **Query Examples**
### **1. Service Registration**
```bash
# Register a service with a 30-second lease
curl -L \
  --request PUT \
  --data '{"host":"10.0.0.1","port":8080}' \
  http://localhost:2379/v3/kv/put?key=/services/api/v1/instance-1&lease=30&prevExist=false
```

### **2. Leader Election (Candidate)**
```bash
# Attempt to claim leadership; fails if another candidate exists
curl -L \
  --request PUT \
  --data '{"leader":"pod-42"}' \
  http://localhost:2379/v3/kv/put?key=/election/pod-manager/current&lease=300&compare=absence=true
```

### **3. Watch for Config Changes**
```bash
# Stream config updates for webapp
curl -L \
  --request POST \
  --data '{"key":"/config/webapp/database/url","limit":0}' \
  http://localhost:2379/v3/watch?range.end=/config/webapp/database/url
```

### **4. Delete a Key with Lease**
```bash
# Remove a service registration (triggered by lease expiration)
curl -L \
  --request DELETE \
  http://localhost:2379/v3/kv/delete?key=/services/api/v1/instance-1
```

### **5. List All Services**
```bash
# Fetch all API instances (prefix range)
curl -L \
  --request GET \
  http://localhost:2379/v3/kv/range?key=/services/api/v1&limit=100
```

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Leader Election]**                 | Select a single coordinator for distributed systems (e.g., Kafka, ZooKeeper).                                                                                                                      | Critical coordination (e.g., database replication, backend orchestration).                          |
| **[Distributed Locks]**              | Serialize access to shared resources (e.g., database connections, caches).                                                                                                                       | Preventing race conditions in multi-instance apps.                                                 |
| **[Config Sync]**                    | Dynamically update application configs without restarts.                                                                                                                                               | Microservices, cloud-native apps (e.g., Kubernetes ConfigMaps).                                      |
| **[Service Discovery]**              | Register/discover service endpoints for client-side routing.                                                                                                                                           | Load balancers, API gateways, or peer-to-peer communication.                                       |
| **[Circuit Breaker]**                 | Fault-tolerant fallback for dependent services (complements etcd with retry logic).                                                                                                                | Resilient architectures (e.g., handling etcd unavailability).                                     |
| **[Idempotent Writes]**              | Ensure safe repeated operations (e.g., config updates) via etcd CAS.                                                                                                                               | High-throughput systems where retries are common.                                                  |
| **[Workflow Coordination]**           | Orchestrate multi-step processes (e.g., CI/CD pipelines).                                                                                                                                              | Stateful workflows (e.g., data processing, order processing).                                      |

---

## **References**
- [Etcd Documentation](https://etcd.io/docs/)
- [Etcd Go Client API](https://github.com/coreos/etcd/blob/master/Documentation/dev-guide.md)
- [CNCF Etcd Operator](https://github.com/coreos/etcd-operator) (for Kubernetes)
- [Raft Consensus Algorithm](https://raft.github.io/) (underlying etcd protocol)