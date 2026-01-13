**[Pattern] Distributed Configuration Reference Guide**

---

### **Title**
**[Pattern] Distributed Configuration**

---

### **1. Overview**
The **Distributed Configuration** pattern provides a centralized, scalable mechanism for managing runtime configuration across loosely coupled services in distributed systems. Unlike monolithic applications, distributed systems require configurations to be dynamically updated, versioned, and accessible without redeploying services. This pattern ensures low-latency access, fine-grained control, and resilience to service failures by decoupling configuration management from application logic. It leverages a **configuration server** (e.g., Apache ZooKeeper, etcd, or Consul) to store, sync, and retrieve configurations in real-time, while clients (services) poll or subscribe to changes. Key use cases include microservices orchestration, dynamic feature flags, and environment-specific settings (e.g., Dev/Staging/Prod).

---

### **2. Key Concepts**
| **Concept**               | **Definition**                                                                 | **Example**                                  |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Configuration Server** | Central repository for storing key-value pairs (KVs) or structured configs.   | etcd, Consul, ZooKeeper.                    |
| **Client (Service)**      | Any service that reads/writes configurations dynamically.                   | API Gateway, Microservice A.               |
| **Namespace**             | Logical grouping of configurations (e.g., `/app/logging` for all logging rules). | `/prod`, `/feature/X`.                     |
| **Lease Time**            | TTL (Time-to-Live) for a configuration entry to auto-expire if not refreshed. | 5-minute lease for cache invalidation.      |
| **Change Notification**   | Mechanism (e.g., event bus, watch callbacks) to alert clients of updates.    | Pub/Sub via Kafka or WebSocket subscriptions.|
| **Versioning**            | Tracking config changes to enable rollback or audit.                         | `config-v2` vs. `config-v1`.                |
| **Encryption**            | Securing sensitive data (e.g., API keys) at rest or in transit.              | AES-256 or TLS for endpoints.               |

---

### **3. Schema Reference**
Distributed configurations typically follow a **hierarchical key-value store** or **document-based** schema. Below are common patterns:

#### **Table 1: Key-Value Store Schema**
| **Field**       | **Type**       | **Description**                                                                 | **Example**                          |
|-----------------|----------------|-------------------------------------------------------------------------------|--------------------------------------|
| `namespace`     | String         | Logical grouping (e.g., `/app`, `/db`).                                     | `/app/settings`                      |
| `key`           | String         | Unique identifier for a configuration.                                       | `max_retries`                        |
| `value`         | String/JSON    | The configuration data (supports structured JSON for nested configs).       | `{"enabled": true, "threshold": 3}`  |
| `metadata`      | Object         | Additional attributes (e.g., `version`, `lease`, `last_updated`).             | `{ "version": "1.2", "lease": 300s }`|
| `owner`         | String         | Service or team responsible for the config.                                  | `team-auth`                          |

**Example JSON Payload:**
```json
{
  "namespace": "/app/logging",
  "key": "level",
  "value": "DEBUG",
  "metadata": {
    "version": "1.0",
    "lease": "PT5M",
    "last_updated": "2023-10-01T12:00:00Z"
  }
}
```

---

#### **Table 2: Document-Based Schema (Alternative)**
| **Field**       | **Type**       | **Description**                                                                 | **Example**                          |
|-----------------|----------------|-------------------------------------------------------------------------------|--------------------------------------|
| `id`            | String         | Unique identifier for the config document.                                    | `logging-config`                     |
| `type`          | String         | Config type (e.g., `service`, `feature`, `database`).                         | `service`                            |
| `environment`   | String         | Target environment (e.g., `prod`, `staging`).                                 | `prod`                               |
| `data`          | JSON           | Nested configuration object.                                                 | `{ "log_level": "DEBUG", "size_limit": 1024 }` |
| `schema_version`| String         | Version of the config schema (for backward compatibility).                   | `v2`                                 |

**Example JSON Payload:**
```json
{
  "id": "feature-x/flags",
  "type": "feature",
  "environment": "staging",
  "data": {
    "enable_dark_mode": true,
    "beta_users": ["user1", "user2"]
  },
  "schema_version": "v1.1"
}
```

---

### **4. Implementation Details**
#### **4.1 Architecture Components**
```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│   ┌─────────────┐    ┌─────────────┐    ┌───────────────────────────────────┐  │
│   │             │    │             │    │                                   │  │
│   │  Service A  │───▶│ Config     │───▶│   Distributed Configuration      │  │
│   │             │    │  Client    │    │   Server (e.g., etcd/Consul)      │  │
│   │ (Polling/   │    │ (SDK)      │    │                                   │  │
│   │  Watch)     │    │             │    └───────────┬───────────────────────┘  │
│   └─────────────┘    └─────────────┘                 │                       │  │
│                                             ┌─────────┴───────────┐       │  │
│                                             │                     │       │  │
│                                             │   Change           │       │  │
│                                             │   Notification      │       │  │
│                                             │   (Pub/Sub/Events) │       │  │
│                                             └───────────────────┘       │  │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### **4.2 Data Flow Workflow**
1. **Write Operation**:
   - A **service** or **admin tool** (e.g., CLI) updates a config via the **configuration server**.
   - The server validates the request (e.g., ACLs, lease time) and persists the change.
   - *Example*: `PUT /v1/kv/app/logging/level?value=DEBUG`.

2. **Read Operation**:
   - A **client service** queries the server for a config (either by polling or subscribing to watches).
   - The server returns the latest value + metadata (e.g., version, lease).
   - *Example*: `GET /v1/kv/app/logging/level`.

3. **Change Notification**:
   - Clients **watch** a namespace/key for updates (e.g., via etcd’s `/watch` API).
   - The server pushes an event (e.g., `{ "op": "UPDATE", "key": "/app/logging" }`) to subscribed clients.

#### **4.3 Client Libraries**
| **Server**       | **Client SDK Language**                     | **Key Features**                                  |
|------------------|--------------------------------------------|----------------------------------------------------|
| etcd             | Go, Python, Java, .NET                     | CRUD, watch, lease management                    |
| Consul           | Go, Python, Java, CLI                     | Health checks, KV store, service discovery        |
| ZooKeeper        | Java (curator), Python (kazoo), C#         | Strong consistency, leader election               |
| Custom (e.g., DB)| Any (REST/gRPC)                            | Requires custom watch mechanisms (e.g., DB triggers)|

---
### **5. Query Examples**
#### **5.1 CRUD Operations (etcd/Consul)**
| **Operation**       | **HTTP/gRPC Command**                          | **Example Request**                              | **Response**                              |
|---------------------|-----------------------------------------------|-------------------------------------------------|-------------------------------------------|
| **Create/Update**   | `PUT /v1/kv/{namespace}/{key}`                | `PUT /v1/kv/app/logging/level?value=INFO`       | `200 OK`                                  |
| **Read**            | `GET /v1/kv/{namespace}/{key}`                | `GET /v1/kv/app/logging/level`                  | `{"key": "app/logging/level", "value": "INFO"}` |
| **Delete**          | `DELETE /v1/kv/{namespace}/{key}`              | `DELETE /v1/kv/app/logging/level`               | `200 OK`                                  |
| **List Keys**       | `GET /v1/kv/{namespace}/?recursive=true`     | `GET /v1/kv/app/?recursive=true`                | `[{"key": "app/logging/level", ...}]`     |
| **Watch Changes**   | `POST /v1/watch/{namespace}/{key}`            | `POST /v1/watch/app/logging/level`              | Streaming updates (e.g., `{ "action": "UPDATE", "new_value": "DEBUG" }`) |

#### **5.2 Example: Dynamic Feature Toggle (Go Client with Consul)**
```go
package main

import (
	"github.com/hashicorp/consul/api"
)

func main() {
	// Initialize Consul client
	c, _ := api.NewClient(api.DefaultConfig())
	kv := c.KV()

	// Read feature flag
	pairs, _, err := kv.Get("feature-x/enabled", &api.QueryOptions{})
	if err != nil {
		panic(err)
	}
	if pairs != nil && string(pairs.Value()) == "true" {
		// Enable feature
	}
}
```

#### **5.3 Example: Lease-Based Config (etcd)**
```python
import etcd3

client = etcd3.client(host='localhost', port=2379)

# Write with lease (auto-expires after 30s)
client.put('/app/timeout', '30s', lease=30)
client.lease_grant(30)  # Explicitly grant a lease
```

---

### **6. Best Practices**
1. **Namespace Design**:
   - Use **hierarchical paths** (e.g., `/serviceX/env/prod`) to avoid collisions.
   - Avoid deep nesting; use **flattened keys** (e.g., `appX.max_retries` vs. `appX/config/max_retries`).

2. **Versioning**:
   - Append version suffixes (e.g., `config-v1.json`) or use `metadata.version`.
   - Implement **canary rollouts** by updating configs incrementally.

3. **Security**:
   - **Encrypt sensitive data** (e.g., API keys) at rest (e.g., etcd’s encryption-at-rest).
   - Use **RBAC** (Role-Based Access Control) to restrict write access.
   - Rotate **lease tokens** periodically for secrets.

4. **Resilience**:
   - **Retry transient failures** (e.g., config server downtime) with exponential backoff.
   - **Cache locally** with short TTLs (e.g., 1 minute) to reduce server load.
   - **Fallback mechanisms**: Use default configs if the server is unreachable.

5. **Monitoring**:
   - Track **config latency** (client read/write times).
   - Alert on **high change frequency** (potential misconfigurations).
   - Log **config access** (audit trail).

---

### **7. Related Patterns**
| **Pattern**                  | **Description**                                                                 | **When to Use**                                  |
|------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **Config Map**               | Inline configuration in container orchestration (e.g., Kubernetes ConfigMaps). | Tightly coupled with orchestration (e.g., K8s).  |
| **Feature Toggle**           | Runtime feature flags managed via config.                                    | Gradual rollouts of new features.               |
| **Circuit Breaker**          | Limits config server load by failing fast on outages.                       | High-traffic systems.                           |
| **Saga Pattern**             | Distributed transactions requiring updated configs.                         | Microservices with ACID-like guarantees.         |
| **Service Mesh (e.g., Istio)**| Integrates with config servers for dynamic service policies.               | Cloud-native environments.                      |
| **Observability Pipeline**   | Logs/metrics for config changes (e.g., Prometheus + Grafana).                | Debugging misconfigurations.                    |

---

### **8. Anti-Patterns**
| **Anti-Pattern**                     | **Risks**                                                                   | **Mitigation**                                  |
|--------------------------------------|-----------------------------------------------------------------------------|------------------------------------------------|
| **Hardcoding Configs**               | Tight coupling; impossible to update without redeploy.                     | Use externalized configs from the start.       |
| **No Lease Management**              | Stale configs linger after a service restart.                              | Set short leases or TTLs.                      |
| **No Change Notifications**         | Clients miss updates and use outdated configs.                             | Enable watches/subscriptions.                  |
| **Overly Complex Namespaces**        | Hard to locate configs; risk of collisions.                              | Follow consistent naming conventions.          |
| **Ignoring Metadata**                | No audit trail or version control.                                         | Include `version`, `last_updated`, and `owner`. |

---
### **9. Tools & Libraries**
| **Tool/Library**       | **Purpose**                                  | **Links**                                      |
|------------------------|---------------------------------------------|------------------------------------------------|
| etcd                   | Distributed KV store with lease support.    | [etcd.io](https://etcd.io)                     |
| Consul                 | KV store + service discovery + health checks. | [Consul.io](https://www.consul.io)            |
| ZooKeeper              | Strong consistency for config/session state.| [ZooKeeper](https://zookeeper.apache.org)      |
| Spring Cloud Config    | Java-based config server for Spring apps.   | [Spring.io](https://spring.io/projects/spring-cloud-config) |
| Kubernetes ConfigMaps  | Configs for containers (integrates with dist. systems). | [K8s Docs](https://kubernetes.io/docs/tasks/configuration/configure-pod-container/) |
| HashiCorp Vault        | Secret management + dynamic config.       | [Vault](https://www.vaultproject.io)           |

---
### **10. Further Reading**
- [Etcd Documentation](https://etcd.io/docs/)
- [Consul KV Store Guide](https://developer.hashicorp.com/consul/tutorials/configuration/centralized-configuration)
- [Distributed Systems Patterns (Book)](https://www.oreilly.com/library/view/distributed-systems-patterns/9781491950358/)
- [Kubernetes ConfigMaps vs. Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)