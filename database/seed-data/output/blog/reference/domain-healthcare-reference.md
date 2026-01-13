---
# **[Pattern Name] Healthcare Domain Patterns – Reference Guide**
*Structuring and modeling domain-specific data for healthcare applications.*

---

## **Overview**
The **Healthcare Domain Patterns** reference defines standardized data models, relationships, and conventions tailored for healthcare systems. This guide outlines best practices for implementing domain-specific entities like `Patient`, `Appointment`, `Medication`, and `Diagnosis`, ensuring compliance with healthcare interoperability standards (e.g., HL7 FHIR, SNOMED-CT) while addressing common challenges like:

- **Data granularity**: Balancing detail (e.g., lab measurements) with scalability.
- **Security**: Role-based access (e.g., clinicians vs. administrators) for sensitive data.
- **Temporal tracking**: Recording historical states (e.g., medication changes).
- **Integration**: Aligning with EHR systems, billing, and regulatory requirements (e.g., GDPR, HIPAA).

This pattern emphasizes **immutability** for audit trails (e.g., `Appointment` history) and **composition** over inheritance to handle domain-specific variants (e.g., `Inpatient` vs. `Outpatient`).

---

## **Schema Reference**
The following table defines core entities, fields, and relationships. *Required fields are marked with `*`.

| **Entity**       | **Field**               | **Type**               | **Description**                                                                                     | **Constraints**                          | **Example**                          |
|------------------|-------------------------|------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|--------------------------------------|
| **Patient**      | `patientId*`            | UUID                   | Unique identifier (e.g., system-generated or healthcare plan).                                      | Must match EHR system ID if shared.      | `a1b2c3d4-5678-90ef`                 |
|                  | `demographics`          | Struct                | { `name`: string, `dob`: date, `gender`: Enum, `contact`: Struct }                                | `gender` must be in `[M, F, O, U]`.      | `{ name: "J. Doe", dob: "1980-05-15" }` |
|                  | `allergies`             | Array[Allergy]         | List of known allergies (referenced by SNOMED-CT codes).                                             | Min 1 entry if clinically relevant.     | `[{ code: "SNOMED-CT-1234", severity: "high" }]` |
|                  | `healthInsurance`       | Struct                | { `policyId`: string, `provider`: string, `coveragePeriod`: [start, end] }                       | `policyId` must match insurer’s format.  | `{ policyId: "INS12345678", provider: "BlueCross" }` |
| **Appointment**  | `appointmentId*`        | UUID                   | Unique identifier.                                                                                 | Must include temporal metadata.           | `x9y8z7w6-456u-123v`                 |
|                  | `patientId*`            | UUID                   | References `Patient.patientId`.                                                                     | Must exist in `Patient` table.           | `a1b2c3d4-5678-90ef`                 |
|                  | `type`                  | Enum                  | `[inpatient, outpatient, telehealth]`.                                                             | Required for billing classification.     | `outpatient`                          |
|                  | `status`                | Enum                  | `[scheduled, completed, canceled, no-show]`.                                                       | Automatic transitions via event hooks.   | `completed`                           |
|                  | `startTime*`            | ISO8601 (datetime)     | Scheduled or actual start time.                                                                     | Must align with provider’s calendar.     | `"2023-11-15T09:00:00Z"`              |
|                  | `duration`              | Duration (ISO8601)    | Expected/appointed duration (e.g., `PT1H30M`).                                                     | Must match provider’s slot duration.      | `PT45M`                               |
|                  | `provider`              | Struct                | { `id`: UUID, `specialty`: string, `availability`: Struct }                                        | `specialty` tied to credentialing.       | `{ id: "provider-xyz", specialty: "Cardiology" }` |
| **Diagnosis**    | `diagnosisId*`          | UUID                   | Unique identifier.                                                                                 | Must link to `Appointment` via `appointmentId`. | `qwe123rty-456uv-789op`            |
|                  | `appointmentId*`        | UUID                   | References `Appointment.appointmentId`.                                                             | Required for context.                   | `x9y8z7w6-456u-123v`                 |
|                  | `icdCode*`              | string                 | Standardized diagnosis code (ICD-10-CM).                                                           | Validate against latest HL7 FHIR bundle. | `"I10"` (Essential hypertension)      |
|                  | `description`           | string                 | Plain-text summary (for non-standard codes).                                                        | Max 255 chars.                          | `"Hypertension, stage 2"`              |
|                  | `confirmedBy`           | UUID                   | References `Provider.id`.                                                                            | Must be a licensed clinician.            | `"provider-abc123"`                   |
|                  | `confirmedAt*`          | ISO8601 (datetime)     | Timestamp of diagnosis confirmation.                                                              | Must be ≤ `appointment.endTime`.         | `"2023-11-15T09:45:00Z"`              |
| **Medication**   | `medicationId*`         | UUID                   | Unique identifier.                                                                                 | Must track lifecycle (prescription → fulfillment). | `llk90m12-n345p-678qr`            |
|                  | `prescriptionId*`       | UUID                   | References `Prescription.prescriptionId`.                                                           | Required for audit.                     | `prescr-7890`                         |
|                  | `drug`                  | Struct                | { `code`: string (ATC/NDC), `name`: string, `form`: Enum }                                          | `code` must match PharmGKB.               | `{ code: "ATC-0513", name: "Lisinopril" }` |
|                  | `dosage`                | Struct                | { `strength`: string, `frequency`: string, `route`: Enum }                                         | `strength` must be quantifiable.         | `{ strength: "10mg", frequency: "daily" }` |
|                  | `status`                | Enum                  | `[active, discontinued, completed]`.                                                               | Auto-transition on patient actions.     | `active`                              |
|                  | `startDate*`            | ISO8601 (date)         | Start date of medication regimen.                                                                  | Must be ≥ `appointment.startTime`.        | `"2023-11-16"`                         |
|                  | `endDate`               | ISO8601 (date)         | Optional: End date for short-term regimens.                                                         | If null, defaults to future date.       | `"2024-05-15"`                         |

---
### **Relationships**
| **Entity**       | **Navigation**                          | **Description**                                                                                     |
|------------------|-----------------------------------------|-----------------------------------------------------------------------------------------------------|
| `Appointment`    | ↔ `Patient`                             | 1-to-many; a patient can have multiple appointments.                                               |
| `Appointment`    | ↔ `Provider`                            | Many-to-many via `appointmentProvider` (auxiliary table for scheduling conflicts).                  |
| `Appointment`    | ↔ `Diagnosis` (cascade delete)         | 1-to-many; diagnoses are tied to appointments for clinical flow.                                |
| `Medication`     | ↔ `Prescription` (1:1)                 | Medications are derived from prescriptions; track fulfillment via `Fulfillment` entity.           |
| `Patient`        | ↔ `HealthInsurance` (1:1)              | Single primary insurer per patient; use auxiliary table for secondary insurers.                   |

---
### **Auxiliary Tables**
| **Table**        | **Purpose**                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `appointmentProvider` | Resolves many-to-many between `Appointment` and `Provider`.               |
| `Fulfillment`    | Tracks pharmacy dispensing (e.g., `fulfilledAt`, `quantityDispensed`).       |
| `LabResult`      | Stores test results (e.g., `value`, `units`, `referenceRange`).              |

---

## **Query Examples**
Use the following queries to interact with the schema. *Parameterize inputs for security.*

### **1. Retrieve a Patient’s Active Appointments**
```sql
SELECT a.*
FROM Appointment a
JOIN Patient p ON a.patientId = p.patientId
WHERE p.patientId = 'a1b2c3d4-5678-90ef'
  AND a.status IN ('scheduled', 'completed')
  AND a.startTime >= NOW() - INTERVAL '30 days'
ORDER BY a.startTime DESC;
```

### **2. List Medications for a Patient (Current + Past)**
```sql
SELECT m.*
FROM Medication m
JOIN Prescription p ON m.prescriptionId = p.prescriptionId
WHERE p.patientId = 'a1b2c3d4-5678-90ef'
  AND (m.endDate IS NULL OR m.endDate >= CURRENT_DATE)
ORDER BY m.startDate DESC;
```

### **3. Find Appointments with Unconfirmed Diagnoses**
```sql
SELECT a.appointmentId, a.startTime, d.diagnosisId
FROM Appointment a
LEFT JOIN Diagnosis d ON a.appointmentId = d.appointmentId
WHERE a.status = 'completed'
  AND d.confirmedAt IS NULL
ORDER BY a.startTime DESC;
```

### **4. Validate ICD-10 Code Against HL7 FHIR Bundle**
```javascript
// Example using FHIR validation (pseudo-code)
const icdCode = "I10";
const fhirBundle = await fetchHL7FHIRBundle();
const isValid = fhirBundle.codes.includes(icdCode);
if (!isValid) throw new Error("Invalid ICD-10 code");
```

### **5. Audit Trail: Track Medication Status Changes**
```sql
SELECT
  m.medicationId,
  m.status,
  JSON_BUILD_OBJECT(
    'changedBy', e.userId,
    'timestamp', e.eventTime,
    'oldStatus', e.oldValue
  ) AS metadata
FROM Medication m
JOIN audit_events e ON m.medicationId = e.entityId
WHERE e.entityType = 'Medication'
  AND e.eventType = 'status_update'
  AND m.patientId = 'a1b2c3d4-5678-90ef'
ORDER BY e.eventTime DESC;
```

---

## **Best Practices**
1. **Immutability for Audit**:
   - Use append-only logs (e.g., `audit_events`) for fields like `Diagnosis.confirmedAt` or `Appointment.status`.
   - Example: Store `oldValue` in the audit table when `status` changes.

2. **Temporal Data Handling**:
   - Use **valid-time** modeling for records with expiry (e.g., `HealthInsurance.coveragePeriod`).
   - Example: Query `Appointment` with `startTime` between two dates to filter by time period.

3. **Code Standardization**:
   - Enforce standardized codes (e.g., **ICD-10**, **ATC**) via:
     - Database constraints (e.g., `CHECK (icdCode LIKE 'I%'` for ICD-10).
     - Application-level validation (e.g., regex for NDC codes).

4. **Role-Based Access**:
   - Implement **row-level security** (RLS) or **attribute-based access control (ABAC)**:
     ```sql
     -- Example RLS policy for Patient data
     CREATE POLICY patient_access_policy
     ON Patient FOR SELECT
     USING (user_id IN (
       SELECT user_id FROM provider_roles
       WHERE provider_id = current_user_provider_id()
     ));
     ```

5. **Data Retention**:
   - Archive inactive records (e.g., `status = 'discontinued'` medications) to a cold storage tier after 5 years.
   - Example partition strategy:
     ```sql
     CREATE TABLE Medication_archive (
       LIKE Medication INCLUDING ALL
     ) PARTITION BY RANGE (endDate);
     ```

6. **Interoperability**:
   - Expose FHIR-compliant endpoints for integration:
     ```http
     GET /Patient/{id}/$everything
     Accept: application/fhir+json
     ```

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Risk**                                          | **Mitigation**                                                                 |
|--------------------------------------|---------------------------------------------------|--------------------------------------------------------------------------------|
| **Lack of temporal precision**       | Misaligned appointment slots or diagnosis timelines. | Use `startTime`/`endTime` with timezone awareness (ISO8601).                   |
| **Over-normalizing medication data** | Complex joins for regimens.                      | Denormalize into `MedicationRegimen` for common queries.                      |
| **Hardcoded insurance logic**        | Non-compliant with insurer updates.               | Externalize rules via API (e.g., `/insurer/rules/{policyId}`).               |
| **Ignoring SNOMED-CT hierarchies**   | Inconsistent allergy terminology.                 | Use Ontology APIs (e.g., [SNOMED CT Web Service](https://browser.ihtsdotools.org/)). |
| **No conflict resolution**           | Duplicate appointments or overlapping diagnoses.  | Enforce unique constraints on `(patientId, startTime, duration)`.              |

---

## **Related Patterns**
Consume or extend these patterns for complementary healthcare use cases:

1. **[Event Sourcing for Healthcare](link)**
   - Replace CRUD with append-only logs for `Appointment` or `Diagnosis` events (e.g., `AppointmentScheduled`, `DiagnosisConfirmed`).

2. **[Healthcare API Gateway](link)**
   - Standardize requests/responses for FHIR, HL7v2, or custom workflows (e.g., `/appointment/book`).

3. **[Patient Consent Management](link)**
   - Model granular consent (e.g., `Patient.canAccess: { healthRecords: true, research: false }`).

4. **[Observation Patterns](link)**
   - Extend `LabResult` for HL7 FHIR Observation resources (e.g., `Observation.status = "final"`).

5. **[Billing Integration](link)**
   - Map `Appointment.type` to revenue codes (e.g., `outpatient → 99201-99215`).

6. **[Telehealth Workflows](link)**
   - Add `Appointment.technicalSetup` field (e.g., `{ platform: "Zoom", link: "..." }`).

---

## **Tools & Libraries**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **HL7 FHIR SDK**       | Generate models from FHIR profiles (e.g., `Patient` → `com.hl7.fhir.r4.model.Patient`). |
| **PostgreSQL JSONB**   | Flexible schemas for `demographics` or `audit_events`.                     |
| **Eclipse HAPI**       | FHIR server implementation for interoperability.                           |
| **SNOMED-CT Browser**  | Code lookup for `allergies` or `diagnosis`.                                  |
| **OpenTelemetry**      | Trace patient journeys across microservices.                                |

---
## **Further Reading**
- [HL7 FHIR Patient Resource](https://hl7.org/fhir/patient.html)
- [ICD-10-CM Official Guidelines](https://www.cms.gov/Medicare/Coding/ICD10)
- [SNOMED CT International](https://www.snomed.org/)
- [GDPR Healthcare Compliance](https://gdpr.eu/healthcare/)