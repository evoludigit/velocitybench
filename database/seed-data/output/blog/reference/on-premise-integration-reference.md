**[Pattern] On-Premise Integration Reference Guide**

---
---
### **Overview**
**On-Premise Integration** is a pattern used to connect legacy or sensitive systems hosted in an organization’s private data center or internal network with external cloud services, partner APIs, or other enterprise applications. This pattern ensures data sovereignty, compliance with stringent regulatory requirements (e.g., GDPR, HIPAA), and secure control over infrastructure while enabling integration capabilities. It is commonly used when:
- **Data residency restrictions** prevent raw cloud ingestion (e.g., healthcare, finance).
- **Legacy systems** must remain on-premise while extending capabilities.
- **Network security policies** prohibit public internet access for critical systems.

---

### **Key Concepts & Architecture**
1. **Deployment Model**
   - **On-Premise Hosting**: Integration logic (e.g., event processors, middleware) runs in the private network.
   - **Hybrid Connectivity**: Uses VPNs, private links, or Direct Connect (AWS) to securely route requests/responses.

2. **Components**
   | Component          | Description                                                                 |
   |--------------------|-----------------------------------------------------------------------------|
   | **Edge Gateway**   | Secure entry point for inbound/outbound traffic (e.g., Apigee, AWS API Gateway). |
   | **On-Premise Proxy** | Local proxy (e.g., Nginx, HAProxy) to route requests to internal services.   |
   | **ETL/Data Pipeline** | Transforms/validates data before/after integration.                          |
   | **Authentication Layer** | OIDC, JWT, or certificate-based auth for API security.                      |
   | **Audit Logs**      | Critical for compliance; logs all inbound/outbound API calls.               |

3. **Data Flow**
   ```
   External API → (HTTPS) Edge Gateway [Auth] → Proxy → On-Premise App → Response → Proxy → Edge Gateway → External API
   ```

---

### **Schema Reference**
Below are the core schemas for common on-premise integration scenarios.

#### **1. API Gateway Request/Response Schema**
| Field               | Type       | Description                                                                 | Example Value                     |
|---------------------|------------|-----------------------------------------------------------------------------|-----------------------------------|
| `api_key`           | String     | Mandatory API key for authentication.                                       | `"abc123-xyz"`                    |
| `timestamp`         | ISO 8601   | Request timestamp (validity: 5 min).                                       | `"2024-05-15T12:00:00Z"`         |
| `data`              | JSON       | Payload (structured per API spec).                                          | `{"transaction_id": "txn-123"}`   |
| `client_ip`         | IPv4/IPv6  | Source IP (for rate-limiting).                                              | `"192.168.1.100"`                 |

**Response Schema**
```json
{
  "status": "success",
  "code": 200,
  "data": { "response": "Processed" },
  "id": "req-123"
}
```

#### **2. Event-Driven Schema (Kafka/RabbitMQ)**
| Field          | Type    | Description                                                                 |
|----------------|---------|-----------------------------------------------------------------------------|
| `event_type`   | String  | Event category (e.g., `"payment_processed"`, `"user_created"`).             |
| `payload`      | JSON    | Structured event data.                                                     |
| `metadata`     | Object  | Non-sensitive context (e.g., timestamps, correlations).                     |
| `signature`    | String  | HMAC-SHA256 hash (secure validation).                                      |

**Example Event**
```json
{
  "event_type": "inventory_adjusted",
  "payload": {
    "product_id": "P1005",
    "quantity": 50,
    "location": "warehouse-01"
  },
  "metadata": {
    "timestamp": "2024-05-15T14:30:00.000Z",
    "correlation_id": "evt-456"
  }
}
```

---

### **Implementation Steps**

#### **1. Set Up Secure Connectivity**
- **Option A: VPN Tunnel** (OpenVPN/WireGuard)
  ```bash
  # Example OpenVPN config (server-side)
  port 1194
  proto udp
  dev tun0
  ca ca.crt
  cert server.crt
  key server.key
  dh dh.pem
  server 10.8.0.0 255.255.255.0
  ```
- **Option B: Private AWS Direct Connect**
  - Provision a **1 Gbps** connection to AWS via your ISP.
  - Configure VPC peering or transit gateway for routing.

#### **2. Deploy the Edge Gateway (Apigee Example)**
```yaml
# Terraform snippet for Apigee Edge (GCP)
resource "google_apigee_api_proxy" "onprem_proxy" {
  name           = "onprem-integration-proxy"
  api_id         = "onprem-api"
  api_display_name = "On-Premise Integration"
  api_version    = "v1"

  environments {
    name = "production"
    servers {
      name = "backend-server"
      url  = "https://onprem.example.com/api"
    }
  }
}
```

#### **3. On-Premise Proxy Configuration (Nginx)**
```nginx
server {
    listen 8443 ssl;
    server_name api.onprem.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.crt;
    ssl_certificate_key /etc/letsencrypt/live/api.key;

    location /secure-api/ {
        proxy_pass http://localhost:8080;  # Internal backend
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        auth_request /auth;
    }

    location = /auth {
        internal;
        proxy_pass http://oidc-provider:3000/validate;
    }
}
```

#### **4. Data Pipeline Example (ETL with Airflow)**
```python
# DAG for daily data sync (airflow/dags/etl_to_cloud.py)
from airflow import DAG
from airflow.providers.http.operators.http import SimpleHttpOperator
from datetime import datetime

with DAG("onprem_to_cloud_sync", start_date=datetime(2024, 1, 1)) as dag:
    sync_task = SimpleHttpOperator(
        task_id="sync_customer_data",
        method="POST",
        http_conn_id="cloud_api_conn",
        endpoint="/v1/customers",
        data='{"customers": "{{ ti.xcom_pull('extract_task') }}"',
        headers={"Authorization": "Bearer {{ vars.api_key }}"},
    )
```

---

### **Query Examples**
#### **1. REST API Example (Sync Data)**
```http
POST /v1/customers/batch
Host: api.onprem.example.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "customers": [
    {"id": "cust-001", "name": "John Doe", "updated_at": "2024-05-15T10:00:00Z"},
    {"id": "cust-002", "name": "Jane Smith", "status": "active"}
  ]
}
```

#### **2. Event Subscription (Webhook)**
```json
# Request to subscribe to events (HTTP POST)
{
  "subscription": {
    "event_types": ["payment_processed", "order_status"],
    "callback_url": "https://cloud-service.example.com/webhooks",
    "auth_token": "{{ onprem_auth_token }}"
  }
}
```

#### **3. Query Data via GraphQL (Compose Query)**
```graphql
query GetCustomerData($customerId: ID!) {
  customer(id: $customerId) {
    id
    name
    orders {
      id
      totalAmount
    }
  }
}
```

---

### **Security Considerations**
| Risk                          | Mitigation Strategy                          |
|-------------------------------|----------------------------------------------|
| **Data Leakage**              | Encrypt data in transit (TLS 1.3) and at rest (AES-256). |
| **Unauthorized Access**       | Enforce mutual TLS (mTLS) or certificate-based auth. |
| **DDoS Attacks**              | Rate-limiting (e.g., 1000 requests/minute) via edge gateway. |
| **Compliance Audits**         | Log all API calls with `client_ip`, `user_agent`, and `timestamp`. |

---

### **Performance Optimization**
- **Caching**: Use Redis on-premise to cache frequent API responses (e.g., `GET /products/{id}`).
- **Load Balancing**: Deploy multiple on-premise proxies behind HAProxy.
- **Asynchronous Processing**: Offload heavy transformations to Kafka/RabbitMQ queues.

---

### **Related Patterns**
1. **API Gateway Pattern**
   - Centralized routing and auth for on-premise integrations.
   - *Reference*: [API Gateway Pattern](https://microservices.io/patterns/apigateway.html).

2. **Event-Driven Architecture**
   - Decouple systems using Kafka or RabbitMQ for event streaming.
   - *Reference*: [Event Sourcing](https://martinfowler.com/eaaCatalog/eventSourcing.html).

3. **Service Mesh (Istio/Linkerd)**
   - Manage traffic, security, and monitoring for microservices in hybrid environments.
   - *Reference*: [Istio Hybrid Cloud](https://istio.io/latest/docs/setup/getting-started/).

4. **Data Mesh**
   - Distribute data ownership across domains while ensuring interoperability.
   - *Reference*: [Zalando Tech Blog](https://engineering.zalando.com/topics/data/data-mesh.html).

5. **Zero Trust Network Access (ZTNA)**
   - Replace VPNs with identity-based access control (e.g., Cloudflare Access).
   - *Reference*: [Google BeyondCorp](https://cloud.google.com/beyondcorp).

---
---
**Note**: Customize schemas and examples based on your specific on-premise tools (e.g., replace Apigee with Kong, Kafka with RabbitMQ). Always test connectivity with a staging VPN before production deployment.