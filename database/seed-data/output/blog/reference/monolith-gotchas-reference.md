**[Pattern] Monolith Gotchas: Reference Guide**
*Version 1.2 — Last updated: [INSERT DATE]*

---

### **Overview**
This guide documents common pitfalls ("gotchas") when working with **monolithic architectures**, where a single, tightly coupled system handles all application components. While monoliths simplify early-stage development, they introduce scalability, maintainability, and performance challenges as applications grow. This reference outlines critical anti-patterns, their root causes, and mitigations without advocating for vs. against monoliths; instead, it provides actionable insights for teams managing them.

Key focus areas:
- **Technical debt accumulation** (e.g., rigid dependencies, circular refactoring).
- **Operational fragility** (e.g., deployment risks, scaling bottlenecks).
- **Team velocity erosion** (e.g., onboarding complexity, coordination overhead).
- **Hidden complexity** (e.g., shadow domains, implicit contracts).

---

## **Schema Reference: Monolith Gotchas (Anti-Patterns)**

| **Category**               | **Gotcha**                          | **Description**                                                                                                                                                     | **Indicators**                                                                                                                                                     | **Impact**                                                                                                                                                     | **Mitigation**                                                                                                                                                     |
|----------------------------|-------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Architectural Rigidity** | **Tight Coupling**                  | Over-reliance on shared libraries, databases, or service contracts makes changes risky or impossible to isolate.                                                     | Frequent "nothing works after a merge"; "changing X breaks Y".                                                                                                         | High refactoring costs; slow feature iteration.                                                                                                                   | Adopt **modular design patterns** (e.g., Domain-Driven Design boundaries); use **dependency inversion** (e.g., interfaces for external services).                        |
|                            | **God Class**                       | Single classes/files handling unrelated logic (e.g., `AppService.cs` with 5,000 lines).                                                                             | Code duplication; "find usages" reveals unrelated callers.                                                                                                            | Poor readability; violates **Single Responsibility Principle (SRP)**.                                                                                               | Break into **smaller, focused classes**; leverage **composition over inheritance**.                                                                                |
| **Scalability Issues**     | **Single-Process Bottleneck**       | All workloads (e.g., API, batch, messaging) compete for CPU/memory in one JVM/process.                                                                             | High latency under load; "out-of-memory" errors.                                                                                                                  | Poor horizontal scaling; costly cloud resource over-provisioning.                                                                                                | **Micro-service decomposition** (start with high-contention modules); use **queue-based isolation** (e.g., RabbitMQ for async tasks).                           |
|                            | **Database Lock Contention**        | Long-running transactions (e.g., `SELECT *`) block concurrent reads/writes in shared DB schemas.                                                                        | High `pg_locks` or `sys.dm_tran_locks` (SQL Server) metrics; timeout errors.                                                                                        | Degraded performance under concurrency.                                                                                                                       | **Shard data** by feature (e.g., `orders` vs. `users` schemas); use **optimistic locking** or **eventual consistency**.                                            |
| **Deployment Risks**       | **Big-Bang Deployments**            | Entire monolith must redeploy for a single feature change, risking downtime.                                                                                        | Downtime during "release windows"; "roll-forward" needed after failures.                                                                                            | Long lead times; high risk of cascading failures.                                                                                                                  | **Canary deployments**; **feature flags**; **blue-green deployments** (requires sidecar or load-balanced instances).                                               |
| **Testing Challenges**     | **Slow Test Suites**                | Monolithic test suites (e.g., 5,000 unit tests) run for hours, slowing feedback loops.                                                                             | CI/CD pipeline takes >30 minutes; "skipped tests" due to timeouts.                                                                                                | Burnout; reduced developer velocity.                                                                                                                           | **Test isolation**: mock external services; **parallelize tests**; **split suites** by domain.                                                                   |
| **Team Coordination**      | **Domain Overlap**                  | Teams own intersecting codebases (e.g., "frontend" and "backend" share auth logic).                                                                               | "Blame games" during bugs; "I didn’t know you changed that!"                                                                                                       | Low trust; knowledge silos.                                                                                                                                         | Define **clear ownership boundaries** (e.g., "Team A owns Orders, Team B owns Payments"); use **contract tests** for cross-boundary interactions.                  |
| **Hidden Complexity**      | **Shadow Domains**                  | Invisible layers of indirect dependencies (e.g., `logger` → `aws-sdk` → `dynamodb`).                                                                             | Refactoring `logger` breaks unrelated features.                                                                                                                   | Unexpected breakages during refactors.                                                                                                                          | **Dependency maps** (e.g., `depject`, `CodeScene`); **dependency injection** to isolate libraries.                                                              |
|                            | **Implicit Contracts**              | Undocumented assumptions (e.g., "API v1 always returns `status: 200` for valid requests").                                                                       | "Why does this endpoint fail silently?"                                                                                                                           | Bugs in unseen interactions; difficult to document.                                                                                                               | **Explicit contracts**: API specs (OpenAPI); **schema validation** (e.g., Pydantic, JSON Schema).                                                                 |
| **Observability Gaps**     | **Single Log Stream**               | All services log to one file/console, making debugging noisy and slow.                                                                                               | "Needle in a haystack" during incidents.                                                                                                                         | Slow MTTR (Mean Time to Resolve).                                                                                                                              | **Structured logging** (e.g., JSON); **distributed tracing** (e.g., Jaeger); **service-specific metrics**.                                                     |
|                            | **Noisy Neighbor Problem**         | Resource-hogging modules (e.g., a batch job) starve others.                                                                                                       | "Disk I/O spikes after midnight"; "CPU throttled".                                                                                                                | Unpredictable performance.                                                                                                                                          | **Resource isolation**: Containerization (Docker/K8s); **queue-based throttling**.                                                                                     |

---

## **Query Examples: Detecting Monolith Gotchas**
Use these patterns to audit your monolith for anti-patterns.

### **1. Detect Tight Coupling**
**Tool:** `grep`, `cloc`, or IDE "Find Usages"
**Example (Python):**
```bash
# Check for classes/methods with 100+ dependencies (arbitrary threshold)
grep -r "import.*from.*[" ../src | grep -v "__pycache__" | sort | uniq -c | sort -nr | head -20
```
**Output:**
```
  120   ../src/auth/services/__init__.py
   87    ../src/payment/routes.py
```
**Action:** Refactor `auth/services` into modular components.

---

### **2. Find God Classes**
**Tool:** `cloc` (Count Lines of Code) or IDE "Open All References"
**Example (Java):**
```bash
# Count lines per class (threshold: >200 LoC)
find src -name "*.java" -exec cloc {} + | grep -E "^Java\s+\d+\s+\d+\s+.*\s+(\d{3,})"
```
**Output:**
```
Java          1500         0   src/main/java/com/example/AppService.java
```
**Action:** Split `AppService` into `OrderService`, `UserService`, etc.

---

### **3. Identify Database Contention**
**Tool:** Database metrics (Prometheus/Grafana) or SQL logs
**Example (PostgreSQL):**
```sql
-- Find long-running queries (>5s)
SELECT query, state, now() - query_start AS duration
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 seconds';
```
**Output:**
```
                        query                         |   state   | duration
------------------------------------------------------+-----------+----------
 SELECT * FROM orders WHERE status = 'pending' LIMIT 1000 | active    | 42s
```
**Action:** Add indexes to `orders(status)`; consider **materialized views** for aggregates.

---

### **4. Audit Deployment Risks**
**Tool:** Git history or CI/CD logs
**Example (Git):**
```bash
# Find commits touching >50 files (high-risk changes)
git log --oneline --numstat | awk '{add+=$1; files++} END {if (files >= 50) print $1}' | head -5
```
**Output:**
```
abc1234 Commit that touched 68 files (high-risk!)
```
**Action:** Require **manual review** for changes to >30 files; use **feature flags**.

---

### **5. Locate Shadow Domains**
**Tool:** Dependency graph tools (e.g., `depject`, `npm ls --json`)
**Example (Node.js):**
```bash
# Visualize transitive dependencies
npm ls --json > dependencies.json
# Use `depject` to generate a graph
depject --input dependencies.json --output monolith-deps.svg
```
**Output:** A graph showing `src/auth` → `aws-sdk` → `dynamodb`.
**Action:** Replace `dynamodb` with **local-first** storage (e.g., SQLite) or **mock** in tests.

---

## **Related Patterns**
To mitigate monolith gotchas, consider these complementary patterns:

| **Pattern**                | **Purpose**                                                                 | **When to Use**                                                                 | **Tools/Libraries**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Domain-Driven Design (DDD)** | Model bounded contexts to reduce coupling.                                 | When business domains are distinct (e.g., `Orders` vs. `Inventory`).           | EventStorming, Hexagonal Architecture.                                               |
| **Strangler Pattern**      | Incrementally replace monolith modules with microservices.                  | When scaling a specific module (e.g., `Payments`).                                | Sidecar proxies (e.g., Envoy), API gateways.                                        |
| **Event Sourcing**         | Decouple services via immutable event logs.                                  | For audit-heavy domains (e.g., `Billing`).                                      | Kafka, EventStoreDB.                                                                |
| **Contract Testing**       | Enforce API contracts between modules.                                        | When teams own intersecting codebases.                                           | Pact, Postman.                                                                        |
| **Feature Toggles**        | Deploy partially without risk.                                               | During big-bang deployments.                                                     | LaunchDarkly, Flagsmith.                                                              |
| **Polyglot Persistence**   | Use multiple DBs/schemas to isolate data.                                    | When one DB schema can’t scale (e.g., `users` vs. `logs`).                    | PostgreSQL + Redis (for caching), Elasticsearch (for search).                       |
| **Circuit Breakers**       | Isolate failures in dependent services.                                      | When external services (e.g., `payment-gateway`) are prone to outages.         | Hystrix, Resilience4j.                                                               |
| **Modular Monolith**       | Structure monolith as pluggable modules (e.g., Spring Boot @ComponentScan).| When you need to delay full decomposition.                                    | Spring Modules, Go `main()` + plugins.                                               |

---

## **Key Takeaways**
1. **Measure before refactoring**: Use tools like `cloc`, `depject`, and DB metrics to identify pain points.
2. **Start small**: Decompose high-contention modules first (e.g., `payments` vs. `user-profile`).
3. **Document contracts**: Explicitly define API schemas, event schemas, and ownership boundaries.
4. **Automate safeguards**: Enforce limits (e.g., "no commit >50 files") and observe metrics proactively.
5. **Accept trade-offs**: Monoliths excel in simplicity; microservices add complexity. Choose based on team maturity and growth trajectory.

---
**Further Reading:**
- ["When to Use a Monolith"](https://martinfowler.com/articles/monolith-first.html) (Martin Fowler)
- ["The Monolith Trap"](https://www.oreilly.com/library/view/building-microservices/9781491950358/ch01.html) (Sam Newman)
- ["Dependency Hell"](https://www.igorkasyanchuk.com/2017/01/dependency-hell.html) (Igor Kasyanchuk)