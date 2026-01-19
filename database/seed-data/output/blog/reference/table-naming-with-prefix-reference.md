# **[Pattern] Table Naming with `tb_*` Prefix – Reference Guide**

## **1. Overview**
This pattern enforces a consistent **`tb_*` prefix** for all normalized storage tables in a database schema. The prefix:
- **Explicitly distinguishes** tables from views, stored procedures, or temporary objects.
- **Improves readability** by immediately signaling the table’s role in the schema.
- **Reduces ambiguity** during schema exploration and query writing.
- **Supports scalability** by standardizing naming conventions across teams.

All tables storing persistent, normalized data must adhere to this convention. Temporary or session-specific tables (e.g., staging/ETL workspace) may use alternate patterns (see [Related Patterns](#related-patterns)).

---

## **2. Schema Reference**

### **2.1. Pattern Syntax**
| **Component**       | **Example**               | **Description**                                                                 |
|---------------------|---------------------------|---------------------------------------------------------------------------------|
| **Prefix**          | `tb_`                     | Mandatory for all normalized tables.                                            |
| **Noun (Table Type)** | `user`, `order_item`     | Descriptive of the entity (singular, lowercase, underscores for compound words). |
| **Optional Suffix**  | `_v{version}` (e.g., `_v2`) | Indicates schema versions (if versioned tables are used).                       |

### **2.2. Valid vs. Invalid Examples**

| **Valid**                          | **Invalid**                          | **Reason**                                      |
|------------------------------------|--------------------------------------|-------------------------------------------------|
| `tb_customer`                      | `customer`                           | Missing `tb_` prefix.                           |
| `tb_product_category`              | `productCategory`                    | CamelCase violates naming convention.           |
| `tb_log_entry_v2`                  | `tb_logs`                            | Plural or generic name loses clarity.           |
| `tb_transaction_archive_2023`      | `tb_transactions_raw`                | Non-descriptive suffix; use versioning suffix.   |

### **2.3. Exceptions & Edge Cases**
| **Scenario**                     | **Recommendation**                                                                 |
|-----------------------------------|------------------------------------------------------------------------------------|
| **Temporary tables**              | Use `tmp_*` or session-specific prefixes (e.g., `stg_`).                          |
| **Views**                         | Prefix with `vw_` (e.g., `vw_tb_customer_orders`).                                |
| **System-generated tables**      | Append `_sys` (e.g., `tb_audit_log_sys`). If customizable, apply `tb_` prefix.      |
| **Composite tables (sharding)**  | Use clear prefixes (e.g., `tb_region_na_orders`). Avoid `tb_part_`.              |

---

## **3. Query Examples**

### **3.1. Basic CRUD Operations**
```sql
-- Insert into a table
INSERT INTO tb_customer (customer_id, email, signup_date)
VALUES (1001, 'user@example.com', '2023-10-01');

-- Select data (with prefix)
SELECT customer_id, email FROM tb_customer
WHERE signup_date > '2023-01-01';

-- Update with prefix
UPDATE tb_order_item
SET quantity = 3
WHERE item_id = 5001;
```

### **3.2. Joining Tables (with `tb_*` Prefix)**
```sql
-- Join customer and order tables (prefixes omitted in queries for clarity)
SELECT c.customer_name, o.order_date
FROM tb_customer c
JOIN tb_order o ON c.customer_id = o.customer_id
WHERE o.order_date BETWEEN '2023-01-01' AND '2023-12-31';
```

### **3.3. Versioned Tables (if applicable)**
```sql
-- Querying a versioned table (e.g., schema migration)
SELECT * FROM tb_customer_v2
WHERE signup_date > '2023-06-01';
```

### **3.4. Avoiding Ambiguity**
```sql
-- ❌ Ambiguous (missing prefix)
SELECT * FROM customer;  -- Error: No table named 'customer'.

-- ✅ Correct (with prefix)
SELECT * FROM tb_customer;
```

---

## **4. Implementation Guidelines**

### **4.1. Enforcement**
- **Database Constraints**: Use triggers or stored procedures to reject queries on tables without the `tb_*` prefix (if dynamic SQL is a risk).
- **ORM/Tooling**: Configure your ORM (e.g., Hibernate, SQLAlchemy) to generate tables with the `tb_` prefix by default.
- **CI/CD Checks**: Add schema validation in deployment pipelines to enforce the pattern (e.g., using tools like [SchemaCrawler](https://www.schemacrawler.com/) or custom scripts).

### **4.2. Tools & Automation**
| **Tool**               | **Use Case**                                                                 |
|------------------------|------------------------------------------------------------------------------|
| **Database Migrations** | Tools like Flyway or Liquibase to auto-apply `tb_*` prefixes during schema updates. |
| **ORM Frameworks**     | Configure table mappings to include the prefix (e.g., `@Table(name = "tb_user")`). |
| **Schema Documentation** | Generate docs (e.g., with [DbSchema](https://www.dbschema.com/)) highlighting `tb_*` tables. |

### **4.3. Migration Strategy**
1. **Audit Existing Schema**: Identify all tables not prefixed with `tb_`.
2. **Rename Tables**: Update DDL scripts or use `ALTER TABLE RENAME`:
   ```sql
   ALTER TABLE user RENAME TO tb_user;
   ```
3. **Update Applications**: Refactor queries and ORM mappings to use the new prefix.
4. **Document Changes**: Update technical documentation and API specs.

---

## **5. Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------|
| **Legacy Code Ignoring Prefix**       | Deprecate old table references in favor of the prefixed version.               |
| **Confusion with Views**              | Clearly document that `vw_*` ≠ `tb_*`.                                        |
| **Overuse of Suffixes**               | Limit suffixes (e.g., `_v2`) to versioned tables; avoid generic suffixes like `_new`. |
| **Case Sensitivity**                  | Enforce lowercase to avoid `TB_CUSTOMER` vs. `tb_customer` inconsistencies.   |
| **Temporary Tables Misuse**           | Reserve `tb_*` for persistent data; use `tmp_*` for session-specific tables. |

---

## **6. Related Patterns**

| **Pattern**                          | **Description**                                                                 | **When to Use**                                  |
|---------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[`vw_*` for Views](#)**             | Views are prefixed with `vw_` to distinguish from tables.                     | For query results or computed data.              |
| **[`stg_*` for Staging Tables](#)**   | Temporarily stores raw/transformed data before ETL.                            | During data ingestion/pipeline processing.       |
| **[`tmp_*` for Temporary Tables](#)** | Session-specific or short-lived tables.                                      | For intermediate processing (e.g., joins, aggregations). |
| **[`sys_*` for System Tables](#)**    | Meta-data or audit tables (e.g., `tb_audit_log_sys`).                         | For non-user-generated schema objects.           |
| **[Entity-Relationship Naming](#)**  | Tables follow a domain-driven design (e.g., `tb_Order`, `tb_OrderItem`).       | For project-specific naming clarity.             |

---

## **7. Further Reading**
- **[Database Design Best Practices](https://www.oreilly.com/library/view/database-design-with/0596001886/ch03.html)** (Chapter 3: Naming Conventions).
- **[PostgreSQL Table Naming](https://www.postgresql.org/docs/current/sql-createtable.html)** (Official DDL syntax).
- **[SchemaCrawler Documentation](https://www.schemacrawler.com/documentation/)** (For schema validation tools).