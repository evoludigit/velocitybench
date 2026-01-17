---

**[Pattern] Monolith Guidelines Reference Guide**
*Version 1.4*

---

## **Overview**
The **Monolith Guidelines** pattern ensures consistency, maintainability, and scalability when designing a **single-codebase monolith**—a centralized application structure where all components (services, modules, and subsystems) share a unified codebase, database, and deployment. Unlike microservices, a monolith consolidates functionality but requires strict architectural discipline to avoid technical debt. This guide outlines best practices for structuring, organizing, and managing monoliths effectively, including schema design, database conventions, query patterns, and integration boundaries.

Key benefits:
- Simplified **development workflows** (single dependency chain).
- **Easier debugging** (one runtime environment).
- **Lower operational overhead** (single deployment).
- **Faster iteration** (no cross-service coordination).

However, risks like **scaling bottlenecks** and **fragmented codebases** necessitate disciplined adherence to guidelines.

---

## **Schema Reference**
Monoliths require structured schema conventions to prevent drift. Below are mandatory and recommended domains.

### **1. Core Tables (Mandatory)**
| **Table Name**       | **Description**                                                                 | **Constraints**                                                                 |
|----------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `entities`           | Centralized registry of all domain objects (e.g., `User`, `Order`).         | - `id` (PK, UUIDv4)<br>- `name` (enum of supported schemas)<br>- `schema_version` |
| `_migration_log`     | Tracks database schema changes.                                              | - `migration_id` (PK)<br>- `applied_at` (timestamp)<br>- `schema_hash` |
| `audit_log`          | Audit trail for critical actions (CRUD, permission changes).               | - `log_id` (PK, UUIDv4)<br>- `event_type` (enum)<br>- `user_id` (FK)      |

---

### **2. Recommended Tables**
| **Table Name**       | **Description**                                                                 | **Constraints**                                                                 |
|----------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `metadata`           | Stores non-relational config/data (e.g., feature flags, static settings).   | - `key` (PK)<br>- `value` (JSON)<br>- `namespace` (e.g., `app`, `cache`)     |
| `event_queue`        | Buffers async events (e.g., notifications, workflow triggers).               | - `event_id` (PK)<br>- `payload` (JSON)<br>- `status` (enum: `pending`, `processed`) |
| `performance_metrics`| Captures runtime performance (latency, concurrency).                         | - `metric_name` (PK)<br>- `value` (numeric)<br>- `timestamp` (indexed)       |

---

### **3. Database Conventions**
| **Rule**               | **Detail**                                                                   |
|------------------------|------------------------------------------------------------------------------|
| **Naming**             | Use **snake_case** for tables/columns; **PascalCase** for enums/types.        |
| **Indexes**            | Explicitly declare indexes for queries >50ms. Add a `_idx_` suffix.         |
| **Foreign Keys**       | Enforce referential integrity. Use `ON DELETE CASCADE` sparingly.            |
| **Schema Migrations**  | Use versioned files (e.g., `002_add_users_table.sql`). Log via `_migration_log`.|

---

## **Implementation Details**

### **1. Architectural Boundaries**
Monoliths should **logically partition** code into **features** or **domains** using:
- **Feature Folders**: Self-contained modules (e.g., `/src/features/auth`, `/src/features/orders`).
- **Layered Architecture**:
  ```plaintext
  /src
    ├── api/       # REST/GraphQL endpoints
    ├── services/  # Business logic (use DTOs for input/output)
    ├── repositories/  # Database layer (avoid active record)
    └── utils/     # Shared helpers (validation, logging)
  ```
- **Explicit Dependencies**: Use `import` graphs to visualize coupling. Tools: [`depcheck`](https://github.com/depcheck/depcheck).

---

### **2. Query Patterns**
Monoliths often suffer from **N+1 queries**. Mitigate with:

#### **A. Data Fetching Strategies**
| **Pattern**            | **Use Case**                                                                 | **Example**                                                                 |
|------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Batch Loading**      | Fetch related entities in a single query.                                   | `SELECT * FROM orders WHERE user_id IN (1, 2, 3);`                         |
| **Eager Loading**      | Pre-load relationships (ORM-specific).                                      | Prisma: `Order.findMany({ include: { items: true } })`                      |
| **GraphQL**            | Dynamic query shaping (avoid over-fetching).                                | Resolve fields lazily in resolvers.                                         |
| **CQRS**               | Separate read/write models (e.g., denormalized `user_profiles` view).       | Read: `SELECT * FROM user_profiles_v1;`                                    |

---

#### **B. Query Examples**
**1. Batch User Orders (PostgreSQL)**
```sql
SELECT u.*, o.*
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
ORDER BY o.created_at DESC
LIMIT 100;
```
**2. GraphQL Resolver (TypeScript)**
```typescript
import { User, Order } from './models';

export const userResolver = {
  orders: async (parent: User) => {
    return Order.findMany({ where: { userId: parent.id }, include: { items: true } });
  },
};
```

**3. Denormalized View (CQRS)**
```sql
CREATE MATERIALIZED VIEW user_orders_summary AS
SELECT
  u.id AS user_id,
  u.email,
  COUNT(o.id) AS order_count,
  SUM(o.total) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;
```

---

### **3. Scaling Monoliths**
| **Challenge**          | **Solution**                                                                 |
|------------------------|------------------------------------------------------------------------------|
| **Database Bottleneck** | Shard by feature (e.g., `orders_2023`, `users_2023`).                       |
| **Cold Starts**        | Use **warm-up requests** or **sidecars** (e.g., Redis caching).             |
| **Code Bloat**         | Enforce **module size limits** (e.g., <10K lines).                          |
| **Deployment Risk**    | Canary releases with **feature flags** (`metadata` table).                   |

---

## **Requirements Checklist**
| **Category**          | **Requirement**                                                              | **Tool/Reference**                          |
|-----------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Code**              | Static analysis (cyclomatic complexity <10).                                 | ESLint, SonarQube                           |
| **Database**          | Schema migrations logged in `_migration_log`.                                 | Flyway, Liquibase                           |
| **Testing**           | 80%+ code coverage (unit + integration).                                     | Jest, Cypress                               |
| **Monitoring**        | Track query performance in `performance_metrics`.                            | Prometheus, Datadog                        |
| **Security**          | Input validation (e.g., Zod, Joi) and DB sanitization.                      | SQL injection guides, OWASP Top 10          |

---

## **Related Patterns**
1. **Layered Architecture**
   - Separates concerns into API, services, and persistence layers.
   - *Reference*: [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html).

2. **CQRS**
   - Decouples read/write operations to optimize performance.
   - *Example*: Use for analytics dashboards.

3. **Feature Toggles**
   - Gradually roll out changes without deploying the entire monolith.
   - *Tool*: LaunchDarkly, Unleash.

4. **Database Sharding**
   - Horizontal scaling for read-heavy monoliths.
   - *Strategy*: Shard by tenant or time.

5. **Modular Monolith**
   - Evolve toward microservices by **encapsulating** features (e.g., Docker containers per module).
   - *Tool*: [Modular Monolith Guide](https://betterprogramming.pub/modular-monoliths-7f04d50e6156).

---
**See Also**:
- [Database Perils of the Monolith Anti-pattern](https://martinfowler.com/bliki/Monolith.html)
- [How Netflix Scales Monoliths](https://netflixtechblog.com/why-netflix-switched-from-microservices-to-a-modular-monolith-16e5c08740d6)