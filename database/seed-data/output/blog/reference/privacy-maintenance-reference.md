---
# **[Pattern] Privacy Maintenance Reference Guide**
*Ensure compliance with data privacy laws (e.g., GDPR, CCPA) by systematically managing personally identifiable information (PII) and user consent.*

---

## **1. Overview**
The **Privacy Maintenance** pattern ensures that applications adhere to **data privacy regulations** (e.g., GDPR, CCPA, HIPAA) by implementing controls over user data collection, processing, storage, and deletion. This pattern supports **consent management**, **data anonymization**, **right-to-erasure workflows**, and **auditable access controls**.

Key benefits:
✔ **Compliance:** Reduces legal/regulatory risks.
✔ **Trust:** Empowers users with control over their data.
✔ **Security:** Minimizes exposure of sensitive information.
✔ **Auditability:** Tracks data access and modifications.

This pattern is critical for applications handling **PII** (e.g., emails, addresses, financial data) and must integrate with **privacy-aware architectures**.

---

## **2. Core Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Example Use Case**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Data Classification**   | Categorizes data based on sensitivity (e.g., PII, non-PII) to apply appropriate protection.                                                                                                                   | Anonymizing street addresses in anonymized datasets for analytics.                                      |
| **Consent Management**    | Tracks user consent for data collection, storage, and sharing with explicit opt-in/opt-out options.                                                                                                             | GDPR-compliant cookie consent banner.                                                                   |
| **Right to Access/Delete**| Provides users the ability to view/modify/delete their data (Article 15/17 GDPR).                                                                                                                         | A "delete my account" endpoint that removes all associated PII.                                        |
| **Data Minimization**     | Only collects necessary data and discards it post-use.                                                                                                                                                     | Storing only hashed passwords, not plaintext.                                                          |
| **Audit Logging**         | Records all access/modifications to PII for compliance and auditing.                                                                                                                                        | Logging IP addresses when users request data deletion.                                                  |
| **Pseudonymization**      | Replaces PII with artificial identifiers (e.g., tokens) while retaining usability (e.g., for analytics).                                                                                                  | Using UUIDs instead of names in customer support logs.                                                 |
| **Third-Party Compliance**| Ensures vendors/partners handling PII comply with regulations.                                                                                                                                              | Enforcing CCPA-compliant data processing agreements for cloud providers.                                |

---

## **3. Schema Reference**
### **`PrivacyPolicy` Table (Database)**
Tracks privacy-related configurations per user/application.

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `policy_id`             | UUID           | Unique identifier for the privacy policy.                                                                                                                                                                         | `550e8400-e29b-41d4-a716-446655440000` |
| `user_id`               | UUID (FK)      | User associated with the policy.                                                                                                                                                                                     | `660e8400-e29b-41d4-a716-446655440001` |
| `application_id`        | UUID (FK)      | Application scope (e.g., `web-app`, `mobile-app`).                                                                                                                                                           | `1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p` |
| `policy_version`        | String         | Version of the privacy policy (e.g., "v2.0").                                                                                                                                                                       | `"GDPR_2023"`                          |
| `last_updated`          | Timestamp      | When the policy was last modified.                                                                                                                                                                               | `2024-05-20T14:30:00Z`                |
| `consent_status`        | Enum           | `GRANTED`, `REVOKED`, `PENDING`, `DECLINED`.                                                                                                                                                                     | `GRANTED`                              |
| `data_processing_purpose`| JSON           | Purposes for which data is collected (e.g., `["marketing", "analytics"]`).                                                                                                                                        | `{"purposes": ["analytics", "support"]}`|
| `vendor_compliance`     | Boolean        | Whether third-party vendors meet compliance standards.                                                                                                                                                       | `true`                                 |
| `expiry_date`           | Date           | When consent expires (if applicable).                                                                                                                                                                               | `2025-12-31`                           |

---

### **`PIIAuditLog` Table**
Logs all access/modifications to PII for compliance.

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `log_id`                | UUID           | Unique log entry ID.                                                                                                                                                                                           | `7e1a2b3c-4d5e-6f7g-8h9i-0j1k2l3m4n5o` |
| `user_id`               | UUID (FK)      | User whose data was accessed.                                                                                                                                                                                   | `660e8400-e29b-41d4-a716-446655440001` |
| `action`                | Enum           | `VIEW`, `UPDATE`, `DELETE`, `EXPORT`.                                                                                                                                                                           | `DELETE`                               |
| `pii_field`             | String         | Field modified (e.g., `email`, `phone`).                                                                                                                                                                         | `email`                                |
| `timestamp`             | Timestamp      | When the action occurred.                                                                                                                                                                                       | `2024-05-20T15:15:22Z`                |
| `actor_id`              | UUID (FK)      | User/system performing the action.                                                                                                                                                                               | `9e1a2b3c-4d5e-6f7g-8h9i-0j1k2l3m4n6p` |
| `ip_address`            | String         | IP of the actor (pseudonymized if required).                                                                                                                                                                   | `192.168.1.1` (tokenized)              |
| `metadata`              | JSON           | Additional context (e.g., `{"device": "mobile"}`).                                                                                                                                                           | `{"device": "android", "location": "US"}`|

---

## **4. Implementation Details**
### **4.1 Data Classification**
- **Tag sensitive fields** (e.g., `email`, `ssn`) during schema design.
- Use **column-level encryption** for PII (e.g., AWS KMS, PostgreSQL `pgcrypto`).
- **Example (SQL):**
  ```sql
  CREATE TABLE users (
      user_id UUID PRIMARY KEY,
      name VARCHAR(100),  -- Non-PII
      email VARCHAR(255) ENCRYPTED,  -- PII (encrypted at rest)
      ssn VARCHAR(50) ENCRYPTED  -- PII (high sensitivity)
  );
  ```

### **4.2 Consent Management**
- **Frontend:** Display a **consent banner** on first visit.
- **Backend:** Store consent in `PrivacyPolicy` table.
- **Example (Node.js):**
  ```javascript
  // User clicks "Accept" on consent banner
  await db.PrivacyPolicy.create({
      user_id: user.id,
      application_id: "web-app",
      consent_status: "GRANTED",
      data_processing_purpose: { purposes: ["analytics", "support"] }
  });
  ```

### **4.3 Right to Access/Delete**
- **Endpoints:**
  - `GET /api/users/me` → Returns user’s PII.
  - `DELETE /api/users/me` → Deletes PII (with audit log).
- **Example (REST API):**
  ```http
  DELETE /api/users/me
  Headers: { Authorization: "Bearer <token>" }
  ```
  **Response (200 OK):**
  ```json
  {
      "message": "Data deleted successfully",
      "audit_log_id": "7e1a2b3c-4d5e-6f7g-8h9i-0j1k2l3m4n5o"
  }
  ```

### **4.4 Pseudonymization**
- Replace PII with **tokens** (e.g., UUID) for analytics.
- **Example (Python):**
  ```python
  import uuid
  def pseudonymize_email(email):
      return str(uuid.uuid4())  # Replace with token
  ```
- **Output:**
  Original: `user@example.com` → Tokenized: `550e8400-e29b-41d4-a716-446655440000`

### **4.5 Audit Logging**
- **Trigger logs** on PII modifications (e.g., database triggers).
- **Example (PostgreSQL Trigger):**
  ```sql
  CREATE OR REPLACE FUNCTION log_pii_change()
  RETURNS TRIGGER AS $$
  BEGIN
      INSERT INTO PIIAuditLog (log_id, user_id, action, pii_field, timestamp, actor_id)
      VALUES (gen_random_uuid(), NEW.user_id, 'UPDATE', 'email', NOW(), current_user_id());
      RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER trigger_log_email_update
  AFTER UPDATE OF email ON users
  FOR EACH ROW EXECUTE FUNCTION log_pii_change();
  ```

---

## **5. Query Examples**
### **5.1 Check Consent Status**
```sql
SELECT * FROM PrivacyPolicy
WHERE user_id = '660e8400-e29b-41d4-a716-446655440001'
AND application_id = 'web-app';
```
**Output:**
| `policy_id`               | `consent_status` | `last_updated`          |
|---------------------------|------------------|-------------------------|
| `550e8400-e29b-41d4-a716...` | `GRANTED`        | `2024-05-20T14:30:00Z`  |

---

### **5.2 Find PII Access Logs**
```sql
SELECT user_id, action, pii_field, timestamp
FROM PIIAuditLog
WHERE pii_field = 'email'
AND timestamp > '2024-05-01'
ORDER BY timestamp DESC;
```
**Output:**
| `user_id`               | `action` | `pii_field` | `timestamp`               |
|-------------------------|----------|-------------|---------------------------|
| `660e8400-e29b-41d4...` | `DELETE`  | `email`      | `2024-05-20T15:15:22Z`    |

---

### **5.3 List Users with Revoked Consent**
```sql
SELECT u.user_id, p.policy_id, p.consent_status
FROM users u
JOIN PrivacyPolicy p ON u.user_id = p.user_id
WHERE p.consent_status = 'REVOKED';
```

---

## **6. Validation Rules**
| **Rule**                          | **Description**                                                                                                                                                                                                 | **Example Validation**                                                                                     |
|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| **Consent Required**              | Users must grant consent before data collection.                                                                                                                                                             | Reject `:POST /api/signup` if `consent_status` is `PENDING`.                                           |
| **Right to Erasure**              | Permit users to delete PII via `DELETE /api/users/me`.                                                                                                                                                        | Block deletion if `user_id` not authenticated.                                                             |
| **Data Minimization**             | Only store necessary fields (e.g., avoid storing `ssn` unless legally required).                                                                                                                       | Drop `ssn` column from `users` table unless GDPR-exempt.                                                  |
| **Third-Party Compliance**        | Ensure vendors meet compliance (e.g., via `vendor_compliance` flag).                                                                                                                                       | Reject external API calls unless `vendor_compliance = true`.                                               |
| **Audit Trail**                   | Log all PII modifications with `timestamp` and `actor_id`.                                                                                                                                                 | Require `actor_id` in `PIIAuditLog` for all actions.                                                      |

---

## **7. Error Handling**
| **Error**                          | **HTTP Status** | **Response Body (JSON)**                                                                                     | **Handling**                                                                                     |
|------------------------------------|-----------------|-----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Consent Not Granted**            | 403 Forbidden   | `{"error": "Consent required", "details": "No active privacy policy"}`                                   | Redirect to consent banner.                                                                  |
| **Insufficient Permissions**       | 403 Forbidden   | `{"error": "Unauthorized access", "details": "Not data owner"}`                                          | Validate `actor_id` matches `user_id`.                                                         |
| **PII Deletion Failed**            | 500 Internal Error | `{"error": "Deletion failed", "details": "Database error"}`                                             | Retry or notify user.                                                                          |
| **Invalid Policy Version**         | 400 Bad Request | `{"error": "Invalid policy", "details": "Outdated policy version"}`                                      | Update policy version in `PrivacyPolicy`.                                                      |

---

## **8. Performance Considerations**
- **Indexing:** Add indexes on `PrivacyPolicy(user_id)` and `PIIAuditLog(timestamp)`.
  ```sql
  CREATE INDEX idx_privacy_policy_user ON PrivacyPolicy(user_id);
  CREATE INDEX idx_audit_log_time ON PIIAuditLog(timestamp);
  ```
- **Batch Processing:** For bulk deletions (e.g., GDPR Article 17), use transactions:
  ```sql
  BEGIN;
  DELETE FROM users WHERE user_id IN (SELECT user_id FROM revoked_users);
  -- Log deletions
  INSERT INTO PIIAuditLog (...) VALUES (...);
  COMMIT;
  ```
- **Caching:** Cache consent status for frequently accessed users (e.g., Redis).

---

## **9. Security Recommendations**
- **Encrypt at Rest:** Use AES-256 for PII (e.g., AWS KMS, PostgreSQL `pgcrypto`).
- **Tokenize PII:** Replace sensitive data with tokens for analytics.
- **Rate Limiting:** Limit `/api/users/me` calls to prevent abuse (e.g., 10 requests/hour).
- **DLP (Data Loss Prevention):** Scan logs for exposed PII (e.g., using AWS Macie).

---

## **10. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Data Encryption]**     | Encrypts data at rest/transit to prevent unauthorized access.                                                                                                                                               | Always for PII storage/transmission.                                                               |
| **[Access Control]**      | Enforces RBAC/ABAC for data access (e.g., `user` can only access their own data).                                                                                                                             | Multi-tenant applications with PII.                                                                |
| **[Audit Logging]**       | Systematically records all user/system actions for compliance.                                                                                                                                             | Required by GDPR/CCPA for proving data handling practices.                                          |
| **[Tokenization]**        | Replaces sensitive data with non-sensitive tokens (e.g., credit card numbers).                                                                                                                              | Payment processing systems.                                                                        |
| **[Anonymization]**       | Removes or obscures PII to preserve privacy (e.g., for analytics).                                                                                                                                         | Sharing datasets for research.                                                                        |
| **[Secure Deletion]**     | Ensures PII is irrecoverably deleted (e.g., overwriting disk sectors).                                                                                                                                        | Hard deletes per user request.                                                                       |

---

## **11. Example Workflow: User Deletes Account**
1. **User Request:**
   - `DELETE /api/users/me` (authenticated via JWT).
2. **Backend Validation:**
   - Check `PrivacyPolicy` for `consent_status = GRANTED`.
   - Verify `actor_id` matches `user_id`.
3. **Data Deletion:**
   - Soft delete in `users` table (or hard delete if configured).
   - Log in `PIIAuditLog`: `action="DELETE"`, `pii_field="email"`, etc.
   - **Example (Python):**
     ```python
     def delete_user(user_id):
         # Log deletion
         log_entry = PIIAuditLog(
             user_id=user_id,
             action="DELETE",
             pii_field="email",
             timestamp=datetime.utcnow(),
             actor_id=user_id
         )
         PIIAuditLog.create(log_entry)

         # Delete data
         User.query.filter_by(user_id=user_id).delete()
     ```
4. **Response:**
   ```json
   {
       "success": true,
       "audit_log_id": "7e1a2b3c-4d5e-6f7g-8h9i-0j1k2l3m4n5o"
   }
   ```
5. **Audit Review:**
   - Admins can query `PIIAuditLog` to verify deletions:
     ```sql
     SELECT * FROM PIIAuditLog
     WHERE log_id = '7e1a2b3c-4d5e-6f7g-8h9i-0j1k2l3m4n5o';
     ```

---
## **12. Tools & Libraries**
| **Tool/Library**            | **Purpose**                                                                                                                                                                                                 | **Vendor**               |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------|
| **AWS KMS**                 | Managed encryption keys for PII at rest.                                                                                                                                                                       | AWS                      |
| **PostgreSQL `pgcrypto`**   | Column-level encryption and salting.                                                                                                                                                                         | PostgreSQL               |
| **OpenSSL**                 | Pseudonymization/tokenization for sensitive