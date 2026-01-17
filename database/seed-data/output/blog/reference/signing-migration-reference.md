# **[Pattern] Signing Migration Reference Guide**

---

## **Overview**
The **Signing Migration** pattern secures data integrity and authenticity during schema changes in distributed systems by cryptographically signing updates to schema definitions (e.g., column types, constraints, or table structures). This pattern ensures that clients and servers can verify the validity of migration scripts, preventing tampering and unauthorized schema alterations.

Common use cases include:
- **Database schema migrations** (e.g., PostgreSQL, MySQL, or DynamoDB)
- **Configuration-driven systems** (e.g., Kubernetes manifests, Terraform state)
- **API versioning** (e.g., OpenAPI/Swagger spec updates)
- **Multi-team environments** where schema changes require approval.

By signing migrations, teams can enforce:
✔ **Immutable audit trails** for schema changes
✔ **Automated validation** of migrations before execution
✔ **Decentralized control** (e.g., via GitOps or signed PRs)

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                                                                                     |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Schema Signature**    | A cryptographic hash (e.g., SHA-256) of the serialized migration JSON/YAML, signed by a private key.                                                                  |
| **Signer**              | An entity (e.g., a service account, CI/CD bot, or human) with a private key to generate signatures.                                                                 |
| **Verifier**            | A system component (e.g., migration tool, database proxy) that checks signatures using a public key.                                                              |
| **Migration Bundle**    | A ZIP/TAR archive containing:                                                                                    |
|                         | - Schema definition (`schema.json`)                                                                                                                             |
|                         | - Signature file (`signature.sig`)                                                                                                                               |
|                         | - Metadata (e.g., version, release notes)                                                                                                                       |
| **Signature Algorithm** | Typically **RSA-SHA256** or **EdDSA** (e.g., Ed25519).                                                                                                             |
| **Rollback Mechanism**  | A pre-signed "undo" migration to revert invalid changes if verification fails.                                                                                  |

---

## **Implementation Details**

### **1. Schema Signature Generation**
Signatures are generated from a **deterministic serialization** of the migration schema (e.g., JSON with a fixed order of fields). Example:

**Input Schema (`schema.json`):**
```json
{
  "version": "20240101",
  "changes": [
    { "table": "users", "action": "add_column", "name": "email", "type": "string" }
  ]
}
```

**Steps to Sign:**
1. Serialize the schema to a **canonical JSON** (e.g., using [`json-canonicalize`](https://github.com/chrislam Terraform)).
2. Hash the serialized data (SHA-256).
3. Sign the hash with a private key (`--signer-key=private_key.pem`):
   ```bash
   echo "BASE64(sha256(schema))" | openssl dgst -sha256 -sign private_key.pem -out signature.sig
   ```

**Output (`signature.sig`):**
```plaintext
304502201... (DER-encoded RSA signature)
```

---

### **2. Schema Verification**
Before applying a migration, verify the signature using a public key:

```bash
# Decode signature and verify
openssl dgst -sha256 -verify public_key.pem -signature signature.sig <(echo "BASE64(sha256(schema))")
```

**Verification Logic (Pseudocode):**
```python
import hashlib
import sigverify

def verify_migration(schema_bytes, signature, public_key):
    sha256_hash = hashlib.sha256(schema_bytes).digest()
    return sigverify.verify(sha256_hash, signature, public_key)
```

---

### **3. Migration Bundle Structure**
```
migration-v1.0/
├── schema.json
├── signature.sig
├── rollback/
│   └── undo_schema.json
├── rollback/
│   └── undo_signature.sig
└── README.md (release notes)
```

---

### **4. Rollback Support**
Include a **pre-signed rollback migration** in the bundle. Example:
```json
# rollback/undo_schema.json
{
  "version": "20240101-rollback",
  "changes": [
    { "table": "users", "action": "drop_column", "name": "email" }
  ]
}
```

---

## **Schema Reference**
| **Field**          | **Type**   | **Description**                                                                                                                                                     | **Example Value**                     |
|--------------------|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `version`          | `string`   | Migration version (semver or timestamp).                                                                                                                              | `"2024.1.0"`                           |
| `changes`          | `array`    | List of operations (add/drop/alter).                                                                                                                         | `[{"table": "users", "action": "add"}]` |
| `changes[*].table` | `string`   | Target table/collection.                                                                                                                                             | `"users"`                              |
| `changes[*].action`| `string`   | Operation type (`add_column`, `alter_constraint`, `migrate_data`).                                                                                                 | `"add_column"`                         |
| `changes[*].name`  | `string`   | Column/function name.                                                                                                                                             | `"email"`                              |
| `changes[*].type`  | `string`   | Data type (`int`, `string`, `json`).                                                                                                                             | `"string"`                             |
| `signature`        | `base64`   | Der-serialized signature (stored in `signature.sig`).                                                                                                         | `..."` (binary)                        |
| `public_key`       | `object`   | Public key metadata (e.g., `alg: "RS256"`, `kid: "team-a"`).                                                                                                      | `{"kid": "team-a"}`                    |

---

## **Query Examples**
### **1. Generate a Signed Migration (CLI)**
```bash
# Serialize schema, hash, and sign
SCHEMA_JSON="$(jq -S . schema.json)"  # JSON canonicalization
SHA256=$(echo "$SCHEMA_JSON" | openssl dgst -sha256 | cut -d' ' -f2)
openssl dgst -sha256 -sign private_key.pem -out signature.sig <(echo "$SHA256")
```

### **2. Verify a Migration (Python)**
```python
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

public_key = serialization.load_pem_public_key(open("public_key.pem").read())
signature = open("signature.sig", "rb").read()
schema_bytes = open("schema.json", "rb").read()

try:
    public_key.verify(
        signature,
        hashlib.sha256(schema_bytes).digest(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        )
    )
    print("✅ Migration verified.")
except Exception as e:
    print("❌ Verification failed:", e)
```

### **3. Apply a Migration (Database-Specific)**
**PostgreSQL:**
```sql
-- After verifying signature, execute:
do $$
declare
    m record;
begin
    for m in execute 'SELECT * FROM pg_migrations WHERE version = ''2024.1.0'''
    loop
        if m.applied = false then
            perform pg_alter_table(...);  -- Apply changes
            update pg_migrations set applied = true where version = '2024.1.0';
        end if;
    end loop;
end $$;
```

**DynamoDB:**
```bash
# Use AWS CLI to apply changes via signed Lambda function
aws dynamodb update-table \
    --table-name users \
    --attribute-definitions AttributeName=email,AttributeType=S \
    --add-attribute AttributeName=email,AttributeType=S
```

---

## **Error Handling**
| **Error**                     | **Cause**                                                                 | **Solution**                                                                                     |
|-------------------------------|----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `SignatureVerificationFailed` | Invalid signature or corrupted data.                                       | Re-download the migration bundle or regenerate signatures.                                      |
| `PublicKeyMismatch`           | Wrong public key used for verification.                                    | Ensure the correct key is loaded (e.g., `--key=team-a`).                                       |
| `SchemaChangedPostSigning`    | Schema modified after signing (e.g., PR edits).                            | Use **immutable Git tags** or **deterministic hashing** (e.g., `git hash-object`).               |
| `RollbackFailed`              | Undo migration signatures don’t match.                                     | Regenerate rollback signatures with the same private key.                                       |

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                     | **When to Use**                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[GitOps for Migrations]**      | Manage migrations via Git (e.g., ArgoCD, Flux) with signed PRs.                                                                                                        | Teams using GitOps workflows.                                                                         |
| **[Canary Deployments]**         | Gradually roll out schema changes to a subset of systems.                                                                                                         | High-availability systems (e.g., e-commerce platforms).                                           |
| **[Schema Registry]**            | Centralized schema versioning (e.g., Confluent Schema Registry).                                                                                                   | Event-driven architectures (e.g., Kafka).                                                          |
| **[Policy-as-Code]**              | Enforce migration rules (e.g., "No `DROP TABLE` on Fridays") via tools like Open Policy Agent (OPA).                                                            | Regulated industries (e.g., finance, healthcare).                                                  |
| **[Double-Write Pattern]**       | Log schema changes to a read-replica before applying to the primary.                                                                                            | Critical systems requiring zero-downtime migrations.                                               |

---

## **Best Practices**
1. **Key Rotation**: Rotate signing keys periodically (e.g., quarterly) and maintain a **revocation list**.
   ```bash
   # Rotate private key (example)
   openssl genpkey -algorithm RSA -out private_key_new.pem -pkeyopt rsa_keygen_bits:4096
   ```
2. **Immutable Signatures**: Store signatures in **immutable storage** (e.g., S3 versioning, Git tags).
3. **Audit Logging**: Log signature verification events (who, when, status) in a central system.
4. **Offline Verification**: For air-gapped environments, bundle public keys with migrations.
5. **Tooling**:
   - **[migrate](https://github.com/golang-migrate/migrate)**: Migration framework with plugin support.
   - **[Terraform](https://www.terraform.io)**: Sign infrastructure-as-code changes.
   - **[Sigstore](https://sigstore.dev)**: Tools for signing and verifying artifacts.

---
**Appendix**
- **RFC 8555 (JSON Web Signatures)**: Standard for signing JSON data.
- **IETF Draft for Migration Signing**: [Draft-Ietf-appsawg-migration-signing](https://datatracker.ietf.org/doc/draft-ietf-appsawg-migration-signing/).
- **Example Repo**: [github.com/example/signing-migrations](https://github.com/example/signing-migrations) (hypothetical).