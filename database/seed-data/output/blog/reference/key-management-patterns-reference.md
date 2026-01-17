# **[Pattern] Key Management Patterns Reference Guide**
*Abstracting Key Management Across Multiple Backends with FraiseQL*

---

## **Overview**
FraiseQL’s **Key Management Patterns** abstraction ensures seamless integration with multiple Key Management System (KMS) backends (e.g., HashiCorp Vault, AWS KMS, GCP KMS, or local key stores) while enforcing best practices like **automated key rotation**, **zero-downtime key updates**, and **backward compatibility**. This pattern standardizes how keys are generated, rotated, and revoked across environments, reducing vendor lock-in and operational overhead.

Key features:
- **Unified API**: Treat all KMS providers uniformly via FraiseQL syntax.
- **Automated Rotation**: Configurable policies for periodic or event-based key rotation.
- **Backward Compatibility**: Transparent key revocation with zero downtime.
- **Multi-Tenancy**: Isolate keys by namespace or service without cross-contamination.
- **Audit & Compliance**: Built-in logging and policy enforcement for governance.

---

## **1. Core Schema Reference**
FraiseQL’s key management aligns with the following schema (core tables and fields):

| **Object**          | **Description**                                                                 | **Fields**                                                                                     | **Notes**                                                                                     |
|---------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **`kms_backend`**   | Defines a KMS provider config (Vault, AWS KMS, GCP KMS, etc.).                | `name` (str), `type` (str, e.g., "vault"), `config` (dict), `enabled` (bool)                   | Base config for all keys tied to this backend.                                                |
| **`kms_key`**       | Represents a cryptographic key in a specific backend.                          | `id` (str, UUID), `backend_id` (ref: `kms_backend.id`), `alias` (str), `created_at` (ts),   | Unique identifier across backends.                                                          |
|                     |                                                                                 | `rotation_policy` (dict), `revoked_at` (ts, nullable)                                          |                                                                                               |
| **`kms_key_version`** | Tracks key material states (current/active, archived, revoked).              | `key_id` (ref: `kms_key.id`), `version` (str), `active` (bool), `valid_since` (ts),          | Supports rolling updates without disruption.                                                 |
|                     |                                                                                 | `valid_until` (ts, nullable)                                                                | `null` = indefinitely valid (unless revoked).                                                |
| **`kms_policy`**    | Grants access to keys via IAM-like rules.                                       | `key_id` (ref: `kms_key.id`), `principal` (str/pattern), `action` (str, e.g., "encrypt"),     | Enforced at query/query-time.                                                               |
|                     |                                                                                 | `condition` (dict, optional)                                                                | Condition keys: `iat`, `exp`, `cidr`, `namespace`.                                           |
| **`kms_audit_log`** | Records operations (generate, revoke, rotate).                                 | `key_id` (ref: `kms_key.id`), `event` (str), `timestamp` (ts), `user_agent` (str)            | Required for compliance.                                                                    |

---

## **2. Query Examples**
FraiseQL’s key management supports declarative operations via SQL-like syntax.

---

### **2.1. Key Operations**
#### **Create a new key with backend-specific config**
```sql
-- Using Vault as the backend
CREATE kms_key
  WITH (
    backend_id: "vault://org/secrets/keys/prod/app-service",
    alias: "app-service-key",
    rotation_policy: { interval: "90d", max_versions: 3 }
  );
```
- **Output**: Returns a `kms_key.id` (e.g., `vault:abc123:app-service-key`).

#### **Rotate a key (automated or manual)**
```sql
-- Trigger rotation now (replaces current version atomically)
UPDATE kms_key SET rotation_policy = { interval: "60d" } WHERE id = "vault:abc123:app-service-key";
```
- **Behavior**: FraiseQL schedules a key replacement at `rotation_policy.interval`, archiving the old version.

#### **Revoke a key (zero-downtime)**
```sql
UPDATE kms_key_version
  SET active = FALSE, valid_until = NOW()
WHERE key_id = "vault:abc123:app-service-key" AND version = "v2";
```
- **FraiseQL ensures**:
  - New clients use the latest `version` with `active = TRUE`.
  - Old clients fail gracefully (via `kms_policy` or retry logic).

---

### **2.2. Key Access Control**
#### **Grant access to a service (e.g., EC2 instance)**
```sql
INSERT INTO kms_policy (
  key_id,
  principal: "arn:aws:iam::123456789012:role/my-app-role",
  action: "encrypt",
  condition: { namespace: "us-west-2" }
);
```
- **Notes**:
  - `principal` supports regex matching (e.g., `arn:aws:iam::*:role/my-app-*`).
  - `condition` filters keys by metadata (e.g., region).

#### **Query allowed keys for a principal**
```sql
SELECT k.*
FROM kms_key k
JOIN kms_policy p ON k.id = p.key_id
WHERE p.principal = "arn:aws:iam::123456789012:role/my-app-role"
  AND p.action = "encrypt"
LIMIT 1;
```
- **Output**: Returns the latest `kms_key` matching criteria.

---

### **2.3. Key Discovery & Audit**
#### **List all keys with rotation status**
```sql
SELECT
  k.id,
  k.alias,
  k.backend_id,
  kv.version,
  kv.active,
  kv.valid_until,
  r.interval
FROM kms_key k
JOIN kms_key_version kv ON k.id = kv.key_id
JOIN k.rotation_policy r ON k.id = r.key_id
WHERE k.backend_id LIKE "vault%";
```
- **Output**:
  ```
  | id                  | alias             | backend_id               | version | active | valid_until  | interval |
  |--------------------|-------------------|--------------------------|---------|--------|--------------|----------|
  | vault:abc123...    | app-service-key   | vault://...              | v2      | TRUE   | NULL         | 60d      |
  ```

#### **Audit revocation events**
```sql
SELECT * FROM kms_audit_log
WHERE key_id = "vault:abc123:app-service-key"
  AND event = "REVOKE"
ORDER BY timestamp DESC
LIMIT 5;
```

---

## **3. Implementation Details**
### **3.1. Backend-Specific Adapters**
FraiseQL routes operations to backends via adapters. Example for **Vault**:

| **Adapter Method**       | **Vault API Equivalent**               | **FraiseQL Behavior**                          |
|--------------------------|----------------------------------------|-----------------------------------------------|
| `generate_key()`         | `secrets/kv/v2/data/keys/<path>`       | Returns a `kms_key.id` with backend-specific `id`. |
| `rotate_key()`           | `secrets/kv/v2/metadata/keys/<path>`  | Atomic replacement via Vault’s `metadata`.    |
| `revoke_key()`           | `secrets/kv/v2/metadata/keys/<path>`  | Sets `valid_until` timestamp.                  |

**AWS KMS/GCP KMS** follow similar patterns but use:
- AWS: `CreateKey`, `ScheduleKeyDeletion`, `GenerateDataKey`.
- GCP: `projects.keys.create`, `projects.keyRings.addKey`.

---

### **3.2. Key Rotation Flow**
1. **Trigger**: On schedule (via `rotation_policy`) or manual `UPDATE`.
2. **Generate**: Backend creates a new key version (`active = TRUE`).
3. **Transition**: FraiseQL updates `kms_key_version.active = FALSE` for old versions.
4. **Cleanup**: Old versions are purged after `max_versions` (default: 3).

**Zero-Downtime Guarantee**:
- Clients poll the `kms_key_version` table for the latest `active` version.
- FraiseQL provides a `current_version()` helper function:
  ```sql
  SELECT current_version("vault:abc123:app-service-key");
  ```

---

### **3.3. Backward Compatibility**
- **Revoked Keys**: Return `403` or `INVALID_KEY` errors to clients.
- **Legacy Systems**: Use `kms_key.alias` to alias legacy keys (e.g., `legacy-db-key`).
- **Versioning**: FraiseQL maintains all key versions in `kms_key_version`.

---

## **4. Related Patterns**
### **4.1. [Secure Data Storage](https://docs.fraiseql.io/patterns/secure-data-storage)**
- Use **Key Management Patterns** to encrypt data before storing it in **Secure Data Storage**.
- Example:
  ```sql
  -- Encrypt data with FraiseQL’s kms_encrypt()
  INSERT INTO secure_data
  VALUES (
    kms_encrypt("sensitive_data", "vault:abc123:app-service-key")
  );
  ```

### **4.2. [Zero-Trust Authentication](https://docs.fraiseql.io/patterns/zero-trust-auth)**
- Generate short-lived tokens encrypted with **Key Management Patterns**-backed keys.
- Example:
  ```sql
  -- Issue a token encrypted with the current key
  SELECT kms_encrypt(
    generate_jwt(payload, "1h"),
    current_version("vault:abc123:token-key")
  );
  ```

### **4.3. [Policy as Code](https://docs.fraiseql.io/patterns/policy-as-code)**
- Enforce KMS policies via FraiseQL’s `kms_policy` table.
- Example policy file (`security/fraiseql/kms-policy.yml`):
  ```yaml
  - key_id: "vault:abc123:app-service-key"
    principal: "arn:aws:iam::*:role/my-app-*"
    action: ["encrypt", "decrypt"]
    condition:
      namespace: "us-west-2|eu-central-1"
  ```

---

## **5. Best Practices**
1. **Key Hierarchy**:
   - Use `/` to namespace keys (e.g., `prod/db`, `dev/api`).
   - Example:
     ```sql
     SELECT * FROM kms_key WHERE backend_id LIKE "vault://prod/%";
     ```

2. **Automated Rotation**:
   - Set `rotation_policy.interval` to match compliance requirements (e.g., 90d for PII).

3. **Audit Logs**:
   - Query `kms_audit_log` daily for anomalies.

4. **Multi-Region Keys**:
   - Replicate keys across backends using `kms_backend` configs:
     ```sql
     CREATE kms_backend
     WITH (
       name: "multi-region",
       type: "vault",
       config: {
         "replication": ["vault-us", "vault-eu"]
       }
     );
     ```

5. **Failover**:
   - Define a primary/secondary backend:
     ```sql
     UPDATE kms_backend SET enabled = FALSE WHERE name = "backup-vault";
     ```

---

## **6. Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| Key rotation fails                  | Check backend-specific limits (e.g., Vault’s `max_versions`).                |
| `403 Forbidden` on decryption       | Verify `kms_policy` allows the principal’s action.                           |
| Missing key versions                | Ensure `kms_key_version.active` is set correctly during rotation.           |
| Slow queries on `kms_key_version`   | Add an index: `CREATE INDEX ON kms_key_version(key_id, active)`.            |

---
**Note**: For advanced use cases (e.g., cross-backend replication), consult the [Advanced Key Sync](https://docs.fraiseql.io/advanced/key-sync) guide.