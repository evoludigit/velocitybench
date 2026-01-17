# **[Pattern] Microservices Gotchas – Reference Guide**

---

## **Overview**
The **Microservices Gotchas** pattern documents common pitfalls and anti-patterns in microservices architectures. Microservices offer scalability and modularity but introduce complexity in areas like **distributed transactions, service discovery, network latency, data consistency, and operational overhead**. This guide outlines **key challenges**, **architectural risks**, and **mitigation strategies** to help developers and architects avoid costly mistakes.

---

## **Key Concepts & Implementation Details**

### **1. Core Gotchas in Microservices**

| **Category**               | **Gotcha**                          | **Description**                                                                 |
|----------------------------|--------------------------------------|---------------------------------------------------------------------------------|
| **Service Granularity**    | Over-Splitting Services              | Excessive splitting leads to **increased network calls**, **orchestration complexity**, and **slow development**. |
|                            | Under-Splitting Services             | Keeps services too monolithic, negating benefits of microservices.              |
| **Communication**          | Latency & Chattiness                | Excessive inter-service calls degrade performance.                               |
|                            | Synchronous Overuse                  | Blocks services, causing cascading failures.                                   |
| **Data Management**        | Distributed Transactions             | ACID guarantees are hard to maintain across services.                           |
|                            | Data Duplication                    | Inconsistent data due to eventual consistency.                                  |
| **Observability**          | Lack of Centralized Logging          | Hard to debug distributed failures.                                             |
|                            | Poor Tracing & Monitoring            | Silence in distributed systems hides issues.                                   |
| **Resilience**             | Cascading Failures                  | A single service failure can bring down dependent services.                     |
|                            | No Circuit Breakers                 | Toxic clients overload failing services.                                        |
| **Deployment & CI/CD**     | Complex Rollbacks                     | Microservices require **canary deployments**, **feature flags**, and **blue-green**. |
|                            | Versioning Chaos                    | API versioning mismatches cause integration failures.                          |
| **Security**               | Distributed Auth                     | Managing identities across services is challenging.                              |
|                            | API Gateways Overhead                | Gateways add latency and complexity.                                           |
| **Testing**                | Integration Overhead                | Testing interactions between services is time-consuming.                        |
|                            | Mocking Over-Use                     | Mocks can hide real issues in distributed workflows.                            |

---

### **2. Mitigation Strategies**

| **Gotcha**                  | **Solution**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **Over-Splitting**          | Follow the **Domain-Driven Design (DDD)** principle. Keep boundaries aligned with business domains. |
| **Under-Splitting**         | Start with **modular monoliths**, then split when scaling is needed.          |
| **High Latency**            | Use **asynchronous communication (Event-Driven Architecture)** where possible. |
| **Distributed Transactions**| Implement **Saga Pattern** for long-running workflows. Avoid 2PC.            |
| **Data Inconsistency**      | Use **event sourcing** or **CQRS** for eventual consistency.                |
| **Cascading Failures**      | Implement **circuit breakers (Hystrix, Resilience4j)** and **retries with backoff**. |
| **Complex Deployments**     | Adopt **Infrastructure as Code (IaC)** and **containerization (Docker/Kubernetes)**. |
| **Security Risks**          | Use **API Gateways (Kong, Apigee)** with OAuth2/OpenID Connect.            |
| **Testing Overhead**        | Shift left with **contract testing (Pact)** and **chaos engineering**.       |

---

## **Schema Reference**
Below are common schema definitions for **service communication, events, and transactions**.

### **1. Service-to-Service Communication (REST/GraphQL)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "service": { "type": "string", "example": "orders" },
    "endpoint": { "type": "string", "example": "/checkout" },
    "headers": {
      "type": "object",
      "properties": {
        "Authorization": { "type": "string", "pattern": "^Bearer .+" },
        "X-Request-ID": { "type": "string" }
      }
    },
    "body": {
      "type": "object",
      "properties": {
        "orderId": { "type": "string" },
        "items": { "type": "array", "items": { "type": "object" } }
      }
    },
    "timeout": { "type": "integer", "minimum": 1000 } // ms
  },
  "required": ["service", "endpoint"]
}
```

### **2. Event-Driven Schema (Kafka/RabbitMQ)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "eventType": { "type": "string", "enum": ["OrderCreated", "PaymentProcessed"] },
    "payload": {
      "type": "object",
      "properties": {
        "orderId": { "type": "string" },
        "status": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "correlationId": { "type": "string" }
      }
    }
  },
  "required": ["eventType", "payload"]
}
```

### **3. Saga Pattern Transaction Log**
```sql
CREATE TABLE saga_transactions (
  saga_id VARCHAR(36) PRIMARY KEY,
  status VARCHAR(20) CHECK (status IN ('STARTED', 'COMPENSATING', 'COMPLETED', 'FAILED')),
  current_step VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## **Query Examples**

### **1. Finding Service Dependencies (Service Mesh)**
**Tool:** Istio/Kiali
**Query:**
```bash
kiali graph -s <namespace> --output-format=dot | dot -Tpng > dependencies.png
```
**Output:** A dependency graph visualizing service calls.

### **2. Detecting API Chattiness (Prometheus)**
**Query:**
```promql
sum(rate(http_requests_total{status=~"2.."}[5m])) by (service)
```
**Interpretation:** High values indicate excessive inter-service calls.

### **3. Saga Status Check (PostgreSQL)**
```sql
SELECT * FROM saga_transactions
WHERE status = 'COMPENSATING' ORDER BY updated_at DESC LIMIT 10;
```
**Action:** Manually trigger compensating transactions if stuck.

### **4. Latency Analysis (OpenTelemetry)**
```bash
otelcol --config-file=latency-config.yaml collect --start-delay=10s --metrics-export-period=5s
```
**Output:** Histograms of service-to-service latency.

---

## **Related Patterns**

| **Pattern**                     | **When to Use**                                                                 | **Reference**                          |
|----------------------------------|---------------------------------------------------------------------------------|----------------------------------------|
| **Event Sourcing**               | When strong audit trails and temporal queries are needed.                       | [Event Sourcing](https://msddd.com/)   |
| **CQRS**                         | For read-heavy workloads with complex queries.                                  | [CQRS Pattern](https://cqrs.com/)      |
| **Saga Pattern**                 | For managing distributed transactions without 2PC.                              | [Saga Pattern](https://microservices.io/) |
| **API Gateway**                  | To consolidate API endpoints and enforce security.                            | [API Gateway](https://aws.amazon.com/api-gateway/) |
| **Chaos Engineering**            | To proactively test resilience.                                                 | [Chaos Mesh](https://chaos-mesh.org/) |
| **Polyglot Persistence**         | When different services need different data models.                            | [Polyglot Persistence](https://martinfowler.com/bliki/PolyglotPersistence.html) |

---

## **Best Practices Summary**
1. **Start simple**: Avoid early over-engineering (e.g., Event Sourcing, Saga).
2. **Monitor everything**: Distributed systems need **end-to-end tracing**.
3. **Design for failure**: Assume services will fail.
4. **Automate deployments**: Use GitOps (ArgoCD, Flux) for consistency.
5. **Document contracts**: API schemas should be versioned and testable.
6. **Balance granularity**: Avoid both **tight coupling** and **over-fragmentation**.

---
**See Also:**
- [12-Factor App](https://12factor.net/)
- [Microservices Anti-Patterns](https://microservices.io/patterns/)