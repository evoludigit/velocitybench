# **[Pattern] Data Type Mapping – Reference Guide**

---

## **Overview**
The **Data Type Mapping** pattern ensures seamless data exchange between systems by standardizing and converting database column types across different database platforms. This pattern is critical when integrating disparate systems, migrating data, or supporting multi-database environments (e.g., SQL Server ↔ PostgreSQL ↔ MySQL).

Key challenges addressed:
- **Inconsistent type semantics** (e.g., `DATE` in MySQL vs. `DATETIME` in SQL Server).
- **Storage limitations** (e.g., `VARCHAR(MAX)` in SQL Server vs. `TEXT` in PostgreSQL).
- **Functionality gaps** (e.g., `JSON` support in PostgreSQL vs. `NVARCHAR` in SQL Server).

By defining clear mappings, this pattern minimizes errors during data transfers, ensures schema compatibility, and simplifies ETL (Extract-Transform-Load) processes.

---

## **Schema Reference**
Below is a standardized mapping table for common database column types. Adjust based on your environment’s supported databases (e.g., add Oracle, MongoDB, or NoSQL mappings).

| **Target System** | **Source Database Type** | **SQL Server**       | **PostgreSQL**       | **MySQL/MariaDB**    | **Oracle**          | **MongoDB (JSON)**  | **Notes**                          |
|-------------------|--------------------------|----------------------|----------------------|----------------------|---------------------|--------------------|------------------------------------|
| **Character**     | `VARCHAR(n)` / `TEXT`    | `NVARCHAR(MAX)`      | `VARCHAR(n)`         | `TEXT`               | `VARCHAR2(n)`       | `String`           | Use `NVARCHAR` for Unicode support. |
|                   | `CHAR(n)`                | `NVARCHAR(n)`        | `CHAR(n)`            | `CHAR(n)`            | `CHAR(n BYTE)`      | `String`           | Fixed-width; avoid for variable data. |
|                   | `CLOB`                   | `NVARCHAR(MAX)`      | `TEXT`               | `LONGTEXT`           | `CLOB`              | `String`           | Large text; consider chunking.      |
| **Numeric**       | `INT`                    | `INT`                | `INTEGER`            | `INT`                | `NUMBER(10)`        | `Number`           | Default precision; adjust for range. |
|                   | `BIGINT`                 | `BIGINT`             | `BIGINT`             | `BIGINT`             | `NUMBER(20)`        | `Number`           |                              |
|                   | `FLOAT` / `DOUBLE`       | `FLOAT(53)`          | `DOUBLE PRECISION`   | `DOUBLE`             | `BINARY_FLOAT`      | `Number`           | Floating-point; lossy for decimals. |
|                   | `DECIMAL(p,s)`           | `DECIMAL(p,s)`       | `NUMERIC(p,s)`       | `DECIMAL(p,s)`       | `NUMBER(p,s)`       | `Number`           | Fixed precision; critical for finance. |
| **Date/Time**     | `DATE`                   | `DATE`               | `DATE`               | `DATE`               | `DATE`              | `Date`             | YYYY-MM-DD format.                   |
|                   | `DATETIME`               | `DATETIME2`          | `TIMESTAMP`          | `DATETIME`           | `TIMESTAMP`         | `Date`             | Include timezone offset if needed.   |
|                   | `TIMESTAMP`              | `DATETIMEOFFSET`     | `TIMESTAMP WITH TIMEZONE` | `DATETIME`       | `TIMESTAMP WITH TIMEZONE` | `Date`       | Prefer UTC for consistency.           |
|                   | `INTERVAL`               | *Not natively supported* | `INTERVAL`          | `INTERVAL`           | `INTERVAL`          | `String` (ISO 8601) | Store as text if unsupported.      |
| **Boolean**       | `BIT`                    | `BIT`                | `BOOLEAN`            | `TINYINT(1)`         | `NUMBER(1)`         | `Boolean`          | Use `1/0` or `TRUE/FALSE` in ETL.   |
| **Binary**        | `BLOB` / `VARBINARY(n)`  | `VARBINARY(MAX)`     | `BYTEA`              | `BLOB`               | `RAW(n)`            | `Binary`           | Base64 encoding may be needed.      |
| **JSON/XML**      | `JSON` / `XML`           | `NVARCHAR(MAX)`      | `JSON` / `JSONB`      | `JSON`               | `CLOB`              | `Document`         | Postgres `JSONB` is faster for queries. |
| **Other**         | `ENUM`                   | *Not natively supported* | `TEXT` (value)       | `VARCHAR` (value)    | `VARCHAR2`         | `String`           | Normalize to a lookup table.         |

---

## **Implementation Details**

### **1. Type Conversion Strategies**
| **Strategy**               | **When to Use**                          | **Example**                                  |
|----------------------------|------------------------------------------|---------------------------------------------|
| **Direct Mapping**         | Types are compatible (e.g., `INT` → `INT`). | `SELECT col AS new_col FROM table;`         |
| **Cast Conversion**        | Minor type differences (e.g., `VARCHAR` → `NVARCHAR`). | `SELECT CAST(col AS NVARCHAR(MAX)) FROM table;` |
| **Function-Based Conversion** | Complex transformations (e.g., `DATETIME` → `TIMESTAMP WITH TIMEZONE`). | `SELECT TO_TIMESTAMP(col::TEXT, 'YYYY-MM-DD HH24:MI:SS') FROM table;` |
| **Lookup Table**           | Custom mappings (e.g., `ENUM` values).   | `SELECT lookup_table.value FROM table JOIN lookup ON table.enum_id = lookup.id;` |
| **Stored Procedure**       | Heavy processing (e.g., large JSON parsing). | `EXEC dbo.ConvertToJSON(@input);`           |
| **Application-Level**     | Non-SQL data (e.g., MongoDB → SQL).     | Use ORMs or custom scripts.                  |

---

### **2. Handling Edge Cases**
| **Case**                          | **Solution**                                                                 |
|-----------------------------------|------------------------------------------------------------------------------|
| **Lossy Conversions** (e.g., `DECIMAL(10,2)` → `FLOAT`) | Use `ROUND()` or warn users of precision loss.                              |
| **NULL Handling**                 | Ensure `ISNULL()` or `COALESCE` is used to replace NULLs with defaults.      |
| **Timezone Differences**          | Convert to UTC in the source, then localize in the target.                  |
| **Unsupported Types** (e.g., Oracle `RAW`) | Encode to `BASE64` or `HEX`.                                                 |
| **Schema Drift**                 | Use versioned scripts or CI/CD to update mappings.                          |

---

### **3. Tools and Extensions**
- **Database-Specific Tools**:
  - **SQL Server**: `sp_rename`, `ALTER COLUMN` with `CONVERT()`.
  - **PostgreSQL**: `ALTER TABLE ... ALTER COLUMN TYPE USING convert_to_new_type();`.
  - **MySQL**: `ALTER TABLE ... MODIFY COLUMN col DATA_TYPE;`.
- **ETL Tools**: SSIS (SQL Server), Apache NiFi, Talend, or custom scripts.
- **ORM Frameworks**: Django (Python), Hibernate (Java) often handle type mapping automatically.

---

## **Query Examples**

### **1. Basic Type Conversion**
Convert a MySQL `DATETIME` column to PostgreSQL `TIMESTAMP WITH TIMEZONE`:
```sql
-- MySQL to PostgreSQL
SELECT
    col_name::TIMESTAMP WITH TIMEZONE AS target_col
FROM my_table;
```

### **2. Handling NULLs and Defaults**
Convert `VARCHAR` to `BIT` with NULL defaults:
```sql
SELECT
    CASE WHEN col_name = 'TRUE' THEN 1
         WHEN col_name = 'FALSE' THEN 0
         ELSE NULL END AS boolean_col
FROM source_table;
```

### **3. JSON/XML Transformation**
Convert Oracle `CLOB` (JSON) to PostgreSQL `JSONB`:
```sql
-- Step 1: Extract JSON text (Oracle)
SELECT EXTRACTVALUE(col_name, '//root/text()') AS json_text
FROM oracle_table;

-- Step 2: Insert into PostgreSQL
INSERT INTO postgresql_table (json_data)
SELECT json_text::jsonb FROM extracted_data;
```

### **4. Batch Processing for Large Datasets**
Use a stored procedure to process chunks (SQL Server example):
```sql
CREATE PROCEDURE dbo.ConvertDataChunk
    @start_id INT,
    @end_id INT
AS
BEGIN
    DECLARE @i INT;
    SET @i = @start_id;

    WHILE @i <= @end_id
    BEGIN
        UPDATE target_table
        SET target_col = CAST(source_col AS NVARCHAR(MAX))
        FROM source_table
        WHERE id = @i;

        SET @i = @i + 1;
    END
END;
```

### **5. Application-Level Mapping (Pseudocode)**
```python
# Python example for MongoDB → SQL (using SQLAlchemy)
def map_mongo_to_sql(data):
    mapped_data = {
        "id": data["_id"],  # Convert ObjectId to INT
        "created_at": data["createdAt"].isoformat(),  # MongoDB Date to ISO string
        "tags": ",".join(data["tags"]),  # Array to CSV
        "metadata": json.dumps(data["metadata"])  # Nested JSON
    }
    return mapped_data
```

---

## **Related Patterns**
1. **[Schema Versioning]**
   - Coordinate type mapping changes across database revisions.
2. **[Data Transformation Logs]**
   - Track type conversions and failures for auditing.
3. **[ETL Pipeline Pattern]**
   - Integrate mappings into end-to-end data workflows.
4. **[Fallback Data Strategy]**
   - Manage data loss during unsupported type conversions (e.g., store `RAW` as hex).
5. **[Micro-Orchestration for Data]**
   - Use lightweight workflows (e.g., Airflow) to manage complex mappings.

---

## **Best Practices**
1. **Document Mappings Explicitly**
   Create a `data_type_mapping.json` file for reference:
   ```json
   {
     "mappings": {
       "mysql_date": { "target": "postgres_timestamp", "function": "CAST(..., 'TIMESTAMP')" },
       "oracle_raw": { "target": "hex_string", "converter": "HEX" }
     }
   }
   ```

2. **Validate Data Post-Conversion**
   Use assertions or checks:
   ```sql
   -- Validate that all converted dates are valid
   SELECT COUNT(*) FROM target_table
   WHERE target_col < '1900-01-01';
   ```

3. **Leverage CI/CD for Migrations**
   Automate type checks in deployment pipelines (e.g., Flyway, Liquibase).

4. **Prioritize Readability Over Performance**
   Use clear variable names and avoid deeply nested conversions.

5. **Plan for Rollback**
   Store original data or use transactions for critical conversions.

---
**Further Reading**:
- [Database-Specific Type Systems](https://dev.mysql.com/doc/refman/8.0/en/data-types.html)
- [PostgreSQL JSON vs. JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [SSIS Data Conversion Tools](https://learn.microsoft.com/en-us/sql/integration-services/data-conversion)