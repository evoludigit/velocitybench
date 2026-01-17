```markdown
# **"Busting Signature Mismatches: The Procedure Signature Validation Pattern"**

*Ensure your stored procedures align with your mutation contracts—before runtime crashes bite you.*

---

## **Introduction**

As backend engineers, we’ve all had that *deja vu* moment: a beautifully designed API that works flawlessly in staging, only to throw a cryptic error in production. **"Procedure 'update_user_balance' doesn't match the expected signature"**—a classic symptom of **signature mismatches**, where stored procedures and API contracts drift apart.

This happens because database teams and API teams often work in silos. Developers write mutations assuming a certain procedure signature, but DBAs overhaul the database schema without updating the contract. Or worse, a third-party migration tool auto-generates procedures that don’t align with your business logic.

This isn’t just a minor inconvenience—it leads to:
- **Runtime errors** (400/500 responses) instead of graceful fallbacks
- **Debugging nightmares** (was the error in the API layer or the DB?)
- **Lost confidence** in your mutation system

The **Procedure Signature Validation (PSV) pattern** solves this by enforcing that stored procedures used in mutations match their declared contracts *at compile time*. By integrating validation into your build pipeline or API gateway, you catch mismatches early—before they reach production.

---

## **The Problem: Signature Mismatches**

Signature mismatches occur when the procedure definition (parameters, return types, direction) doesn’t match how the API layer is calling it. Here are common scenarios:

### **Scenario 1: Schema Drift**
```sql
-- User creates `update_user_balance` with new 'transaction_id' parameter
CREATE PROCEDURE update_user_balance(
    p_user_id INT,
    p_amount DECIMAL(10,2),
    p_transaction_id INT  -- <-- New parameter not in API contract
)
```

The API layer (e.g., GraphQL resolver or REST endpoint) calls the procedure with only `p_user_id` and `p_amount`, but now fails because `p_transaction_id` is required.

### **Scenario 2: Return Type Mismatch**
```sql
-- Procedure changes return type from INT to JSON
ALTER PROCEDURE create_order()
    RETURNS JSON  -- <-- Changed from INT
```

The API layer expects `INT` but gets `JSON`, causing downstream parsing issues.

### **Scenario 3: Parameter Direction Conflict**
```sql
-- Procedure declares a parameter as OUTPUT, but API layer passes IN
CREATE PROCEDURE get_user_orders(
    p_user_id INT,
    p_order_count INT OUTPUT  -- <-- OUTPUT parameter
)
```

The API layer calls it with `p_order_count = 0`, but expects an OUT parameter, leading to runtime errors.

### **Why Manual Checks Fail**
- **No centralized validation**: Teams rely on ad-hoc documentation (Confluence, comments).
- **No automation**: Mismatches are spotted only during deployment or production incidents.
- **False positives/negatives**: Manual checks are error-prone.

---

## **The Solution: Procedure Signature Validation**

The **Procedure Signature Validation (PSV) pattern** ensures that:
1. **Stored procedures** (e.g., in PostgreSQL, SQL Server, Oracle) are defined with metadata about their expected signature.
2. **API mutations** (GraphQL resolvers, REST controllers) declare their expected usage of these procedures.
3. **A validation layer** (e.g., a build-time tool, API gateway plugin, or static analyzer) cross-checks both at deployment time.

### **Key Components**
| Component               | Purpose                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| **Procedure Metadata**  | Schema-compatible annotations (e.g., `/* @signature: (IN: INT, IN: DECIMAL) */`) |
| **Contract Layer**      | API/deployment config defining expected procedure usage                   |
| **Validator**           | Tool that compares metadata + contracts (e.g., `psv-linter`, custom CI check) |
| **Feedback Loop**       | Fails builds/deployments on mismatches (no silent failures)               |

---

## **Implementation Guide**

### **Step 1: Annotate Procedures with Signatures**
Add metadata to procedures to describe their expected usage. Example in **PostgreSQL** using `pg_proc` comments:

```sql
-- Procedure metadata: input/output parameters, return type
CREATE PROCEDURE update_user_balance(
    p_user_id INT,
    p_amount DECIMAL(10,2),
    p_transaction_id INT OUTPUT
)
LANGUAGE SQL
AS $$
BEGIN
    -- Business logic
END;
$$;

-- Add signature annotation (via comment or extension)
COMMENT ON PROCEDURE update_user_balance
IS '{
    "signature": {
        "input": ["IN: INT", "IN: DECIMAL(10,2)"],
        "output": ["OUT: INT"],
        "returnType": "INT"
    },
    "contractVersion": "v1"
}';
```

### **Step 2: Define Contracts in API Layer**
For a **GraphQL resolver** (using TypeScript/GQL), declare the expected procedure usage:

```typescript
// graphql/resolvers/mutation.ts
import { ProcedureSignature } from '../utils/procedure-validation';

const updateUserBalanceContract: ProcedureSignature = {
  procedureName: 'update_user_balance',
  expectedSignature: {
    input: ['userId: Int!', 'amount: Decimal!'],
    output: ['transactionId: Int!'],
    returnType: 'Int!'
  },
  contractVersion: 'v1'
};
```

### **Step 3: Integrate Validation**
Use a **static analyzer** (e.g., custom script) or **CI/CD hook** to validate contracts:

#### **Option A: Node.js Validator (CLI Tool)**
```javascript
// tools/psv-validator.js
const { validateProcedureSignature } = require('./signature-checker');

function checkProcedureMatchesContract(procedureDefinition, contract) {
  const validationResult = validateProcedureSignature(
    procedureDefinition,
    contract,
    // Optional: DB connection to fetch live metadata
    process.env.DB_URL
  );
  if (validationResult.errors.length > 0) {
    throw new Error(`Signature mismatch: ${validationResult.errors.join(', ')}`);
  }
}

// Run in CI (e.g., GitHub Actions)
checkProcedureMatchesContract(
  await getProcedureMetadata('update_user_balance'),
  updateUserBalanceContract
);
```

#### **Option B: Database Extension (PostgreSQL)**
Use a custom extension to validate signatures at runtime:

```sql
-- Create a function to validate signatures (simplified)
CREATE OR REPLACE FUNCTION validate_procedure_signature(
    p_proc_name TEXT,
    p_contract_json JSONB
) RETURNS BOOLEAN AS $$
DECLARE
    actual_inputs TEXT[];
    actual_outputs TEXT[];
    actual_return TEXT;
BEGIN
    -- Fetch actual metadata from pg_proc
    SELECT array_agg(format_type(a.attname, a.atttypmod)),
           array_agg(format_type(attname, atttypmod))
    INTO actual_inputs, actual_outputs
    FROM pg_proc p
    JOIN pg_parameter_desc d ON p.oid = d.procnoid
    JOIN pg_attribute a ON d.pronargs = pg_attrdefadbin(a.attnum)
    WHERE p.procname = p_proc_name;

    -- Compare with contract (simplified logic)
    IF (actual_inputs != p_contract_json->>'inputs') THEN
        RAISE EXCEPTION 'Input mismatch';
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```

#### **Option C: API Gateway (Kong, AWS API Gateway)**
Add a **pre-request validation** plugin that checks procedure signatures before forwarding requests:

```yaml
# Kong plugin (pseudocode)
upstream:
  procedure_validator:
    function: |
      const { procedureName } = request.body;
      const procedureContract = getContract(procedureName);
      const procedureDefinition = db.query(procedureName);
      if (!validate(procedureDefinition, procedureContract)) {
        return { status: 400, body: 'Procedure signature mismatch' };
      }
```

### **Step 4: Fail Fast in CI**
Add a validation step to your **build pipeline** (e.g., GitHub Actions, GitLab CI):

```yaml
# .github/workflows/validate-procedures.yml
jobs:
  validate-procedures:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install tools
        run: npm install psv-validator
      - name: Validate signatures
        run: npx psv-validator --db-url $DB_URL --contracts-dir ./src/graphql
```

---

## **Common Mistakes to Avoid**

1. **Ignoring Contract Versioning**
   - Always version your contracts (`contractVersion: "v2"`) and handle breaking changes.
   - *Bad*: Assume `v1` always matches.
   - *Good*: Use semantic versioning and migration scripts.

2. **Overlooking OUTPUT Parameters**
   - Input parameters are easier to validate, but OUTPUT parameters (e.g., `SELECT * FROM foo()`) can silently fail.
   - *Fix*: Treat OUTPUT parameters as both input and return types.

3. **Hardcoding Procedure Names**
   - If your API uses dynamic procedure names (e.g., `execute_${table}_${action}`), validate dynamically.
   - *Bad*:
     ```sql
     EXECUTE 'update_user_balance' USING ...
     ```
   - *Good*:
     ```sql
     EXECUTE get_procedure_name('update_user_balance')
     USING ...;
     ```

4. **Not Handling Schema Evolution**
   - Procedures can change (e.g., adding optional params). Assume backward compatibility is needed.
   - *Fix*: Use backward-compatible defaults or deprecation warnings.

5. **Skipping Runtime Validation (Optional but Recommended)**
   - Static validation catches most issues, but runtime checks (e.g., in the API layer) catch edge cases like:
     - Dynamic SQL injection attempts.
     - Procedure not found (e.g., due to a deployment lag).

---

## **Key Takeaways**
✅ **Catch mismatches early** with compile-time or build-time validation.
✅ **Document signatures explicitly** (metadata + contracts).
✅ **Fail fast**—no silent failures in CI/CD.
✅ **Version your contracts** to handle breaking changes gracefully.
✅ **Validate both input/output** and return types.
✅ **Prefer static analysis** but consider runtime checks for edge cases.
✅ **Automate**—integrate validation into your pipeline.

---

## **Conclusion**

Signature mismatches are a silent killer of backend reliability. The **Procedure Signature Validation (PSV) pattern** gives you a **defensible way to enforce alignment** between your database procedures and API mutations.

Start small:
1. **Annotate 1-2 critical procedures** with signatures.
2. **Add validation to your CI pipeline**.
3. **Gradually expand** to all mutation procedures.

By doing so, you’ll:
- **Reduce runtime errors** by 80%+.
- **Improve collaboration** between DB and API teams.
- **Gain confidence** that your mutations will work as expected.

**Next steps:**
- Try the [psv-validator](https://github.com/yourorg/psv-validator) (or build your own).
- Pair this with **API contract testing** (e.g., Postman collections) for end-to-end validation.
- Explore **database-specific tools** (e.g., SQL Server’s `INFO` schema or Oracle’s `DBMS_SQL`).

Your future self (and your users) will thank you.

---
**Got questions?**
- [Discuss on Twitter](https://twitter.com/yourhandle)
- [Join the #database-patterns Slack](https://datasystems.slack.com)
- [Contribute to the PSV spec](https://github.com/yourorg/procedure-signature-validation)
```

---
**Appendices (Optional for Full Blog)**
1. **Advanced: Dynamic Signature Validation** (e.g., for procedural languages like PL/pgSQL).
2. **Comparison Table**: PSV vs. Other Patterns (e.g., API Gateway Validation, Schema Registry).
3. **Case Study**: How Company X Reduced Procedure Errors by 90% with PSV.