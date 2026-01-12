**[Pattern] Containers Integration – Reference Guide**

---

### **Overview**
The **Containers Integration** pattern enables seamless interaction between containerized applications (e.g., Docker, Kubernetes) and infrastructure resources, APIs, or services (e.g., databases, cloud providers, legacy systems). This pattern standardizes how containers request and consume external dependencies, ensuring portability, scalability, and isolation. It leverages **service discovery**, **adapter patterns**, and **orchestration-aware configurations** to abstract complexities like network policies, secret management, and dependency lifecycle management.

Key use cases:
- Deploying microservices alongside third-party APIs.
- Managing containerized workloads with pre-configured dependencies (e.g., databases, message brokers).
- Integrating legacy systems via REST/gRPC adapters.
- Resource provisioning (e.g., auto-scaling databases when container traffic spikes).

This guide covers **core components**, **implementation schemas**, **practical queries**, and **related patterns** to help architects and developers design robust container integrations.

---

## **1. Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Example**                                  |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| **Service Mesh**          | A dedicated infrastructure layer for managing service-to-service communication (e.g., Istio, Linkerd). Handles retries, circuit breaking, and observability.                   | Kubernetes sidecar proxies routing requests. |
| **Dependency Injection**  | Dynamically injecting configurations (e.g., DB configs, API keys) into containers at runtime rather than hardcoding them.                                                                           | Kubernetes `ConfigMap`/`Secret` volumes.     |
| **Adapter Pattern**       | Translating containerized apps’ interfaces into compatible formats with external systems (e.g., REST ↔ gRPC).                                                                                       | API Gateway converting HTTP to Kafka.        |
| **Orchestration Awareness**| Containers adapting their behavior based on the orchestrator (e.g., Kubernetes pod metadata, Docker Compose services).                                                                               | Pod labels triggering auto-scaling.         |
| **Stateful vs. Stateless**| Stateful containers (e.g., databases) require persistent storage and session management; stateless containers rely on external state (e.g., Redis).                                                          | PostgreSQL in a StatefulSet vs. Nginx.       |
| **Security Context**      | Restricting container capabilities (e.g., read-only filesystem, non-root user) to mitigate risks.                                                                                                         | `securityContext.runAsNonRoot: true`.        |

---

## **2. Schema Reference**
Below are common schemas for container integrations, categorized by layer.

### **A. Dependency Management Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                          |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `dependency_name`       | String        | Unique identifier for the external service (e.g., `database`, `message_broker`).                                                                                                                                       | `postgres-db`                               |
| `type`                  | Enum          | Type of dependency (`database`, `api`, `storage`, `queue`, `cache`).                                                                                                                                               | `database`                                  |
| `version`               | String        | Version/Release tag for the dependency (e.g., Docker image tag).                                                                                                                                                 | `v12.3.0`                                  |
| `orchestrator_config`  | Object        | Orchestrator-specific settings (e.g., Kubernetes `Service`, Docker `network`).                                                                                                                               | `{ "serviceType": "ClusterIP" }`            |
| `connection_details`    | Object        | Credentials/endpoints (encrypted via Secrets).                                                                                                                                                               | `{ "host": "db.example.com", "port": 5432 }`|
| `health_check`          | Object        | Liveness/readiness probes.                                                                                                                                                                                         | `{ "path": "/health", "interval": "30s" }`  |
| `auto_scaling`          | Boolean       | Enable scaling based on container metrics (e.g., CPU/memory).                                                                                                                                                     | `true`                                      |
| `sidecar_required`      | Boolean       | Indicates if a sidecar (e.g., proxy, logger) is needed.                                                                                                                                                           | `false`                                     |

**Example JSON:**
```json
{
  "dependencies": [
    {
      "dependency_name": "primary-db",
      "type": "database",
      "version": "postgres:14.1",
      "orchestrator_config": {
        "serviceType": "ClusterIP",
        "ports": [5432]
      },
      "connection_details": {
        "host": "${DB_HOST}",
        "port": 5432,
        "username": "${DB_USER}",
        "password": "${DB_PASSWORD}"
      },
      "health_check": {
        "readinessProbe": { "httpGet": { "path": "/ready" } },
        "livenessProbe": { "tcpSocket": { "port": 5432 } }
      },
      "auto_scaling": true
    }
  ]
}
```

---

### **B. Adapter Configuration Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                          |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `adapter_name`          | String        | Name of the adapter (e.g., `rest-to-graphql`, `kafka-producer`).                                                                                                                                                   | `api-gateway`                              |
| `input_format`          | Enum          | Format consumed by the adapter (`json`, `protobuf`, `avro`).                                                                                                                                                     | `json`                                      |
| `output_format`         | Enum          | Format produced by the adapter (`json`, `graphql`, `kafka`).                                                                                                                                                     | `graphql`                                  |
| `mapping_rules`         | Array[Object] | Rules to transform input/output (e.g., field renaming, type conversion).                                                                                                                                           | `[ { "source": "user.id", "target": "userID" }]`|
| `authentication`        | Object        | Credentials or OAuth2 config.                                                                                                                                                                                     | `{ "token": "${API_KEY}" }`                 |
| `retries`               | Integer       | Max retries for failed requests.                                                                                                                                                                                 | `3`                                         |
| `timeout_ms`            | Integer       | Request timeout in milliseconds.                                                                                                                                                                             | `5000`                                      |

**Example JSON:**
```json
{
  "adapters": [
    {
      "adapter_name": "order-service-adapter",
      "input_format": "json",
      "output_format": "graphql",
      "mapping_rules": [
        { "source": "user.email", "target": "clientEmail" }
      ],
      "authentication": {
        "type": "bearer",
        "token": "${ORDER_API_KEY}"
      },
      "retries": 3,
      "timeout_ms": 3000
    }
  ]
}
```

---

### **C. Security Context Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                          |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `capabilities`          | Array[String] | Linux capabilities to grant/deny (e.g., `NET_ADMIN`, `SYS_ADMIN`).                                                                                                                                                        | `["NET_BIND_SERVICE"]`                     |
| `read_only_rootfs`      | Boolean       | Mount root filesystem as read-only.                                                                                                                                                                               | `true`                                      |
| `run_as_non_root`       | Boolean       | Force container to run as non-root user.                                                                                                                                                                           | `true`                                      |
| `secrets`               | Array[String] | List of Kubernetes Secrets mounted as files.                                                                                                                                                                   | `[ "db-credentials", "ssl-cert" ]`         |
| `network_policies`      | Object        | Network restrictions (e.g., egress/ingress rules).                                                                                                                                                               | `{ "allowPorts": [80, 443] }`              |

**Example YAML (Kubernetes):**
```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
    add: ["NET_BIND_SERVICE"]
  volumes:
    - name: db-secrets
      secret:
        secretName: db-credentials
```

---

## **3. Query Examples**
### **A. Dependency Discovery Queries**
**Scenario:** List all dependencies for a containerized app.

**Kubernetes (CLI):**
```bash
kubectl get pods -o jsonpath='{.spec.containers[*].env[*].valueFrom.secretKeyRef.name}'
# Output: ["db-credentials", "api-key"]
```

**Terraform (Infrastructure-as-Code):**
```hcl
resource "kubernetes_service" "db_service" {
  metadata {
    name = "postgres-db"
  }
  spec {
    selector = {
      app = "postgres"
    }
    port {
      name        = "postgres"
      port        = 5432
      target_port = 5432
    }
  }
}
```

**Python (Service Discovery):**
```python
import requests

def discover_dependency(dependency_name):
    url = f"http://service-discovery:8080/v1/dependencies/{dependency_name}"
    response = requests.get(url, headers={"Authorization": "Bearer ${TOKEN}"})
    return response.json()
```

---

### **B. Adapter Execution Queries**
**Scenario:** Transform JSON input to GraphQL output via adapter.

**cURL (REST Adapter):**
```bash
curl -X POST http://adapter-service/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ user(id: $userId) { email } }",
    "variables": { "userId": "123" }
  }'
```

**Kafka Producer (Event Adapter):**
```python
from confluent_kafka import Producer

config = {'bootstrap.servers': 'kafka:9092'}
producer = Producer(config)

def produce_event(topic, key, value):
    producer.produce(topic, key=key, value=value)
    producer.flush()
```

---

### **C. Security Context Validation**
**Scenario:** Validate container security constraints.

**Trivy (Vulnerability Scanner CLI):**
```bash
trivy image --severity CRITICAL,HIGH docker.io/library/alpine:latest
```

**Kubernetes Audit Log Analysis:**
```bash
kubectl audit-log | grep -i "securityContext"
# Check for misconfigured capabilities (e.g., `SYS_ADMIN`).
```

---

## **4. Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                 | **When to Use**                                  |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **[Service Mesh](https://cloud.google.com/blog/products/devops-sre/service-mesh-basics)** | Manages inter-service communication with observability, security, and traffic control.                                                                                                                      | High-latency apps needing retries/circuit breaking. |
| **[Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)** | Prevents cascading failures by limiting calls to failing services.                                                                                                                                              | Fault-tolerant microservices.                    |
| **[Event-Driven Architecture](https://www.eventstore.com/blog/event-driven-architecture)** | Decouples components using events (e.g., Kafka, RabbitMQ).                                                                                                                                                     | Async workflows (e.g., order processing).         |
| **[Canary Releases](https://www.awsarchitectureblog.com/2019/02/canary-deployments.html)** | Gradually roll out updates to a subset of users.                                                                                                                                                              | Reducing risk in production.                      |
| **[Secret Management](https://www.vaultproject.io/)** | Securely stores and rotates credentials.                                                                                                                                                                         | Production deployments with sensitive data.       |
| **[Multi-Cluster Federation](https://kubernetes.io/blog/2020/09/30/kubernetes-multi-cluster/)** | Distributes containers across clusters for resilience.                                                                                                                                                         | Global apps with low-latency requirements.        |

---

## **5. Implementation Checklist**
1. **Define Dependencies:**
   - Document all external services (type, version, connection details).
   - Use `ConfigMap`/`Secret` for environment variables.

2. **Choose an Orchestrator:**
   - Kubernetes for scaling; Docker Compose for local dev.
   - Enable health checks and auto-restart policies.

3. **Implement Adapters:**
   - Use existing libraries (e.g., `Apache Kafka Connect`, `Envoy Proxy`).
   - Test transformations with sample payloads.

4. **Enforce Security:**
   - Run containers as non-root.
   - Scan images for vulnerabilities (Trivy, Clair).
   - Rotate secrets automatically (Vault, AWS Secrets Manager).

5. **Monitor Integrations:**
   - Set up Prometheus/Grafana dashboards for dependency metrics.
   - Alert on connection failures or slow responses.

6. **Test Failover:**
   - Simulate dependency outages (e.g., kill a Postgres pod).
   - Verify retries and circuit breakers work.

7. **Document Onboarding:**
   - Create a `README` with:
     - Dependency schemas.
     - Adapter input/output examples.
     - Troubleshooting steps.

---
**References:**
- [Kubernetes Dependency Management](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#dependencies)
- [CNCF Service Mesh Interface](https://www.cncf.io/projects/service-mesh-interface/)
- [Twelve-Factor App](https://12factor.net/) (Config, Backing Services)