---
# **[Pattern] Media Domain Patterns Reference Guide**

---

## **Overview**
**Media Domain Patterns** define reusable architectural principles for handling media objects (e.g., images, videos, audio) in distributed systems. This pattern standardizes how media is **stored, processed, accessed, and referenced** across services, ensuring scalability, versioning, and integrations with CDNs, transcoders, and analytics tools.

Key benefits:
- **Decoupled storage**: Separates media from application logic.
- **Versioning**: Supports branching/rollbacks (e.g., creative iterations).
- **Event-driven workflows**: Integrates with pipelines (e.g., OCR, auto-captions).
- **Security**: Granular permissions (e.g., public/private assets).
- **Interoperability**: Works with APIs like Digital Asset Management (DAM) or cloud storage (S3, Azure Blob).

Use cases:
- Marketing sites (product images, ads)
- E-learning platforms (video tutorials)
- Media publishing (galleries, news articles)
- IoT dashboards (sensor-generated media logs)

---

## **Core Concepts**

### **1. Media Object Model**
Each media item follows a **standardized schema** with metadata, lifecycle states, and references:

| **Field**               | **Type**               | **Description**                                                                 |
|-------------------------|------------------------|-------------------------------------------------------------------------------|
| `id`                    | UUID                   | Unique global identifier (e.g., `b1a8c3d4-...`).                              |
| `name`                  | String (max 255 chars) | Human-readable label (e.g., `"logo_2024.png"`).                               |
| `path`                  | String                 | Ephemeral storage path (e.g., `user_uploads/2024/01/logo_2024.png`).          |
| `storageLocation`       | Enum                  | Where the media is stored: `S3`, `Local`, `AzureBlob`, `Custom`.               |
| `url`                   | String (CDN-ready)     | Public URL (e.g., `https://cdn.example.com/assets/...`).                     |
| `contentType`           | String                 | MIME type (e.g., `image/png`, `video/mp4`).                                   |
| `size`                  | Integer (bytes)        | Raw file size (e.g., `2097152` for 2MB).                                      |
| `dimensions`            | Object                | Width/height for images (e.g., `{ width: 3000, height: 1500 }`).               |
| `metadata`              | Key-value pairs       | Custom tags (e.g., `{"author": "Alice", "keywords": ["marketing"]}`).          |
| `states`                | Array (Enum)          | Current lifecycle: `draft`, `published`, `archived`, `deleted`.                |
| `createdAt`             | ISO 8601 timestamp     | Creation time.                                                                 |
| `updatedAt`             | ISO 8601 timestamp     | Last modification.                                                           |
| `versions`              | Array (UUIDs)         | Linked to versioned copies (e.g., `[ "v1", "v2" ]`).                          |
| `dependencies`          | Array (UUIDs)         | Related assets (e.g., thumbnails, captions).                                  |
| `permissions`           | Policy object         | Access rules (e.g., `{ "view": ["role:editor"], "edit": ["owner"] }`).          |
| `processingPipeline`    | String                | Applied pipeline (e.g., `"ocr+transcode"`).                                   |
| `tags`                  | Array (strings)       | Categorization (e.g., `["product", "2024"]`).                                  |
| `expiryDate`            | ISO 8601 timestamp     | Auto-delete date (e.g., `2028-12-31`).                                          |

---
### **2. Reference Schema (JSON)**
```json
{
  "media": {
    "id": "b1a8c3d4-123e-4567-8901-abcdef123456",
    "name": "hero-banner",
    "path": "assets/hero-banner/original.mp4",
    "storageLocation": "S3",
    "url": "https://cdn.example.com/assets/hero-banner/original.mp4",
    "contentType": "video/mp4",
    "size": 52428800,
    "dimensions": { "width": 1920, "height": 1080 },
    "metadata": { "resolution": "4K", "duration": 60 },
    "states": ["draft", "published"],
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-01-20T14:30:00Z",
    "versions": ["b1a8c3d4-.../v1", "b1a8c3d4-.../v2"],
    "dependencies": ["thumbnail_1920x1080", "caption_srt"],
    "permissions": {
      "view": ["role:editor", "role:guest"],
      "edit": ["owner:user@example.com"]
    },
    "processingPipeline": "transcode-h264",
    "tags": ["marketing", "2024"],
    "expiryDate": null
  }
}
```

---
## **Implementation Details**
### **1. Storage Layers**
| **Layer**       | **Purpose**                                  | **Examples**                          | **Best Practices**                                  |
|-----------------|---------------------------------------------|---------------------------------------|-----------------------------------------------------|
| **Primary**     | Raw media storage                           | S3, Azure Blob, Cloud Storage       | Use regionally distributed buckets for low latency.   |
| **CDN**         | Cached, public-facing copies                | CloudFront, Fastly, Akamai           | Set TTL based on content type (e.g., 1 day for images).|
| **Processing**  | Temporary files during pipelines            | EFS, GCS                      | Auto-delete after 24h unless versioned.            |
| **Archive**     | Long-term storage                           | Glacier, Coldline                  | Enable lifecycle policies (e.g., 90-day access).     |
| **Metadata DB** | Indexes, permissions, references            | PostgreSQL, DynamoDB               | Partition by `contentType` for query efficiency.    |

---
### **2. Versioning**
- **Semantic Versioning**: Use `/v1`, `/v2` suffixes in paths (e.g., `original_v1.mp4`).
- **Atomic Rollbacks**: Versioned copies are immutable; revert by updating the `id` reference.
- **Change Tracking**:
  ```json
  {
    "versions": [
      {
        "id": "b1a8c3d4-v1",
        "createdAt": "2024-01-15T10:00:00Z",
        "changes": ["added: watermark"],
        "author": "user@example.com"
      }
    ]
  }
  ```

---
### **3. Processing Pipelines**
Define pipelines as **DAGs (Directed Acyclic Graphs)** of steps:
```yaml
# Example: Video Transcoding Pipeline
- name: "resize"
  action: "ffmpeg"
  args: ["-vf", "scale=1280:720"]
- name: "compress"
  action: "ffmpeg"
  args: ["-crf", "23"]
- name: "add-captions"
  action: "burn-srt"
  args: ["captions.srt"]
```
**Triggering**:
- Manual (API calls)
- Event-based (e.g., file upload → `processing-started` event)
- Scheduled (e.g., daily thumbnails)

---
### **4. Security**
| **Rule**               | **Implementation**                                                                 |
|------------------------|-----------------------------------------------------------------------------------|
| **Access Control**     | Use IAM policies or JWT with `permissions` field.                                  |
| **Encryption**         | Encrypt at rest (S3 SSE-KMS) and in transit (TLS 1.2+).                           |
| **Public vs. Private** | Prefix URLs with `public/` or `private/` (e.g., `https://cdn.example.com/public/...`). |
| **Audit Logs**         | Track `modifiedAt` and `metadata.author` for compliance.                          |

---
## **Query Examples**
### **1. Fetch Media by ID**
```http
GET /api/media/b1a8c3d4-123e-4567-8901-abcdef123456
Headers:
  Authorization: Bearer <JWT>
Response:
{
  "media": { ... }  // Full object from schema
}
```

### **2. List Media by Tags**
```http
GET /api/media?tags=marketing
Response:
{
  "items": [
    { "id": "b1a8c3d4-...", "name": "banner_1", "tags": ["marketing"] },
    { "id": "a2b3c4d5-...", "name": "video_1", "tags": ["marketing", "promo"] }
  ],
  "count": 2
}
```

### **3. Search with Filters**
```http
GET /api/media?
  contentType=image%2Fpng
  &size%3E=1048576
  &tags=product
  &states=%5B%22published%22%5D
Headers:
  Authorization: Bearer <JWT>
Response:
{
  "items": [
    {
      "id": "a2b3c4d5-...",
      "name": "product_thumb",
      "contentType": "image/png",
      "size": 1048576,
      "tags": ["product"]
    }
  ]
}
```

### **4. Create a New Media Object**
```http
POST /api/media
Headers:
  Content-Type: application/json
  Authorization: Bearer <JWT>
Body:
{
  "name": "new-logo",
  "contentType": "image/svg+xml",
  "metadata": { "designer": "Bob" },
  "tags": ["logo"]
}
Response:
{
  "id": "a2b3c4d5-123e-4567-8901-abcdef123456",
  "url": "https://cdn.example.com/temp/a2b3c4d5-..."
}
```
**Note**: The initial `url` is temporary; finalize with `PATCH /api/media/{id}`.

### **5. Update Permissions**
```http
PATCH /api/media/b1a8c3d4-123e-4567-8901-abcdef123456
Headers:
  Authorization: Bearer <JWT>
Body:
{
  "permissions": {
    "view": ["role:guest"],
    "edit": []
  }
}
Response: 200 OK
```

### **6. Trigger Processing Pipeline**
```http
POST /api/media/b1a8c3d4-123e-4567-8901-abcdef123456/process
Headers:
  Authorization: Bearer <JWT>
Body:
{
  "pipeline": "transcode-h264",
  "steps": ["resize", "compress"]
}
Response:
{
  "status": "queued",
  "processingId": "proc_789abc..."
}
```

---
## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|--------------------------------------------------------------------------------|
| **Uncontrolled growth**               | Enforce size limits (e.g., 50MB max) and use archival storage.                |
| **Versioning bloat**                  | Prune old versions with TTL policies (e.g., keep only 3 versions).            |
| **CDN cache stale data**              | Invalidate URLs on updates or use low TTL (e.g., 1 hour).                    |
| **Metadata inconsistency**            | Use database transactions for `updatedAt` and `states` changes.                |
| **Race conditions in pipelines**      | Idempotent designs (e.g., retry failed steps).                                |
| **Overly complex permissions**        | Start with RBAC; refine with attribute-based policies (ABAC) later.          |

---
## **Related Patterns**
| **Pattern**                     | **Connection to Media Domain**                                                                 | **When to Use**                                  |
|----------------------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Event Sourcing**               | Track media lifecycle as immutable events (e.g., `version_created`, `permissions_updated`).   | Audit trails, compliance.                        |
| **CQRS**                         | Separate read (CDN) and write (DB) paths for high traffic.                                    | High-scale media galleries.                       |
| **Saga Pattern**                 | Orchestrate cross-service workflows (e.g., media + analytics).                               | Complex pipelines (e.g., video + captions + OCR).|
| **Microservices for Media**      | Decouple processing (transcode) from storage (S3).                                            | Isolated teams; scalable components.             |
| **Cache-Aside**                  | Cache frequently accessed media URLs (e.g., Redis) to reduce DB load.                         | High-read scenarios (e.g., product images).      |
| **Service Mesh**                 | Manage auth/retries for media ingestion (e.g., Istio).                                         | Hybrid cloud or multi-region setups.             |
| **API Gateway**                  | Route media requests (e.g., `/api/v1/media/{id}`) with rate limiting.                        | Public-facing media APIs.                        |

---
## **Tools & Libraries**
| **Category**               | **Tools**                                                                                     | **Notes**                                  |
|----------------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------|
| **Storage**                | AWS S3, Azure Blob, Google Cloud Storage, MinIO                                            | Choose based on regional compliance.      |
| **CDN**                    | CloudFront, Fastly, BunnyCDN, Varnish                                                     | Test cold-start performance.               |
| **Processing**             | FFmpeg, FFprobe, AWS Elemental MediaConvert, Mux                                            | Support for formats (e.g., HLS, DASH).     |
| **Databases**              | PostgreSQL (PostgREST), DynamoDB, MongoDB                                                   | Index `tags` and `contentType` for queries.|
| **Event Platforms**        | Kafka, RabbitMQ, AWS SNS/SQS                                                                  | Choose based on latency needs.              |
| **API Frameworks**         | FastAPI, Express.js, Spring Boot (Spring WebFlux)                                            | Async endpoints for media processing.       |
| **Auth**                   | Auth0, Cognito, Keycloak, Firecracker (e.g., for JWT)                                       | Integrate with `permissions` field.         |

---
## **Best Practices**
1. **Standardize Naming**: Use `snake_case` for paths (e.g., `user_uploads/2024/01/logo_2024.png`).
2. **Compress Early**: Apply lossless compression (e.g., WebP for images) at ingest.
3. **Monitor Pipelines**: Track step failures (e.g., "transcode failed: codec unsupported").
4. **Backup Metadata**: Regularly export DB dumps (e.g., weekly).
5. **Document Formats**: Publish schema validation tools (e.g., OpenAPI for APIs, JSON Schema for metadata).
6. **Cost Optimization**:
   - Use S3 Intelligent Tiering for unpredictable access.
   - Delete temp files after 48h (unless versioned).
7. **Access Logs**: Enable S3/DB access logging for security audits.
8. **Disaster Recovery**: Replicate critical buckets across regions.

---
## **Example Workflow**
**Scenario**: Upload a video, generate thumbnails, and publish.
1. **Client** uploads `video.mp4` to `/api/media` → returns `url: "https://cdn.example.com/temp/..."`.
2. **Server** triggers pipeline:
   ```json
   { "pipeline": "transcode+thumbnails", "steps": ["resize", "h264", "generate-thumbs"] }
   ```
3. **Event Bus** emits:
   - `processing-started` (video.mp4)
   - `thumbnail-generated` (video_thumb_1920x1080.png)
4. **CDN** invalidates old thumbnails.
5. **Client** updates permissions via `PATCH /api/media/{id}` → `states: ["published"]`.
6. **Client** fetches published media via `GET /api/media?states=published`.

---
## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                  |
|-------------------------------------|--------------------------------------------------------------------------------|-----------------------------------------------|
| **403 Forbidden**                   | Missing `permissions.view` in JWT.                                             | Check IAM roles or API keys.                  |
| **Slow thumbnails**                 | Pipeline stuck on FFmpeg.                                                     | Monitor `processingId` in DB; retry failed steps.|
| **CDN stale images**                | TTL too high or cache invalidation failed.                                     | Set TTL=1h or use `Purge` endpoint.           |
| **Database bloat**                  | Too many versions retained.                                                     | Implement version cleanup cron job.          |
| **High storage costs**              | Unoptimized formats (e.g., unencoded MP4).                                    | Use FFmpeg to set `-crf 23` and `-preset medium`.|

---
## **Further Reading**
- [AWS Media Services Guide](https://aws.amazon.com/media/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [CDN Best Practices (Cloudflare)](https://developers.cloudflare.com/cdn/)
- [Event-Driven Architectures (Martin Fowler)](https://martinfowler.com/articles/201701/event-driven.html)