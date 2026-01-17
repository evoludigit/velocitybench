**[Pattern] Microservices Guidelines Reference Guide**

---
### **Overview**
Microservices Guidelines define best practices, architectural principles, and operational standards for designing, deploying, and maintaining a **microservices-based system**. Unlike monolithic applications, microservices are independent, loosely coupled, and managed via domain-specific teams. This guide provides actionable rules to ensure scalability, fault isolation, observability, and maintainability while avoiding common anti-patterns (e.g., "distributed monolith").

Key objectives:
- **Decouple services** for agile development.
- **Standardize interactions** (REST/gRPC, async messaging).
- **Enforce observability** (logging, tracing, metrics).
- **Optimize deployment** (CI/CD, containerization, service mesh).
- **Manage data consistency** (sagas, eventual consistency).

Adhering to these guidelines improves resilience, reduces technical debt, and aligns with DevOps practices.

---

### **Schema Reference**
Below are core **Microservices Guidelines** categorized by domain. Use this as a **checklist** for design reviews.

| **Category**               | **Guideline**                                                                                     | **Rationale**                                                                                     | **Exceptions**                                                                                     |
|----------------------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Service Boundaries**     | Align boundaries with **business domains** (Domain-Driven Design).                              | Avoids over-fragmentation while enabling independent scaling.                                      | Shared kernels (e.g., authentication) may span domains.                                          |
|                            | **Service size**: ≤ 10K lines of code, ≤ 50 endpoints.                                             | Prevents complexity bloat; enforces modularity.                                                   | Legacy systems may require larger initial boundaries.                                            |
|                            | **No shared codebase** (except libraries).                                                      | Decouples dependencies; isolates changes.                                                         | Shared utilities (e.g., logging libs) are permitted.                                            |
| **Communication**          | **Synchronous**: REST/gRPC for request-response (idempotency required).                          | Simplifies retry logic; use for interactive flows.                                                | High-latency services may require async fallback.                                                |
|                            | **Asynchronous**: Event-driven (Kafka, RabbitMQ) for fire-and-forget or eventual consistency.     | Handles decoupled workflows (e.g., order processing).                                           | Avoid for critical transactions (use compensating transactions instead).                         |
|                            | **Circuit breakers** (Hystrix, Resilience4j) with defaults:                                      |                                                  |
|                              - Max retries: 3                                                 |                                                  |
|                              - Timeouts: 500ms–2s (configurable)                                |                                                  |
|                              - Threshold: 50% failure rate for tipping.                           |                                                  |                                                  |
| **Data Management**        | **Database-per-service** (avoid shared DBs).                                                   | Isolates schema changes; enables independent scaling.                                             | Read replicas or shared reporting DBs are acceptable.                                             |
|                            | **Event sourcing** for auditability (e.g., user actions).                                       | Enables replayability; critical for compliance.                                                  | Not required for simple CRUD services.                                                          |
|                            | **Saga pattern** for distributed transactions.                                                  | Manages ACID across services via choreography/orchestration.                                      | Use optimistic concurrency for lightweight cases.                                                |
| **Observability**          | **Metrics**: Every service emits Prometheus/OpenTelemetry metrics (e.g., latency, error rates). | Enables SLO/SLA monitoring.                                                                     | Metrics overload can be mitigated via sampling.                                                  |
|                            | **Logging**: Structured logs (JSON) with context IDs (trace IDs).                                | Simplifies correlation in distributed tracing.                                                    | Unstructured logs may persist for legacy systems.                                                |
|                            | **Tracing**: Distributed tracing (Jaeger, Zipkin) for latency analysis.                         | Detects bottlenecks in async calls.                                                              | High-cardinality traces may require sampling.                                                    |
| **Deployment**             | **Containerization**: Docker + Kubernetes (or equivalent).                                       | Ensures consistency across environments.                                                          | Serverless (e.g., AWS Lambda) for event-driven workloads.                                        |
|                            | **Immutable deployments**: No in-place updates; rollbacks via blue-green or canary.             | Reduces downtime risk.                                                                          | Stateful services may require careful coordination.                                               |
|                            | **Feature flags**: Enable gradual rollouts (LaunchDarkly, Istio).                                | Mitigates blast radius of bad deployments.                                                         | Avoid for critical configurations (use ConfigMaps/Secrets instead).                               |
| **Security**               | **Service mesh** (Istio, Linkerd) for mTLS and traffic management.                              | Secures inter-service communication.                                                              | Simpler auth (OAuth2) may suffice for low-risk services.                                         |
|                            | **API gateways**: Rate limiting, JWT validation, and request validation.                        | Protects upstream services from abuse.                                                            | Direct client-to-service calls are allowed for internal tools.                                   |
|                            | **Secrets management**: Vault or Kubernetes Secrets (never hardcoded).                          | Prevents credential leaks.                                                                        | Ephemeral secrets (e.g., tokens) may use temporary storage.                                     |
| **Testing**                | **Contract testing**: Pact for API consistency between services.                                  | Catches breaking changes early.                                                                  | Manual testing for complex interactions.                                                         |
|                            | **Chaos engineering**: Randomly inject failures (e.g., 90s latency).                           | Validates resilience.                                                                           | Use cautiously in production-like staging.                                                      |
|                            | **Integration tests**: Mock dependencies; test async flows end-to-end.                          | Ensures workflow correctness.                                                                    | Skip for stateless services with well-defined contracts.                                        |
| **CI/CD**                  | **GitOps**: Declarative pipelines (ArgoCD, Flux) for Git-driven deployments.                     | Auditable, reproducible deployments.                                                              | Imperative pipelines may persist for legacy systems.                                            |
|                            | **Pipeline stages**:                                                                             |                                                  |
|                              - Build: Linting, unit tests                                          |                                                  |
|                              - Test: Integration, contract tests                                   |                                                  |
|                              - Deploy: Canary → Staging → Prod                                       |                                                  |
|                              - Rollback: Automated if SLOs violated                                  |                                                  |                                                  |
| **Monitoring Alerts**      | **Critical alerts**:                                                                             |                                                  |
|                              - Error rates > 1%                                                   |                                                  |
|                              - 99th-percentile latency > target                                   |                                                  |
|                              - Database connection failures                                         |                                                  |                                                  |
|                            | **Semantic alerts**: Describe impact (e.g., "Checkout service failing").                         | Reduces alert fatigue.                                                                        | Informational alerts (e.g., "Log volume high") may be muted.                                   |

---

### **Query Examples**
Below are **real-world scenarios** and their recommended implementations based on these guidelines.

#### **1. Service Boundary Decision**
**Scenario**: Should `OrderService` and `PaymentService` be separate?
**Guidelines Applied**:
- **Domain alignment**: Orders and payments are distinct business domains.
- **Data isolation**: Orders may need to persist before payment; sagas are feasible.
**Implementation**:
```plaintext
OrderService (APIs: createOrder, cancelOrder)
└── Event: OrderCreated → triggers PaymentService
PaymentService (APIs: processPayment, refund)
    └── Event: PaymentFailed → triggers CompensationService
```

#### **2. Async Communication**
**Scenario**: User profile updates should trigger email notifications.
**Guidelines Applied**:
- Use **event-driven** (async) for loose coupling.
- **Idempotency**: Ensure `sendEmail` handles duplicate events.
**Implementation**:
```yaml
# Kafka Topic: user.updated
{
  "event": "profile.updated",
  "userId": "123",
  "email": "user@example.com",
  "metadata": {
    "idempotencyKey": "user_123_email_2023"
  }
}
```
- **Consumer**: EmailService listens to the topic and validates `idempotencyKey`.

#### **3. Distributed Transaction (Saga)**
**Scenario**: Cancel an order if payment fails.
**Guidelines Applied**:
- **Orchestration saga**: Use a `CancellationCoordinator` to manage steps.
- **Compensation**: Roll back inventory and refund payment.
**Implementation**:
```plaintext
1. OrderService emits PaymentFailed event → CancellationCoordinator
2. Coordinator:
   - Calls InventoryService: releaseReservedItems(orderId)
   - Calls PaymentService: refund(orderId)
3. On success: emits OrderCanceled event
```

#### **4. Observability Setup**
**Scenario**: Monitor `AuthService` latency.
**Guidelines Applied**:
- **Metrics**: Expose `/metrics` endpoint (Prometheus scrape target).
- **Tracing**: Inject OpenTelemetry spans in all HTTP calls.
**Implementation**:
```yaml
# auth-service/deployment.yaml
metrics:
  enabled: true
  port: 8081
tracing:
  exporter: jaeger
  serviceName: auth-service
```
- **Query**: `http://auth-service:8081/metrics` → Prometheus:
  ```promql
  http_server_duration_seconds_bucket{service="auth-service", quantile="0.95"}
  ```

#### **5. Rollback Strategy**
**Scenario**: Bad deployment causes 99% error rate in `CheckoutService`.
**Guidelines Applied**:
- **Blue-green deployment** with traffic shifting.
- **Automated rollback** if errors persist.
**Implementation**:
```bash
# ArgoCD pipeline (abridged)
steps:
  - name: canary-deploy
    script: kubectl apply -f checkout-service-canary.yaml
    retries: 3
  - name: monitor
    script: |
      if curl -s http://checkout-service | jq '.errors' | grep -q '>50'; then
        kubectl rollout undo deployment/checkout-service
      fi
```

---

### **Related Patterns**
To complement **Microservices Guidelines**, consider these patterns:

| **Pattern**                  | **Purpose**                                                                 | **When to Use**                                                                 |
|------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Strangler Fig Pattern]**  | Gradually replace monolith with microservices.                              | Legacy modernization; avoid "big bang" refactoring.                             |
| **[CQRS]**                   | Separate read/write models for scalability.                                  | High-read workloads (e.g., dashboards) with event-sourced writes.               |
| **[Event Sourcing]**         | Store state as a sequence of events for auditability.                       | Audit trails (finance, healthcare) or complex workflows.                        |
| **[Service Mesh]**           | Manage service-to-service communication (mTLS, retries, observability).     | Production environments with >10 services.                                      |
| **[Domain-Driven Design]**   | Define bounded contexts for service boundaries.                             | Complex domains (e.g., e-commerce, banking) with multiple teams.                |
| **[Chaos Engineering]**      | Test resilience by injecting failures.                                      | Post-launch stability; during on-call rotations.                               |
| **[API Gateway]**            | Centralize routing, auth, and rate limiting.                               | Public-facing APIs or internal API hubs.                                         |
| **[GitOps]**                 | Declare infrastructure as code in Git.                                      | Kubernetes environments; compliance-heavy deployments.                          |

---
### **Anti-Patterns to Avoid**
1. **Distributed Monolith**: Services that are tightly coupled (e.g., sharing DB schemas).
2. **Over-Async**: Using events for every interaction (increases complexity).
3. **Ignoring SLOs**: No observability leads to "blind deployments."
4. **No Rollback Plan**: Always design for failure recovery.
5. **Monolithic Logging**: Centralized logs make correlation harder.

---
### **Tools & Libraries**
| **Category**          | **Tools**                                                                 |
|-----------------------|---------------------------------------------------------------------------|
| **Observability**     | Prometheus, Grafana, OpenTelemetry, Jaeger                               |
| **Service Mesh**      | Istio, Linkerd, Consul Connect                                            |
| **Async Messaging**   | Kafka, RabbitMQ, NATS                                                      |
| **CI/CD**             | ArgoCD, Jenkins, GitHub Actions, Tekton                                     |
| **Testing**           | Pact (contract), Postman (API), Chaos Mesh                                 |
| **Secrets**           | HashiCorp Vault, AWS Secrets Manager, Kyma                                |
| **API Gateways**      | Kong, Apigee, AWS API Gateway                                             |