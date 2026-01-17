# **[Pattern] Schema Snapshot Diffing Reference Guide**
*A FraiseQL Pattern for Safe Schema Evolution via Automated Change Detection*

---

## **1. Overview**
Schema snapshot diffing is a **real-time comparison** mechanism in FraiseQL that identifies **breaking changes** between schema versions—such as field deletions, type modifications, or added constraints. By generating **detailed diff reports**, this pattern enables teams to:
- **Proactively detect regressions** before deployment.
- **Automate migration planning** with clear actionable steps.
- **Maintain backward/forward compatibility** with minimal manual review.

Unlike manual diffing or third-party tools, FraiseQL’s diffing is **integrated** into the query engine, parsing schema metadata directly from FraiseQL’s internal model. This ensures accuracy across **any database dialect** (PostgreSQL, MySQL, Snowflake, etc.) and eliminates parsing inconsistencies.

---

## **2. Key Schema Reference**
FraiseQL’s diffing compares two schema snapshots (versions) using the following **core constructs**:

| **Field**               | **Description**                                                                 | **Example Value**                     |
|-------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **`snapshot_id`**       | Unique identifier for a schema version (e.g., commit hash or timestamp).       | `"v2024-01-15T14:30:00Z"`              |
| **`tables`**            | Array of table objects, each with metadata.                                     | `[{"name": "users", "columns": [...]}]`|
| **`columns`**           | Array of column objects per table, including:                                   | `{name: "email", type: "TEXT", ...}`  |
| **`type`**              | Data type (e.g., `TEXT`, `INT`, `JSONB`).                                      | `"JSONB"`                              |
| **`is_required`**       | Boolean flag if the column is `NOT NULL`.                                       | `true`/`false`                        |
| **`default_value`**     | Default value (if specified).                                                   | `"DEFAULT_ROLE"`                      |
| **`deprecated`**        | Boolean flag marking columns as obsolete (for future removal).                | `true`                                |
| **`added_at`**          | Timestamp when the column was introduced.                                       | `"2024-01-10T09:00:00Z"`              |
| **`removed_at`**        | Timestamp when the column was deleted (if `null`, still exists).               | `"2024-01-14T12:00:00Z"`              |

---
**Example Schema Snapshot (JSON):**
```json
{
  "snapshot_id": "v2024-01-15",
  "tables": [
    {
      "name": "users",
      "columns": [
        { "name": "id", "type": "BIGSERIAL", "is_required": true },
        { "name": "email", "type": "TEXT", "is_required": true, "default_value": null },
        { "name": "premium_status", "type": "BOOLEAN", "default_value": false },
        { "name": "legacy_data", "type": "JSONB", "deprecated": true }
      ]
    }
  ]
}
```

---

## **3. Schema Diffing Query Examples**
FraiseQL provides **native diffing queries** to compare snapshots. Use the [`diff_snapshots()`](https://fraise.com/docs/api/diff_snapshots) function to generate reports.

---

### **3.1 Basic Diff (All Breaking Changes)**
```sql
-- Compare two snapshots and list all breaking changes
SELECT
  diff_snapshots(
    snapshot_a: 'v2024-01-10',
    snapshot_b: 'v2024-01-15'
  )
  ->> 'breaking_changes';
```
**Output:**
```json
{
  "removed_columns": ["legacy_data"],
  "type_changes": [
    { "table": "users", "column": "email", "old_type": "VARCHAR(255)", "new_type": "TEXT" }
  ],
  "added_constraints": ["users.email.is_required"]
}
```

---

### **3.2 Filtered Diff (Only Critical Changes)**
```sql
-- Focus on changes that would break existing applications
SELECT
  diff_snapshots(
    snapshot_a: 'v2024-01-10',
    snapshot_b: 'v2024-01-15',
    filter: 'CRITICAL'
  )
  ->> 'critical_changes';
```
**Output:**
```json
{
  "removed_columns": ["legacy_data"],
  "required_field_added": ["email"]  -- Previously optional, now required
}
```

---

### **3.3 Migration Plan Generator**
```sql
-- Generate SQL migration steps for schema updates
SELECT
  generate_migration_plan(
    snapshot_a: 'v2024-01-10',
    snapshot_b: 'v2024-01-15'
  )
  ->> 'steps';
```
**Output:**
```sql
[
  { "action": "ADD_CONSTRAINT", "sql": "ALTER TABLE users ADD CONSTRAINT email_not_null CHECK (email IS NOT NULL);" },
  { "action": "DROP_COLUMN", "sql": "ALTER TABLE users DROP COLUMN legacy_data;" }
]
```

---

### **3.4 Deprecation Roadmap**
```sql
-- Identify deprecated columns + their usage
SELECT
  find_deprecated_columns(
    snapshot_id: 'v2024-01-15'
  )
  ->> 'roadmap';
```
**Output:**
```json
{
  "columns": [
    {
      "name": "legacy_data",
      "replaces": ["user_prefs", "settings"],
      "deprecation_date": "2024-06-01",
      "replacement_query": "SELECT jsonb_to_recordset(settings -> 'user_prefs') AS user_prefs"
    }
  ]
}
```

---

## **4. Change Severity Levels**
FraiseQL categorizes changes by impact. Use the `severity` filter to prioritize fixes:

| **Severity**       | **Description**                                                                 | **Example**                          |
|--------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **CRITICAL**       | Breaks all existing applications (removed fields, type changes).            | Dropping a primary key column.       |
| **MAJOR**          | Breaks specific queries (e.g., required fields, default value removal).     | Making `email` `NOT NULL`.          |
| **MINOR**          | New columns or optional changes (safe to apply).                           | Adding `created_at` timestamp.       |
| **DEPRECATED**     | Columns marked for future removal (no immediate impact).                     | `legacy_data` flagged as obsolete.   |

**Query Example:**
```sql
SELECT
  diff_snapshots(
    snapshot_a: 'v2024-01-10',
    snapshot_b: 'v2024-01-15',
    severity: ['CRITICAL', 'MAJOR']
  )
  ->> 'results';
```

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Use Case**                          |
|----------------------------------|---------------------------------------------------------------------------------|----------------------------------------|
| **[Schema Versioning](https://fraise.com/docs/patterns/versioning)** | Track schema changes with semantic versioning (e.g., `v1.0.0` → `v2.0.0`).   | Managing release cycles.               |
| **[Backward Compatibility Checks](https://fraise.com/docs/patterns/compatibility)** | Validate schema changes won’t break legacy apps.                          | CI/CD pipeline validation.             |
| **[Query Migration Scripts](https://fraise.com/docs/patterns/migrate)** | Auto-generate SQL for schema updates.                                     | Database deployment automation.        |
| **[Schema-as-Code](https://fraise.com/docs/patterns/as-code)**         | Define schemas in code (e.g., Terraform, SQL scripts).                     | Infrastructure-as-code workflows.      |

---

## **6. Best Practices**
1. **Snapshot Frequently**
   - Take snapshots before **every major release** or **feature branch merge**.
   - Use Git commits or CI pipeline triggers (`on: push`).

2. **Automate Critical Checks**
   - Integrate diffing into **pre-deployment hooks** (e.g., GitHub Actions):
     ```yaml
     - name: Run Schema Diff
       run: |
         fraise diff --snapshot-a v1.0.0 --snapshot-b HEAD --severity CRITICAL
     ```

3. **Plan for Deprecations**
   - Use `deprecated: true` for columns marked for removal.
   - Provide **replacement queries** in the roadmap (see **3.4**).

4. **Test Migrations**
   - Run `generate_migration_plan()` in a **staging environment** before production.

5. **Document Breaking Changes**
   - Surface diff results in **release notes** or **CHANGELOG.md**:
     ```markdown
     ## Breaking Changes (v2.0.0)
     - Removed `legacy_data` column (use `settings` instead).
     - Made `email` field required.
     ```

---
## **7. Limitations**
- **No Live Data Impact**: Diffing is **metadata-only**; always test migrations on a copy of production data.
- **Third-Party Schema**: External schemas (e.g., Kafka topics) require manual validation.
- **Performance**: Large schemas (>10k columns) may slow down diffing. Use `filter` to narrow scope.

---
## **8. Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| Diff shows false positives.         | Verify snapshots were taken at the same logical time (e.g., same DB state). |
| Missing columns in diff.            | Ensure snapshots include all tables (check `schema.included_tables`).       |
| Migration plan generates invalid SQL. | Review `generate_migration_plan()` output for dialect-specific quirks.    |

---
**See Also:**
- [FraiseQL Diffing API Docs](https://fraise.com/docs/api/diff_snapshots)
- [Schema Versioning Guide](https://fraise.com/docs/patterns/versioning)