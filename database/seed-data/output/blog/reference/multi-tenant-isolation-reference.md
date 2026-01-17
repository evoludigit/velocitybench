# **[Pattern] Multi-Tenant Isolation Reference Guide**
*Secure and Scalable Data Partitioning in FraiseQL*

---

## **1. Overview**
Multi-Tenant Isolation in FraiseQL enables applications to serve multiple independent tenants while strictly enforcing data separation. This pattern ensures:
- **Security**: Tenant data remains inaccessible to unauthorized users.
- **Performance**: Queries are optimized via compile-time filtering, RLS policies, and tenant-aware caching.
- **Flexibility**: Supports embedded tenant IDs (columns), schema-per-tenant, or hybrid isolation.

FraiseQL enforces isolation at the database level using:
- Tenant ID columns (compile-time injection).
- Row-Level Security (RLS) policies.
- Optional schema partitioning.
- Tenant-specific caching layers.

This guide covers implementation details, schema design, query patterns, and integration considerations.

---

## **2. Key Concepts**
| Concept                     | Description                                                                                                                                                     | Example                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Tenant ID Column**        | A column (typically `tenant_id`) that embeds tenant context in records.                                                                                          | `users(tenant_id UUID NOT NULL, user_data JSONB)`                                            |
| **Compile-Time Filtering**  | FraiseQL injects `WHERE tenant_id = current_user_tenant` during query compilation, reducing runtime overhead.                                                  | `SELECT * FROM users WHERE tenant_id = <injected_value>` (never evaluated at runtime)      |
| **Row-Level Security (RLS)** | PostgreSQL RLS policies enforce tenant-specific row access.                                                                                                     | `CREATE POLICY tenant_policy ON orders FOR ALL USING (tenant_id = current_user_tenant);`   |
| **Schema-Per-Tenant**       | Tenants are isolated in separate schemas (e.g., `tenant_123.users`). Enabled via `tenant_schema_config`.                                                     | `CREATE SCHEMA IF NOT EXISTS tenant_456; CREATE TABLE tenant_456.users (...)`               |
| **Tenant-Aware Caching**    | Cache layer prefixes keys with `tenant_id` (e.g., `tenant_456:user:123`).                                                                                     | `REDIS_KEY = f"tenant:{tenant_id}:user:{user_id}"`                                          |
| **Hybrid Isolation**        | Combines tenant_id columns + schema separation for high-security scenarios.                                                                                 | `users(tenant_id UUID, ...) + schema tenant_456.users`                                      |

---

## **3. Schema Reference**
### **3.1 Core Tenant Isolation Schema**
| Table            | Tenant ID Column | Notes                                                                                     |
|------------------|------------------|-------------------------------------------------------------------------------------------|
| `tenants`        | `id` (UUID)      | Stores tenant metadata (e.g., `subdomain`, `plan`).                                         |
| `users`          | `tenant_id` (UUID)| Embedded tenant reference. Example: `users(tenant_id UUID REFERENCES tenants(id), ...)`. |
| `orders`         | `tenant_id` (UUID)| Shared table with tenant filtering.                                                     |

### **3.2 Schema-Per-Tenant Example**
```sql
-- Tenant metadata (shared)
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    subdomain VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Per-tenant tables (e.g., tenant_456.users)
CREATE SCHEMA tenant_456;
CREATE TABLE tenant_456.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    tenant_id UUID REFERENCES tenants(id)
);
```

### **3.3 Hybrid Model (Tenant Column + Schema)**
```sql
-- Shared table with tenant_id column
CREATE TABLE hybrid_orders (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id)
);

-- Schema-scoped tenant-specific data
CREATE SCHEMA tenant_abc;
CREATE TABLE tenant_abc.private_data (
    id SERIAL PRIMARY KEY,
    content JSONB,
    tenant_id UUID DEFAULT (current_setting('app.tenant_id')::UUID)
);
```

---

## **4. Query Examples**
### **4.1 Compile-Time Filtering (Embedded Tenant ID)**
FraiseQL injects `WHERE tenant_id = current_user_tenant` during query parsing.
```go
// Go SDK: Set tenant context
ctx := context.WithValue(ctx, "tenant_id", "123e4567-e89b-12d3-a456-426614174000")

// Database query (automatically filtered)
rows, err := db.Query(ctx, "SELECT * FROM users WHERE name = $1", "Alice")
```

### **4.2 Row-Level Security (RLS) Policies**
```sql
-- Enable RLS on a table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Define tenant-specific policy
CREATE POLICY tenant_orders_policy ON orders
    USING (tenant_id = current_setting('app.tenant_id')::UUID);
```

### **4.3 Schema-Per-Tenant Queries**
```sql
-- Dynamically generate schema-qualified queries
tenantId := "456"
query := fmt.Sprintf(`SELECT * FROM %s.users WHERE id = $1`, tenantId)
row := db.QueryRow(query, userId)
```

### **4.4 Hybrid Query (Tenant Column + Schema)**
```sql
-- Mix of shared and scoped data
SELECT u.id, o.amount, td.content
FROM users u
JOIN orders o ON u.id = o.user_id AND o.tenant_id = current_setting('app.tenant_id')
JOIN tenant_abc.private_data td ON u.id = td.tenant_id;
```

---

## **5. Tenant Context Propagation**
FraiseQL supports multiple ways to inject tenant context:

| Method               | Usage                                                                                     | Example                                                                                     |
|----------------------|-----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Request Header**   | Pass `X-Tenant-ID` in HTTP requests.                                                   | `header.Set("X-Tenant-ID", tenantId)`                                                      |
| **Database Setting** | Set via `SET LOCAL app.tenant_id = '123e4567-...'` during connection.                   | `db.Exec("SET LOCAL app.tenant_id = $1", tenantId)`                                         |
| **Go Context**       | Inject into `context.Context` for SDK queries.                                           | `ctx := context.WithValue(ctx, "tenant_id", tenantId)`                                      |
| **Middleware**       | FraiseQL middleware auto-detects tenant ID from context.                                 | `app.Use(TenantMiddleware)`                                                              |

---

## **6. Performance Considerations**
| Technique                     | Benefit                                                                                     | Configuration                                                              |
|-------------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Compile-Time Filtering**    | Reduces runtime query overhead by eliminating tenant_id checks.                            | Enable via `fraiseql.enable_compile_filtering = true`                     |
| **Schema Partitioning**       | Faster scans (no cross-tenant joins) but higher schema management cost.                      | Use for high-security tenants (>100).                                    |
| **Tenant-Aware Caching**      | Caches tenant-specific data separately (e.g., Redis keys prefixed with tenant_id).         | `cache_key = fmt.Sprintf("tenant:%s:%s", tenantId, userId)`               |
| **Indexing**                  | Add indexes on `tenant_id` for faster filtering.                                           | `CREATE INDEX idx_tenant_orders ON orders(tenant_id)`                       |

---

## **7. Error Handling**
| Error Type               | Cause                                                                                     | Solution                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Tenant Not Found**     | Invalid `tenant_id` in context.                                                          | Validate tenant existence: `SELECT 1 FROM tenants WHERE id = $1`.                          |
| **Permission Denied**    | RLS policy blocks access to tenant data.                                                 | Ensure `current_setting('app.tenant_id')` matches the queried tenant.                       |
| **Schema Not Found**     | Schema-per-tenant query targets non-existent schema.                                    | Use dynamic schema resolution (e.g., `tenant_$1.users`).                                    |
| **Cache Invalidation**   | Stale data due to concurrent tenant changes.                                             | Implement cache invalidation triggers (e.g., `ON UPDATE` triggers for `tenants`).            |

---

## **8. Related Patterns**
| Pattern                          | Description                                                                                     | Integration Notes                                                                          |
|----------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **[Shared Database, Isolated Tables]** | Single database with tenant_id columns (default in FraiseQL).                                  | Combine with RLS for fine-grained access control.                                          |
| **[Schema Per Tenant]**          | Tenants in separate schemas (high isolation, higher overhead).                                  | Use for extreme security/compliance requirements.                                        |
| **[Database Per Tenant]**        | Each tenant has its own database (max isolation, lowest scalability).                          | Requires FraiseQL’s `multi_db` plugin.                                                  |
| **[Event Sourcing for Tenancy]** | Append-only tenant-specific events (e.g., `TenantCreated`, `OrderPlaced`).                   | Pair with CQRS for read models.                                                            |
| **[Tenant-Aware Authentication]** | OAuth2/OpenID scopes scoped to tenants.                                                      | Use `fraiseql.auth.tenant_scope` middleware.                                              |

---

## **9. Migration Guide**
### **9.1 From Shared Tables to Schema-Per-Tenant**
```sql
-- Step 1: Add tenant_id column if missing
ALTER TABLE users ADD COLUMN tenant_id UUID;

-- Step 2: Migrate data to schemas
CREATE SCHEMA tenant_123;
INSERT INTO tenant_123.users SELECT * FROM users WHERE tenant_id = '123'::UUID;

-- Step 3: Update app code to use qualified names
-- Old: db.Query("SELECT * FROM users")
-- New: db.Query("SELECT * FROM tenant_123.users")
```

### **9.2 Enabling RLS on Existing Tables**
```sql
-- 1. Add tenant_id column (if not present)
ALTER TABLE orders ADD COLUMN tenant_id UUID;

-- 2. Backfill tenant_id (e.g., via app logic)
UPDATE orders SET tenant_id = current_user_tenant;

-- 3. Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 4. Create policy
CREATE POLICY tenant_orders_policy
    ON orders USING (tenant_id = current_setting('app.tenant_id')::UUID);
```

---

## **10. Troubleshooting**
| Issue                          | Diagnosis                                                                                 | Fix                                                                                       |
|--------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Queries returning cross-tenant data** | Check if `fraiseql.enable_compile_filtering` is enabled.                                  | Enable: `fraiseql.enable_compile_filtering = on` in `.env`.                              |
| **RLS policies not working**    | Verify `current_setting('app.tenant_id')` matches the queried tenant.                     | Log tenant context: `LOG current_setting('app.tenant_id')` in PostgreSQL.               |
| **Schema-per-tenant queries failing** | Confirm schema exists and user has `USAGE` privilege.                                    | Grant privileges: `GRANT USAGE ON SCHEMA tenant_456 TO app_user`.                        |
| **Slow performance**           | Analyze query plans for full table scans on non-indexed `tenant_id`.                      | Add index: `CREATE INDEX idx_orders_tenant ON orders(tenant_id)`.                        |

---

## **11. Example Application Flow**
1. **Auth Flow**:
   - User logs in via OAuth → JWT includes `tenant_id`.
   - Middleware extracts `tenant_id` and injects into `context.Context`.

2. **Database Query**:
   ```go
   func GetUserOrders(ctx context.Context, userId string) ([]Order, error) {
       ctx := context.WithValue(ctx, "tenant_id", "123e4567...")
       rows, err := db.Query(ctx, "SELECT * FROM orders WHERE user_id = $1", userId)
       // FraiseQL automatically filters by tenant_id
   }
   ```

3. **Cache Layer**:
   - Redis keys: `tenant:123e4567:user:456:orders` (TTL: 5m).
   - Invalidate on `ORDER_CREATED` event.

4. **Schema-Per-Tenant** (Optional):
   - Dynamically resolve schema: `fmt.Sprintf("tenant_%s.orders", tenantId)`.

---

## **12. Configuration Options**
| Option                          | Default       | Description                                                                                     |
|---------------------------------|---------------|-------------------------------------------------------------------------------------------------|
| `fraiseql.tenant_id_header`    | `X-Tenant-ID` | HTTP header name for tenant context.                                                            |
| `fraiseql.enable_compile_filtering` | `on`          | Inject `WHERE tenant_id` during query compilation.                                             |
| `fraiseql.rls_enabled`          | `on`          | Enable/disable Row-Level Security policies.                                                     |
| `fraiseql.schema_per_tenant`   | `off`         | Enable schema partitioning per tenant.                                                         |
| `fraiseql.cache_prefix`         | `tenant:`     | Prefix for tenant-aware cache keys.                                                            |

---
**See Also**:
- [FraiseQL RLS Documentation](https://fraise.dev/docs/rls)
- [Schema Partitioning Guide](https://fraise.dev/docs/partitioning)
- [Tenant Context Middleware](https://fraise.dev/docs/middleware)