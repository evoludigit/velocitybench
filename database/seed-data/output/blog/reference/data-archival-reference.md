---
# **[Pattern] Data Archival & Cold Storage Reference Guide**

---

## **1. Overview**
The **Data Archival & Cold Storage** pattern addresses the long-term retention and cost-effective preservation of historical data while ensuring **compliance, accessibility, and performance optimization**. Unlike hot storage (frequently accessed data) or warm storage (infrequently accessed but retained on primary systems), cold storage is designed for data that is rarely accessed but must be retained for regulatory, legal, or business continuity purposes (e.g., audit logs, backups, or legacy datasets).

This pattern outlines:
- **When** to use cold storage (e.g., data > 90 days old, rarely queried).
- **How** to implement tiered storage (e.g., moving data from hot → warm → cold).
- **Best practices** for data lifecycle management, retrieval strategies, and cost reduction.
- **Technical considerations** (e.g., compression, partitioning, and access patterns).

Cold storage integrates with **archival systems** (e.g., tape libraries), **object storage** (e.g., AWS S3 Glacier, Azure Cold Storage), or **hybrid architectures** (e.g., tiered databases). This guide assumes familiarity with **data retention policies** and basic cloud/storage concepts.

---

## **2. Schema Reference**
The following tables define key components of the **Data Archival & Cold Storage** pattern.

### **2.1 Core Components**
| **Component**               | **Description**                                                                                                                                 | **Example Technologies**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Primary Storage (Hot)**  | Active data tier with low-latency access (e.g., transactional databases, in-memory caches).                                               | PostgreSQL, Redis, Amazon RDS                                                                                 |
| **Warm Storage**            | Infrequently accessed but retained near primary storage (e.g., archived logs, backups).                                                     | Amazon S3 Standard-IA, Azure Blob Storage Cool, self-managed HDDs                                            |
| **Cold Storage**            | Long-term, rarely accessed data (e.g., historical records, compliance archives). Retrieval may introduce delays (hours/days).                | AWS S3 Glacier, Azure Archive Storage, tape libraries (e.g., IBM Linear Tape-Open)                          |
| **Archival Gateway**        | Interface for managing cold storage (e.g., initiating retrievals, lifecycle policies).                                                      | AWS S3 Batch Operations, Azure Data Lake Storage API, custom ETL pipelines                                    |
| **Metadata Catalog**        | Catalog of archived data (e.g., metadata, access policies, retention dates) to enable discovery.                                         | AWS Glue Data Catalog, Apache Atlas, custom NoSQL database (e.g., MongoDB)                                    |
| **Lifecycle Manager**       | Automates transitions between storage tiers (e.g., TTL-based deletions, compression, or cold migration).                               | AWS S3 Lifecycle Policies, Azure Blob Lifecycle Management, custom scripts (e.g., Python + Airflow)          |
| **Retrieval Pipeline**      | Processes for restoring cold data to warm/hot tiers when needed (e.g., batch jobs, on-demand requests).                               | Serverless functions (AWS Lambda), Spark jobs, or custom microservices                                        |

---

### **2.2 Data Lifecycle Phases**
| **Phase**               | **Duration**       | **Access Frequency** | **Storage Tier**       | **Use Case Examples**                                      | **Retrieval Latency** |
|-------------------------|--------------------|----------------------|------------------------|-----------------------------------------------------------|-----------------------|
| **Hot**                 | <30 days           | Frequent (real-time) | Primary storage        | User-facing data, active transactions                       | Sub-millisecond       |
| **Warm**                | 30–365 days        | Infrequent           | Nearline storage       | Archived logs, reporting data, backups                     | Seconds to minutes     |
| **Cold (Active Archival)** | 1–10 years      | Very rare            | Cold storage (e.g., Glacier) | Compliance archives, long-term backups                     | Minutes to hours       |
| **Cold (Deep Archive)**  | >10 years          | Rare (exceptional)  | Deep archive (tape)    | Legal holds, historical research                           | Hours to days          |

---

### **2.3 Access Patterns**
| **Pattern**              | **Description**                                                                                                                                 | **Example Query**                                                                                             |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Time-Based Retrieval** | Fetch data within a specific date range (e.g., "show all orders from 2020").                                                          | `SELECT * FROM orders WHERE order_date BETWEEN '2020-01-01' AND '2020-12-31'`                                  |
| **Metadata Query**       | Search archived data by metadata (e.g., "find all records with tag='compliance'").                                                     | `GET /archive?tags=compliance` (API call to metadata catalog)                                                   |
| **Batch Restore**        | Restore a large dataset from cold to warm storage for analysis.                                                                          | `aws s3 cp s3://cold-bucket/data-2020 --target bucket-warm` (AWS CLI)                                        |
| **On-Demand Retrieval**  | Request specific files/documents (e.g., "restore user-profile-12345.zip").                                                              | `POST /archive/restore?file_id=12345` (via API)                                                                |
| **Compliance Scan**      | Audit or validate data integrity in cold storage (e.g., "check all records from 2015 for PII compliance").                           | Custom script to compare checksums in cold storage vs. warm storage                                             |

---

## **3. Implementation Details**
### **3.1 Choose Your Storage Tier**
Select based on **cost, retrieval speed, and compliance needs**:
- **Cold Storage (e.g., S3 Glacier Flexible Retrieval)**
  - **Cost**: ~$0.0036/GB/month + retrieval fees ($0.01–$0.05/GB).
  - **Speed**: Minutes to hours for retrieval.
  - **Best for**: Data accessed <1x/year (e.g., backups, legal holds).
- **Deep Archive (e.g., S3 Glacier Deep Archive)**
  - **Cost**: ~$0.00099/GB/month + retrieval fees ($0.01/GB for standard, $0.25/GB for expedited).
  - **Speed**: 12+ hours (standard) or hours (expedited).
  - **Best for**: Near-immutable data (e.g., decades-old logs).

**Rule of Thumb**:
- **<90 days old** → Warm storage (e.g., S3 Standard-IA).
- **90 days–10 years** → Cold storage (e.g., Glacier Flexible).
- **>10 years** → Deep archive or tape.

---

### **3.2 Design for Retrieval Efficiency**
Cold storage introduces **latency**. Mitigate this with:
1. **Pre-Fetching**: Restore data to warm storage **before** a query is run (e.g., nightly batch jobs).
   ```python
   # Example: AWS Lambda triggered by CloudWatch Event (daily at 2 AM)
   import boto3
   s3 = boto3.client('s3')
   def lambda_handler(event, context):
       s3.copy_object(
           Bucket='cold-data-bucket',
           CopySource={'Bucket': 'cold-data-bucket', 'Key': 'data-2020.zip'},
           Key='warm-data/data-2020.zip'
       )
   ```
2. **Metadata Optimization**:
   - Store **indexes** in warm storage (e.g., Elasticsearch for metadata search).
   - Use **partitioning** (e.g., `year/month/day/` folders in S3) for faster retrieval.
3. **Hybrid Queries**:
   - Combine cold storage with **hot caches** (e.g., Redis) for frequently needed metadata.
   - Example: Cache `SELECT COUNT(*) FROM archived_orders WHERE year=2020` in Redis.

---

### **3.3 Automate Lifecycle Management**
Use **policies** to automate tier transitions:
- **AWS S3 Lifecycle Rule Example**:
  ```json
  {
    "Rules": [
      {
        "ID": "MoveToColdAfter90Days",
        "Status": "Enabled",
        "Transitions": [
          {
            "Days": 90,
            "StorageClass": "GLACIER"
          }
        ],
        "Expiration": {
          "Days": 3650  // 10 years
        }
      }
    ]
  }
  ```
- **Custom Scripts** (for non-cloud environments):
  ```bash
  # Example: Move files older than 30 days to cold storage
  find /path/to/data -type f -mtime +30 -exec mv {} /cold_storage/ \;
  ```

---

### **3.4 Compliance and Security**
- **Encryption**: Enable **at-rest encryption** (e.g., AWS KMS, Azure Storage Service Encryption).
- **Access Control**:
  - Use **IAM policies** (AWS) or **Azure RBAC** to restrict cold storage access.
  - Example IAM policy for cold storage retrieval:
    ```json
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::cold-bucket/*"],
      "Condition": {
        "StringEquals": {"aws:ResourceTag/Compliance": "Audit"}
      }
    }
    ```
- **Retention Locks**: Use **WORM (Write Once, Read Many)** storage (e.g., AWS S3 Object Lock) to prevent deletions.

---

## **4. Query Examples**
### **4.1 Time-Based Retrieval (SQL)**
Assume a **staged archive table** in PostgreSQL with partitions:
```sql
-- Partitioned table: archived_orders (partitioned by year)
CREATE TABLE archived_orders (
    order_id VARCHAR(36),
    customer_id VARCHAR(36),
    amount DECIMAL(10, 2)
)
PARTITION BY RANGE (order_date)
INTERVAL ('1 year');

-- Query orders from 2020 (partition prunes irrelevant data)
SELECT SUM(amount)
FROM archived_orders
WHERE order_date BETWEEN '2020-01-01' AND '2020-12-31';
```
**Optimization**:
- Use `PARTITION prune` to avoid scanning all cold partitions.
- Offload aggregations to **materialized views** in warm storage.

---

### **4.2 Cold Storage Retrieval (AWS CLI)**
Restore a dataset from S3 Glacier Flexible Retrieval:
```bash
# Initiate retrieval (returns retrieval job ID)
aws s3api restore-object \
    --bucket cold-bucket \
    --key data-2020.zip \
    --restore-request '{"Days": 1}'  # Expedited (1 day) retrieval

# Wait for completion (~1 day), then copy to warm storage
aws s3 cp s3://cold-bucket/data-2020.zip s3://warm-bucket/
```

---

### **4.3 Metadata Search (Elasticsearch)**
Index metadata in Elasticsearch for fast queries:
```json
# Sample document in Elasticsearch
{
  "order_id": "123e4567-e89b-12d3-a456-426614174000",
  "year": 2020,
  "customer_id": "abc123",
  "storage_tier": "cold",
  "restore_url": "s3://cold-bucket/orders/123e4567..."
}

# Query: Find all 2020 orders with customer_id starting with 'abc'
GET /archived-orders/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "year": 2020 } },
        { "prefix": { "customer_id": "abc" } }
      ]
    }
  }
}
```

---

## **5. Related Patterns**
To complement **Data Archival & Cold Storage**, consider:
1. **[Data Tiering](https://example.com/tiers-pattern)**
   - Explores multi-tiered storage strategies (hot/warm/cold) and migration tools.
2. **[Event Sourcing](https://example.com/event-sourcing-pattern)**
   - Use case for storing immutable event logs in cold storage for audit trails.
3. **[Data Masking](https://example.com/data-masking-pattern)**
   - Apply redaction to sensitive data in archived records before retrieval.
4. **[Batch Processing](https://example.com/batch-processing-pattern)**
   - Offload cold data analytics to batch jobs (e.g., Spark on warm storage).
5. **[Compliance-Driven Storage](https://example.com/compliance-storage-pattern)**
   - Enforce retention policies and access controls for regulated industries (e.g., HIPAA, GDPR).

---

## **6. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|-------------------------------------|----------------------------------------|------------------------------------------------------------------------------|
| Slow retrieval times                | Cold storage latency (e.g., Glacier).   | Pre-fetch data to warm storage or use expedited retrieval (extra cost).     |
| High storage costs                  | Over-retrieval of deep archive data.   | Review lifecycle policies; use cheaper tiers for older data.               |
| Metadata queries are slow           | No index on archived data.             | Rebuild metadata catalog with proper indexing (e.g., Elasticsearch).       |
| Compliance violations               | Data deleted before retention period.   | Enable WORM storage and set retention locks.                                |
| API throttling                      | Too many concurrent retrievals.        | Implement request limiting (e.g., token buckets) or batch requests.        |

---

## **7. Best Practices**
1. **Define Clear Retention Policies**:
   - Align with regulations (e.g., GDPR’s 7-year retention for personal data).
   - Example: *"All transaction logs older than 5 years move to cold storage; delete after 10 years."*
2. **Monitor Costs**:
   - Use cloud provider cost tools (e.g., AWS Cost Explorer) to track cold storage usage.
3. **Test Retrieval Times**:
   - Simulate retrieval scenarios to ensure SLA compliance (e.g., "95% of requests must complete in <2 hours").
4. **Document Retrieval Processes**:
   - Maintain runbooks for restoring critical data (e.g., disaster recovery playbooks).
5. **Hybrid Architectures**:
   - Combine cold storage with **data lakes** (e.g., Azure Data Lake + cold storage) for flexibility.

---
**References**:
- [AWS S3 Storage Classes](https://aws.amazon.com/s3/storage-classes/)
- [Azure Cold Storage](https://azure.microsoft.com/en-us/products/storage/blobs/#cold-storage)
- [GDPR Data Retention Guidelines](https://gdpr-info.eu/art-5-gdpr/)