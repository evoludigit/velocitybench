---
# **[Pattern] On-Premise Configuration Reference Guide**

---

## **1. Overview**
The **On-Premise Configuration** pattern ensures applications, services, or systems are deployed, managed, and secured within an organization’s private infrastructure. Unlike cloud-based configurations, this pattern emphasizes **local control, data sovereignty, and reduced dependency on external providers**, while maintaining flexibility for hybrid or fully on-premise environments.

This guide covers:
- **Key concepts** (architectural components, security, and compliance).
- **Implementation steps** (setup, deployment, and maintenance).
- **Configuration schema** (YAML/JSON/INI formats, where applicable).
- **Query and validation examples** for common use cases.
- **Related patterns** for integration with other architectural approaches.

---

## **2. Key Concepts**

### **Core Components**
| Component               | Description                                                                                                                                                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **On-Premise Server**   | Physical or virtual machine hosting the configuration service. Supports high availability via clustering or failover systems.                                                                         |
| **Configuration Store** | Secure database (e.g., Redis, PostgreSQL, HashiCorp Vault) or file-based store (e.g., JSON/YAML) for storing dynamic configurations.                                                                      |
| **API Gateway/Proxy**   | Optional intermediary layer for secure access to configuration endpoints (e.g., Kong, Nginx with TLS).                                                                                                       |
| **Sync Mechanism**      | Periodic or event-driven sync (e.g., Polling, Webhooks, or change data capture [CDC]) to update configs across services.                                                                                    |
| **Validation Layer**    | Schema checks (e.g., JSON Schema, OpenAPI) or custom validators to enforce consistency and security constraints.                                                                                             |
| **Audit Logging**       | Immutable logs of config changes (e.g., ELK Stack, Splunk) for compliance and debugging.                                                                                                                   |
| **Secrets Management**  | Integration with tools like **Vault**, **AWS Secrets Manager**, or **Azure Key Vault** for encrypted credentials.                                                                                               |
| **Disaster Recovery**   | Backup/replication strategies (e.g., snapshots, cross-region mirrors) to ensure config availability during outages.                                                                                            |

---

### **Security & Compliance Considerations**
- **Data Encryption**:
  - At rest: AES-256 for databases/files.
  - In transit: TLS 1.2+ for API communication.
- **Access Control**:
  - Role-Based Access Control (RBAC) or Attribute-Based Access Control (ABAC) for granular permissions.
  - Multi-Factor Authentication (MFA) for admin interfaces.
- **Compliance**:
  - Align with **GDPR**, **HIPAA**, or **SOC 2** requirements (e.g., data localization, audit trails).
  - Regular penetration testing and vulnerability scans.

---

### **Hybrid Scenarios**
- **Read Replicas**: Sync configs to cloud read replicas for scalability while keeping writes on-premise.
- **Edge Configs**: Deploy lightweight config stores at edge locations (e.g., CDNs, IoT gateways) with periodic syncs from the primary store.

---

## **3. Schema Reference**
Below are example schemas for common configuration formats. Replace placeholders (`{{}}`) with actual values.

---

### **3.1 JSON Schema (Dynamic Configs)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "On-Premise Service Config",
  "type": "object",
  "properties": {
    "app": {
      "type": "object",
      "properties": {
        "name": { "type": "string", "example": "order-service" },
        "version": { "type": "string", "format": "semver" },
        "env": { "type": "string", "enum": ["dev", "staging", "prod"] }
      },
      "required": ["name", "env"]
    },
    "database": {
      "type": "object",
      "properties": {
        "host": { "type": "string", "format": "hostname" },
        "port": { "type": "integer", "minimum": 1, "maximum": 65535 },
        "username": { "type": "string", "format": "secret" },
        "password": { "type": "string", "format": "secret" },
        "ssl": { "type": "boolean", "default": false }
      },
      "required": ["host", "port", "username", "password"]
    },
    "logging": {
      "type": "object",
      "properties": {
        "level": { "type": "string", "enum": ["DEBUG", "INFO", "WARN", "ERROR"] },
        "destination": {
          "type": "string",
          "enum": ["console", "file", "syslog", "aws-cloudwatch"]
        }
      },
      "default": { "level": "INFO", "destination": "console" }
    }
  },
  "required": ["app", "database"]
}
```
**Validation Tool**: Use [JSON Schema Validator](https://www.jsonschemavalidator.net/) or programmatic libraries (e.g., `jsonschema` for Python).

---

### **3.2 YAML Example (Static Configs)**
```yaml
# config.yml
app:
  name: "inventory-service"
  version: "1.2.0"
  env: "prod"

database:
  host: "db.internal.corp.example"
  port: 5432
  username: "{{DB_USER}}"  # Reference to secrets vault
  password: "{{DB_PASS}}"
  ssl: true

logging:
  level: WARN
  destination: aws-cloudwatch

# Environment-specific overrides (e.g., config-dev.yml)
# env: "dev"
# database:
#   host: "dev-db.internal.corp.example"
```

**Tools**: Validate with [`yamllint`](https://yamllint.readthedocs.io/) or inline checks in deployment pipelines.

---

### **3.3 INI Example (Legacy Systems)**
```ini
[app]
name = metrics-collector
version = 1.0.1
env = staging

[database]
host = db.internal.corp
port = 3306
username = sa
password = "SecurePass123!"  # Avoid plaintext; use secrets manager

[logging]
level = INFO
destination = /var/log/app.log
```

**Use Case**: Legacy applications or embedded systems with INI support.

---

## **4. Implementation Steps**

### **4.1 Prerequisites**
- **Infrastructure**:
  - VMs or containerized environments (e.g., Docker/Kubernetes).
  - Network isolation for config stores (VLANs, firewalls).
- **Tools**:
  - Configuration server (e.g., [Consul](https://www.consul.io/), [etcd](https://etcd.io/)).
  - Secrets management (e.g., [Vault](https://www.vaultproject.io/)).
  - CI/CD pipeline (e.g., GitLab CI, Jenkins) for automated deployments.

---

### **4.2 Setup**
1. **Choose a Config Store**:
   - For **real-time sync**: Use **etcd** or **Redis**.
   - For **versioned configs**: Use **PostgreSQL** with CDC.
   - For **immutable configs**: Use **S3-compatible storage** (e.g., MinIO) with versioning.

2. **Deploy the Config Server**:
   ```bash
   # Example: Deploy etcd in Kubernetes
   kubectl apply -f etcd-deployment.yaml
   ```
   **Sample `etcd-deployment.yaml`**:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: etcd
   spec:
     replicas: 3
     template:
       spec:
         containers:
           - name: etcd
             image: bitnami/etcd:3.5
             ports:
               - containerPort: 2379
             volumeMounts:
               - name: etcd-data
                 mountPath: /bitnami/etcd
     volumes:
       - name: etcd-data
         persistentVolumeClaim:
           claimName: etcd-pvc
   ```

3. **Integrate Secrets Management**:
   - Store credentials in **Vault** and reference them in configs:
     ```json
     {
       "database": {
         "password": "$vault:secret/data/db/root?key=password"
       }
     }
     ```

4. **Implement Sync Mechanism**:
   - **Polling**: Services query the config store on startup and at intervals (e.g., every 5 minutes).
   - **Webhooks**: Config store notifies services of changes via HTTP callbacks.
   - **Change Data Capture (CDC)**: Use **Debezium** or **etcd’s watch API** for event-driven updates.

5. **Enable Validation**:
   - Add middleware to reject invalid configs (e.g., FastAPI’s `Pydantic` or Express’s ` Joi`).
   - Example (Python/Flask):
     ```python
     from jsonschema import validate

     def validate_config(config_data):
         with open("schema.json") as f:
             schema = json.load(f)
         validate(instance=config_data, schema=schema)
     ```

6. **Configure Auditing**:
   - Enable **etcd’s audit logging** or **PostgreSQL’s log_statement**:
     ```ini
     # etcd config (etcd.conf)
     [log]
       level = info
       output_paths = ["/var/log/etcd/audit.log"]
     ```

---

### **4.3 Deployment**
1. **Infrastructure as Code (IaC)**:
   - Use **Terraform** or **Ansible** to provision servers/stores.
   - Example Terraform snippet:
     ```hcl
     resource "aws_instance" "config_server" {
       ami           = "ami-0c55b159cbfafe1f0"
       instance_type = "t3.medium"
       subnet_id     = aws_subnet.private.id
       security_groups = [aws_security_group.config_server.id]
     }
     ```

2. **CI/CD Pipeline**:
   - **Trigger**: On `git push` to `main` branch.
   - **Steps**:
     1. Lint configs (`yamllint`, `schemaviewer`).
     2. Deploy config store (e.g., `kubectl apply -f etcd`).
     3. Sync updates to target environments.
     4. Rollback on failure.

   **Sample GitLab CI**:
   ```yaml
   stages:
     - validate
     - deploy
   validate_config:
     stage: validate
     script:
       - docker run --rm -v $(pwd):/config jsonschemavalidator/schema-validator
   deploy_config:
     stage: deploy
     script:
       - kubectl apply -f k8s/config-store/
       - kubectl rollout status deployment/config-server
   ```

---

### **4.4 Maintenance**
- **Monitoring**:
  - Use **Prometheus + Grafana** to track:
    - Config sync latency.
    - Store health (e.g., etcd membership).
    - API request errors.
- **Backup**:
  - **etcd**: `ETCDCTL_API=3 etcdctl snapshot save snapshot.db`.
  - **PostgreSQL**: `pg_dump`.
- **Disaster Recovery**:
  - Test failover procedures (e.g., promote a replica in etcd).
  - Document restore procedures for config stores.

---

## **5. Query Examples**
Below are common query patterns for interacting with the config store.

---

### **5.1 Fetching Configs**
#### **etcd (HTTP API)**
```bash
# Get a single key
curl --cert ca.crt --key client.key --cacert ca.crt \
     https://localhost:2379/v2/keys/config/app -u user:pass

# Get a directory (recursive)
curl --cert ca.crt --key client.key --cacert ca.crt \
     https://localhost:2379/v2/keys/config --recursive -u user:pass
```

#### **PostgreSQL**
```sql
-- Fetch app configs
SELECT * FROM configs WHERE env = 'prod' AND path = 'app';

-- Fetch with latest version
SELECT value FROM configs
WHERE path = 'database/ssl' AND version = (
  SELECT MAX(version) FROM configs WHERE path = 'database/ssl'
);
```

#### **Redis (Hashes)**
```bash
# Get all app configs
redis-cli HGETALL app:config

# Get specific field
redis-cli HGET app:config env
```

---

### **5.2 Updating Configs**
#### **etcd (PUT)**
```bash
# Update a key (atomic replace)
curl --cert ca.crt --key client.key --cacert ca.crt \
     -XPUT https://localhost:2379/v2/keys/config/app/env -d value=prod \
     -u user:pass
```

#### **PostgreSQL**
```sql
-- Upsert a config (using `ON CONFLICT`)
INSERT INTO configs (path, value, version)
VALUES ('app/version', '1.2.0', 3)
ON CONFLICT (path) DO UPDATE SET
  value = EXCLUDED.value, version = EXCLUDED.version + 1;
```

#### **Vault (Dynamic Secrets Rotation)**
```bash
# Write a new password
vault kv put db/creds/password password="NewPass123!" metadata=rotation:1

# Read the new password (ephemeral)
vault kv get -field=password db/creds/password
```

---

### **5.3 Watching for Changes**
#### **etcd (Watch API)**
```bash
# Stream changes to a directory
ETCDCTL_API=3 etcdctl watch --prefix --keys-only /config/
```

#### **PostgreSQL (Logical Decoding)**
```sql
-- Enable CDC (PostgreSQL 10+)
CREATE PUBLICATION config_changes FOR TABLE configs;

-- Consumer (e.g., Kafka connector)
SELECT * FROM pg_logical_slot_get_changes('config_changes', NULL, NULL);
```

#### **Redis (Pub/Sub)**
```bash
# Subscribe to config updates
redis-cli SUBSCRIBE config_updates

# In another terminal, publish an update
redis-cli PUBLISH config_updates "Config changed: app/version=1.2.0"
```

---

### **5.4 Validating Configs**
#### **Programmatic Validation (Python)**
```python
import jsonschema
from jsonschema import validate

schema = {
  "type": "object",
  "properties": {
    "app": { ... }  # From Section 3.1
  }
}

config_data = {"app": {"name": "order-service", "env": "prod"}}
validate(instance=config_data, schema=schema)
```

#### **Shell Script (YAML)**
```bash
#!/bin/bash
# Validate YAML against schema using jsonschema
yaml2json < config.yml | jq -S . > config.json
jsonschema -i schema.json config.json
```

---

## **6. Related Patterns**
| Pattern                      | Description                                                                                                                                                                                                 | When to Use                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Feature Flags**            | Dynamically enable/disable features without redeploying.                                                                                                                                                      | A/B testing, gradual rollouts, or canary deployments.                                              |
| **Secret Management**        | Secure storage and rotation of credentials/API keys.                                                                                                                                                         | Applications requiring sensitive data (e.g., databases, OAuth tokens).                            |
| **Canary Deployment**        | Gradually roll out changes to a subset of users.                                                                                                                                                          | Reducing risk in production releases.                                                             |
| **Config-as-Code**           | Manage configs in version control (e.g., Git) with templating (e.g., Helm, Ansible).                                                                                                                 | Infrastructure-as-code workflows.                                                                |
| **Multi-Region Config Sync** | Sync configs across geographically distributed regions.                                                                                                                                                     | Global applications with low-latency requirements.                                               |
| **Immutable Configs**        | Treat configs as immutable; versioned via Git or distributed storage.                                                                                                                                  | Highly available systems requiring auditability (e.g., Kubernetes manifests).                    |
| **Service Mesh (e.g., Istio)** | Manage configs via sidecar proxies for dynamic routing/retries.                                                                                                                                              | Microservices with complex traffic patterns.                                                     |
| **Zero Trust Architecture**  | Enforce least-privilege access to configs and services.                                                                                                                                                     | High-security environments (e.g., finance, healthcare).                                           |

---

## **7. Troubleshooting**
| Issue                          | Diagnosis                                                                                     | Solution                                                                                          |
|--------------------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Config not syncing**         | Check sync interval, network connectivity, or store health.                                     | Verify logs (`etcdctl endpoint health`), adjust polling frequency, or use Webhooks.              |
| **Validation failures**        | Validate schema matches the store’s format.                                                   | Update schema or configs; test with `jsonschema` locally.                                       |
| **Performance bottlenecks**    | High latency in config fetches or syncs.                                                      | Optimize store queries (e.g., Redis hashes), use caching (e.g., Redis).                            |
| **Secrets leakage**            | Secrets exposed in logs or config dumps.                                                       | Rotate secrets, enable Vault’s dynamic secrets, or use ephemeral keys.                            |
| **Store corruption**           | etcd split-brain or PostgreSQL crash.                                                          | Use etcd’s raft consensus or PostgreSQL replication; restore from backups.                        |
| **Audit trail gaps**           | Missing entries in log files.                                                                 | Increase log retention, enable CDC for real-time replication.                                      |

---

## **8. Best Practices**
1. **Idempotency**:
   - Ensure config updates are idempotent (e.g., `PUT` with version checks).
2. **Minimal Scope**:
   - Scope configs to the smallest deployable unit (e.g., per microservice).
3. **Encryption**:
   - Encrypt configs at rest and in transit; avoid plaintext secrets.
4. **Monitoring**:
   - Set up alerts for config store errors (e.g., etcd leader changes).
5. **Rollback Plan**:
   - Maintain a backup of the previous config version for quick rollback.
6. **Testing**:
   - Test config changes in staging before production (e.g., using feature flags).
7. **Documentation**:
   - Document config schemas and critical settings (e.g., in Confluence or Markdown).

