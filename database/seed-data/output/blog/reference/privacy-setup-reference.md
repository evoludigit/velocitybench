```markdown
# **[Pattern] Privacy Setup Reference Guide**

---

## **1. Overview**
The **Privacy Setup** pattern defines a structured approach to configure privacy-related settings across applications, services, or systems. It ensures users can control data sharing, consent preferences, and access controls while maintaining compliance with regulations like **GDPR, CCPA, or industry standards (e.g., HIPAA)**. This pattern standardizes privacy configurations, reduces friction for users, and minimizes security risks by enforcing consistent privacy policies.

The pattern supports the following key privacy use cases:
- **Data Collection Preferences** (e.g., tracking, analytics, ads)
- **Consent Management** (one-time or time-bound permissions)
- **Access Controls** (Granular permissions for user data)
- **Regulatory Compliance** (Automated adjustments for legal requirements)
- **Data Export/Deletion** (User-triggered actions like "right to erasure")

Best suited for: **Apps, Web Portals, SaaS Platforms, IoT Services**, and any system handling personally identifiable information (PII).

---

## **2. Schema Reference**
The following schema defines the core components of the **Privacy Setup** pattern. All fields are **mandatory** unless noted.

| **Field**               | **Type**      | **Description**                                                                                                                                                                                                 | **Example Values**                                                                 |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `privacyId`             | `string`      | Unique identifier for the privacy configuration set. Used to reference related settings.                                                                                                                     | `"privacy-2024-0515-v1"`                                                       |
| `userId`                | `string`      | Identifier for the user accessing the settings (e.g., JWT token or UUID).                                                                                                                                       | `"user_abc123"`                                                                   |
| `timestamp`             | `datetime`    | When the configuration was created/updated.                                                                                                                                                              | `"2024-05-15T14:30:00Z"`                                                      |
| `dataCollection`        | `object`      | Defines how user data is collected and processed.                                                                                                                                                          |                                                                                   |
| &nbsp;&nbsp;`enabled`   | `boolean`     | Whether data collection is active.                                                                                                                                                                       | `true/false`                                                                  |
| &nbsp;&nbsp;`purpose`   | `array[enum]` | Specifies purposes for data collection (e.g., `"marketing"`, `"analytics"`, `"support"`).                                                                                                                  | `["analytics", "marketing"]`                                                   |
| &nbsp;&nbsp;`dataTypes` | `array[string]`| Types of data collected (e.g., `"email"`, `"location"`, `"browsing_history"`).                                                                                                                             | `["email", "browsing_history"]`                                                |
| `consent`               | `object`      | User consent status tied to specific data uses.                                                                                                                                                             |                                                                                   |
| &nbsp;&nbsp;`status`    | `enum`        | `"granted"`, `"denied"`, or `"pending"` for consent.                                                                                                                                                      | `"granted"`                                                                  |
| &nbsp;&nbsp;`expiry`    | `datetime`    | Consent expiration date (e.g., for time-bound permissions).                                                                                                                                                 | `"2024-12-31T23:59:59Z"`                                                      |
| &nbsp;&nbsp;`termsLink` | `string`      | URL to the privacy policy or terms of consent.                                                                                                                                                          | `"https://example.com/privacy-policy"`                                       |
| `accessControls`        | `object`      | Rules governing who can access user data.                                                                                                                                                                    |                                                                                   |
| &nbsp;&nbsp;`thirdParty`| `array[object]`| List of permitted third-party integrations with access scopes.                                                                                                                                        | `[{ "id": "ad_provider_1", "scopes": ["ads"] }]`                              |
| &nbsp;&nbsp;`sharing`   | `enum`        | `"limited"`, `"restricted"`, or `"public"` for data sharing permissions.                                                                                                                                    | `"restricted"`                                                                |
| `compliance`            | `object`      | Auto-adjustments for legal requirements.                                                                                                                                                                     |                                                                                   |
| &nbsp;&nbsp;`region`    | `string`      | Jurisdiction (e.g., `"EU"`, `"US-CCPA"`) triggering compliance rules.                                                                                                                                      | `"EU"`                                                                          |
| &nbsp;&nbsp;`rules`     | `array[enum]` | Applied compliance rules (e.g., `"gdrp-right-to-erasure"`, `"ccpa-opt-out"`).                                                                                                                               | `["ccpa-opt-out"]`                                                            |
| `dataExport`            | `object`      | Configures export/delete actions.                                                                                                                                                                          |                                                                                   |
| &nbsp;&nbsp;`enabled`   | `boolean`     | Whether export/delete is accessible to users.                                                                                                                                                           | `true`                                                                           |
| &nbsp;&nbsp;`endpoint`  | `string`      | API/URL for exporting user data (e.g., `/api/export`).                                                                                                                                                  | `"/api/data-export"`                                                          |
| `metadata`              | `object`      | Free-form notes for admins (e.g., "Updated for GDPR compliance").                                                                                                                                       | `{ "notes": "Reviewed by Legal Team" }`                                         |

---

## **3. Query Examples**
Use these queries to interact with the **Privacy Setup** pattern via APIs (e.g., REST/GraphQL).

### **3.1. Fetch Current Privacy Settings**
Retrieve a user’s active privacy configuration.

**Endpoint:** `GET /api/privacy/settings?userId=user_abc123`

**Request:**
```json
{
  "userId": "user_abc123"
}
```

**Response:**
```json
{
  "privacyId": "privacy-2024-0515-v1",
  "userId": "user_abc123",
  "timestamp": "2024-05-15T14:30:00Z",
  "dataCollection": {
    "enabled": true,
    "purpose": ["analytics", "marketing"],
    "dataTypes": ["email", "browsing_history"]
  },
  "consent": {
    "status": "granted",
    "expiry": "2024-12-31T23:59:59Z",
    "termsLink": "https://example.com/privacy-policy"
  },
  "accessControls": {
    "thirdParty": [
      { "id": "ad_provider_1", "scopes": ["ads"] }
    ],
    "sharing": "restricted"
  }
}
```

---

### **3.2. Update Consent Status**
Modify a user’s consent (e.g., revoke marketing consent).

**Endpoint:** `PATCH /api/privacy/consent`

**Request:**
```json
{
  "userId": "user_abc123",
  "consent": {
    "purpose": ["analytics"], // Remove "marketing"
    "status": "granted",
    "expiry": null // No expiry
  }
}
```

**Response:**
```json
{
  "success": true,
  "privacyId": "privacy-2024-0515-v2", // Auto-incremented ID
  "updatedTimestamp": "2024-05-16T09:15:00Z"
}
```

---

### **3.3. Trigger Data Export**
Initiate a data export request (e.g., for GDPR right to access).

**Endpoint:** `POST /api/privacy/export`

**Request:**
```json
{
  "userId": "user_abc123",
  "exportType": "full" // "full" or "partial"
}
```

**Response:**
```json
{
  "exportId": "export_req_789",
  "status": "pending",
  "endpoint": "https://example.com/download?token=abc123"
}
```

---

### **3.4. Apply Compliance Rules**
Auto-adjust settings for a new jurisdiction (e.g., switching from US to EU).

**Endpoint:** `POST /api/privacy/compliance`

**Request:**
```json
{
  "userId": "user_abc123",
  "region": "EU",
  "rules": ["gdrp-right-to-erasure"]
}
```

**Response:**
```json
{
  "privacyId": "privacy-2024-0516-v3",
  "accessControls": {
    "sharing": "limited",
    "thirdParty": [] // Revoked third-party access
  },
  "compliance": {
    "region": "EU",
    "rules": ["gdrp-right-to-erasure"]
  }
}
```

---

## **4. Implementation Notes**
### **4.1. Data Flow**
1. **User Action**: User modifies settings via UI/API.
2. **Validation**: System checks for conflicts (e.g., revoking all consent).
3. **Storage**: Updates stored in a **privacy database** (e.g., Redis for speed, PostgreSQL for auditing).
4. **Propagation**: Adjusts access controls across services (e.g., triggers a webhook to analytics tools).

### **4.2. Security Considerations**
- **Encryption**: Encrypt `privacyId` and `userId` in transit/use.
- **Audit Logs**: Log changes to `privacyId` with timestamps (e.g., for GDPR Article 30).
- **Rate Limiting**: Prevent brute-force attacks on `/privacy` endpoints.

### **4.3. UI/UX Best Practices**
- **Progressive Disclosure**: Hide advanced options (e.g., `accessControls`) behind a toggle.
- **Visual Feedback**: Show icons for consent status (e.g., ✅/❌ for granted/denied).
- **Accessibility**: Support keyboard navigation and screen readers for privacy controls.

---

## **5. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **Connection to Privacy Setup**                                                                 |
|---------------------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **[Consent Management]**   | Tracks user consent across sessions/apps.                                 | Reuses `consent.status` and `consent.expiry` fields from **Privacy Setup**.                     |
| **[Data Masking]**        | Redacts PII in logs/databases.                                            | Complements **Privacy Setup** by enforcing `accessControls.sharing`.                           |
| **[User Authentication]** | Verifies user identity for sensitive actions (e.g., exporting data).       | Requires `userId` from **Privacy Setup** to authenticate export requests.                      |
| **[Audit Logging]**       | Logs privacy-related actions for compliance.                               | Logs updates to `privacyId`, `consent`, and `compliance` rules.                                 |
| **[Third-Party Integrations]** | Manages external service access (e.g., analytics, ads).               | Uses `accessControls.thirdParty` to scope permissions.                                           |
| **[Data Residency]**      | Ensures data is stored in compliant regions.                              | Works with `compliance.region` to auto-route data storage.                                       |

---

## **6. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                                     |
|-------------------------------------|----------------------------------------|--------------------------------------------------------------------------------------------------|
| Consent not saving                  | Missing `termsLink` or invalid `purpose`. | Validate schema before submission; ensure `purpose` is in `["analytics", "marketing", ...]`.    |
| Third-party access blocked         | Incorrect `scopes` in `thirdParty`.     | Verify scopes match the provider’s API (e.g., `["ads"]` for ad networks).                         |
| Export fails                       | `exportType` not supported.            | Check documentation for valid types (e.g., `"full"` vs. `"partial"`).                            |
| Compliance rules not applied       | Region mismatch in `compliance.region`. | Ensure `region` matches the user’s profile (e.g., `"EU"` for GDPR).                              |

---
**Version:** `1.2`
**Last Updated:** `2024-05-15`
**Contact:** `privacy-support@example.com`
```