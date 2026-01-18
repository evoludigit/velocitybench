---
# **[Pattern] Strangler Fig Pattern Reference Guide**

---

## **1. Overview**
The **Strangler Fig Pattern** is a **strategic migration approach** for incrementally decomposing a legacy monolithic application into modular microservices. Named after the parasitic plant that slowly suffocates a host tree while maintaining its own growth, this pattern avoids the risks of a "big bang" refactor by **phasing out the monolith piece by piece** while exposing a clean, modern API layer. It is particularly valuable for large, established systems where a full rewrite or immediate migration would be costly, risky, or impractical.

Starting with a **limited new service**, the Strangler Fig Pattern gradually replaces or "strangles" dependent components of the monolith by:
- **Exposing a lightweight API wrapper** around monolith functionality.
- **Incrementally refactoring** parts of the monolith to new services.
- **Redirecting calls** from the monolith to the new service layer.
- **Eventually decommissioning** the old monolithic code while ensuring backward compatibility.

This approach minimizes downtime, reduces technical debt, and allows teams to adopt new technologies without overhauling the entire system at once.

---

## **2. Core Concepts & Implementation Schema**

| **Component**               | **Description**                                                                                                                                                                                                                                                                 | **Key Considerations**                                                                                                                                                                                                                     |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Monolith Core**            | The existing, well-established, but rigid monolithic application. Acts as the "host" for the strangling process.                                                                                                                                               | - Maintains stability during migration.<br>- Gradually isolated via API boundaries.<br>- Critical paths must be preserved.                                                                                             |
| **Strangler Wrapper API**    | A **minimal, stateless API layer** (e.g., REST/gRPC) that **proxies requests** to the monolith. Later, routes calls to new microservices.                                                                                                             | - Must mirror the monolith’s original API contracts.<br>- Instrumented for monitoring/logging.<br>- Rate-limited to avoid overloading the monolith.<br>- Should support **graceful degradation**.                                  |
| **New Microservice**         | A **distinct service** built to replace a subset of monolithic functionality. Written in modern tech stack (e.g., Spring Boot, Node.js, Go).                                                                                                        | - Focused on a **single responsibility** (e.g., "User Management" or "Order Processing").<br>- Stateless by design.<br>- Adheres to **bounded contexts** and **domain-driven design (DDD)** patterns.<br>- Leverages event-driven architecture if applicable. |
| **Decorator Pattern**        | A **dynamic routing layer** (e.g., API Gateway, proxy, or service mesh) that **redirects traffic** between the monolith and new services based on rules (e.g., feature flagging, versioning, or feature toggles).                          | - Avoids hardcoding logic in the monolith.<br>- Supports **A/B testing** and canary deployments.<br>- Example: Use **Envoy, Kong, or AWS ALB** for routing.                                                                                 |
| **Canary Releases**          | Gradual rollout of the new service to a subset of users/traffic while monitoring performance and errors.                                                                                                                                                       | - Monitor **latency, error rates, and business metrics**.<br>- Use **feature flags** to toggle between old/new logic.<br>- Roll back if anomalies detected.                                                                                      |
| **Event Sourcing/Async**     | Optional: Decouple services using **event buses** (e.g., Kafka, RabbitMQ) for asynchronous communication, ideal for complex workflows (e.g., payments, inventory updates).                                                                                     | - Reduces tight coupling.<br>- Enables eventual consistency.<br>- Requires **eventual consistency** handling.                                                                                                                  |
| **Database Gradual Migration** | Phased transition of data storage from monolith DB (e.g., SQL) to microservices’ databases (e.g., NoSQL).                                                                                                                                                 | - **Dual-write**: Sync data between old/new stores.<br>- **Evaluate**: Migration tool (e.g., **Flyway, Liquibase**) or **CDC** (Change Data Capture, e.g., Debezium).<br>- **Schema migration** must be backward-compatible.              |
| **Legacy Integration**       | Maintains necessary integrations with legacy systems (e.g., batch jobs, external APIs) until fully migrated.                                                                                                                                                 | - Use **adapters** (e.g., Java → Node.js bridges) if needed.<br>- Automate syncs (e.g., cron jobs).<br>- Document **SLA dependencies**.                                                                                                  |

---

## **3. Schema Reference (Migration Phases)**
The Strangler Fig Pattern follows a **multi-phase lifecycle**. Below is a high-level schema:

| **Phase**               | **Action Items**                                                                                                                   | **Outcome**                                                                                                                                                                                                                            | **Technical Debt Mitigation**                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| **Phase 1: Wrapper API** | Build a REST/gRPC layer around the monolith’s endpoints.                                                                             | - Public API is now extensible.<br>- Monolith remains "untouched" internally.                                                                                                                                                     | - Use **OpenAPI/Swagger** for contract documentation.<br>- Implement **auth** (e.g., JWT, OAuth) early.                |
| **Phase 2: New Service** | Develop a microservice for a **replaceable subset** (e.g., user auth) with its own DB.                                            | - Traffic can be directed to new service via proxy.<br>- Monolith still serves as a fallback.                                                                                                                                       | - Leverage **gRPC** for internal service-to-service communication if needed.<br>- Avoid tight coupling.              |
| **Phase 3: Canary**      | Deploy the new service alongside the monolith, routing a subset of traffic (e.g., 5%) to it.                                     | - Monitor performance/stability.<br>- Adjust feature flags dynamically.                                                                                                                                                              | - Implement **distributed tracing** (e.g., Jaeger) for latency analysis.                                          |
| **Phase 4: Dual-Write**  | Synchronize data between monolith and new service (e.g., via ETL or CDC).                                                         | - Dual layer supports seamless transitions.<br>- Prevents data loss during cutover.                                                                                                                                                            | - Use **transactional outbox pattern** for reliability.<br>- Ensure **idempotency**.                                |
| **Phase 5: Cutover**     | Gradually shift traffic to the new service until the monolith’s functionality is fully replaced.                                   | - Monolith is decommissioned for the replaced feature.<br>- New service operates independently.                                                                                                                                           | - Document **rollback procedures**.<br>- Archive monolith backups.                                                 |
| **Phase 6: Iterate**     | Repeat the process for the next monolith component (e.g., order processing).                                                     | - Complete migration without downtime.<br>- Continuous improvement in microservices.                                                                                                                                                     | - Optimize for **cost, scalability, and maintainability**.                                                     |

---

## **4. Query Examples**

### **Example 1: API Endpoint Migration (Phase 1)**
**Use Case**: Replace `/monolith/api/v1/users/{id}` with a new service.
**Before (Monolith Direct Call)**:
```bash
GET http://monolith:8080/api/v1/users/123
```
**After (Wrapper API)**:
```bash
GET http://wrapper-api:3000/api/v1/users/123
```
*Backend Logic* (Wrapper API):
```java
// Pseudocode for dynamic routing
if (request.path.contains("/users")) {
    if (newServiceHealthy()) {
        return forwardToNewService(); // e.g., `http://users-service:5000`
    } else {
        return callMonolith();        // Fallback
    }
}
```

---

### **Example 2: Database Dual-Write**
**Use Case**: Sync user data between monolith (PostgreSQL) and new service (MongoDB).
**ETL Script (simplified)**:
```python
# Pseudocode for CDC (Change Data Capture)
def sync_users():
    while True:
        new_users = monolith_db.query("SELECT * FROM users WHERE created_at > last_sync")
        for user in new_users:
            users_service.put(user)  # POST to MongoDB
            save_sync_point(user.id) # Record last synced ID
```
*Monitoring Alert*: Trigger if `users_service.put()` fails repeatedly (indicating a blocker).

---

### **Example 3: Feature Flagging (Canary)**
**Use Case**: Roll out the new auth service to 10% of users.
**Configuration (Envoy Proxy)**:
```yaml
# envoy_v3_config.proto snippet
routes:
  - match:
      prefix: "/api/v1/auth"
    route:
      cluster: monolith_auth_cluster
      runtime_fraction:
        denominator: HUNDRED
        numerator: 10  # 10% traffic
  - match:
      prefix: "/api/v1/auth"
    route:
      cluster: new_auth_service
      runtime_fraction:
        denominator: HUNDRED
        numerator: 90  # 90% traffic
```

---

## **5. Query Examples (Database Schema Changes)**

### **Example 4: Domain-Driven Migration**
**Monolith Schema (SQL)**:
```sql
CREATE TABLE products (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10, 2)
);
```
**New Service Schema (NoSQL - DynamoDB)**:
```json
{
  "projections": {
    "id": "string",
    "name": "string",
    "price": "decimal",
    "createdAt": "timestamp",
    "version": "integer"  // For conflict resolution
  }
}
```
**Migration Strategy**:
1. **Initial Load**: Export monolith data to DynamoDB via ETL.
2. **Sync Layer**: Use **AWS DMS** (Database Migration Service) for ongoing changes.
3. **Conflict Handling**: Prefer new service writes; resolve conflicts via `version` field.

---

## **6. Monitoring & Observability**
Critical to track migration health:
- **Metrics**:
  - `wrapper_api.latency` (p99, p95).
  - `monolith_vs_new_service.errors`.
  - `database_dual_write.failed_syncs`.
- **Alerts**:
  - Trigger if `new_service.health < 99%` for >5 minutes.
  - Alert on `monolith.db.connections > 80%`.
- **Tools**:
  - **APM**: Datadog, New Relic.
  - **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana).
  - **Tracing**: Jaeger, OpenTelemetry.

---

## **7. Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation Strategy**                                                                                                                                                                                                                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Incomplete API Contracts**          | Document all monolith endpoints via **OpenAPI** before building wrappers.<br>Validate contracts with tools like **Prismatic Schema**.                                                                                                                     |
| **Tight Coupling Between Services**   | Use **event-driven architecture** (e.g., Kafka) or **async APIs** (gRPC).<br>Avoid shared DBs or direct dependencies between services.                                                                                                                          |
| **Data Inconsency**                  | Implement **eventual consistency** patterns (e.g., **Saga** for distributed transactions).<br>Use **idempotency keys** for retries.<br>Monitor `database_dual_write.drift`.                                                                         |
| **Performance Bottlenecks**           | Profile the monolith with **JVM Profilers** or **eBPF** before migration.<br>Optimize new services for **cold starts** (e.g., use **warm-up requests**).<br>Rate-limit wrapper API to avoid overload.                                                 |
| **Team Resistance**                  | Conduct **code reviews** to validate migrations.<br>Use **pair programming** between legacy and microservices teams.<br>Celebrate small wins (e.g., "Service X is now 100% decoupled").                                                                       |
| **Downtime During Cutover**           | Plan for **blue-green deployments** with feature flags.<br>Use **database mirrors** (e.g., PostgreSQL streaming replication) for zero-downtime switchover.<br>Test failover scenarios in staging.                                                          |

---

## **8. Related Patterns**

| **Pattern**                     | **Purpose**                                                                                                                                                                                                                                                                 | **When to Use Together**                                                                                                                                                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Event-Driven Architecture (EDA)** | Decouples services using events (e.g., Kafka, RabbitMQ).                                                                                                                                                                                                       | Useful for **complex workflows** (e.g., order processing with payments, inventory, notifications) during/after Strangler Fig migration.                                                                                            |
| **CQRS**                         | Separates read and write models for performance/scalability.                                                                                                                                                                                                       | Apply to **read-heavy services** (e.g., analytics dashboards) post-migration to offload the monolith.                                                                                                                              |
| **Service Mesh (Istio, Linkerd)** | Manages inter-service traffic, retries, circuit breaking.                                                                                                                                                                                                    | Deploy alongside Strangler Fig to **handle failures gracefully** during canary transitions.                                                                                                                                  |
| **Database-per-Service**         | Isolates each microservice’s data store.                                                                                                                                                                                                                 | Critical for **scalability and autonomy**—avoid shared DBs post-migration.                                                                                                                                                                    |
| **Feature Toggles**               | Dynamically enables/disables features via flags.                                                                                                                                                                                                           | Essential for **canary releases** and gradual rollouts. Tools: **LaunchDarkly, Unleash**.                                                                                                                                               |
| **Saga Pattern**                  | Manages distributed transactions via choreography/orchestration.                                                                                                                                                                                                | Handles **compensating transactions** (e.g., refunds if inventory fails to update).                                                                                                                                                          |
| **API Gateway**                  | Centralizes routing, auth, and rate-limiting.                                                                                                                                                                                                          | Use to **consolidate wrapper APIs** and enforce policies (e.g., JWT validation) across services.                                                                                                                                         |
| **Progressive Delivery (Blue/Green)** | Zero-downtime deployments via full environment swaps.                                                                                                                                                                                                       | Pair with Strangler Fig for **phased cutovers** (e.g., replace `/v1` with `/v2` endpoints).                                                                                                                                                         |

---

## **9. Tools & Technologies**
| **Category**               | **Tools/Libraries**                                                                                                                                                                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **API Wrappers**           | Spring Cloud Gateway, Kong, AWS API Gateway, Envoy Proxy.                                                                                                                                                                                |
| **Service Mesh**           | Istio, Linkerd, Consul Connect.                                                                                                                                                                                                              |
| **Event Bus**              | Apache Kafka, RabbitMQ, AWS SNS/SQS.                                                                                                                                                                                                               |
| **ORM/ODM**                | Hibernate (SQL), MongoDB ODM, TypeORM.                                                                                                                                                                                                          |
| **Monitoring**             | Prometheus + Grafana, Datadog, New Relic, OpenTelemetry.                                                                                                                                                                                       |
| **Database Migration**     | Flyway, Liquibase, AWS DMS, Debezium (CDC).                                                                                                                                                                                                     |
| **Feature Flags**          | LaunchDarkly, Unleash, Flagsmith.                                                                                                                                                                                                                  |
| **Containerization**       | Docker, Kubernetes (EKS, AKS, GKE).                                                                                                                                                                                                             |
| **Testing**                | Postman/Newman (API testing), TestContainers (integration tests), Chaos Engineering (Gremlin).                                                                                                                                    |

---

## **10. Conclusion**
The **Strangler Fig Pattern** is a **low-risk, incremental strategy** for migrating monoliths to microservices. By leveraging **API wrappers, phased rollouts, and dual-write databases**, teams can gradually replace legacy systems without major disruptions. Key to success is:
1. **Start small**: Focus on **replaceable components** (e.g., CRUD-heavy services).
2. **Automate monitoring**: Use observability tools to detect issues early.
3. **Iterate**: Treat each migration as a **sprint**, not a monolithic effort.
4. **Document contracts**: Maintain **API specs** (OpenAPI) to avoid contract drift.

For teams with **high-availability requirements**, combine this with **blue-green deployments** or **canary analysis**. For **event-driven workflows**, integrate with **event buses** during or after migration.

---
**References**:
- Martin Fowler, *Strangler Fig Application*.
- James Lewis & Michelle Barker, *Microservices Patterns*.
- AWS Well-Architected Framework (Migration Lens).
- Istio & Service Mesh Interface (SMI) documentation.