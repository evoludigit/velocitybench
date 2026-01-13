**[Pattern] Conditional Aggregates with `FILTER` and `CASE WHEN`**
*Efficiently compute multiple filtered aggregations in a single query across databases.*

---

### **Overview**
This pattern calculates **filtered aggregations** (e.g., revenue broken down by payment method) in **one query** instead of multiple queries or `UNION` operations. PostgreSQL provides native conditional aggregation via the `FILTER` clause, while MySQL/SQLite/SQL Server require `CASE WHEN` emulation. This pattern improves performance, readability, and maintainability by avoiding query duplication.

---

### **Schema Reference**
| Table: `transactions` |
|-----------------------|
| **Column**            | **Data Type**       | **Description**                |
| `id`                  | `SERIAL`            | Primary key (auto-incremented) |
| `amount`              | `DECIMAL(10,2)`     | Transaction amount (USD)       |
| `payment_method`      | `VARCHAR(50)`       | Payment type (e.g., "credit_card", "paypal") |
| `date`                | `TIMESTAMP`         | Transaction date/time          |

---

### **Implementation Details**
#### **Key Concepts**
1. **Filtering Aggregates**
   Apply conditions directly to aggregated values (e.g., sum only rows where `payment_method = 'credit_card'`).

2. **Database-Specific Syntax**
   - **PostgreSQL**: Uses `FILTER (WHERE condition)`.
   - **Others**: Uses `CASE WHEN` logic for compatibility.

3. **Performance**
   Filtering happens at the aggregation level (not row-by-row), optimizing query execution plans.

4. **Multiple Conditions**
   Combine multiple filters in a single query using `CASE WHEN` or `FILTER` groups.

---

### **Components/Solutions**
#### **1. FILTER Clause (PostgreSQL)**
**Syntax**: `AGGREGATE(field) FILTER (WHERE condition)`
- **Advantages**: Native, readable, and optimized for PostgreSQL.

**Example**:
```sql
SELECT
    SUM(amount) FILTER (WHERE payment_method = 'credit_card') AS credit_card_revenue,
    SUM(amount) FILTER (WHERE payment_method = 'paypal') AS paypal_revenue,
    SUM(amount) FILTER (WHERE payment_method IN ('credit_card', 'paypal')) AS combined_revenue;
```

#### **2. CASE WHEN Emulation (MySQL/SQLite/SQL Server)**
**Syntax**: `AGGREGATE(CASE WHEN condition THEN field ELSE NULL END)`
- **Advantages**: Works across databases; treats `NULL` as excluded from aggregation.

**Example**:
```sql
SELECT
    SUM(CASE WHEN payment_method = 'credit_card' THEN amount ELSE NULL END) AS credit_card_revenue,
    SUM(CASE WHEN payment_method = 'paypal' THEN amount ELSE NULL END) AS paypal_revenue,
    SUM(CASE WHEN payment_method IN ('credit_card', 'paypal') THEN amount ELSE NULL END) AS combined_revenue;
```

#### **3. Multiple Conditions (Scalable Approach)**
**PostgreSQL (FILTER)**:
```sql
SELECT
    SUM(amount) FILTER (WHERE date >= '2023-01-01') AS january_revenue,
    SUM(amount) FILTER (WHERE payment_method = 'credit_card') AS credit_revenue,
    SUM(amount) FILTER (WHERE payment_method = 'paypal' AND date >= '2023-01-01')
        AS paypal_january_revenue;
```

**MySQL (CASE WHEN)**:
```sql
SELECT
    SUM(CASE WHEN date >= '2023-01-01' THEN amount ELSE NULL END) AS january_revenue,
    SUM(CASE WHEN payment_method = 'credit_card' THEN amount ELSE NULL END) AS credit_revenue,
    SUM(CASE WHEN payment_method = 'paypal' AND date >= '2023-01-01' THEN amount ELSE NULL END)
        AS paypal_january_revenue;
```

---
### **Query Examples**
#### **Example 1: Revenue by Payment Method**
**PostgreSQL**:
```sql
SELECT
    SUM(amount) FILTER (WHERE payment_method = 'credit_card') AS credit_revenue,
    SUM(amount) FILTER (WHERE payment_method = 'paypal') AS paypal_revenue,
    SUM(amount) AS total_revenue;
```

**MySQL**:
```sql
SELECT
    SUM(CASE WHEN payment_method = 'credit_card' THEN amount ELSE NULL END) AS credit_revenue,
    SUM(CASE WHEN payment_method = 'paypal' THEN amount ELSE NULL END) AS paypal_revenue,
    SUM(amount) AS total_revenue;
```

#### **Example 2: Regional Sales Breakdown**
**PostgreSQL**:
```sql
SELECT
    region,
    SUM(amount) FILTER (WHERE region = 'North') AS north_revenue,
    SUM(amount) FILTER (WHERE region = 'South') AS south_revenue,
    SUM(amount) AS total_by_region;
```

**MySQL**:
```sql
SELECT
    region,
    SUM(CASE WHEN region = 'North' THEN amount ELSE NULL END) AS north_revenue,
    SUM(CASE WHEN region = 'South' THEN amount ELSE NULL END) AS south_revenue,
    SUM(amount) AS total_by_region;
```

#### **Example 3: Time-Series Filtering**
**PostgreSQL**:
```sql
SELECT
    EXTRACT(MONTH FROM date) AS month,
    SUM(amount) FILTER (WHERE EXTRACT(YEAR FROM date) = 2023) AS monthly_2023_revenue;
```

**MySQL**:
```sql
SELECT
    MONTH(date) AS month,
    SUM(CASE WHEN YEAR(date) = 2023 THEN amount ELSE NULL END) AS monthly_2023_revenue;
```

---

### **Advanced Patterns**
#### **1. Dynamic Filtering with Parameters**
Use prepared statements to swap conditions dynamically:
```sql
-- PostgreSQL (with parameter)
PREPARE dynamic_filter (TEXT) AS
SELECT SUM(amount) FILTER (WHERE payment_method = $1);
EXECUTE dynamic_filter('credit_card');
```

#### **2. Grouped Filtered Aggregates**
Combine with `GROUP BY` for hierarchical filtering:
```sql
-- PostgreSQL
SELECT
    region,
    SUM(amount) FILTER (WHERE payment_method = 'credit_card') AS credit_by_region,
    SUM(amount) AS total_by_region
FROM transactions
GROUP BY region;
```

#### **3. Window Functions + Filtered Aggregates**
Use filtered aggregates alongside window functions:
```sql
-- PostgreSQL
SELECT
    id,
    amount,
    SUM(amount) OVER (PARTITION BY payment_method) FILTER (WHERE date >= CURRENT_DATE - INTERVAL '1 month')
        AS monthly_spend_by_method;
```

---

### **Performance Considerations**
1. **Indexing**:
   Ensure `payment_method`, `date`, and filtered columns are indexed for large datasets. Example:
   ```sql
   CREATE INDEX idx_transactions_payment_method ON transactions(payment_method);
   CREATE INDEX idx_transactions_date ON transactions(date);
   ```

2. **Avoid `NULL` in Aggregates**:
   Explicitly use `CASE WHEN ... ELSE NULL END` to exclude rows, not `WHERE` clauses, for compatibility.

3. **Database-Specific Optimizations**:
   - PostgreSQL: `FILTER` is optimized for the query planner.
   - MySQL: Use `CASE WHEN` with `NULL` handling for clarity.

4. **Testing**:
   Validate query performance with `EXPLAIN ANALYZE`:
   ```sql
   EXPLAIN ANALYZE
   SELECT SUM(amount) FILTER (WHERE payment_method = 'credit_card') FROM transactions;
   ```

---

### **Common Pitfalls**
| Pitfall                          | Solution                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| Forgetting `ELSE NULL` in `CASE`  | Always include `ELSE NULL` to exclude rows from aggregation.              |
| Overusing `FILTER` in MySQL      | Replace with `CASE WHEN` syntax for compatibility.                         |
| Ignoring `GROUP BY` conflicts     | Ensure filtered aggregates align with grouped columns.                   |
| Poor indexing                     | Index filtered columns to avoid full scans.                              |

---

### **Related Patterns**
1. **[Window Functions](https://example.com/window-functions-pattern)**
   Use filtered window functions alongside aggregations for ranked metrics.

2. **[Pivot Tables](https://example.com/pivot-tables-pattern)**
   Transform filtered aggregates into row-column layouts (e.g., crosstabs).

3. **[Subquery-Free Joins](https://example.com/subquery-free-joins-pattern)**
   Replace correlated subqueries with filtered aggregations for performance.

4. **[Conditional Logic in SELECT](https://example.com/select-case-pattern)**
   Extend `CASE WHEN` for non-aggregated conditional logic.

---
### **References**
- [PostgreSQL `FILTER` Documentation](https://www.postgresql.org/docs/current/sql-expressions.html#SQL-FILTER)
- [MySQL `CASE` Statement](https://dev.mysql.com/doc/refman/8.0/en/case-statement.html)
- [SQLite `CASE` in Aggregations](https://www.sqlite.org/lang_aggfunc.html#case)