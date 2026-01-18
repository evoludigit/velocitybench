# **[Pattern] Stored Procedure Naming (fn_* Prefix) Reference Guide**

---

## **Overview**
This pattern standardizes naming conventions for stored procedures implementing **mutation actions** (e.g., INSERT, UPDATE, DELETE) by prefixing them with `fn_*`. The convention distinguishes these procedures from **query-only views** (typically prefixed with `v_*`) and ensures consistency in database schema design.

By enforcing `fn_*` for mutations, developers:
- Improve code readability by signaling side effects (e.g., data modification).
- Follow a consistent, modular naming system across projects.
- Align with industry best practices for procedural logic separation.

---

## **Schema Reference**

| **Component**          | **Convention**                          | **Example**                     | **Rationale** |
|------------------------|-----------------------------------------|---------------------------------|---------------|
| **Prefix**             | `fn_` (lowercase, underscore)           | `fn_update_customer_status`      | Indicates a **function-like** procedure with mutations. |
| **Verb**               | Action keyword (`insert`, `update`, `delete`, `create`, `merge`) | `update` in `fn_update_customer_status` | Explicitly defines the mutation type. |
| **Entity**             | Noun representing the affected table   | `customer` in `fn_update_customer_status` | Reflects the target schema/table. |
| **Action/Qualifier**   | Optional descriptor (e.g., `_soft`, `_by_id`) | `fn_soft_delete_order` | Clarifies edge cases (e.g., soft delete). |
| **Parameter Prefixes** | `p_` for inputs, `o_` for outputs       | `p_customer_id`, `o_result`      | Avoids ambiguity in stored procedure signatures. |

### **Key Rules**
1. **Case Sensitivity**: Prefixes are **lowercase**; verbs and nouns are **PascalCase**.
2. **Avoid Redundancy**: No need for `fn_*` in view-like procedures (use `v_*` instead).
3. **Pluralization**: Typically **singular** for CRUD operations (e.g., `fn_get_user` vs. `fn_get_users` for queries).
4. **Reserved Keywords**: Escape SQL keywords (e.g., `fn_alter_table_schema` instead of `fn_alter_table`).

---
## **Query Examples**

### **1. Basic Mutation**
**Procedure**:
```sql
CREATE PROCEDURE fn_update_customer_status(
    p_customer_id INT,
    p_new_status VARCHAR(50),
    o_success BIT OUTPUT
)
AS
BEGIN
    UPDATE Customers
    SET Status = p_new_status
    WHERE Id = p_customer_id;
    SET o_success = @@ROWCOUNT > 0;
END;
```
**Call**:
```sql
EXEC fn_update_customer_status
    @p_customer_id = 123,
    @p_new_status = 'active',
    @o_success OUTPUT;
```

### **2. Soft Delete**
**Procedure**:
```sql
CREATE PROCEDURE fn_soft_delete_order(
    p_order_id INT,
    p_deleted_by INT,
    p_deleted_date DATETIME OUTPUT
)
AS
BEGIN
    UPDATE [Orders]
    SET DeletedFlag = 1, DeletedBy = p_deleted_by, DeletedDate = GETDATE()
    WHERE Id = p_order_id;
    SET p_deleted_date = GETDATE();
END;
```
**Call**:
```sql
EXEC fn_soft_delete_order
    @p_order_id = 456,
    @p_deleted_by = 1,
    @p_deleted_date OUTPUT;
```

### **3. Transactional Merge**
**Procedure**:
```sql
CREATE PROCEDURE fn_merge_customer_data(
    p_customer_id INT,
    p_first_name VARCHAR(100),
    p_last_name VARCHAR(100),
    o_was_updated BIT OUTPUT
)
AS
BEGIN
    MERGE INTO Customers AS target
    USING (SELECT 1) AS source
    ON target.Id = p_customer_id
    WHEN MATCHED THEN
        UPDATE SET FirstName = p_first_name, LastName = p_last_name
    WHEN NOT MATCHED THEN
        INSERT (Id, FirstName, LastName) VALUES (p_customer_id, p_first_name, p_last_name);
    SET o_was_updated = @@ROWCOUNT > 1;
END;
```
**Call**:
```sql
EXEC fn_merge_customer_data
    @p_customer_id = 789,
    @p_first_name = 'John',
    @p_last_name = 'Doe',
    @o_was_updated OUTPUT;
```

### **4. Error Handling Example**
**Procedure**:
```sql
CREATE PROCEDURE fn_update_product_price(
    p_product_id INT,
    p_new_price DECIMAL(10, 2),
    o_error_message NVARCHAR(255) OUTPUT
)
AS
BEGIN
    BEGIN TRY
        UPDATE Products
        SET UnitPrice = p_new_price
        WHERE Id = p_product_id;
        SET o_error_message = 'Success';
    END TRY
    BEGIN CATCH
        SET o_error_message = ERROR_MESSAGE();
    END CATCH
END;
```
**Call**:
```sql
EXEC fn_update_product_price
    @p_product_id = 101,
    @p_new_price = 99.99,
    @o_error_message OUTPUT;
```

---

## **Related Patterns**

### **1. View Naming Pattern (v_*)**
- **Purpose**: Distinguishes query-only procedures from mutations.
- **Example**: `v_get_customer_orders` vs. `fn_update_customer_orders`.
- **Reference**: [View Naming Convention](link-to-pattern).

### **2. Parameter Naming (p_*, o_*)**
- **Purpose**: Standardizes input/output parameters to avoid ambiguity.
- **Example**: `p_customer_id` (input) vs. `o_result` (output).
- **Reference**: [Parameter Naming Conventions](link-to-pattern).

### **3. Transaction Management**
- **Purpose**: Ensures atomicity for critical mutations.
- **Example**: Wrap `fn_merge_customer_data` in a transaction block.
- **Reference**: [Transaction Patterns in Stored Procedures](link-to-pattern).

### **4. Logging Pattern**
- **Purpose**: Audit mutations for compliance.
- **Example**: Log changes in `fn_update_customer_status` via a `Logging` table.
- **Reference**: [Audit Logging for Stored Procedures](link-to-pattern).

### **5. Performance Optimization**
- **Purpose**: Avoid cursor/loop-heavy mutations.
- **Example**: Use `MERGE` instead of nested loops in `fn_merge_customer_data`.
- **Reference**: [High-Performance Stored Procedure Design](link-to-pattern).

---
## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------|
| Using `fn_*` for non-mutation logic   | Rename to `v_*` (view) or `usp_*` (utility stored procedure).                 |
| Overly generic names (e.g., `fn_do`)  | Be explicit: `fn_update_product_inventory` instead of `fn_do_update`.       |
| Ignoring parameter prefixes           | Enforce `p_*` for inputs, `o_*` for outputs in CI/CD checks.                 |
| Hardcoding IDs instead of parameters | Use parameters for flexibility and reusability.                              |
| No error handling                     | Always include `TRY/CATCH` (SQL Server) or `EXCEPTION` (PL/SQL).              |

---
## **Tools & Enforcement**
- **Static Code Analysis**: Use tools like **SQL Prompt** or **ApexSQL Analyze** to enforce `fn_*` prefix.
- **Database Documentation**: Document procedures in tools like **SQL Doc** or **DbSchema**.
- **Documentation Comments**: Add inline comments for parameters and behavior:
  ```sql
  -- @param p_customer_id: Identifies the customer to update (not null)
  -- @return o_success: Boolean indicating whether the update succeeded
  ```

---
## **Migration Guidance**
1. **Audit Existing Procedures**: Identify mutations using `fn_*` (or lack thereof).
2. **Rename Views**: Move query-only procedures to `v_*` prefix.
3. **Update Consumers**: Refactor application code to use the new naming.
4. **Test Thoroughly**: Validate mutations in staging before production deployment.

---
## **Appendix: SQL Server-Specific Notes**
- **Schema Binding**: For high-level integrity, bind procedures to schemas (e.g., `dbo.fn_update_customer`).
- **Dynamic SQL**: Use sp_executesql with parameters to avoid SQL injection:
  ```sql
  EXEC sp_executesql N'fn_update_product_price @p_id, @p_price',
                  N'@p_id INT, @p_price DECIMAL(10,2)',
                  @p_id = 101, @p_price = 99.99;
  ```
- **Table-Valued Parameters**: For bulk mutations, use TVPs:
  ```sql
  CREATE PROCEDURE fn_batch_update_status(
      @status_updates TVP,
      @o_rows_affected INT OUTPUT
  )
  AS ...;
  ```