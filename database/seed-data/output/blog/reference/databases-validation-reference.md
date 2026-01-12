# **[Pattern] Databases Validation – Reference Guide**

## **Overview**
The **Databases Validation** pattern ensures that database schemas, data integrity, and operational consistency align with organizational requirements. This pattern enforces validation rules across relational, NoSQL, and cloud databases, preventing invalid data entry, maintaining referential integrity, and detecting schema drift over time. It supports **pre-commit validation** (before data changes), **post-commit auditing**, and **automated schema checks**, enabling compliance with standards like **ACID (Atomicity, Consistency, Isolation, Durability)** and **RESTful database best practices**. Use cases include financial systems, healthcare data, and e-commerce platforms requiring strict data governance.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**          | **Description**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Validation Rules**   | Defines constraints (e.g., `NOT NULL`, `UNIQUE`, regex patterns, custom business logic, domain restrictions).                                                                                                     |
| **Trigger-Based Checks** | Database triggers (e.g., `BEFORE INSERT/UPDATE`) enforce rules in real-time.                                                                                                                               |
| **Schema Validation**  | Automated checks against expected schema (ER diagrams, migration scripts, or tooling like **Flyway**, **Liquibase**).                                                                                        |
| **Data Profiling**     | Analyzes data distributions (e.g., null rates, outliers) using tools like **Great Expectations**, **Deequ**, or custom Python scripts.                                                                       |
| **Audit Logging**      | Tracks validation failures (e.g., failed transactions, schema deviations) for compliance (e.g., **GDPR**, **HIPAA**). Logs stored in separate tables or SIEM systems (e.g., **Splunk**).                |
| **Validation Frameworks** | Libraries/APIs for rule enforcement (e.g., **SQL Server CHECK constraints**, **PostgreSQL pg_constraints**, **MongoDB $where**, **AWS Glue DataBrew**).                                             |
| **Integration Points** | Connects with **ETL pipelines** (e.g., **Apache Airflow**, **dbt**), **microservices**, or **API gateways** to validate incoming data before persistence.                                                   |

---

### **2. Validation Types**
| **Type**               | **Scope**                          | **Example**                                                                                     |
|------------------------|------------------------------------|--------------------------------------------------------------------------------------------------|
| **Structural**         | Schema integrity                  | Column data types, foreign key constraints, indexing.                                             |
| **Referential**        | Relationships                     | `ON DELETE CASCADE` for parent-child records.                                                    |
| **Semantic**           | Business logic                    | Validate `age > 0` in a user table; check `order_total > 0`.                                        |
| **Format-Specific**    | Data formatting                   | Email regex (`^[^\s@]+@[^\s@]+\.[^\s@]+$`), ZIP code validation.                                   |
| **Temporal**           | Time-based constraints            | Prevent future-dated transactions in accounting systems.                                          |
| **Compliance**         | Regulatory checks                 | Mask PII (e.g., **CCPA**), enforce encryption standards (e.g., **AES-256**).                     |

---

### **3. Validation Strategies**
| **Strategy**           | **When to Use**                                                                 | **Tools/Techniques**                                                                           |
|------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Server-Side**        | Critical data (e.g., financial systems). Prevents invalid data at the DB level.   | SQL constraints, stored procedures, database triggers.                                         |
| **Application-Level** | Flexibility (e.g., REST APIs). Validates before DB write.                       | Framework validators (e.g., **Spring Validation**, **Django Forms**), custom functions.          |
| **ETL/ELT**            | Batch processing (e.g., data warehouses). Validates during transformations.      | **Great Expectations**, **dbt tests**, **Apache NiFi** processors.                              |
| **Scheduled Checks**  | Detect schema drift or data corruption over time.                                | **Flyway/Liquibase** for schema diffs; **Python scripts** for ad-hoc data scans.               |
| **Real-Time API**      | Microservices validating payloads (e.g., GraphQL mutations).                     | **GraphQL schema directives**, **OpenAPI/Swagger validators**, **custom middleware**.            |

---

## **Schema Reference**
Below are common validation schemas for relational and NoSQL databases.

### **Relational Database (SQL)**
| **Constraint Type**    | **SQL Syntax**                                                                                     | **Purpose**                                                                                     |
|------------------------|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **NOT NULL**           | `CREATE TABLE users (id INT PRIMARY KEY NOT NULL, name VARCHAR(100) NOT NULL);`                 | Enforces mandatory fields.                                                                       |
| **UNIQUE**             | `ALTER TABLE products ADD CONSTRAINT unique_email UNIQUE (email);`                                | Prevents duplicate entries (e.g., emails).                                                     |
| **CHECK**              | `ALTER TABLE orders ADD CONSTRAINT valid_amount CHECK (amount > 0);`                              | Validates business logic (e.g., positive values).                                               |
| **FOREIGN KEY**        | `ALTER TABLE orders ADD CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(id);` | Ensures referential integrity.                                                                 |
| **DEFAULT**            | `CREATE TABLE logs (id INT, status VARCHAR(20) DEFAULT 'pending');`                               | Provides fallback values.                                                                      |
| **Composite Unique**   | `CREATE UNIQUE INDEX idx_user_email ON users (email, organization_id);`                          | Combines fields for uniqueness (e.g., user + org pair).                                         |

### **NoSQL (MongoDB Example)**
| **Validation Rule**    | **MongoDB Schema (JSON)**                                                                         | **Tool/Method**                                                                                 |
|------------------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Required Fields**    | `"users": { "$required": ["name", "email"] }`                                                    | **Schema Validation** (MongoDB 4.2+) or **custom middleware**.                                 |
| **Pattern Matching**   | `"email": { "$pattern": "^[^\s@]+@[^\s@]+\.[^\s@]+$" }`                                          | **$regex** operator or **pre-save hooks** in application code.                                  |
| **Min/Max Length**     | `"bio": { "$minLength": 10, "$maxLength": 500 }`                                                 | **$where** clauses or **application validation**.                                               |
| **Custom Logic**       | `$expr: { $gt: ["$age", 18] }` (in aggregation pipeline)                                         | **Aggregation framework** or **pre-save triggers**.                                             |
| **Embedded Validation**| Nested documents with same rules (e.g., `addresses` array with `street: { "$required": true }`).| **Denormalized validation** (applied per document).                                             |

---

## **Query Examples**

### **1. SQL Server: CHECK Constraint with Custom Validation**
```sql
-- Create table with a CHECK constraint for positive sales
CREATE TABLE sales (
    id INT PRIMARY KEY,
    amount DECIMAL(10, 2) CHECK (amount >= 0),
    sale_date DATETIME DEFAULT GETDATE()
);

-- Insert invalid data (will fail)
INSERT INTO sales (id, amount) VALUES (1, -100.00); -- Error: CHECK constraint violated.
```

### **2. PostgreSQL: Trigger for Data Profiling**
```sql
-- Create a function to log null counts
CREATE OR REPLACE FUNCTION log_null_counts()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.column_name IS NULL THEN
        INSERT INTO data_anomalies (table_name, column_name, anomaly_type)
        VALUES ('sales', 'column_name', 'NULL_VALUE');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to a table
CREATE TRIGGER trg_null_check
AFTER INSERT OR UPDATE ON sales
FOR EACH ROW EXECUTE FUNCTION log_null_counts();
```

### **3. MongoDB: Schema Validation (v4.2+)**
```json
// Define collection-level validation in MongoDB Atlas/Data API
{
  "bsonType": "object",
  "required": ["name", "email"],
  "properties": {
    "email": {
      "bsonType": "string",
      "pattern": "^[^\s@]+@[^\s@]+\\.[^\s@]+$"
    },
    "age": {
      "bsonType": "int",
      "minimum": 0,
      "maximum": 120
    }
  }
}
```

### **4. Python (FastAPI): Application-Level Validation**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, condecimal

app = FastAPI()

class OrderItem(BaseModel):
    product_id: int
    quantity: int = condecimal(gt=0)  # Validate quantity > 0
    unit_price: condecimal(gt=0)

@app.post("/items/")
async def create_item(item: OrderItem):
    return {"message": "Valid item created"}
```

### **5. dbt: Data Test Validation**
```sql
-- In a dbt model (e.g., `models/sales/sales_test.sql`)
{{
  config(
    materialized='table',
    test_disabled=['not_null', 'unique']
  )
}}

-- Add tests to a model
SELECT
  *,
  CASE WHEN amount < 0 THEN 'FAIL' ELSE 'PASS' END AS test_amount_positive
FROM sales

-- Run tests via dbt: `dbt test --select test_amount_positive`
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Pair With**                                                                              |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **[Data Migration]**      | Structured movement of data between systems/stages.                                                 | Use to validate data during **ETL pipelines** before loading into the target schema.              |
| **[Event Sourcing]**      | Stores state changes as a sequence of immutable events.                                             | Validate events (e.g., `OrderCreated`) with schema constraints and business rules.               |
| **[CQRS]**                | Separates read (queries) and write (commands) models.                                               | Apply validation in **command handlers** before writing to the database.                          |
| **[Schema Evolution]**    | Gradually updates database schemas without downtime.                                                | Pair for **backward-compatible validation** during schema changes.                                |
| **[Audit Logging]**       | Tracks changes to data for compliance/recovery.                                                     | Log all validation failures (e.g., failed transactions) for forensic analysis.                    |
| **[Database Encryption]** | Secures sensitive data at rest/transit.                                                            | Validate that encrypted fields (e.g., **TDE**, **column-level encryption**) meet compliance.      |
| **[Canary Deployment]**   | Gradually rolls out database changes to minimize risk.                                              | Validate schema changes against a **staging subset** before full rollout.                         |

---

## **Best Practices**
1. **Layered Validation**: Combine **server-side** (DB constraints) and **application-level** checks for robustness.
2. **Automate Testing**: Integrate validation into **CI/CD pipelines** (e.g., **dbt tests** in GitHub Actions).
3. **Document Rules**: Maintain a **validation rules registry** (e.g., Confluence wiki) for team consistency.
4. **Monitor Failures**: Set up alerts for frequent validation errors (e.g., **Prometheus + Grafana**).
5. **Performance**: Avoid heavy validation in **hot paths** (e.g., use **indexes** for CHECK constraints).
6. **Compliance**: Map validations to **regulatory requirements** (e.g., **PCI-DSS** for payment data).
7. **Graceful Degradation**: For non-critical systems, log errors instead of blocking writes.

---
**See also**:
- [Database Schema Design Patterns](link)
- [ETL Pipeline Validation](link)
- [API Schema Validation](link)