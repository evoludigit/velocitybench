# **Debugging the Capability Manifest Design Pattern: A Troubleshooting Guide**
*Quickly diagnose and resolve issues in capability-driven database compilation*

---

## **1. Introduction**
The **Capability Manifest Design** pattern enables database-specific feature declarations to drive code generation, ensuring compatibility and performance optimizations. If implemented correctly, it allows seamless addition of new databases and prevents manual operator overrides. However, issues like incorrect operator selection or manual overrides can arise if the pattern isn’t followed strictly.

This guide provides a structured approach to troubleshoot common problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, verify which symptoms match your issue:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| Wrong operators generated           | Generated SQL/plan uses incorrect operators (e.g., `LIKE` → `=`).              |
| Manual SQL overrides                  | Developers bypass capability declarations (violating the pattern).             |
| New database support is cumbersome    | Adding a new database requires excessive changes outside the manifest.         |
| Performance degradation              | Generated operators are suboptimal (e.g., full table scans instead of indexes). |
| Build/compilation errors             | Capability files are missing, misconfigured, or incompatible.                  |

*(Check all applicable symptoms before proceeding.)*

---

## **3. Common Issues and Fixes**

### **Issue 1: Wrong Operators Generated**
**Symptoms:**
- Generated SQL uses unsupported operators (e.g., PostgreSQL `ILIKE` → `LIKE`).
- Operator mapping is inconsistent across databases.

**Root Cause:**
- Incorrect **operator mappings** in the capability manifest (`manifest.yaml`/`capability.json`).
- Missing or outdated mappings for new operators.

**Fix:**
1. **Verify Operator Mappings**
   Ensure the capability manifest defines correct mappings per database. Example:
   ```yaml
   # manifest.yaml
   databases:
     postgres:
       operators:
         LIKE: POSTGRES_LIKE
         ILIKE: POSTGRES_ILIKE  # Custom implementation
     mysql:
       operators:
         LIKE: MYSQL_LIKE
   ```
   - If `ILIKE` isn’t natively supported, define a custom implementation (e.g., `LOWER(column) LIKE LOWER(%term%)`).

2. **Check Code Generation Logic**
   If operators are hardcoded, modify the generator to use the manifest:
   ```java
   // Pseudo-code: Ensure compiler respects manifest
   String operator = capabilityManifest.getOperatorForDB(dbType, "ILIKE");
   String sql = "SELECT * FROM table WHERE col " + operator + " ?";
   ```

3. **Test with Multiple Databases**
   Confirm mappings work across supported databases via unit tests.

---

### **Issue 2: Manual SQL Overrides Violate the Pattern**
**Symptoms:**
- Developers directly write SQL instead of using capability-generated operators.
- Build system ignores capability declarations.

**Root Cause:**
- Lack of enforcement (e.g., no compile-time checks).
- Developers unaware of the pattern’s purpose.

**Fix:**
1. **Enforce Capability Usage**
   Add a **pre-build hook** to validate SQL against the manifest:
   ```bash
   # Example: Script to validate SQL before build
   ! grep -v "SELECT" generated_queries.sql || {
     echo "Error: SQL bypasses capability manifest!"
     exit 1
   }
   ```
   Or use a linter (e.g., SQLFluff) to enforce compliance.

2. **Update Documentation**
   Add comments in code/templates reminding devs to use capabilities:
   ```java
   // ❌ Avoid: Hardcoded SQL
   String badQuery = "SELECT * FROM users WHERE name = 'John';"

   // ✅ Use capability-generated operator
   String goodQuery = capabilityService.buildQuery("ILIKE", name, "John");
   ```

3. **Deprecate Direct SQL**
   Flag deprecated direct-SQL methods in code with warnings:
   ```java
   @Deprecated(since = "v2.0", forRemoval = true)
   String legacySqlQuery(String query) { ... }
   ```

---

### **Issue 3: Adding a New Database is Tedious**
**Symptoms:**
- Extending support to a new database (e.g., Snowflake) requires changes beyond the manifest.
- Build fails due to missing capability files.

**Root Cause:**
- Incomplete capability templates.
- Database-specific logic scattered across codebase.

**Fix:**
1. **Standardize Capability Files**
   Ensure all databases follow the same structure:
   ```
   /capabilities/
   ├── postgres/
   │   ├── operators.yaml
   │   ├── functions.yaml
   │   └── dialect.sqo
   ├── mysql/
   ├── snowflake/
   ```

2. **Automate Manifest Generation**
   Use a **generator script** to scaffold new database capabilities:
   ```bash
   # Script to create a new capability directory
   mkdir -p capabilities/{new_db}
   cp capabilities/postgres/operators.yaml capabilities/new_db/
   # Replace placeholders (e.g., "POSTGRES_LIKE" → "SNOWFLAKE_LIKE")
   ```

3. **Centralize Database-Specific Logic**
   Move dialect-specific code to capability modules:
   ```java
   // Before: Scattered logic
   public String buildLikeQuery(String dbType, String column, String term) {
     if (dbType.equals("POSTGRES")) { ... }
     if (dbType.equals("SNOWFLAKE")) { ... }
   }

   // After: Delegate to capability module
   public String buildLikeQuery(String dbType) {
     return capabilities.get(dbType).buildLikeQuery();
   }
   ```

---

### **Issue 4: Performance Degradation Due to Incorrect Operators**
**Symptoms:**
- Generated queries ignore indexes (e.g., `WHERE col LIKE '%term'` instead of `WHERE col ILIKE :term`).
- Full table scans despite index availability.

**Root Cause:**
- Operator mappings prioritize correctness over efficiency.
- No performance benchmarks in capability tests.

**Fix:**
1. **Benchmark Operator Choices**
   Test operator alternatives before finalizing manifests:
   ```sql
   -- Test: Which is faster? LIKE '%term' or ILIKE :term?
   EXPLAIN ANALYZE
   SELECT * FROM users WHERE name LIKE '%John';
   ```

2. **Flag Inefficient Operators**
   Add warnings in the manifest for suboptimal choices:
   ```yaml
   databases:
     mysql:
       operators:
         LIKE: MYSQL_LIKE  # ⚠️ Avoid leading wildcards; use `LIKE :term` instead
   ```

3. **Update Defaults to Optimized Operators**
   Replace:
   ```yaml
   ILIKE: ILIKE  # Default (may be slow)
   ```
   With:
   ```yaml
   ILIKE: CASE_WHEN_DB_IS_MYSQL THEN "LOWER(col) LIKE LOWER(:term)" ELSE ILIKE END
   ```

---

## **4. Debugging Tools and Techniques**

| **Tool/Technique**               | **Purpose**                                                                 | **Example Usage**                                  |
|-----------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **SQL Profiler**                 | Inspect generated queries for inefficiencies.                            | `pg_stat_statements` (PostgreSQL)                  |
| **Manifest Validator**           | Validate capability files for syntax/consistency errors.                 | Run `./validate_manifest.sh capabilities/`        |
| **Capability Test Suite**        | Unit tests for operator correctness per database.                         | `pytest tests/capability_tests.py`               |
| **Query Plan Analyzer**          | Compare planned execution paths.                                           | `EXPLAIN ANALYZE SELECT ...`                      |
| **Dependency Injection Mocks**   | Isolate capability logic for debugging.                                   | Mock `CapabilityService` in unit tests.           |
| **Build-Time Checks**            | Catch violations early (e.g., missing operators).                          | CI pre-build step: `check-capability-compliance` |

**Example Debug Workflow:**
1. **Reproduce the issue** by running a query with a problematic operator.
2. **Inspect the generated SQL** (e.g., via logs or profiler).
3. **Compare against the manifest** to find mismatches.
4. **Unit test the capability** in isolation:
   ```java
   @Test
   void testPostgresILikeMapping() {
     assertEquals("LOWER(col) LIKE LOWER(:term)",
                  postgresCapability.buildILikeQuery());
   }
   ```

---

## **5. Prevention Strategies**

### **A. Design-Time Rules**
1. **Standardize Capability Files**
   Enforce a schema (e.g., JSON Schema) for manifests:
   ```json
   {
     "$schema": "https://example.com/capability-schema.json",
     "databases": {
       "postgres": { "operators": { "ILIKE": "LOWER(col) LIKE LOWER(:term)" } }
     }
   }
   ```

2. **Automate Manifest Validation**
   Add a **pre-commit hook** to lint manifests:
   ```yaml
   # .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: validate-capability
         name: Validate capability files
         entry: ./scripts/validate_capability.py
         language: system
   ```

### **B. Runtime Enforcement**
1. **Compile-Time Checks**
   Use build tools (Maven/Gradle) to verify capabilities:
   ```xml
   <!-- Maven plugin to validate capabilities -->
   <plugin>
     <groupId>com.example</groupId>
     <artifactId>capability-validator</artifactId>
     <executions>
       <execution>
         <phase>validate</phase>
         <goals><goal>check</goal></goals>
       </execution>
     </executions>
   </plugin>
   ```

2. **Feature Flags for Deprecated Operators**
   Gradually phase out inefficient operators:
   ```java
   public String buildLikeQuery(String dbType, boolean useNewSyntax) {
     if (useNewSyntax) {
       // Use parameterized ILIKE
       return capabilityService.buildQuery("ILIKE", term);
     } else {
       // Legacy LIKE (deprecated)
       return capabilityService.buildQuery("LIKE", term);
     }
   }
   ```

### **C. CI/CD Integration**
1. **Test Capabilities Across Databases**
   Use CI to validate manifests against multiple database backends:
   ```yaml
   # GitHub Actions
   jobs:
     test-capabilities:
       runs-on: ubuntu-latest
       services:
         postgres:   { ports: ["5432"] }
         mysql:      { ports: ["3306"] }
       steps:
         - run: ./test-capability.sh postgres mysql
   ```

2. **Alert on Manifest Changes**
   Notify the team when capabilities are updated:
   ```bash
   # Script to alert on manifest changes
   git diff --name-only HEAD~1 | grep 'capabilities/.*\.yaml$' | tee /dev/null && \
   echo "⚠️ Capability files modified! Notify team." | write-to-slack
   ```

### **D. Documentation and Training**
1. **Onboarding Guide**
   Add a **capability pattern cheat sheet** for new devs:
   ```
   📌 How to add a new operator:
   1. Edit capabilities/{db}/operators.yaml
   2. Test with: ./run-capability-tests.sh {db}
   3. Merge with /approve
   ```

2. **Running Examples**
   Include **do’s and don’ts** in code reviews:
   ```markdown
   🚫 Avoid:
   ```sql
   -- Hardcoded SQL breaks the pattern!
   SELECT * FROM users WHERE name = 'John';
   ```

   ✅ Prefer:
   ```java
   // Use capability-generated SQL
   String query = capabilityService.buildQuery("=", "name", "John");
   ```

   ```

---

## **6. Summary Checklist for Quick Resolution**
| **Step**                          | **Action**                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| 1. **Identify the symptom**       | Use the symptom checklist to pinpoint the issue.                          |
| 2. **Inspect the manifest**       | Check `capabilities/{db}/operators.yaml` for errors.                      |
| 3. **Test generated SQL**         | Run queries and compare plans with `EXPLAIN`.                            |
| 4. **Validate capability code**   | Run unit tests targeting the manifest logic.                              |
| 5. **Enforce compliance**         | Add build checks/linters to prevent bypasses.                             |
| 6. **Benchmark fixes**            | Verify performance improvements.                                           |
| 7. **Document the fix**           | Update onboarding docs and add comments to affected code.                 |

---

## **7. Next Steps**
- **For immediate fixes:** Use the **Issue 1-4 fixes** above to resolve symptoms.
- **For long-term health:** Implement **prevention strategies** (CI/CD, training).
- **For new databases:** Follow the **automated scaffold** approach.

By following this guide, you’ll **diagnose issues efficiently** and **prevent reoccurrences** in capability-driven database compilation.