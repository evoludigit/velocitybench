---
# **[Pattern] Hashing Configuration Reference Guide**

---

## **Overview**
The **Hashing Configuration** pattern ensures data integrity and security by generating a unique, fixed-length hash representation of configuration data. This pattern is essential in systems where configuration files, secrets, or sensitive parameters need verification without exposing their original values (e.g., validation, caching, or versioning). Hashes are typically generated using cryptographic hash functions (e.g., SHA-256, MD5) or checksum algorithms (e.g., CRC32). This guide covers implementation details, schema design, query examples, and related patterns to integrate hashing into your system’s configuration management.

---

## **Key Concepts**
1. **Purpose**:
   - Detect unintended modifications to configuration data.
   - Enable secure comparison of configurations without transmitting raw values.
   - Support caching strategies (e.g., only reload configurations if their hash changes).

2. **Common Hash Functions**:
   - **Cryptographic**: SHA-256, SHA-3, BLAKE3 (secure, collision-resistant).
   - **Non-Cryptographic**: MD5, CRC32 (faster but less secure; use only for non-sensitive data).

3. **Hashing Workflow**:
   - Input: Raw configuration data (e.g., JSON/INI file, environment variables, or secrets).
   - Process: Convert input to a string representation, then apply the hash function.
   - Output: Hexadecimal or base64-encoded hash value for storage/comparison.

4. **Schema Integration**:
   - Store hashes alongside configurations (e.g., in a database or metadata store).
   - Use hashes to trigger actions (e.g., "reload config if hash changed").

---

## **Schema Reference**
Below is a schema for a **ConfigurationHash** entity, supporting integration with configuration systems. Adjust fields as needed for your use case.

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     | **Required** |
|-------------------------|---------------|-------------------------------------------------------------------------------|----------------------------------------|--------------|
| `config_id`             | String (UUID) | Unique identifier for the configuration entry (e.g., linked to a config file). | `550e8400-e29b-41d4-a716-446655440000` | Yes          |
| `hash_algorithm`        | Enum          | Hash function used (e.g., `SHA256`, `MD5`, `CRC32`).                          | `SHA256`                              | Yes          |
| `hash_value`            | String        | Hexadecimal or base64-encoded hash of the configuration.                      | `a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e` | Yes          |
| `hash_version`          | Integer       | Version of the hashing algorithm (e.g., `2` for SHA-256).                    | `2`                                    | No           |
| `generated_at`          | Timestamp     | When the hash was generated (for tracking changes).                          | `2023-10-01T12:00:00Z`                 | No           |
| `original_config`       | String        | Optional: Raw configuration data (for debugging or verification).              | `{ "timeout": 30, "retries": 3 }`    | No           |
| `config_type`           | Enum          | Type of configuration (e.g., `JSON`, `INI`, `ENV_VARIABLES`).                 | `JSON`                                 | No           |

---
**Note**: For large configurations, store `original_config` externally (e.g., in a blob store) and reference it via `config_id`.

---

## **Implementation Details**

### **1. Hash Generation**
Generate a hash from raw configuration data:
```python
import hashlib

def generate_hash(config_data: str, algorithm: str = "SHA256") -> str:
    """Generate a hash for configuration data."""
    if algorithm == "SHA256":
        return hashlib.sha256(config_data.encode()).hexdigest()
    elif algorithm == "MD5":
        return hashlib.md5(config_data.encode()).hexdigest()
    elif algorithm == "CRC32":
        import zlib
        return str(zlib.crc32(config_data.encode()) & 0xFFFFFFFF)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
```

### **2. Schema Storage**
Store generated hashes in a database (e.g., PostgreSQL, MongoDB). Example for PostgreSQL:
```sql
CREATE TABLE configuration_hashes (
    config_id UUID PRIMARY KEY,
    hash_algorithm VARCHAR(32) NOT NULL,
    hash_value TEXT NOT NULL,
    hash_version INTEGER,
    generated_at TIMESTAMP,
    original_config TEXT,
    config_type VARCHAR(32)
);
```

### **3. Serialization**
Convert configuration data to a string for hashing:
- **JSON**: Use `json.dumps()` and sort keys for consistency.
- **INI**: Convert to a string with consistent line ordering.
- **Environment Variables**: Combine into a string (e.g., `KEY1=VAL1|KEY2=VAL2`).

Example for JSON:
```python
import json

def serialize_json(config: dict) -> str:
    """Serialize JSON config with sorted keys for consistent hashing."""
    return json.dumps(config, sort_keys=True)
```

### **4. Hash Comparison**
Compare hashes to detect changes:
```python
def is_config_changed(stored_hash: str, new_hash: str) -> bool:
    """Check if configuration has changed."""
    return stored_hash != new_hash
```

### **5. Versioning**
Support hash algorithm upgrades:
- Store `hash_version` to handle changes (e.g., upgrading from MD5 to SHA-256).
- Recompute hashes for existing configs when upgrading.

---

## **Query Examples**

### **1. Insert a New Hash**
```sql
-- Insert a new hash for a config file
INSERT INTO configuration_hashes (
    config_id, hash_algorithm, hash_value, generated_at, original_config
)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'SHA256',
    'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e',
    '2023-10-01T12:00:00Z',
    '{"timeout": 30, "retries": 3}'
);
```

### **2. Check for Configuration Changes**
```sql
-- Query to check if a config has changed
SELECT
    config_id,
    hash_value,
    generated_at
FROM configuration_hashes
WHERE config_id = '550e8400-e29b-41d4-a716-446655440000';
```
**Result**:
| `config_id`                          | `hash_value`                                                                 | `generated_at`       |
|--------------------------------------|-----------------------------------------------------------------------------|----------------------|
| `550e8400-e29b-41d4-a716-446655440000` | `a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e`         | `2023-10-01T12:00:00Z` |

Compare with the new hash:
```python
new_hash = generate_hash('{"timeout": 30, "retries": 4}', "SHA256")
if new_hash == stored_hash:
    print("No changes.")
else:
    print("Configuration changed!")
```

### **3. List All Configs by Hash Algorithm**
```sql
-- Filter hashes by algorithm (e.g., for migration)
SELECT *
FROM configuration_hashes
WHERE hash_algorithm = 'MD5';
```

### **4. Update Hash on Config Change**
```python
# 1. Read new config, generate hash, and update DB
new_config = {"timeout": 30, "retries": 4}
new_hash = generate_hash(json.dumps(new_config, sort_keys=True), "SHA256")

# 2. Update the stored hash
UPDATE configuration_hashes
SET hash_value = new_hash, generated_at = NOW()
WHERE config_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

## **Performance Considerations**
1. **Hashing Overhead**:
   - Cryptographic hashes (e.g., SHA-256) are slower than checksums (e.g., CRC32).
   - Use faster algorithms (e.g., BLAKE3) for non-security-sensitive use cases.

2. **Storage**:
   - Store only the hash value (not the original config) unless debugging is required.
   - Compress `original_config` if storing it.

3. **Concurrency**:
   - Use database locks or optimistic concurrency control (e.g., `generated_at` timestamps) to avoid race conditions when updating hashes.

---

## **Security Best Practices**
1. **Avoid MD5/CRC32 for Sensitive Data**:
   - MD5 is cryptographically broken; CRC32 has collisions.
   - Use SHA-256 or BLAKE3 for security-critical systems.

2. **Salting**:
   - Add a unique salt to hashes if comparing configs across systems (to handle minor formatting differences).

3. **Hash Leakage**:
   - Never expose raw hashes in logs or UI. Use them only for internal validation.

4. **Algorithm Rotation**:
   - Plan for hash algorithm upgrades (e.g., SHA-256 → SHA-3) by storing `hash_version`.

---

## **Related Patterns**
1. **[Configuration Versioning]**
   - Track changes to configurations over time using version numbers or timestamps.
   - *Complement*: Hashes can help detect unintended changes between versions.

2. **[Configuration Encryption]**
   - Securely store sensitive configuration values (e.g., secrets) alongside hashes.
   - *Complement*: Hashes verify integrity; encryption hides values.

3. **[Caching with Conditional Updates]**
   - Cache configuration data but reload only if the hash changes.
   - *Example*: Use `generated_at` + hash to implement stale-while-revalidate caching.

4. **[Immutable Configurations]**
   - Treat configuration as immutable; use hashes to enforce consistency.
   - *Complement*: Hashes prevent accidental modifications.

5. **[Secret Management]**
   - Store secrets in a vault (e.g., HashiCorp Vault) and hash only the metadata (e.g., environment variable names).
   - *Complement*: Hashes detect leaks without exposing secrets.

6. **[Configuration Diffing]**
   - Compare hashes to generate diffs between configuration versions.
   - *Tooling*: Integrate with tools like `diff` or custom scripts using hash outputs.

---

## **Example Workflow**
1. **System Startup**:
   - Load config file (`app.json`).
   - Generate hash: `generate_hash(json.dumps(config), "SHA256")`.
   - Store hash in database: `INSERT INTO configuration_hashes(...)`.

2. **Config Reload**:
   - Read new `app.json`, compute new hash.
   - Query database for old hash.
   - If hashes differ: reload config; else: skip.

3. **Alerting**:
   - Monitor `generated_at` for sudden hash changes (potential attack or misconfiguration).

---
**See Also**:
- [OWASP Hashing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Hashing_Cheat_Sheet.html)
- [BLAKE3 Documentation](https://github.com/BLAKE3-team/BLAKE3)