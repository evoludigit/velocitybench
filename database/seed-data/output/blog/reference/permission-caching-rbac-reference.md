# **[Pattern] Permission Caching Role-Based Access Control (RBAC) Reference Guide**

---

## **Overview**
The **Permission Caching RBAC** pattern in FraiseQL optimizes permission checks for large-scale enterprise applications by leveraging three distinct caching layers while maintaining strict security compliance. This approach enables **sub-millisecond (sub-0.3ms) permission resolution** without compromising granular access control. The solution combines:
- **Request-level caching** for real-time permission validation,
- **UNLOGGED table caching** for high-frequency permission lookups,
- **Hierarchical role-based caching** with **domain versioning** to ensure consistency across dynamic organizational structures.

This guide explains implementation details, schema design, query patterns, and integration considerations.

---

## **Key Concepts**

| **Layer**               | **Purpose**                                                                 | **Performance Impact**                     | **Key Features**                                                                 |
|--------------------------|-----------------------------------------------------------------------------|--------------------------------------------|---------------------------------------------------------------------------------|
| **Request-Level Cache**  | Validates permissions per HTTP request at sub-millisecond latency.          | Near-instant (0.1–0.3ms).                  | Thread-safe in-memory cache with TTL (Time-to-Live) for invalidation.            |
| **UNLOGGED Table Cache** | Stores role-to-permission mappings for low-latency reads without WAL logs.  | Ultra-low latency (synchronized via Figure). | Atomic updates via transactional Figure calls; supports incremental refreshes.  |
| **Hierarchical Cache**   | Cache domain-specific role hierarchies (e.g., `Department → Team → User`).   | Scalable permission inheritance.           | Versioned to handle concurrent structural changes without cascading invalidations. |

---

## **Schema Reference**

### **Core Tables**
| Table Name          | Purpose                                                                                     | Key Fields                                                                                     | Cache Strategy                     |
|---------------------|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|-------------------------------------|
| `users`             | Stores end-user accounts and their assigned roles.                                         | `user_id (PK)`, `domain_id (FK)`, `role_id (FK)`                                             | Request-level + UNLOGGED            |
| `roles`             | Defines role-specific permissions (e.g., `admin`, `editor`).                              | `role_id (PK)`, `domain_id (FK)`, `name`, `permissions (JSONB array)`.                       | UNLOGGED + Hierarchical Cache       |
| `permissions`       | Atomic permission definitions (e.g., `read_data`, `manage_users`).                          | `permission_id (PK)`, `name`, `description`.                                                   | Static (read-only).                 |
| `role_hierarchy`    | Tracks parent-child role relationships (e.g., `manager` → ` employee`).                    | `role_id (PK)`, `parent_role_id (FK)`, `domain_id (FK)`.                                     | Hierarchical Cache (versioned).     |
| `domain_versions`   | Tracks structural changes to role hierarchies per domain.                                   | `version_id (PK)`, `domain_id (FK)`, `created_at`, `expires_at`.                             | Optimized for domain-specific sync.  |

### **Auxiliary Tables**
| Table Name          | Purpose                                                                                     | Notes                                                                                         |
|---------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `cache_invalidation_queue` | Manages stale cache entries (e.g., role deletions, permission updates).               | Polls via a background worker (recommended: 10s interval).                                    |
| `permission_cache_meta`  | Tracks hit/miss rates, cache size, and domain-specific TTL adjustments.                   | Used for auto-scaling and monitoring.                                                         |

---

## **Query Examples**

### **1. Request-Level Permission Check**
**Use Case:** Validate a user’s permissions for a resource (e.g., API endpoint) **per request**.
**Query:**
```sql
-- Pseudocode (implemented in application layer via middleware)
SELECT EXISTS (
    SELECT 1
    FROM permissions p
    JOIN roles r ON JSONB_CONTAINS(r.permissions, p.permission_id::text)
    JOIN users u ON u.role_id = r.role_id
    WHERE u.user_id = '12345'
      AND p.name = 'read_project_42'
);
```
**Optimization:**
- FraiseQL caches this result in a **request-scoped map** (e.g., Redis or in-memory cache).
- **Latency:** ~0.2ms (cached), ~5ms (uncached).

---

### **2. UNLOGGED Role-Permission Lookup**
**Use Case:** Retrieve all permissions for a role **without WAL overhead**.
**Query:**
```sql
-- UNLOGGED table for atomic, low-latency reads
SELECT permissions
FROM UNLOGGED roles
WHERE role_id = 'manager'
  AND domain_id = 'acme_company';
```
**Implementation Notes:**
- Use **Figure** for synchronous UNLOGGED updates:
  ```javascript
  await figure.query(`
    INSERT INTO UNLOGGED roles (role_id, domain_id, permissions)
    VALUES ('manager', 'acme_company', ARRAY['read_data', 'manage_users'])
    ON CONFLICT (role_id, domain_id) DO UPDATE SET permissions = EXCLUDED.permissions
  `);
  ```
- **Latency:** ~1ms (Figure-synchronized).

---

### **3. Hierarchical Role Inheritance**
**Use Case:** Resolve all inherited permissions for a user (e.g., `employee` → `team_member` → `admin`).
**Query:**
```sql
WITH RECURSIVE role_tree AS (
    SELECT role_id, permissions
    FROM roles
    WHERE role_id = 'employee' AND domain_id = 'acme_company'

    UNION ALL

    SELECT r.role_id, r.permissions
    FROM roles r
    JOIN role_hierarchy h ON r.role_id = h.child_role_id
    JOIN role_tree rt ON h.parent_role_id = rt.role_id
    WHERE rt.domain_id = 'acme_company'
)
SELECT array_agg(DISTINCT p.name)
FROM role_tree rt
JOIN JSONB_ARRAY_ELEMENTS(rt.permissions) p ON true;
```
**Optimization:**
- **Hierarchical Cache:** Store pre-computed permission sets per domain version (e.g., `domain_1_v2`).
- **Invalidation:** Trigger cache refresh on `domain_versions.expires_at` or manual `PURGE`:
  ```sql
  DELETE FROM hierarchical_cache
  WHERE domain_id = 'acme_company' AND version_id < (SELECT MAX(version_id) FROM domain_versions WHERE domain_id = 'acme_company');
  ```

---

### **4. Domain-Specific Cache Invalidation**
**Use Case:** Invalidate caches when a role hierarchy changes (e.g., `manager` promoted to `parent_of` `director`).
**Steps:**
1. **Update hierarchy:**
   ```sql
   INSERT INTO role_hierarchy (role_id, parent_role_id, domain_id)
   VALUES ('director', 'manager', 'acme_company')
   ON CONFLICT DO NOTHING;
   ```
2. **Increment domain version:**
   ```sql
   INSERT INTO domain_versions (domain_id, expires_at)
   VALUES ('acme_company', NOW() + INTERVAL '5 minutes')
   ON CONFLICT (domain_id) DO UPDATE SET expires_at = NOW() + INTERVAL '5 minutes';
   ```
3. **Trigger cache refresh:**
   - Poll `cache_invalidation_queue` in a worker:
     ```sql
     -- Pseudocode
     WHILE TRUE:
         DELETE FROM cache_invalidation_queue WHERE processed = FALSE;
         -- Refresh hierarchical_cache for affected domains
     ```

---

## **Performance Guidelines**
| **Operation**               | **Target Latency** | **Throughput**               | **Notes**                                                                 |
|-----------------------------|--------------------|------------------------------|---------------------------------------------------------------------------|
| Request-level check         | <0.3ms             | 10K+ RPS                     | Cache hits only; cold starts ~5ms.                                        |
| UNLOGGED lookup             | <1ms               | 50K+ RPS                     | Synchronized via Figure; no WAL delay.                                    |
| Hierarchical resolution     | <3ms               | 1K–5K RPS                    | Prefer domain-Scoped Caches; avoid recursive scans for deep hierarchies. |
| Cache invalidation          | <500ms             | Batch-processed              | Use workers; avoid blocking application traffic.                           |

---

## **Integration Considerations**
### **1. Middleware Layer**
- **FraiseQL Middleware:** Add a `PermissionCheckMiddleware` to validate permissions before processing requests:
  ```typescript
  // Example (Node.js)
  app.use(async (req, res, next) => {
      const user = req.user; // Authenticated user from JWT/OAuth
      const allowed = await checkPermission(user.user_id, req.path, req.method);
      if (!allowed) return res.status(403).send('Forbidden');
      next();
  });
  ```
- **Cache Invalidation:** On role/permission updates, emit an event to a queue (e.g., Kafka) or trigger a worker.

### **2. Database-Side Optimizations**
- **UNLOGGED Tables:** Limit to role-permission mappings (avoid overloading with reference data).
- **Partitioning:** Shard `domain_versions` by `domain_id` for large organizations.
- **Monitoring:** Track cache hit ratios:
  ```sql
  SELECT
      domain_id,
      cache_hits,
      cache_misses,
      cache_hits / (cache_hits + cache_misses) AS hit_ratio
  FROM permission_cache_meta
  GROUP BY domain_id;
  ```

### **3. Security Hardening**
- **Least Privilege:** Restrict `cache_invalidation_queue` writes to admin roles only.
- **Audit Logs:** Log all role hierarchy changes:
  ```sql
  INSERT INTO audit_logs (action, entity, changed_by)
  SELECT 'UPDATE_ROLE_HIERARCHY', r.role_id, CURRENT_USER
  FROM role_hierarchy r
  WHERE r.role_id IN (SELECT NEW.role_id FROM cte_role_updates);
  ```

---

## **Related Patterns**
1. **[Attribute-Based Access Control (ABAC)](https://docs.fraiseql.com/patterns/abac)**
   - *Use Case:* Combine RBAC with dynamic attributes (e.g., `user.department = "finance"`).
   - *Synergy:* Cache ABAC policies separately and merge with RBAC results.

2. **[Multi-Tiered Authorization](https://docs.fraiseql.com/patterns/multi-tier)**
   - *Use Case:* Layer RBAC on top of **row-level security (RLS)** for database-level granularity.
   - *Example:*
     ```sql
     ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
     CREATE POLICY project_access ON projects
     USING (department_id = current_setting('user.department'));
     ```

3. **[Event-Driven Cache Invalidation](https://docs.fraiseql.com/patterns/event-driven)**
   - *Use Case:* Replace polling-based invalidation with Kafka/RabbitMQ pub/sub for real-time sync.
   - *Implementation:*
     ```sql
     -- Subscribe to "role_updated" topic
     INSERT INTO cache_invalidation_queue (event_type, entity_id)
     SELECT 'ROLE_UPDATE', NEW.role_id
     FROM cte_role_updates;
     ```

4. **[Permission Benchmarking](https://docs.fraiseql.com/patterns/benchmarking)**
   - *Use Case:* Stress-test cache layers under 100K+ concurrent requests.
   - *Tools:* Use **FraiseQL’s `EXPLAIN ANALYZE`** to profile UNLOGGED queries.

---

## **Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------|------------------------------------------------------------------------------|
| High request-level cache misses     | Stale TTL or frequent role changes.      | Reduce TTL (e.g., 10s) or implement event-driven invalidation.               |
| UNLOGGED table lag                   | Figure replication delay.               | Increase Figure worker pool or use local UNLOGGED cache with async sync.     |
| Hierarchical cache inconsistency    | Version skew across domains.            | Audit `domain_versions.expires_at`; force refresh with `PURGE`.               |
| Permission checks >5ms               | Missing cache or recursive hierarchy.   | Pre-warm cache for expected queries; flatten deep hierarchies.              |

---

## **Migration Path**
1. **Phase 1: Enable Request-Level Cache**
   - Add middleware and cache role-permission mappings in-memory.
2. **Phase 2: Adopt UNLOGGED Tables**
   - Migrate static role-permission data to UNLOGGED tables.
3. **Phase 3: Hierarchical Caching**
   - Implement domain-Scoped caches with versioning.
4. **Phase 4: Auto-Scaling**
   - Use `permission_cache_meta` to adjust TTL dynamically based on hit ratios.

---
**Note:** For production deployments, consult the [FraiseQL Enterprise Guide](https://docs.fraiseql.com/enterprise) for cluster-specific tuning (e.g., Figure replication settings).