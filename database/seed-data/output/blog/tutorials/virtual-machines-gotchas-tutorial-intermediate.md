```markdown
# **Virtual Machines Gotchas: The Hidden Pitfalls in Distributed Monoliths**

*Building distributed systems with shared databases is hard. This post explores the "Virtual-Machines Gotchas" pattern—how to avoid the sneaky problems that arise when your microservices pretend to be independent but still rely on shared DBs. We’ll cover real-world pain points, solutions, and hard-learned lessons from architecting large-scale systems.*

---

## **Introduction: The Illusion of Independence**

Monolithic applications are straightforward: one codebase, one database, one responsibility. But as systems grow, teams break monoliths into microservices—usually because they want *independence*. "Each service owns its own database," we tell ourselves. "Now we can scale, deploy, and change things without coordination!"

Sounds great… until you realize that most "microservices" still *share* the database. Maybe not *all* tables, but often enough that the system still behaves like a monolith—just with more moving parts. This is the **"virtual-machines gotchas"** problem: the hidden technical debt of pretending independence exists when it doesn’t.

In this post, we’ll dissect:
- Why shared databases undermine autonomy.
- How seemingly innocent refactorings create subtle bugs.
- Practical ways to detect and fix "virtual-machine" anti-patterns.
- Code patterns to enforce real separation.

---

## **The Problem: The Shared Database Anti-Pattern**

The "shared database" pattern is so common that many teams don’t even recognize it as an anti-pattern. Here’s how it manifests:

### **1. The False Sense of Freedom**
Teams refactor a monolith into services but keep a single database, splitting tables by "business domain." Example:
- `users` table → `auth_service`
- `orders` table → `checkout_service`
- `products` table → `inventory_service`

**Problem:** Each service *thinks* it can deploy independently, but all services are coupled through the shared schema. A schema migration in one service blocks others.

### **2. Cascading Failures**
If `auth_service` crashes, the entire system goes down—even for "independent" features. Worse, if `checkout_service` starts failing due to a database timeout, it might starve the users table, causing `auth_service` to time out too.

### **3. Hidden Dependencies**
"Oh, we migrated `users` to a different DB!" Except—everywhere in the codebase, we still use `SELECT * FROM users`. Later, you discover the new service can’t access its table because the old schema is still referenced in cached SQL queries.

### **4. The "Just Share the DB" Workaround**
Teams mask these problems with ad-hoc solutions:
- **Service A** polls **Service B** for data instead of querying the DB directly.
- **Service C** calls a "gateway" service to abstract the DB schema.
- Groups of services share a "private" DB connection pool.

**Result:** A fragile, undocumented spaghetti architecture.

### **5. Consistency Nightmares**
Eventual consistency is hard enough when DBs are separate. With shared DBs, you get:
- **Temporary inconsistencies** (e.g., `checkout_service` sees a `user` record that was deleted in `auth_service`).
- **Deadlocks** (services lock tables they shouldn’t own).
- **Data races** (services overwrite each other’s changes).

---

## **The Solution: Enforce True Independence**

The goal isn’t to *avoid* sharing databases—it’s to **make sharing explicit and controlled**. We’ll use the **"Virtual-Machines Gotchas"** pattern to:
1. **Detect shared database usage** (static analysis).
2. **Refactor to explicit dependencies** (APIs, events, or separate DBs).
3. **Add safeguards** to prevent regression (e.g., migration blockers).

---

## **Components/Solutions**

### **1. Schema Ownership Enforcement**
**Problem:** Services query tables they don’t "own."
**Solution:** Enforce schema boundaries via:
- **Database-level permissions** (only grant read/write to owned tables).
- **Code-level restrictions** (ban `SELECT * FROM users` in `checkout_service`).

**Example (Python with SQLAlchemy):**
```python
# checkout_service/models.py
from sqlalchemy import MetaData, inspect

def assert_table_ownership(model):
    """Prevent accessing tables not owned by this service."""
    owned_tables = {"orders", "payments"}  # Service ownership
    inspector = inspect(model.metadata)
    for table in inspector.tables:
        if table.name not in owned_tables:
            raise RuntimeError(f"Unauthorized access to '{table.name}'")

class UserModel(Base):
    __tablename__ = "users"
    # ...
    __table_args__ = {"schema": "auth"}  # Explicit schema for auditing

# This will fail at runtime:
# assert_table_ownership(UserModel)  # "Unauthorized access to 'users'"
```

### **2. Wrappers for Shared Access**
**Problem:** "OH, just let them read from the shared `users` table—it’s okay."
**Solution:** Add a **wrapper layer** to track usage and enforce rules.

```python
# auth_service/wrappers.py
class UserWrapper:
    def __init__(self, user):
        self.user = user

    @classmethod
    def get(cls, user_id: int):
        # Log the caller (e.g., checkout_service)
        caller = get_caller_service()  # From middleware
        print(f"[AUDIT] {caller} accessed user {user_id}")
        return cls(User.query.get(user_id))

    def check_permission(self):
        if self.user.role != "admin":
            raise PermissionError("Not authorized")

# Usage in checkout_service
user = UserWrapper.get(123)
user.check_permission()  # Blocks unauthorized access
```

### **3. Database Migration Guardrails**
**Problem:** "We’ll just run migrations in parallel!"
**Solution:** **Block migrations** if a service would break.

```sql
-- PostgreSQL: Create a migration lock table
CREATE TABLE migration_locks (
    service_name VARCHAR(50) PRIMARY KEY,
    locked_until TIMESTAMP
);

-- Before running a migration:
INSERT INTO migration_locks VALUES ('checkout_service', NOW() + INTERVAL '5 minutes')
ON CONFLICT DO NOTHING;

-- Check if a service is locked:
SELECT EXISTS (
    SELECT 1 FROM migration_locks
    WHERE service_name = 'auth_service'
    AND locked_until > NOW()
);
```

### **4. Event-Driven Fallbacks**
**Problem:** Services need data *immediately*, not via async events.
**Solution:** Use **materialized views** or **replication slots** to keep critical data in sync.

**Example (Materialized View for Orders):**
```sql
-- In checkout_service's DB
CREATE MATERIALIZED VIEW mv_orders_with_user AS
SELECT o.*, u.username
FROM orders o
JOIN users u ON o.user_id = u.id;

-- Refresh periodically (or on change via triggers)
REFRESH MATERIALIZED VIEW mv_orders_with_user;

-- Now checkout_service can query mv_orders_with_user without hitting auth_service's DB.
```

---

## **Implementation Guide**

### **Step 1: Audit Your Current State**
Run a **database usage analyzer** to find shared tables:
```bash
# Example using pg_stat_statements (PostgreSQL)
SELECT schemaname, tablename, calls
FROM pg_stat_statements
WHERE schemaname NOT IN ('public', 'auth', 'checkout')
ORDER BY calls DESC;
```

### **Step 2: Enforce Ownership**
- **Permissioning:** Restrict DB access using roles (e.g., `checkout_service` only has `SELECT` on `orders`).
- **Code Checks:** Add static analysis (e.g., pylint rules to detect unauthorized queries).

### **Step 3: Add Wrappers**
Replace direct DB calls with service-specific wrappers (see above).

### **Step 4: Test Failures**
- **Chaos Engineering:** Simulate DB outages to test fallback paths.
- **Permission Tests:** Verify wrappers block unauthorized access.

### **Step 5: Automate Safeguards**
- **Pre-Migration Checks:** Block CI/CD if a service is locked.
- **Alerting:** Monitor for unauthorized queries.

---

## **Common Mistakes to Avoid**

### **1. "We’ll Just Use a Read Replica"**
- **Problem:** Shared read replicas introduce staleness and complexity.
- **Solution:** Use **logical replication** or **change data capture (CDC)** for async consistency.

### **2. "We’re Fine with Timestamps"**
- **Problem:** Relying on `created_at` for ordering is fragile with shared DBs.
- **Solution:** Use **distributed transactions** (Saga pattern) or **outbox tables**.

### **3. "We’ll Cache Everything"**
- **Problem:** Caching shared data creates more inconsistency.
- **Solution:** Cache only within a service’s boundary.

### **4. "We’ll Fix It Later"**
- **Problem:** Shared DBs create "technical debt" that compounds.
- **Solution:** Treat shared DBs as **technical debt to be repaid**.

---

## **Key Takeaways**

✅ **Shared databases break independence**—treat them as anti-patterns unless absolutely necessary.
✅ **Enforce ownership** with permissions, code checks, and wrappers.
✅ **Use wrappers** to track and control access to shared data.
✅ **Block migrations** if a service would break.
✅ **Test failures**—shared DBs hide cascading risks.
✅ **Prefer event-driven or replicated data** over shared queries.

---

## **Conclusion: Virtual Machines Gotchas → Real Independence**

The "virtual-machines gotchas" pattern isn’t about avoiding shared databases—it’s about **making their risks explicit**. By adding safeguards, wrappers, and automated checks, you can:
- Detect shared dependencies early.
- Prevent regressions in shared usage.
- Gradually refactor toward true independence.

**Next steps:**
1. Audit your shared DBs today.
2. Add one safeguard (e.g., permission checks).
3. Start small and scale the pattern.

Shared databases are a **temporary solution**, not a design goal. The path to real microservices begins with awareness—and this pattern gives you the tools to see what’s hidden.

---
*Want to dive deeper? Check out:*
- [PostgreSQL Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html)
- [Saga Pattern for Distributed Transactions](https://microservices.io/patterns/data/saga.html)
- [Database Permissioning Guide](https://www.postgresql.org/docs/current/ddl-priv.html)
```