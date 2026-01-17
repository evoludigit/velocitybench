# **[Pattern] Query Cost Analysis Reference Guide**

---

## **1. Overview**
FraiseQL’s **Query Cost Analysis** pattern dynamically evaluates SQL queries for computational expense before execution, preventing excessive resource consumption and mitigating risks of denial-of-service (DoS) attacks. Queries are scored based on:
- **Depth** (nested subqueries, joins)
- **Breadth** (large result sets)
- **Field count** (number of selected columns)
- **Database operations** (INSERTs, DELETEs, complex aggregations)

If a query exceeds a configurable **cost threshold**, FraiseQL **rejects it immediately** with a `403 Forbidden` response, minimizing server load. This ensures efficient query handling while maintaining performance and security.

---

## **2. Core Concepts**

### **2.1. Cost Scoring Model**
| **Metric**          | **Description**                                                                 | **Weight** | **Example Impact**                     |
|---------------------|---------------------------------------------------------------------------------|------------|-----------------------------------------|
| **Depth (D)**       | Max nesting level of subqueries/joins                                         | ×2         | `SELECT * FROM (SELECT * FROM t1 JOIN t2) AS x` → D=2  |
| **Breadth (B)**     | Estimated result set size (rows)                                               | ×1         | `FROM table WITH (ROWS=10M)` → B=10M   |
| **Field Count (F)** | Number of selected columns (excluding `*`)                                    | ×0.5       | `SELECT col1, col2, col3` → F=3         |
| **Operation Type**  | Complexity of base operations (e.g., `GROUP BY`, `UNION`)                     | ×1.5–3.0   | `GROUP BY id HAVING COUNT(*) > 100` → ×3 |

**Total Cost Formula:**
`C = (D × 2) + (B × 1) + (F × 0.5) + (Op × [1.5–3.0])`

---
### **2.2. Thresholds & Rejection**
- **Default Threshold**: 100 (adjustable via config).
- **Rejection Triggers**:
  - `C > threshold` → `403 Forbidden` with `{ "error": "Query too expensive" }`.
  - **Exceptions**: Admin users (e.g., `user.is_admin=true`) bypass checks.

---
### **2.3. Dynamic Metrics**
FraiseQL estimates `B` and `D` using:
- **Table stats** (cached metadata like `rows`).
- **Query parsing** (e.g., `COUNT(*)` in `WHERE` implies large `B`).
- **Join heuristics** (cross-joins inflate `D` more than `INNER JOIN`).

---

## **3. Schema Reference**
### **3.1. Configurable Parameters**
| **Key**               | **Type**   | **Default** | **Description**                                                                 |
|-----------------------|------------|-------------|---------------------------------------------------------------------------------|
| `max.query_cost`      | `int`      | `100`       | Hard rejection threshold for cost `C`.                                         |
| `admin_bypass`        | `bool`     | `false`     | Allow admins to exceed thresholds.                                              |
| `slow_query_warn`     | `int`      | `80`        | Log warnings for queries near threshold (optional).                           |
| `cost.op_weights`     | `object`   | `{...}`     | Per-operation multipliers (e.g., `"GROUP BY": 2.5` in config).                   |

---

## **4. Query Examples**

### **4.1. Low-Cost Query (Safe)**
```sql
SELECT id, name FROM users WHERE status = 'active';
```
- **D**: 0 (no joins/subqueries)
- **B**: ~100 rows (estimated)
- **F**: 2
- **Op**: `WHERE` filter (×1.0)
- **Cost**: `(0×2) + (100×1) + (2×0.5) + (1.0) = 100` → **Passes** (if `max_cost=100`).

---

### **4.2. Medium-Cost Query (Warnings)**
```sql
SELECT * FROM orders
JOIN users ON orders.user_id = users.id
WHERE orders.date > '2023-01-01'
GROUP BY users.id HAVING COUNT(*) > 10;
```
- **D**: 2 (1 join)
- **B**: ~500K rows
- **F**: 5 (*` counts as 10 fields)
- **Op**: `GROUP BY` (×2.5)
- **Cost**: `(2×2) + (500K×1) + (10×0.5) + (2.5) = 500,002` →
  **Rejected** (if `max_cost=100`) or **warned** (if `slow_query_warn=80`).

---

### **4.3. High-Cost Query (Rejected)**
```sql
-- Nested subquery with wildcard + union
SELECT * FROM (
  SELECT * FROM products
  WHERE category = 'electronics'
  UNION ALL
  SELECT * FROM products
  WHERE price > 1000
) AS filtered
JOIN inventory ON filtered.id = inventory.product_id;
```
- **D**: 3 (1 union + 1 join)
- **B**: ~5M rows (estimated)
- **F**: 5 (`*` → 10 fields)
- **Op**: `UNION ALL` (×2.0), join (×1.5)
- **Cost**: `(3×2) + (5M×1) + (10×0.5) + (2.0 + 1.5) = 5,000,010` → **Rejected**.

---
### **4.4. Admin Bypass Example**
```bash
curl -H "X-Admin-Token: secret123" \
  https://api.fraiseql.com/query \
  -d 'SELECT * FROM sensitive_data'  # Cost: ~10,000 → **Allowed** if `admin_bypass=true`.
```

---

## **5. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **Synergy**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Rate Limiting**         | Throttle query frequency per user.                                           | Combine with cost analysis to block both *expensive* and *frequent* queries. |
| **Query Optimization**    | Rewrite queries to reduce cost (e.g., `SELECT id` instead of `SELECT *`).    | Cost analysis flags issues for optimization tools to fix.                     |
| **Multi-Tenancy Isolation**| Separate tenant-specific queries to prevent resource hogging.                | Cost analysis ensures no tenant monopolizes resources.                       |
| **Dynamic Caching**       | Cache frequent low-cost queries.                                             | Reduces repeated costs for identical queries.                              |

---
## **6. Troubleshooting**
### **6.1. False Positives**
- **Issue**: Legitimate queries rejected due to overestimated `B`/`D`.
- **Fix**:
  - Update table stats: `UPDATE table_stats SET rows = 10000 WHERE table_name = 'users';`.
  - Adjust `cost.op_weights` for operation types (e.g., reduce `GROUP BY` weight).

### **6.2. Performance Bottlenecks**
- **Issue**: Cost checks slow down query parsing.
- **Fix**:
  - Offload scoring to a **proxy layer** (e.g., Envoy) if FraiseQL is the bottleneck.
  - Cache parsed queries for returning users.

### **6.3. Admin Workarounds**
- **Issue**: Admins bypass cost checks but abuse privileges.
- **Fix**:
  - Implement **cost limits per admin** (e.g., `admin.max_cost: 500`).
  - Log all admin queries to `admin_audit` table.

---
## **7. Configuration Examples**
### **7.1. Basic (Default)**
```yaml
fraiseql:
  cost_analysis:
    max_query_cost: 100
    admin_bypass: false
```

### **7.2. Strict Mode (Prevent Heavy Joins)**
```yaml
fraiseql:
  cost_analysis:
    max_query_cost: 50
    cost:
      op_weights:
        GROUP BY: 3.0   # Penalize heavy aggregations
        JOIN: 2.2       # Prefer single-table queries
```

### **7.3. Tenant-Aware Throttling**
```yaml
fraiseql:
  cost_analysis:
    tenant_based_thresholds:
      free: 30
      premium: 200
      enterprise: 1000
```

---
## **8. API Reference**
### **8.1. Response Headers**
| **Header**            | **Example**       | **Description**                                  |
|-----------------------|-------------------|--------------------------------------------------|
| `X-Query-Cost`        | `120`             | Computed cost of the query.                      |
| `X-Threshold`         | `100`             | Current `max_query_cost` threshold.               |
| `X-Warning`           | `slow_query=true` | Indicates query is near the `slow_query_warn` limit. |

---
### **8.2. Error Responses**
| **Code** | **Message**                      | **Example Payload**                              |
|----------|----------------------------------|--------------------------------------------------|
| `403`    | `Query too expensive`            | `{ "error": "Query cost (150) exceeds threshold (100)" }` |
| `429`    | `Too many requests` (rate limit) | `{ "error": "Rate limit exceeded" }`             |

---
## **9. Best Practices**
1. **Monitor Cost Distribution**:
   Use `SELECT AVG(x_query_cost), MAX(x_query_cost) FROM query_log;` to adjust thresholds.
2. **Optimize Queries**:
   - Avoid `SELECT *`; limit fields.
   - Use indexes for filtered columns (reduces `B`).
3. **Test Edge Cases**:
   ```sql
   -- Stress test: Deeply nested query
   SELECT * FROM (
     SELECT * FROM users WHERE id IN (
       SELECT user_id FROM orders WHERE amount > (
         SELECT AVG(amount) FROM orders
       )
     )
   ) AS filtered;
   ```
4. **Document Thresholds**:
   Add comments in code/docs explaining cost implications (e.g., "This query costs 200").

---
## **10. Limitations**
- **Estimation Accuracy**: `B`/`D` are approximations; overestimates may reject valid queries.
- **Dynamic Schema**: Costs recalculate on schema changes; add a cache invalidation hook if needed.
- **NoSQL Workloads**: Primarily designed for SQL; extensions for document queries may require custom scoring.