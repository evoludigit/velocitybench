```markdown
---
title: "Governance Migration: Keeping Your Data in Sync Across Systems"
date: 2024-03-20
tags: ["database", "API", "migration", "data-governance", "patterns", "microservices"]
authors: ["backend-engineer"]
---
# Governance Migration: Keeping Your Data in Sync Across Systems

![Governance Migration Diagram](https://via.placeholder.com/800x500/0077B6/FFFFFF?text=Governance+Migration+Example)

Managing data across multiple systems—whether they’re databases, APIs, or even legacy applications—is a challenge most modern backend engineers face daily. **Governance migration** is a pattern that ensures data consistency, security, and compliance across systems when they evolve, merge, or are replaced. This becomes especially critical in microservices architectures, where data can live in disparate services, databases, or even external platforms.

This pattern isn’t about moving data from point A to point B—it’s about **managing data relationships and dependencies** while maintaining governance (i.e., access control, validation, and consistency rules) as systems change. In this guide, we’ll explore why governance migration matters, how to implement it, and the pitfalls to avoid with practical examples.

---

## **The Problem: When Data Governance Breaks**

Imagine this: your team is refactoring a monolithic backend into microservices. Each new service gets its own database schema, but customer data—once stored in a single `users` table—now spreads across `users_api.db`, `auth_service.postgres`, and even a `legacy_customer_management` database. Suddenly, you face these challenges:

1. **Inconsistent Data**
   - If the `users` API updates a user’s email but the `auth_service` hasn’t synced, you get race conditions or duplicate records.
   - Example: A user changes their email in the frontend, but if the `auth_service` reads from an old snapshot, authentication fails.

2. **Security Gaps**
   - A new microservice inherits an overly permissive database role, exposing sensitive fields like `SSN` to unauthorized services.
   - Example: An internal dashboard service accidentally queries `users.*` instead of just `{id, email}`.

3. **Compliance Risks**
   - GDPR requires right-to-erasure, but your `analytics_service` keeps a stale copy of user data in `users_backup.db` without proper synchronization.
   - Example: A user requests deletion, but their data lingers in a read-only archival table.

4. **Technical Debt**
   - Ad-hoc scripts for manually syncing tables lead to brittle workflows. When a schema changes, these scripts break.
   - Example: A SQL-based ETL job fails when a foreign key constraint is added to `users`.

5. **Operational Overhead**
   - Teams waste time debugging "ghost records" that appear at random times due to unsynchronized writes.
   - Example: An API user sees `user_id=123` in one response but `user_id=456` in another from the same call.

---
## **The Solution: Governance Migration Pattern**

Governance migration ensures that **data remains valid, secure, and consistent** as systems evolve—without requiring a big-bang rewrite. The pattern combines:

- **Idempotent Synchronization**: Ensures data consistency even after retries or concurrent updates.
- **Policy Enforcement**: Applies access controls and validation rules at every step.
- **Audit Trails**: Tracks changes for compliance and debugging.
- **Graceful Degradation**: Handles conflicts without breaking services.

At its core, governance migration involves:
1. **Defining Data Ownership**: Which service is the "source of truth" for a given entity (e.g., `users`).
2. **Implementing Sync Mechanisms**: How changes propagate to dependent systems.
3. **Enforcing Policies**: Rules for who can read/write/delete data.
4. **Monitoring**: Alerts on inconsistencies or policy violations.

---

## **Components of Governance Migration**

| Component          | Purpose                                                                 | Example Tools/Techniques                     |
|--------------------|-------------------------------------------------------------------------|-----------------------------------------------|
| **Data Ownership** | Identifies the authoritative source for each entity.                   | Database schemas, API contracts (OpenAPI).   |
| **Sync Layer**     | Handles bidirectional or unidirectional data propagation.             | Kafka, Debezium, Change Data Capture (CDC).   |
| **Policy Engine**  | Validates data before/after sync.                                      | OAuth2, Row-Level Security (RLS), Spanner.   |
| **Audit Log**      | Tracks changes for compliance and debugging.                           | PostgreSQL WAL logs, AWS CloudTrail.          |
| **Conflict Handler** | Resolves inconsistencies during sync.                                  | Last-write-wins, Manual review, 3-way merge. |

---

## **Code Examples**

### **1. Defining Data Ownership with API Contracts**
A well-designed OpenAPI spec enforces that the `users` API is the source of truth.

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: Users API
  version: 1.0.0
paths:
  /users/{id}:
    get:
      summary: "Authoritative user data (source of truth)."
      responses:
        '200':
          description: User details.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
          readonly: true  # Enforces write-only via API
```

### **2. Idempotent Sync with CDC (Debezium + Kafka)**
Use Debezium to capture database changes and sync them to dependent systems.

```java
// Kafka Consumer (Example: Listens to User changes)
public class UserChangeConsumer {
  @KafkaListener(topics = "users.changes")
  public void process(UserChangeEvent event) {
    String operation = event.getOperation();
    Map<String, Object> before = event.getBefore();
    Map<String, Object> after = event.getAfter();

    // Example: Update auth_service if the email changed
    if (operation.equals("UPDATE") && after.get("email") != before.get("email")) {
      updateAuthService(email, after.get("id"));
    }
  }

  private void updateAuthService(String email, String userId) {
    // Validates access and applies policies before update
    if (!isAdmin() && !userId.equals(getCurrentUserId())) {
      throw new SecurityException("Unauthorized update");
    }

    // Sync to auth_service (e.g., via REST or gRPC)
    RestTemplate restTemplate = new RestTemplate();
    restTemplate.exchange(
      "http://auth-service/users/{id}/email",
      HttpMethod.PUT,
      new HttpEntity<>(email),
      Void.class,
      userId
    );
  }
}
```

### **3. Policy Enforcement with Row-Level Security (PostgreSQL)**
Restrict access to sensitive fields at the database level.

```sql
-- Enable RLS on the users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create a policy to only allow admins to view SSN
CREATE POLICY user_sensitive_fields_policy ON users
  USING (current_user = 'admin' OR (current_user != 'admin' AND column_name != 'ssn'));
```

### **4. Audit Log with Database Triggers**
Log all changes to a separate `user_audit` table.

```sql
-- PostgreSQL trigger for audit logging
CREATE TABLE user_audit (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action TEXT NOT NULL,  -- "CREATE", "UPDATE", "DELETE"
  old_data JSONB,
  new_data JSONB,
  changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION audit_user_changes()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO user_audit (user_id, action, new_data) VALUES (NEW.id, 'CREATE', to_jsonb(NEW));
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO user_audit (user_id, action, old_data, new_data)
    VALUES (NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO user_audit (user_id, action, old_data)
    VALUES (OLD.id, 'DELETE', to_jsonb(OLD));
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION audit_user_changes();
```

### **5. Conflict Handler: Last-Write-Wins with Versioning**
Use a `version` column to detect and resolve conflicts.

```sql
-- Add a version column to users table
ALTER TABLE users ADD COLUMN version INTEGER DEFAULT 1;

-- Update logic with version check (SQL + Application Code)
BEGIN;
  -- Attempt to update the user
  UPDATE users
  SET email = 'new@example.com', version = version + 1
  WHERE id = '123e4567-e89b-12d3-a456-426614174000'
  AND version = (SELECT version FROM users WHERE id = '123e4567-e89b-12d3-a456-426614174000');

  IF NOT FOUND THEN
    -- Conflict: Another transaction updated the record
    RAISE EXCEPTION 'Conflict detected. Expected version % but got %',
      (SELECT version FROM users WHERE id = '123e4567-e89b-12d3-a456-426614174000'),
      (SELECT version FROM users WHERE id = '123e4567-e89b-12d3-a456-426614174000') - 1;
  END IF;
COMMIT;
```

---

## **Implementation Guide**

### **Step 1: Map Data Ownership**
- Document which service owns each entity (e.g., `users` → `users_api`).
- Use API contracts (OpenAPI/Swagger) to enforce ownership at the API level.
- Example: Label fields as `readonly` or `writes_only` in schemas.

### **Step 2: Choose a Sync Strategy**
| Strategy               | Use Case                                  | Tools                          |
|------------------------|-------------------------------------------|--------------------------------|
| **Unidirectional Sync** | One service is the source of truth.      | Debezium, Kafka                 |
| **Bidirectional Sync** | Changes propagate to all systems.        | Conflict-free replicated data types (CRDTs) |
| **Event-Driven**       | Async updates via events.                | Kafka, RabbitMQ                |
| **Periodic Sync**      | Low-frequency updates.                   | Cron jobs, Airflow              |

### **Step 3: Enforce Policies**
- **At the Database Level**: Use RLS (PostgreSQL), Spanner, or DynamoDB TTL.
- **At the API Level**: Validate requests with middleware (e.g., Spring Security).
- **At the Application Level**: Implement business rules (e.g., "Only admins can delete users").

### **Step 4: Implement Audit Logging**
- Use database triggers (PostgreSQL/MySQL) or application logs (ELK Stack).
- Store logs in a separate database or platform like AWS CloudTrail.

### **Step 5: Test for Consistency**
- Write integration tests that verify data syncs across services.
- Example:
  ```java
  @Test
  public void testUserUpdateSync() {
    // Step 1: Update via Users API
    User updatedUser = usersApi.updateEmail(userId, "new@example.com");

    // Step 2: Verify auth_service has synced
    User authUser = authService.getUser(userId);
    assertEquals("new@example.com", authUser.getEmail());

    // Step 3: Verify audit log
    assertEquals(1, userAuditRepo.count());
  }
  ```

### **Step 6: Monitor and Alert**
- Set up alerts for:
  - Sync failures (e.g., Kafka consumer lag).
  - Policy violations (e.g., unauthorized access).
  - Data inconsistencies (e.g., `SELECT COUNT(*) FROM users` vs. `SELECT COUNT(*) FROM auth_users`).
- Tools: Prometheus + Grafana, Datadog, or custom scripts.

---

## **Common Mistakes to Avoid**

1. **Assuming Sync is Automatic**
   - Don’t rely on "eventual consistency" without monitoring. Always verify data is synced before acting on it.
   - **Fix**: Add health checks (e.g., `/health/ready` endpoints) that validate sync status.

2. **Ignoring Conflicts**
   - Last-write-wins or manual resolution is necessary, but don’t bury conflicts in logs. Alert engineers proactively.
   - **Fix**: Use a conflict resolution dashboard (e.g., [Conflict Free Replicated Data Types](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type)).

3. **Overlooking Performance**
   - Real-time sync (e.g., CDC) can overload databases. Limit change streams to critical fields.
   - **Fix**: Use sampling or batch processing for non-critical updates.

4. **Skipping Policy Enforcement**
   - If you don’t validate data at sync time, you risk inconsistent policies (e.g., a service accepts invalid emails).
   - **Fix**: Run policy checks in both the source and target systems.

5. **Not Documenting Ownership**
   - Without clear ownership, teams argue over who "owns" a table or API.
   - **Fix**: Maintain a governance doc (e.g., in Confluence or a wiki) with:
     - Data owners.
     - Sync strategies.
     - Access policies.

6. **Underestimating Audit Needs**
   - If compliance requires 7-years of logs, don’t assume "we’ll figure it out later."
   - **Fix**: Design the audit system from day one with retention policies.

---

## **Key Takeaways**
✅ **Governance migration is about managing data relationships**, not just moving data.
✅ **Define ownership early** to avoid debates during refactoring.
✅ **Use sync layers (CDC, Kafka, etc.)** to automate consistency, but monitor them.
✅ **Enforce policies at every level** (database, API, application).
✅ **Audit everything**—compliance isn’t optional.
✅ **Test for consistency**—assume nothing will sync perfectly.
✅ **Monitor and alert**—don’t let silent failures accumulate.
✅ **Document everything**—future you (or your replacement) will thank you.

---

## **Conclusion: Start Small, Scale Smart**

Governance migration isn’t a one-time project—it’s an ongoing practice. Start by syncing critical data (e.g., users) and gradually expand. Use tools like Debezium for CDC, OpenAPI for ownership contracts, and PostgreSQL RLS for policy enforcement.

Remember: **No system is perfect**. Conflicts will happen. But with governance migration, you’ll have the tools to detect, resolve, and prevent them—keeping your data (and your peace of mind) intact.

---
**Next Steps:**
1. Audit your current systems: Which data needs governance?
2. Pick one entity (e.g., `users`) and implement basic sync + audit.
3. Gradually expand to other critical tables.

Happy migrating!
```