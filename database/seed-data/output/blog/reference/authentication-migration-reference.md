# **[Pattern] Authentication Migration: Reference Guide**

---

## **Overview**
The **Authentication Migration** pattern addresses the need to transition users, credentials, and security policies from an **existing authentication system** (Legacy Auth) to a **modern, scalable solution** (Target Auth) while minimizing downtime, preserving user experience, and ensuring security compliance. This guide covers key concepts, schema requirements, implementation steps, and best practices for a seamless migration.

The pattern is critical when:
- A legacy system lacks modern security features (e.g., OAuth, MFA, or centralized identity management).
- Compliance mandates (e.g., GDPR, HIPAA) require upgrading authentication.
- Performance or scalability bottlenecks arise due to outdated infrastructure.

---

## **Key Concepts & Schema Reference**

### **1. Core Components**
| **Component**               | **Description**                                                                 | **Example Systems**                          |
|-----------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **Legacy Auth System**      | Source authentication provider (e.g., local DB, LDAP, legacy SSO).             | Custom SQL auth, Active Directory           |
| **Target Auth System**      | New authentication provider (e.g., OAuth 2.0, JWT, identity-as-a-service).     | Auth0, Okta, Azure AD, Firebase Auth        |
| **Migration Service**       | Middleware that bridges Legacy Auth → Target Auth during transition.            | Custom API gateway, AWS Cognito Lambda      |
| **User Mapping Table**      | Synchronizes legacy users with target identities.                                | `legacy_user_id → target_user_id`           |
| **Credential Sync**         | Securely transfers hashed passwords (if applicable) or enables passwordless auth. | Hash migration via bcrypt/scrypt           |
| **Session Bridge**          | Maintains active sessions during migration (e.g., via JWT tokens).              | Token forwarding, session replication       |
| **Audit Logs**              | Tracks migration events for compliance (e.g., failed logins, access denied).    | ELK Stack, Splunk                           |

---

### **2. Data Schema Reference**
### **Table 1: `user_migration_mapping`**
| Field               | Type         | Description                                                                 | Example                          |
|---------------------|--------------|-----------------------------------------------------------------------------|----------------------------------|
| `legacy_user_id`    | VARCHAR(64)  | Unique identifier from Legacy Auth system.                                   | `legacy_user_123`                |
| `target_user_id`    | VARCHAR(64)  | New UUID/GUID in Target Auth system.                                         | `uuid-3b8e-413d-90a1-2c3d4e5f6a` |
| `migration_status`  | ENUM         | `pending`, `completed`, `failed`, `revoked`.                               | `completed`                      |
| `fallback_auth`     | BOOLEAN      | Flag to enable Legacy Auth as fallback.                                      | `false`                          |
| `last_updated`      | TIMESTAMP    | Timestamp of last sync/validation.                                           | `2024-03-15 14:30:00 UTC`       |
| `notes`             | TEXT         | Admin notes (e.g., "Manual review needed").                                 | `User requested local auth`      |

---

### **Table 2: `auth_credential_history`**
| Field               | Type         | Description                                                                 | Example                          |
|---------------------|--------------|-----------------------------------------------------------------------------|----------------------------------|
| `user_id`           | VARCHAR(64)  | Target Auth user identifier.                                                | `uuid-3b8e-413d-90a1-2c3d4e5f6a` |
| `credential_type`   | ENUM         | `password_hash`, `jwt_key`, `api_key`.                                       | `password_hash`                   |
| `hash_algorithm`    | VARCHAR(20)  | Algorithm used (e.g., `bcrypt`, `argon2`).                                  | `bcrypt`                         |
| `hash_value`        | VARCHAR(255) | Securely hashed credential (never store plaintext).                        | `$2b$12$EixZaYVK1fsbw1ZfbX3OXe`  |
| `created_at`        | TIMESTAMP    | When the credential was set.                                                | `2024-03-10 08:00:00 UTC`       |
| `is_active`         | BOOLEAN      | Whether the credential is valid.                                            | `true`                           |

---

### **Table 3: `session_bridge`**
| Field               | Type         | Description                                                                 | Example                          |
|---------------------|--------------|-----------------------------------------------------------------------------|----------------------------------|
| `session_id`        | VARCHAR(128) | Unique session token from Legacy Auth.                                      | `legacy_sess_abc123xyz789`       |
| `target_user_id`    | VARCHAR(64)  | Corresponding Target Auth user.                                             | `uuid-3b8e-413d-90a1-2c3d4e5f6a` |
| `token`             | TEXT         | JWT or session token for Target Auth.                                       | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` |
| `expires_at`        | TIMESTAMP    | Token expiration.                                                           | `2024-03-18 12:00:00 UTC`       |
| `legacy_session_id` | VARCHAR(128) | Reference to original Legacy Auth session (for debugging).                  | `legacy_db_session_456`          |

---

## **Implementation Steps**
### **1. Pre-Migration**
- **Assessment**:
  - Audit legacy credentials (store hashes, not plaintext).
  - Identify high-value users (e.g., admins) for manual review.
- **Schema Setup**:
  - Deploy `user_migration_mapping` and `auth_credential_history`.
  - Configure Target Auth (e.g., enable API keys for initial access).
- **Fallback Plan**:
  - Ensure Legacy Auth remains operational until migration completes.

### **2. Credential Migration**
#### **Option A: Password Hash Migration (Recommended)**
1. **Hash Sync**:
   - Query Legacy Auth for hashed passwords (e.g., via SQL or LDAP).
   - Store in `auth_credential_history` with the same algorithm.
   - Example SQL:
     ```sql
     INSERT INTO auth_credential_history
     SELECT
       legacy_user_id AS user_id,
       'password_hash' AS credential_type,
       'bcrypt' AS hash_algorithm,
       password_hash,
       CURRENT_TIMESTAMP AS created_at,
       true AS is_active
     FROM legacy_users;
     ```
2. **Validation**:
   - Test target login with hashed passwords (no plaintext exposure).

#### **Option B: Passwordless Migration**
- Use **magic links** or **TOTP** (Time-based OTP) for new logins.
- Store recovery codes in `user_migration_mapping.notes`.

### **3. Session Bridge**
1. **Token Generation**:
   - When a Legacy Auth session expires, generate a JWT for Target Auth.
   - Example (Pseudocode):
     ```javascript
     function bridgeSession(legacySessionId, userId) {
       const token = jwt.sign({ userId }, TARGET_AUTH_SECRET, { expiresIn: '1h' });
       db.insertSessionBridge(legacySessionId, userId, token, new Date(Date.now() + 3600000));
     }
     ```
2. **Middleware**:
   - Deploy a proxy that redirects legacy auth requests to Target Auth via JWT.

### **4. Cutover Phase**
- **Gradual Rollout**:
  - Enable Target Auth for 5–10% of users first (monitor for errors).
  - Disable Legacy Auth only after confirmation.
- **Monitoring**:
  - Track failed logins in `auth_credential_history`.
  - Use `session_bridge` to debug stale sessions.

### **5. Post-Migration**
- **Finalize**:
  - Drop Legacy Auth tables or decommission the system.
  - Update all client SDKs to use Target Auth endpoints.
- **Audit**:
  - Verify all users are mapped (`migration_status = 'completed'`).
  - Archieve old session logs.

---

## **Query Examples**
### **1. Check Migration Status**
```sql
SELECT
  legacy_user_id,
  target_user_id,
  migration_status,
  fallback_auth
FROM user_migration_mapping
WHERE migration_status = 'pending'
LIMIT 10;
```

### **2. Validate Credential Hashes**
```sql
SELECT
  user_id,
  credential_type,
  hash_algorithm
FROM auth_credential_history
WHERE is_active = true
AND credential_type = 'password_hash';
```

### **3. Find Stale Sessions**
```sql
SELECT
  session_id,
  target_user_id,
  expires_at
FROM session_bridge
WHERE expires_at < CURRENT_TIMESTAMP
ORDER BY expires_at;
```

### **4. Update Fallback Auth Flag**
```sql
UPDATE user_migration_mapping
SET fallback_auth = false
WHERE target_user_id = 'uuid-3b8e-413d-90a1-2c3d4e5f6a';
```

---

## **Error Handling & Edge Cases**
| **Scenario**               | **Solution**                                                                 |
|-----------------------------|------------------------------------------------------------------------------|
| **Hash Algorithm Mismatch** | Re-hash passwords using Target Auth’s algorithm (e.g., switch from MD5 to bcrypt). |
| **Duplicate Mappings**      | Use a merge strategy (e.g., prefer `target_user_id` if exists).              |
| **Failed Logins**           | Log to `auth_credential_history` and enable fallback auth temporarily.      |
| **Session Timeouts**        | Extend `expires_at` in `session_bridge` or issue new tokens.               |

---

## **Security Considerations**
- **Never store plaintext passwords** (use salted hashes).
- **Encrypt sensitive data** (e.g., `session_bridge.token`).
- **Rate-limit migration endpoints** to prevent brute-force attacks.
- **Use TLS** for all auth traffic during migration.

---

## **Related Patterns**
1. **[Multi-Factor Authentication (MFA) Integration]**
   - Extend Target Auth with TOTP/SMS/MFA after migration.
2. **[Token Rotation]**
   - Rotate `session_bridge` tokens post-migration to enhance security.
3. **[Service Mesh for Auth Proxy]**
   - Use Envoy or Istio to manage auth traffic during cutover.
4. **[Canary Deployment]**
   - Gradually shift user traffic to Target Auth via feature flags.
5. **[Data Masking]**
   - Apply dynamic data masking to legacy auth tables during migration.

---
**Further Reading**:
- [OAuth 2.0 Migration Checklist](https://oauth.net/2/migration/)
- [AWS Cognito Migration Guide](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-migrate.html)