# **[Pattern] Durability Integration Reference Guide**

---

## **Overview**
The **Durability Integration** pattern ensures that state changes—such as configuration updates, system configurations, or application settings—are persisted reliably across restarts, failures, or distributed environments. This pattern is critical in microservices, cloud-native applications, and systems where transient failures or component restarts are common.

Durability integration decouples temporary state (e.g., in-memory caches) from persistent state (e.g., databases, configuration stores). By leveraging backends like **etcd**, **Consul**, **Redis**, or **DynamoDB**, the pattern guarantees that changes survive failures and are synchronized across nodes. This guide covers key concepts, implementation strategies, API specifications, and query examples.

---

## **Key Concepts**
| Concept            | Description                                                                                                                                                                                                 |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Persistent Store** | A backend (e.g., etcd, DynamoDB) that retains state even after restarts.                                                                                                                                       |
| **Watcher**        | A client-side mechanism (e.g., etcd watchers, Redis pub/sub) that notifies clients of state changes.                                                                                                            |
| **Idempotency**    | Ensures repeated state updates (e.g., after crashes) don’t cause unintended side effects.                                                                                                                      |
| **Replication**    | Syncs state across multiple nodes (e.g., via etcd’s consensus protocol) for fault tolerance.                                                                                                                  |
| **TTL (Time-to-Live)** | Automatically expires transient values (e.g., session tokens) after a defined duration.                                                                                                                     |
| **Conflict Resolution** | Mechanism (e.g., last-write-wins, version vectors) to handle concurrent updates.                                                                                                                            |
| **Integration Layer** | Middleware (e.g., a service mesh or API gateway) that bridges transient and persistent stores.                                                                                                              |

---

## **Schema Reference**
The following table outlines common data models for durability stores (adapt as needed).

| Field/Parameter       | Type          | Description                                                                                                                                                       | Example Value               |
|-----------------------|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| **Key**               | `string`      | Unique identifier for the state entry (e.g., `app:config:timeout`).                                                                        | `app:config:timeout`        |
| **Value**             | `string`/JSON | Serialized state data (e.g., JSON, YAML).                                                                                                              | `{"timeout": 30000}`        |
| **Version**           | `integer`     | Optimistic concurrency control (incremented on updates).                                                                                               | `3`                         |
| **TTL (Seconds)**     | `integer`     | Auto-delete after this duration (0 = no TTL).                                                                                                           | `3600`                      |
| **CreatedAt**         | `timestamp`   | ISO 8601 timestamp of creation.                                                                                                                      | `2024-02-20T14:30:00Z`      |
| **UpdatedAt**         | `timestamp`   | Last update timestamp.                                                                                                                             | `2024-02-20T14:35:00Z`      |
| **LeaseID**           | `string`      | Reference to a leasing system (e.g., etcd) for dynamic TTL.                                                                                               | `lease00000000000000000001` |

---

## **Implementation Details**
### **1. Choose a Backend**
| Backend         | Use Case                                  | Pros                          | Cons                          |
|-----------------|------------------------------------------|-------------------------------|-------------------------------|
| **etcd**        | Service discovery, config management     | Strong consistency, built-in watches | Higher latency than Redis     |
| **Consul**      | Hybrid config + service mesh             | Rich UI, ACME support         | Slower than etcd for writes   |
| **Redis**       | Low-latency key-value storage            | Fast, pub/sub for real-time   | Requires TTL management       |
| **DynamoDB**    | Serverless, auto-scaling                 | Global tables, high throughput| Higher cost at scale         |

### **2. Core Operations**
All durability backends support these CRUD operations (examples in **etcd CLI** syntax):

| Operation       | Command/Endpoint                          | Description                                                                                     |
|-----------------|------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Create/Update** | `etcdctl put /key "value"`               | Stores or updates a key-value pair (atomic).                                                    |
| **Read**        | `etcdctl get /key`                       | Retrieves the latest value for a key.                                                          |
| **Delete**      | `etcdctl del /key`                       | Removes a key (TTL=0 if present).                                                              |
| **Watch**       | `etcdctl watch /key`                     | Streams updates to the client (use `--api-version=3`).                                         |
| **Lease**       | `etcdctl lease grant 3600`               | Creates a lease for TTL management (e.g., for dynamic TTL).                                    |
| **TTL Update**  | `etcdctl put /key "value" --lease=LEASEID` | Links a key to a lease for auto-expiry.                                                        |

### **3. Conflict Resolution**
- **Last-Write-Wins**: Default in etcd/Consul (use `Version` field to detect conflicts).
  ```json
  {
    "key": "/app/config:timeout",
    "value": "{\"timeout\": 45000}",
    "version": 4  // Increment if rewriting
  }
  ```
- **Version Vectors**: Multi-DC setups (e.g., Consul) track causal order via `Version` + `LastContact`.

### **4. Idempotent Updates**
To avoid race conditions:
```go
// Pseudo-code for idempotent update in Go
func UpdateConfig(key string, value interface{}, version int) error {
  // Fetch current version
  current, err := client.Get(key)
  if err != nil || current.Version != version {
    return errors.New("stale version")
  }
  // Update with new value + incremented version
  _, err = client.Update(key, value, version+1)
  return err
}
```

---

## **Query Examples**
### **1. Basic CRUD with etcd**
```bash
# Create/update a config
etcdctl put /app/config:timeout '{"timeout": 30000}' --lease=default-lease

# Read
etcdctl get /app/config:timeout

# Watch for changes
etcdctl watch /app/config:timeout --prefix
```

### **2. Dynamic TTL with Redis**
```bash
# Set with TTL (3600s)
redis-cli SET app:session:user1 '{"token": "abc123"}' EX 3600

# Watch for expiry (requires Redis Streams or Pub/Sub)
redis-cli SUBSCRIBE __keyevent@0__:expired
```

### **3. Conflict Handling in DynamoDB**
```javascript
// AWS SDK (JavaScript) example
const params = {
  TableName: "AppConfig",
  Key: { "Key": { S: "timeout" } },
  UpdateExpression: "SET Value = :val",
  ConditionExpression: "Version = :currentVersion",
  ExpressionAttributeValues: {
    ":val": { S: '{"timeout": 45000}' },
    ":currentVersion": { N: "1" }
  }
};
await dynamodb.updateItem(params).promise();
```

---

## **Error Handling**
| Error Type               | Cause                                      | Solution                                                                 |
|--------------------------|--------------------------------------------|---------------------------------------------------------------------------|
| **Lease Revoked**        | TTL expired (etcd).                        | Auto-retry or notify dependent services.                                  |
| **Stale Version**        | Concurrent update conflict.               | Use CAS (Compare-And-Swap) or exponential backoff.                         |
| **Backend Unavailable**  | Network partition (DynamoDB/etcd).        | Implement retries with jitter (e.g., `backoff` library in Go).             |
| **Quota Exceeded**       | DynamoDB/RDS read/write limits.            | Use caching (e.g., Redis) or split keys.                                  |

---

## **Configuring Watchers**
### **etcd Watcher (Go)**
```go
client, _ := etcd.New("http://localhost:2379")
watcher := client.Watcher("/app/config", &etcd.WatcherOptions{Recursive: true})
for notify := range watcher {
  if notify.IsDelete() {
    log.Println("Key deleted:", notify.Node.Key)
  }
}
```

### **Redis Pub/Sub**
```bash
# Publisher
redis-cli PUBLISH app:config:channel '{"timeout": 45000}'

# Subscriber
redis-cli SUBSCRIBE app:config:channel
```

---

## **Related Patterns**
| Pattern                     | Purpose                                                                 | When to Use                          |
|-----------------------------|-------------------------------------------------------------------------|--------------------------------------|
| **[Saga Pattern]**          | Manage distributed transactions using durable logs (e.g., Kafka).        | Microservices with compensating actions. |
| **[Circuit Breaker]**       | Fail fast and gracefully when durability backends are unavailable.       | High-latency or unreliable stores.   |
| **[Config as Code]**        | Version-control configs (e.g., GitOps with etcd).                       | DevOps environments.                  |
| **[Event Sourcing]**        | Append-only log for auditability (e.g., Kafka + DynamoDB).               | Financial systems requiring compliance.|
| **[Service Mesh (Istio)**] | Integrate durability with mTLS and retries.                            | Multi-service architectures.         |

---
**Note:** For serverless architectures, pair durability integration with **AWS Parameter Store** or **Azure Key Vault** for secrets management.

---
**Appendix: Tools**
- **[etcd-tools](https://github.com/etcd-io/etcd)**: CLI and Go SDK.
- **[Redis Stack](https://redis.io/stack/)**: Adds search and time-series to Redis.
- **[DynamoDB Accelerator (DAX)**: In-memory cache for DynamoDB.