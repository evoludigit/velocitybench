# **[Pattern] Privacy Profiling Reference Guide**

---

## **Overview**
**Privacy Profiling** is a security pattern used to dynamically classify data subjects (e.g., users, customers, or entities) based on their privacy preferences, access rights, and contextual risk factors. By aggregating and evaluating privacy-related attributes (e.g., anonymization needs, consent levels, or regulatory compliance requirements), organizations can enforce granular, context-aware access controls and data handling policies.

This pattern supports **differentiated privacy**, where data is processed according to an entity’s sensitivity profile rather than a one-size-fits-all approach. It is critical for compliance with regulations like **GDPR (Article 25)**, **CCPA**, and **HIPAA**, as well as for reducing exposure risks in **zero-trust architectures** and **privacy-preserving AI/ML systems**.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                                                                                                                                                 | **Example**                                                                                                                                                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Privacy Profile**    | A structured set of attributes (static/dynamic) defining an entity’s privacy requirements, risks, and access policies. Can include consent status, PII sensitivity, compliance jurisdiction, and anonymization needs.                                                                                     | `{"consent_level": "opt-out", "pii_sensitivity": "high", "jurisdiction": ["GDPR", "CCPA"], "anonymization": "hashed", "risk_score": 0.85}`                                                  |
| **Profile Source**     | The origin of profile data (e.g., user consent forms, IT policy assignments, or third-party risk assessments).                                                                                                                                                                                                                             | - User-provided preferences via a consent management platform (e.g., OneTrust).<br>- Automated risk scoring from a threat intelligence feed.<br>- Legacy system attributes (e.g., departmental clearance levels). |
| **Profile Update Rule**| Logic to refresh or modify a profile based on new data (e.g., time decay, event triggers, or user actions).                                                                                                                                                                                                                  | - Reset consent decay counter after explicit re-consent.<br>- Update risk score if a new privacy breach is detected in the entity’s jurisdiction.<br>- Anonymize data if sensitivity grade increases beyond threshold. |
| **Risk Context**      | External factors influencing profile validity (e.g., geolocation, time-of-day, or device type).                                                                                                                                                                                                                             | - A user in **EU jurisdiction** at **night** may have stricter anonymization applied.<br>- A **corporate device** accessing sensitive data triggers stricter audit logging.                                               |
| **Action Policies**    | Rules defining system responses to a profile (e.g., "If `pii_sensitivity = high`, apply tokenization").                                                                                                                                                                                                                     | - **Low risk**: Return raw data + metadata.<br>- **Medium risk**: Tokenize PII + apply differential privacy.<br>- **High risk**: Return only aggregate statistics.<br>- **Blocking**: Deny access via RBAC.                                         |
| **Profile Repository** | The storage mechanism for profiles (e.g., database table, graph database, or federated identity store). Should support fast lookups, versioning, and cross-system synchronization.                                                                                                                                  | - **Centralized**: PostgreSQL table with JSONB columns for flexibility.<br>- **Distributed**: Redis cache with TTL for ephemeral profiles.<br>- **Federated**: Sync profiles across systems via OAuth tokens.             |

---

## **Schema Reference**
Below is a **standardized schema** for implementing Privacy Profiles. Adjust fields according to your organization’s needs.

| **Field**               | **Type**      | **Description**                                                                                                                                                                                                                                                                                     | **Example Values**                                                                                                                                                                                                                                                  |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **profile_id**          | UUID          | Unique identifier for the profile.                                                                                                                                                                                                                             | `550e8400-e29b-41d4-a716-446655440000`                                                                                                                                                                                                                                              |
| **subject_id**          | String        | Identifier for the data subject (e.g., email, user ID, or anonymized token).                                                                                                                                                                                                         | `user123@example.com`                                                                                                                                                                                                                                                 |
| **profile_version**     | Integer       | Version for tracking changes (e.g., v1 = initial consent).                                                                                                                                                                                                                   | `2`                                                                                                                                                                                                                                                          |
| **attributes**          | JSON          | Key-value pairs of privacy-related attributes.                                                                                                                                                                                                                                | `{"consent": {"status": "granted", "expiry": "2025-01-01"}, "pii_sensitivity": "high", "jurisdictions": ["GDPR", "US"]}`                                                                                                         |
| **profile_sources**     | Array[Object] | Metadata on how the profile was generated or last updated.                                                                                                                                                                                                                     | `[{"source": "consent_form", "timestamp": "2024-05-01", "confidence": 0.95}, {"source": "risk_assessment", "timestamp": "2024-06-15"}]`                                                                                                                      |
| **risk_context**        | JSON          | Dynamic risk factors (e.g., geolocation, device risk score).                                                                                                                                                                                                                        | `{"location": "EU", "device_risk": "medium", "time": "14:00:00"}`                                                                                                                                                                                                                      |
| **action_policies**     | Array[Object] | Rules dictating system behavior based on the profile.                                                                                                                                                                                                                                       | `[{"condition": "pii_sensitivity = 'high'", "action": "tokenize"}, {"condition": "jurisdiction = 'CCPA'", "action": "right_to_delete"}]`                                                                                                                   |
| **last_updated**        | datetime      | Timestamp of the most recent profile modification.                                                                                                                                                                                                                                  | `2024-10-10T12:34:56Z`                                                                                                                                                                                                                                                 |
| **ttl**                 | Integer       | Time-to-live (seconds) for ephemeral profiles (e.g., session-based).                                                                                                                                                                                                                | `3600` (1 hour)                                                                                                                                                                                                                                                        |

---

## **Implementation Details**
### **1. Profile Sources**
Collect data from:
- **User Consent Management**: Platforms like **OneTrust**, **TrustArc**, or custom forms.
- ** Regulatory Checks**: APIs for GDPR/CCPA jurisdiction detection (e.g., [MaxMind GeoIP](https://www.maxmind.com/)).
- **Risk Scores**: Third-party threat feeds (e.g., **Recorded Future**, **Spikes Security**).
- **Legacy Systems**: Extract attributes from HR (e.g., role-based access) or CRM data.

**Example Integration**:
```python
# Pseudocode: Fetch consent data from a CMS
def fetch_consent(subject_id):
    response = requests.get(f"https://consent-api.example.com/users/{subject_id}")
    return {
        "profile_id": response.json()["id"],
        "subject_id": subject_id,
        "attributes": {
            "consent": response.json()["preferences"],
            "jurisdictions": detect_jurisdiction(subject_id)  # Call MaxMind API
        }
    }
```

### **2. Profile Updates**
- **Trigger-Based**: Update on events (e.g., user clicks "edit preferences").
- **Scheduled**: Refresh risky attributes daily (e.g., device risk scores).
- **Event-Driven**: Sync with profile changes in other systems (e.g., via **Apache Kafka**).

**Example Rule**:
> *"If `consent.expiry < current_date` AND `jurisdiction = 'GDPR'`, set `action_policies` to block anonymous requests."*

### **3. Profile Repository**
Options:
- **Relational DB**: PostgreSQL (for structured queries).
  ```sql
  CREATE TABLE privacy_profiles (
      profile_id UUID PRIMARY KEY,
      subject_id VARCHAR(255),
      attributes JSONB,
      last_updated TIMESTAMP
  );
  ```
- **NoSQL**: MongoDB (for flexible schemas).
  ```json
  {
      "_id": "550e8400-e29b-41d4-a716-446655440000",
      "subject_id": "user@example.com",
      "attributes": { "consent": { "status": "granted" } },
      "risk_context": { "location": "EU" }
  }
  ```
- **In-Memory**: Redis (for low-latency lookups).

**Performance Tip**: Cache frequently accessed profiles (e.g., `GET /profiles/{id}`) with a TTL matching `ttl` field.

### **4. Action Policies**
Enforce policies via:
- **Middleware**: Filter requests based on profiles (e.g., **OWASP ModSecurity** rules).
- **API Gateways**: Modify responses dynamically (e.g., **Kong**, **AWS API Gateway**).
- **Application Logic**: Check profiles before data access (e.g., Python `decorator`).

**Example Middleware Rule (Pseudocode)**:
```python
def privacy_filter(request, response):
    profile = get_profile(request.user)
    if profile["attributes"]["pii_sensitivity"] == "high":
        if request.params.get("anonymize") != "true":
            return AnonymizeResponse(response)
    return response
```

---

## **Query Examples**
### **1. Retrieve a Profile**
```http
GET /api/v1/profiles/user123@example.com
Headers: { "Authorization": "Bearer {JWT}" }
Response:
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440000",
  "subject_id": "user123@example.com",
  "attributes": {
    "consent": { "status": "granted", "expiry": "2025-01-01" },
    "pii_sensitivity": "medium"
  },
  "action_policies": [
    { "condition": "*", "action": "log_access" }
  ]
}
```

### **2. Update Consent Status**
```http
PATCH /api/v1/profiles/user123@example.com
Headers: { "Authorization": "Bearer {JWT}" }
Body:
{
  "attributes": {
    "consent": { "status": "revoked" }
  }
}
Response: 200 OK
```

### **3. List Profiles by Jurisdiction**
```http
GET /api/v1/profiles?jurisdiction=GDPR
Headers: { "Authorization": "Bearer {JWT}" }
Response:
[
  { "subject_id": "alice@example.com", "attributes": { "jurisdictions": ["GDPR"] } },
  { "subject_id": "bob@example.com", "attributes": { "jurisdictions": ["GDPR", "CCPA"] } }
]
```

### **4. Apply Risk Context**
```http
GET /api/v1/profiles/user123@example.com?location=EU&time=14:00:00
Headers: { "Authorization": "Bearer {JWT}" }
Response:
{
  "profile_id": "...",
  "action_policies": [
    { "condition": "*", "action": "tokenize" }  # EU default policy
  ]
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                                                                                 | **Use Case**                                                                                                                                                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Attribute-Based Access Control (ABAC)** | Grants access based on attributes (e.g., role, time, location) rather than static roles.                                                                                                                                                                               | Enforce dynamic access to sensitive data based on a user’s privacy profile.                                                                                                                                                       |
| **Consent Management**    | Tracks user consent for data processing, including granular opt-ins/opt-outs.                                                                                                                                                                                                       | Compliance with GDPR Art. 6/9 and CCPA “Do Not Sell” flags.                                                                                                                                                                          |
| **Data Masking**          | Applies anonymization techniques (e.g., tokenization, redaction) to PII.                                                                                                                                                                                                             | Reduce exposure of high-sensitivity data in logs or reports.                                                                                                                                                                           |
| **Zero Trust Architecture** |Verifies every access request, regardless of network location, using identity and context.                                                                                                                                                                                         | Combine with Privacy Profiling to enforce least-privilege access.                                                                                                                                                                      |
| **Differential Privacy**  | Adds noise to data to preserve individual privacy in aggregations.                                                                                                                                                                                                             | Use in analytics when profiling high-sensitivity groups.                                                                                                                                                                           |
| **Federated Identity**    | Centralizes identity management across systems via tokens (e.g., OAuth, OpenID Connect).                                                                                                                                                                                           | Sync privacy profiles across microservices.                                                                                                                                                                                       |

---

## **Best Practices**
1. **Granularity**: Avoid over-generalizing profiles (e.g., "all EU users" → instead, track consent per user).
2. **Auditability**: Log profile updates and policy changes for compliance (e.g., GDPR Art. 15).
3. **Performance**: Cache profiles but respect `ttl` to avoid stale data.
4. **Interoperability**: Use standardized schemas (e.g., [W3C PEP](https://www.w3.org/2001/tag/doc/pep-overview.html)) for cross-system sharing.
5. **Testing**: Validate profiles with **penetration tests** and **data protection impact assessments (DPIAs)**.