# **[Pattern] Storage-Projection Separation**
*Decoupling normalized storage from denormalized API projections in FraiseQL*

---

## **1. Overview**
The **Storage-Projection Separation** pattern in FraiseQL ensures that normalized, transactional data tables (`tb_*`) and denormalized API projections (`v_*`) are managed independently. This separation prevents schema lock-in, allows API designers to redesign projections without DBA intervention, and enables multiple API shapes to share the same underlying data.

By default, FraiseQL enforces ownership: DBAs control storage tables, while API designers own projections. This ensures:
✅ **Schema independence** – Projections can evolve without touching the source tables.
✅ **API flexibility** – Multiple APIs can serve different views of the same data.
✅ **Performance isolation** – Projections can optimize for query patterns without impacting storage.

---

## **2. Schema Reference**
FraiseQL organizes schemas into two distinct layers:

| **Category**       | **Convention**       | **Ownership**          | **Purpose**                                                                 | **Example**          |
|---------------------|----------------------|------------------------|-----------------------------------------------------------------------------|----------------------|
| **Storage (Base Tables)** | `tb_*`              | DBAs                   | Normalized, transactional data (e.g., EAV, relational)                      | `tb_user_profiles`   |
| **Projection (Views)**     | `v_*`               | API designers         | Denormalized, optimized for API responses                                  | `v_user_public_data` |
| **Projection Base**      | `vb_[table]_base`    | DBAs                   | Reference table for projection lineage (auto-managed by FraiseQL)          | `vb_user_profiles_base` |
| **Projection Index**      | `v_[table]_idx`     | DBAs                   | Optimized indexes for projection queries                                  | `v_user_profiles_idx`|

### **Key Relationships**
- A projection (`v_*`) **depends on** one or more storage tables (`tb_*`) via a `vb_[table]_base` reference.
- Projections can include computed fields, joins, or aggregations not present in the base tables.
- Storage tables are immutable for API designers but can be modified by DBAs without breaking projections (via incremental changes).

---

## **3. Query Examples**

### **3.1 Creating Projections**
Projections are defined using the `CREATE VIEW` syntax with metadata tags to enforce ownership:

```sql
-- API designer creates a projection (requires 'v_*' access)
CREATE VIEW v_user_public_data (
    id VARCHAR(36),
    full_name VARCHAR(255),
    email VARCHAR(255),
    last_login_at TIMESTAMP
)
AS SELECT
    u.id,
    CONCAT(u.first_name, ' ', u.last_name) AS full_name,
    u.email,
    MAX(l.login_time) AS last_login_at
FROM tb_user_profiles u
LEFT JOIN tb_user_logins l ON u.id = l.user_id
GROUP BY u.id, u.first_name, u.last_name, u.email
WITH OWNER = 'api_designer', LINK_BASE = 'vb_user_profiles_base';
```

**Output:**
- FraiseQL auto-creates `vb_user_profiles_base` (tracking the projection’s lineage).
- The projection is optimized for read-heavy API queries (e.g., caching, indexing).

---

### **3.2 Querying Projections**
Projections can be queried like regular views:

```sql
-- API client reads the projection
SELECT * FROM v_user_public_data WHERE last_login_at > '2024-01-01';
```

**Performance Notes:**
- FraiseQL materializes projections incrementally (e.g., nightly) or on-demand.
- Use `REFRESH MATERIALIZED VIEW v_user_public_data` to update projections.

---

### **3.3 Updating Storage Without Breaking Projections**
DBAs can modify `tb_*` tables **if** they:
1. Maintain backward compatibility (e.g., add columns, rename unused ones).
2. Use **incremental projection updates** (FraiseQL auto-detects schema drift and adjusts).

**Example:**
```sql
-- DBA adds a column to the storage table
ALTER TABLE tb_user_profiles ADD COLUMN phone_number VARCHAR(20);
```
- The projection `v_user_public_data` **remains intact** until explicitly updated.

---

### **3.4 Creating Multiple Projections from One Table**
API designers can define distinct views for different use cases:

```sql
-- Projection 1: Simple user data (e.g., for auth)
CREATE VIEW v_user_auth_data (
    id VARCHAR(36),
    email VARCHAR(255)
)
AS SELECT id, email FROM tb_user_profiles;

-- Projection 2: Analytics-ready data
CREATE VIEW v_user_analytics (
    id VARCHAR(36),
    signup_date DATE,
    country VARCHAR(100)
)
AS SELECT
    id,
    signup_date,
    GET_COUNTRY_BY_IP(user_ip) AS country
FROM tb_user_profiles;
```

---

## **4. Implementation Guidelines**

### **4.1 For DBAs (Storage Owners)**
- **Schema Design:** Keep storage tables **normalized** for transactional integrity.
- **Backward Compatibility:** Avoid dropping columns or changing data types in `tb_*`.
- **Indexing:** Create projection-specific indexes in `v_[table]_idx` for hot queries.

```sql
-- DBA creates an index for a projection
CREATE INDEX idx_v_user_public_data_last_login ON v_user_profiles_idx(last_login_at);
```

### **4.2 For API Designers (Projection Owners)**
- **Ownership:** All projections must be prefixed with `v_*`.
- **Lineage:** Use `LINK_BASE` in `CREATE VIEW` to tie projections to storage tables.
- **Performance:** Denormalize aggressively for API efficiency (e.g., pre-compute aggregations).

---

## **5. Query Patterns**

| **Pattern**               | **Use Case**                          | **Example**                                                                 |
|---------------------------|---------------------------------------|-----------------------------------------------------------------------------|
| **Join Projections**      | Combine multiple projections          | `SELECT * FROM v_user_public_data JOIN v_user_analytics ON id = id;`         |
| **Filter Projections**    | Apply API-specific filters            | `SELECT * FROM v_user_public_data WHERE country = 'US';`                   |
| **Projection Refresh**    | Force an update                        | `REFRESH MATERIALIZED VIEW v_user_public_data;`                           |
| **Conditional Projections** | Dynamic view selection          | `SELECT * FROM v_user_public_data WHERE is_premium = TRUE;` (filter in app) |

---

## **6. Edge Cases & Troubleshooting**

| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|------------------------------------|----------------------------------------|-----------------------------------------------------------------------------|
| Projection not updating             | Base table changed without refresh      | Run `REFRESH MATERIALIZED VIEW v_*` or configure auto-refresh.              |
| Projection dependency conflicts     | Multiple projections link to the same `tb_*` | Use `vb_[table]_base` to manage lineage explicitly.                          |
| Performance degradation             | Projection lacks optimal indexing      | Add indexes in `v_[table]_idx` or denormalize further.                      |
| Schema drift breaking projections   | DBA alters `tb_*` without caution      | Use incremental updates and backward-compatible changes.                     |

---

## **7. Related Patterns**
- **[Event Sourcing](https://docs.fraiseql.io/patterns/event-sourcing)**: Complementary for audit logs on projection changes.
- **[Schema Evolution](https://docs.fraiseql.io/patterns/schema-evolution)**: Ensures storage tables can update safely.
- **[Materialized Views](https://docs.fraiseql.io/patterns/materialized-views)**: Underpins projection performance.
- **[API-Layer Abstraction](https://docs.fraiseql.io/patterns/api-abstraction)**: Works with this pattern to isolate API logic.

---
**See Also:**
- [FraiseQL Schema Design Guide](https://docs.fraiseql.io/guides/schema-design)
- [Incremental Projection Updates](https://docs.fraiseql.io/advanced/updates)