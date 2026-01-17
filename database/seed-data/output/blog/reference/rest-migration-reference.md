# **[Pattern] REST Migration Reference Guide**

---
## **Overview**
The **REST Migration Pattern** enables seamless data migration between systems while maintaining API consistency, minimal downtime, and backward compatibility. It leverages RESTful principles (stateless interactions, resource-based endpoints, and HTTP methods) to transfer, transform, and validate data during migration. This pattern is ideal for:
- Moving data from legacy systems to modern APIs.
- Gradually replacing monolithic services with microservices.
- Implementing hybrid environments where old and new systems coexist.

The pattern ensures **idempotency**, **versioning**, and **parallel processing** to handle large datasets without disrupting production workloads.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|
| **Migration Endpoint**    | A dedicated REST route (e.g., `/api/v1/migrate/{source}/{target}`) to trigger migrations. |
| **Chunked Processing**    | Data is fetched/processed in batches (`?page=2&limit=1000`) to avoid memory overload. |
| **Delta Sync**            | Only updated records are transferred (via `If-Modified-Since` headers or timestamps). |
| **Validation Layer**      | Pre/post-migration checks (e.g., schema validation via [OpenAPI](https://www.openapis.org/)). |
| **Retry Mechanism**       | Exponential backoff for failed requests (e.g., `Retry-After` header).            |
| **Idempotency Key**       | Unique identifier (e.g., `X-Idempotency-Key`) to prevent duplicate operations. |
| **Logging & Monitoring**  | Centralized logs (e.g., ELK stack) for audit trails and failure analysis.       |

---

## **Schema Reference**
### **1. Migration Request Body (`POST /api/v1/migrate`)**
| Field               | Type      | Required | Description                                                                 |
|---------------------|-----------|----------|-----------------------------------------------------------------------------|
| `sourceSystem`      | String    | Yes      | Legacy system identifier (e.g., `"salesforce"`, `"mysql_db"`).               |
| `targetSystem`      | String    | Yes      | Target system identifier (e.g., `"aws_s3"`, `"graphql_api"`).               |
| `resourceType`      | String    | Yes      | Data resource to migrate (e.g., `"users"`, `"orders"`).                     |
| `fromTimestamp`     | ISO8601   | No       | Filter data from this timestamp (delta sync).                                 |
| `batchSize`         | Integer   | No       | Records per batch (default: `500`). Cannot exceed `10,000`.                   |
| `dryRun`            | Boolean   | No       | Preview changes without applying (default: `false`).                         |

**Example Request:**
```json
{
  "sourceSystem": "mysql_db",
  "targetSystem": "postgres_db",
  "resourceType": "products",
  "fromTimestamp": "2023-01-01T00:00:00Z",
  "batchSize": 1000
}
```

---

### **2. Migration Response**
| Field               | Type      | Description                                                                 |
|---------------------|-----------|-----------------------------------------------------------------------------|
| `status`            | String    | `"started"`, `"in_progress"`, `"completed"`, `"failed"`.                   |
| `totalRecords`      | Integer   | Total records in the migration job.                                         |
| `processedRecords`  | Integer   | Records processed so far.                                                   |
| `errors`            | Array     | List of error objects (if applicable).                                       |
| `jobId`             | String    | Unique identifier for monitoring progress.                                    |
| `etag`              | String    | Versioning token for idempotency (e.g., `"abc123"`).                        |

**Example Response:**
```json
{
  "status": "in_progress",
  "totalRecords": 25000,
  "processedRecords": 5000,
  "jobId": "mig_789xyz",
  "etag": "def456"
}
```

---

### **3. Error Object**
| Field       | Type    | Description                                                                 |
|-------------|---------|-----------------------------------------------------------------------------|
| `code`      | String  | Error classification (e.g., `"schema_mismatch"`, `"rate_limit_exceeded"`). |
| `message`   | String  | Human-readable error detail.                                                |
| `details`   | Object  | Machine-readable context (e.g., `{"field": "email", "reason": "invalid_format"}`). |
| `retryAfter`| Integer | Seconds to wait before retrying (if applicable).                            |

**Example Error:**
```json
{
  "errors": [
    {
      "code": "schema_mismatch",
      "message": "Field `legacy_id` not found in target schema.",
      "details": {"expectedFields": ["id", "name"]},
      "retryAfter": 0
    }
  ]
}
```

---

## **Query Examples**
### **1. Start a Migration Job**
```bash
curl -X POST "https://api.example.com/api/v1/migrate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "sourceSystem": "salesforce",
    "targetSystem": "mongodb",
    "resourceType": "contacts",
    "batchSize": 200,
    "dryRun": false
  }'
```

### **2. Check Job Status**
```bash
curl "https://api.example.com/api/v1/migrate/mig_789xyz" \
  -H "Authorization: Bearer <token>"
```
**Response:**
```json
{
  "status": "completed",
  "totalRecords": 1200,
  "processedRecords": 1200,
  "jobId": "mig_789xyz",
  "etag": "def456"
}
```

### **3. Pause/Resume a Job**
```bash
# Pause (suspend processing)
curl -X PUT "https://api.example.com/api/v1/migrate/mig_789xyz/pause" \
  -H "Authorization: Bearer <token>"

# Resume
curl -X PUT "https://api.example.com/api/v1/migrate/mig_789xyz/resume" \
  -H "Authorization: Bearer <token>"
```

### **4. Retrieve Failed Records**
```bash
curl "https://api.example.com/api/v1/migrate/mig_789xyz/errors" \
  -H "Authorization: Bearer <token>"
```
**Response:**
```json
[
  {
    "record": { "id": 42, "name": "Invalid Data" },
    "error": { "code": "validation_failed", "message": "Email format invalid." }
  }
]
```

### **5. Delta Sync (Incremental Update)**
```bash
curl -X POST "https://api.example.com/api/v1/migrate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "sourceSystem": "mysql_db",
    "targetSystem": "postgres_db",
    "resourceType": "orders",
    "fromTimestamp": "2023-05-15T00:00:00Z"
  }'
```

---

## **Implementation Steps**
### **1. Define Migration Endpoints**
- Use versioned paths (`/api/v1/migrate`) to support multiple migration versions.
- Implement **rate limiting** (e.g., 100 requests/minute) to avoid overloading target systems.

### **2. Implement Chunked Processing**
- Fetch records in batches (e.g., `LIMIT 1000` in SQL queries).
- Use **pagination headers** (e.g., `Link: <http://...?page=2>; rel="next"`).

### **3. Add Validation Layers**
- **Pre-migration**: Validate source data schema against a contract (e.g., using [JSON Schema](https://json-schema.org/)).
- **Post-migration**: Log discrepancies and notify stakeholders.

### **4. Enable Idempotency**
- Generate a unique `etag` for each job and store it in a database.
- Reject duplicate requests with the same `etag`.

### **5. Handle Failures Gracefully**
- Implement **exponential backoff** for retries (e.g., 1s → 2s → 4s).
- Provide **compensating transactions** (e.g., rollback partial migrations).

### **6. Monitor & Log**
- Use **metrics** (e.g., Prometheus) to track job duration, throughput, and errors.
- Store logs in a centralized system (e.g., [ELK Stack](https://www.elastic.co/elk-stack)).

---

## **Related Patterns**
| Pattern                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **CQRS (Command Query Responsibility Segregation)** | Separate read and write APIs to isolate migration traffic from production loads. |
| **Event Sourcing**          | Use migration events (e.g., `OrderCreated`) to reconstruct target state.    |
| **API Versioning**          | Maintain backward compatibility by supporting legacy API versions during migration. |
| **Saga Pattern**            | Orchestrate long-running migrations as a series of transactions.           |
| **Asynchronous Processing** | Offload migrations to a queue (e.g., [Kafka](https://kafka.apache.org/)) for scalability. |
| **Canary Deployment**       | Gradually shift traffic from legacy to new systems post-migration.          |

---
## **Troubleshooting**
| Issue                          | Solution                                                                 |
|--------------------------------|--------------------------------------------------------------------------|
| **Rate Limits Reached**        | Increase `batchSize` or implement retries with backoff.                  |
| **Schema Mismatches**          | Align source and target schemas pre-migration (use tools like [SchemaSpy](http://schemaspy.org/)). |
| **Duplicate Records**          | Add a unique constraint (e.g., `UNIQUE(id)`) to the target table.        |
| **Slow Performance**           | Optimize queries (add indexes) or use asynchronous processing.            |
| **Idempotency Conflicts**      | Regenerate `etag` if the job times out or is interrupted.                 |

---
### **Best Practices**
1. **Test in Staging**: Always run migrations in a non-production environment first.
2. **Document Changes**: Maintain a changelog for schema updates during migration.
3. **Notify Stakeholders**: Use webhooks or emails to alert teams of migration completion/failures.
4. **Support Rollback**: Design migrations to be reversible (e.g., store original data backups).
5. **Security**: Encrypt sensitive data (e.g., PII) during transit and at rest.

---
**See Also**:
- [REST API Design Best Practices](https://restfulapi.net/)
- [Delta Sync Patterns](https://martinfowler.com/articles/patterns-of-distributed-systems/delta-sync.html)
- [Idempotency in APIs](https://restfulapi.net/idempotency/)