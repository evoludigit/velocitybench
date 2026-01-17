# **[Pattern] Operator Availability Matrix Reference Guide**

## **Overview**
The **Operator Availability Matrix (OAM)** pattern ensures that database operations (e.g., reads, writes, backups) are executed by specific operators or teams based on predefined rules, such as geographic location, workload type, or priority. This pattern prevents unauthorized or inefficient operator assignments, enforces compliance, and optimizes resource utilization by dynamically routing tasks to the most suitable operators.

OAM is particularly useful in heterogeneous database environments where different operators may manage distinct databases (e.g., SQL vs. NoSQL, on-prem vs. cloud) or where operational policies require strict separation (e.g., audit trails, regulatory constraints). By centralizing control via a matrix definition, OAM eliminates ad-hoc operator selection, reduces errors, and supports scalability across large-scale deployments.

---

## **Key Concepts**
| **Term**               | **Description**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Operator**           | A user, team, or service account with defined permissions to perform operations. |
| **Database (DB)**      | A logical or physical database instance (e.g., a SQL server, MongoDB cluster). |
| **Operation Type**     | A specific action (e.g., `backup`, `restore`, `patch`, `monitor`).              |
| **Availability Rule**  | Conditions determining which operators can perform operations on databases.    |
| **Matrix Entry**       | A row in the matrix specifying an operator, DB, and operation type.             |

### **Core Principles**
1. **Granular Control**: Assign operations to operators at a fine-grained level (e.g., per DB or per operation).
2. **Dynamic Routing**: Use metadata (e.g., DB tags, operator roles) to enforce rules programmatically.
3. **Auditability**: Log all operator-DB-operation mappings for compliance and debugging.
4. **Flexibility**: Support static (hardcoded) and dynamic (context-aware) rules.

---

## **Schema Reference**
Below is the reference schema for implementing an **Operator Availability Matrix**. This can be modeled in a relational database, NoSQL document store, or as configuration files (e.g., YAML/JSON).

### **1. Core Tables (Relational Example)**
| Table               | Columns                                                                 | Description                                                                 |
|---------------------|--------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **`operators`**     | `operator_id` (PK), `name`, `role`, `contact_email`, `active` (bool)   | Registry of all available operators.                                         |
| **`databases`**     | `db_id` (PK), `name`, `type` (e.g., "PostgreSQL", "MongoDB"), `region`, `tags` (JSON) | List of managed databases with metadata.                                  |
| **`operations`**    | `op_id` (PK), `name` (e.g., "backup", "monitor"), `description`         | Standardized set of supported operations.                                  |
| **`availability_matrix`** | `entry_id` (PK), `operator_id` (FK), `db_id` (FK), `op_id` (FK), `rule_condition` (e.g., `"region = 'us-west' AND role = 'admin'"`) | The matrix defining operator-DB-op permissions.                          |

### **2. Sample JSON Schema (NoSQL Alternative)**
```json
{
  "operators": [
    {
      "id": "op-001",
      "name": "DBAdminTeam",
      "role": "admin",
      "contact": "admin@company.com",
      "active": true
    }
  ],
  "databases": [
    {
      "id": "db-001",
      "name": "prod-order-service",
      "type": "PostgreSQL",
      "region": "us-west",
      "tags": {"priority": "high", "env": "production"}
    }
  ],
  "operations": [
    {
      "id": "op-backup",
      "name": "backup",
      "description": "Full database backup"
    }
  ],
  "availability_rules": [
    {
      "operator_id": "op-001",
      "db_id": "db-001",
      "op_id": "op-backup",
      "condition": "tags['priority'] == 'high' AND region == 'us-west'"
    }
  ]
}
```

---

## **Query Examples**
### **1. Check Operator Availability for a Database-Operation Pair**
**Use Case**: Verify if `operator_id="op-001"` can perform `backup` on `db_id="db-001"`.

#### **SQL Query**
```sql
SELECT a.entry_id
FROM availability_matrix a
JOIN operators o ON a.operator_id = o.operator_id
JOIN databases d ON a.db_id = d.db_id
JOIN operations op ON a.op_id = op.op_id
WHERE o.operator_id = 'op-001'
  AND d.db_id = 'db-001'
  AND op.name = 'backup'
  AND (a.rule_condition IS NULL OR EVALUATE_CONDITION(d, a.rule_condition) = true);
```
**Note**: Replace `EVALUATE_CONDITION` with a custom function to parse `rule_condition` (e.g., using a library like [SQLJMESPath](https://github.com/agiliq/sqljmespath)).

#### **JSON Query (MongoDB)**
```javascript
db.availability_matrix.find({
  operator_id: "op-001",
  db_id: "db-001",
  op_id: "op-backup",
  condition: {
    $expr: {
      $and: [
        { $eq: [ "$$DB_region", "us-west" ] },
        { $eq: [ "$$DB_tags.priority", "high" ] }
      ]
    }
  }
}).allowDiskUse();
```
**Context Variables**:
- `$$DB_region` and `$$DB_tags` are pre-registered as MongoDB [aggregation context variables](https://www.mongodb.com/docs/manual/reference/aggregation/context/).

---

### **2. List All Operators for a Database**
**Use Case**: Get all operators authorized to perform any operation on `db_id="db-001"`.

#### **SQL Query**
```sql
SELECT DISTINCT o.name, o.role
FROM availability_matrix a
JOIN operators o ON a.operator_id = o.operator_id
JOIN databases d ON a.db_id = d.db_id
WHERE d.db_id = 'db-001';
```

#### **JSON Query (MongoDB)**
```javascript
db.availability_matrix.aggregate([
  { $match: { db_id: "db-001" } },
  { $lookup: {
      from: "operators",
      localField: "operator_id",
      foreignField: "operator_id",
      as: "operator_details"
    }
  },
  { $unwind: "$operator_details" },
  { $group: {
      _id: null,
      operators: { $addToSet: "$operator_details" }
    }
  }
]);
```

---

### **3. Dynamic Rule Evaluation (Pseudocode)**
**Use Case**: Programmatically determine if an operator-DB-op combination is valid.

```python
def is_operator_available(operator_id, db_id, op_id, db_metadata):
    # Fetch the rule from the matrix
    rule = db.query("""
        SELECT rule_condition
        FROM availability_matrix
        WHERE operator_id = %s AND db_id = %s AND op_id = %s
    """, (operator_id, db_id, op_id))

    if not rule or not rule.rule_condition:
        return True  # Default: allowed if no explicit rule

    # Evaluate condition (e.g., using Python's `eval` with sandboxing)
    try:
        # Replace placeholders like "$DB_region" with actual values
        safe_condition = rule.rule_condition.replace("$$DB_region", repr(db_metadata["region"]))
        return eval(safe_condition, {}, {
            "DB": db_metadata,
            "tags": db_metadata.get("tags", {})
        })
    except:
        return False  # Rule evaluation failed; assume denied
```

---

## **Implementation Considerations**
### **1. Rule Condition Syntax**
Support a concise syntax for conditions. Examples:
- **Simple**: `region = 'us-west'`
- **Complex**: `role == 'admin' AND (tags['env'] == 'production' OR tags['priority'] == 'critical')`
- **Wildcards**: `type == 'PostgreSQL'` (supports regex or exact matches).

### **2. Performance Optimization**
- **Indexing**: Add indexes on `(operator_id, db_id, op_id)` in `availability_matrix`.
- **Caching**: Cache evaluated rules for frequently accessed DBs.
- **Pre-computation**: For static rules, pre-compute all valid operator-DB-op combinations.

### **3. Dynamic Operator Assignment**
Extend the pattern to support:
- **Time-based rules**: `HOUR(BACKUP_TIME) BETWEEN 2 AND 6`.
- **Load-based rules**: `cur_db_load < 80%`.
- **Autoscaling**: Route ops to operators with available capacity.

### **4. Audit Trails**
Log all rule evaluations with:
- Timestamp of check.
- Operator, DB, and operation involved.
- Result (`allowed`/`denied`).
- Condition evaluated (sanitized).

---

## **Query Examples: Advanced Scenarios**

### **1. Find All Databases an Operator Can Access**
**SQL**:
```sql
SELECT DISTINCT d.name, d.type, d.region
FROM availability_matrix a
JOIN databases d ON a.db_id = d.db_id
JOIN operations op ON a.op_id = op.op_id
WHERE a.operator_id = 'op-001'
  AND a.rule_condition IS NULL
  OR (a.rule_condition IS NOT NULL
      AND EVALUATE_CONDITION(d, a.rule_condition) = true);
```

### **2. Simulate Operator Swapping**
**Use Case**: Temporarily assign an operator (`op-002`) to a DB during maintenance.

**SQL**:
```sql
-- Add a temporary rule (expires after 24h)
INSERT INTO availability_matrix (operator_id, db_id, op_id, rule_condition)
VALUES ('op-002', 'db-001', 'op-backup', 'NOT EXISTS(SELECT 1 FROM temp_exclusions WHERE db_id = $$DB_id)');

-- Later, remove the rule
DELETE FROM availability_matrix
WHERE operator_id = 'op-002' AND rule_condition = 'NOT EXISTS(SELECT 1 FROM temp_exclusions WHERE db_id = $$DB_id)';
```

### **3. Generate a Compliance Report**
**SQL**:
```sql
SELECT
    o.role,
    COUNT(DISTINCT d.name) as databases_authorized,
    COUNT(DISTINCT op.name) as operations_authorized
FROM availability_matrix a
JOIN operators o ON a.operator_id = o.operator_id
JOIN databases d ON a.db_id = d.db_id
JOIN operations op ON a.op_id = op.op_id
GROUP BY o.role
HAVING COUNT(DISTINCT d.name) > 0;
```

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                 | **When to Use Together**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **[Least Privilege Principle](https://docs.aws.amazon.com/ioc/latest/userguide/least-privilege.html)** | Restrict operators to only necessary permissions.                                  | Combine with OAM to enforce minimal access rights.                                    |
| **[Service Mesh for DB Operations](https://istio.io/latest/docs/concepts/traffic-management/)** | Route DB ops via a service mesh for centralized control.                         | Use OAM to define which mesh-sidecar operators can invoke DB services.                |
| **[Database Tagging](https://docs.aws.amazon.com/AWSSupport/latest/user/gs-tagging.html)** | Tag databases for categorization (e.g., `env=production`).                      | Leverage tags in OAM conditions for dynamic rule evaluation.                            |
| **[Operation Chaining](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch07.html)** | Sequence multiple ops (e.g., backup → verify → alert).                           | Use OAM to ensure each step in the chain is assigned to the correct operator.          |
| **[Canary Releases for DB Updates](https://cloud.google.com/blog/products/devops-sre/canary-deployments-for-microservices)** | Gradually roll out DB changes to a subset of operators.                         | Pair with OAM to restrict canary ops to approved operators.                            |
| **[Event-Driven Operator Assignment](https://www.event-driven.io/en/)** | Assign operators based on real-time events (e.g., DB alert).                     | Use OAM rules triggered by event streams (e.g., Kafka, Pub/Sub).                        |

---

## **Anti-Patterns to Avoid**
1. **Hardcoding Operator-DB Mappings**
   - *Problem*: Rule changes require schema migrations.
   - *Solution*: Use dynamic conditions and audit logs.

2. **Overly Complex Conditions**
   - *Problem*: Conditions like `IF (HOSTNAME() LIKE '%server%') AND (USER() = 'admin') THEN ALLOW` are hard to maintain.
   - *Solution*: Limit conditions to DB metadata (tags, region) and operator roles.

3. **No Fallback for Dynamic Rules**
   - *Problem*: If a rule evaluation fails, assume denial without fallback.
   - *Solution*: Default to `ALLOW` unless explicitly denied.

4. **Ignoring Operator Capacity**
   - *Problem*: Assigning too many ops to a single operator during peak loads.
   - *Solution*: Integrate with capacity monitoring tools (e.g., Prometheus).

---

## **Tools and Libraries**
| **Tool/Library**               | **Purpose**                                                                 | **Link**                                                                 |
|---------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **SQLJMESPath**                | Evaluate JSONPath-like conditions in SQL.                                  | [GitHub](https://github.com/agiliq/sqljmespath)                          |
| **Apache Drill**                | SQL engine for dynamic rule evaluation on NoSQL.                           | [Website](https://drill.apache.org/)                                     |
| **OpenPolicyAgent (OPA)**       | Enforce policies (including OAM rules) via Rego language.                    | [Website](https://www.openpolicyagent.org/)                             |
| **Slack/Teams Notifications**   | Alert operators when ops are assigned to them.                             | Integrate with OPA or custom scripts.                                    |
| **Terraform Provider for DBs**  | Manage OAM rules as infrastructure-as-code (IaC).                         | Example: [AWS RDS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/rds_instance) |

---
## **Example: Full Workflow**
1. **Define the Matrix**:
   ```json
   // availability_matrix.json
   {
     "rules": [
       {
         "operator": "op-001",
         "db": "prod-db",
         "op": "backup",
         "condition": "region == 'us-west' && tags['backup_schedule'] == 'daily'"
       }
     ]
   }
   ```
2. **Query the Matrix**:
   ```bash
   # Using OPA (Open Policy Agent)
   opactl eval -f availability_matrix.rego \
     --input '{"db": {"region": "us-west", "tags": {"backup_schedule": "daily"}}}' \
     --bundle policies/opa-bundle
   ```
3. **Automate with CI/CD**:
   - Hook the OAM check into a GitHub Action before deploying a DB patch:
     ```yaml
     # .github/workflows/db-patch-check.yml
     - name: Check OAM
       run: |
         echo "Operator: ${{ github.actor }}"
         echo "DB: ${{ env.TARGET_DB }}"
         echo "Op: patch"
         opactl eval -f availability_matrix.rego \
           --input "{\"db\": {\"region\": \"${{ env.DB_REGION }}\"}}"
     ```

---
## **Summary of Key Actions**
| **Action**                          | **Query/Code Example**                                                                 |
|-------------------------------------|---------------------------------------------------------------------------------------|
| **Add a new operator-DB-op rule**   | `INSERT INTO availability_matrix VALUES ('op-001', 'db-001', 'op-backup', 'region = "us-west"')` |
| **List all rules for a DB**         | `SELECT * FROM availability_matrix WHERE db_id = 'db-001'`                              |
| **Check operator availability**    | `SELECT EXISTS(SELECT 1 FROM availability_matrix WHERE ...)`                           |
| **Generate a compliance report**   | Aggregation query joining `operators`, `databases`, and `availability_matrix`.      |
| **Dynamic rule evaluation**        | Use `eval()` with sanitized conditions or OPA.                                      |

---
This guide provides a structured approach to implementing the **Operator Availability Matrix** pattern. For production use, validate rule conditions thoroughly and monitor for edge cases (e.g., conflicting rules, metadata changes).