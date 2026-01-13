# **[Pattern] Social-Media Domain Patterns – Reference Guide**

---

## **1. Overview**
Social-Media Domain Patterns define standardized structures, interactions, and best practices for modeling and managing user-generated content (UGC), engagement, and networking in digital ecosystems. This reference provides a **schema-based framework** for designing scalable, interoperable systems—ensuring consistency in APIs, data models, and workflows across platforms like forums, chat apps, or influencer networks.

Key use cases include:
- Structuring **posts, comments, reactions, and shares** with metadata (e.g., timestamps, moderation flags).
- Enabling **real-time updates** via event-driven architectures (e.g., WebSockets).
- Integrating **cross-platform data** (e.g., migrating from Twitter to a proprietary network).

**Core principles**:
- **Atomicity**: Break interactions into discrete, composable elements (e.g., `Post` → `Body`, `Author`, `Attachments`).
- **Idempotency**: Design queries to avoid unintended side effects (e.g., retries after API failures).
- **Extensibility**: Use object-relational mappings (ORMs) or GraphQL for flexible schema updates.

---

## **2. Schema Reference**

| **Component**          | **Type**       | **Description**                                                                                     | **Fields**                                                                                     | **Example Value**                          |
|------------------------|----------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------|
| **User**               | Object         | Core user profile                                                                                   | `id`, `username`, `email`, `displayName`, `profilePictureUrl`, `joinedAt`, `isVerified`    | `{ "id": "u123", "username": "@jdoe" }`     |
| **Post**               | Object         | User-generated content                                                                              | `id`, `userId`, `content`, `mediaUrls`, `createdAt`, `lastModifiedAt`, `likesCount`, `sharesCount` | `{ "id": "p456", "content": "Hello!" }` |
| **Comment**            | Object         | Reply to a post or comment                                                                            | `id`, `postId`, `userId`, `content`, `parentCommentId`, `createdAt`, `isDeleted`           | `{ "id": "c789", "postId": "p456" }`       |
| **Reaction**           | Object         | Emoji-based interaction (e.g., 👍, ❤️)                                                                   | `id`, `postId`, `userId`, `emoji`, `createdAt`                                              | `{ "postId": "p456", "emoji": "🔥" }`      |
| **Share**              | Object         | Content redistribution                                                                               | `id`, `postId`, `userId`, `sharedPostId`, `createdAt`, `platform`                          | `{ "postId": "p456", "platform": "Instagram" }` |
| **DirectMessage**      | Object         | Private 1:1 or group chat                                                                             | `id`, `senderId`, `recipientIds`, `content`, `status` (e.g., `sent`, `delivered`, `read`)    | `{ "status": "delivered" }`                 |
| **ModerationFlag**     | Object         | Reported or flagged content                                                                         | `id`, `postId`, `reason` (e.g., `spam`, `hateSpeech`), `reporterId`, `status` (e.g., `pending`, `resolved`) | `{ "reason": "hateSpeech" }` |

---
**Relationships**:
- A `Post` **has many** `Comments` and `Reactions`.
- A `User` **owns** `Posts`, `Comments`, and `DirectMessages`.
- `Shares` reference **both** the original (`postId`) and shared (`sharedPostId`) content.

---

## **3. Query Examples**

### **A. CRUD Operations**
#### **1. Create a Post**
**Request**:
```http
POST /api/posts
Content-Type: application/json

{
  "userId": "u123",
  "content": "Launching a new feature next week!",
  "mediaUrls": ["https://example.com/image.jpg"]
}
```
**Response**:
```json
{
  "id": "p789",
  "userId": "u123",
  "createdAt": "2023-10-01T12:00:00Z"
}
```

#### **2. Get a Post with Comments**
**Request**:
```http
GET /api/posts/p789?include=comments
```
**Response**:
```json
{
  "id": "p789",
  "content": "Launching...",
  "comments": [
    {
      "id": "c1011",
      "content": "Wow!",
      "userId": "u456"
    }
  ]
}
```

#### **3. Add a Reaction**
**Request**:
```http
POST /api/posts/p789/reactions
Content-Type: application/json

{ "emoji": "❤️" }
```
**Response**:
```json
{
  "id": "r1213",
  "userId": "u123",
  "emoji": "❤️",
  "createdAt": "2023-10-01T12:05:00Z"
}
```

---
### **B. Event-Driven Updates**
**WebSocket Subscription** (for real-time reactions):
```http
SUBSCRIBE /api/posts/p789/reactions
```
**Event Payload** (emitted on new reaction):
```json
{
  "event": "reaction_added",
  "data": {
    "postId": "p789",
    "userId": "u789",
    "emoji": "🔥",
    "timestamp": "2023-10-01T12:07:00Z"
  }
}
```

---
### **C. Aggregations**
**Fetch Trending Posts (Top 5 by Likes)**:
```http
GET /api/posts?sort=likesCount&limit=5
```
**Response**:
```json
[
  { "id": "p789", "likesCount": 42 },
  { "id": "p1012", "likesCount": 37 }
]
```

---
## **4. Best Practices**
| **Category**          | **Recommendation**                                                                                     | **Why**                                                                                             |
|-----------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Idempotency**       | Use `idempotency-key` headers for mutations (e.g., POST/PUT).                                         | Prevent duplicate reactions/shares if retries occur.                                               |
| **Pagination**        | Implement cursor-based pagination (e.g., `nextCursor`) instead of offset.                             | Efficient for large datasets (avoids `LIMIT/OFFSET` performance issues).                           |
| **Rate Limiting**     | Enforce per-user limits (e.g., 100 reactions/minute) via API gateways.                               | Mitigate abuse (e.g., fake engagement).                                                            |
| **Data Validation**   | Validate inputs client-side and server-side (e.g., `content` length < 1000 chars).                  | Ensure consistency and security.                                                                  |
| **Audit Logs**        | Log moderation actions (e.g., `ModerationFlag` updates) to `/api/logs`.                              | Compliance and debugging.                                                                          |

---
## **5. Common Pitfalls & Mitigations**

| **Pitfall**                          | **Risk**                                                                 | **Solution**                                                                                     |
|---------------------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **N+1 Queries**                       | Performance degradation when fetching related data (e.g., `Post` + all `Comments`). | Use **batch fetching** (e.g., `include=user,comments` in GraphQL) or **DQL** (e.g., `JOIN` in SQL). |
| **Over-Posting**                      | Uncontrolled API calls (e.g., spammers creating 1000 posts).            | Rate-limit by `userId` + implement **CAPTCHA** for new accounts.                                |
| **Race Conditions**                   | Concurrent reactions causing duplicate entries.                         | Use **database transactions** or **optimistic locking** (e.g., `Version` field).                 |
| **Data Leakage**                      | Sensitive user data (e.g., `email`) exposed in public APIs.              | Mask PII in non-admin endpoints (e.g., return only `username` in `User` objects).                |
| **Schema Drift**                      | Incompatible changes (e.g., adding `isPin` to `Post` without backward compatibility). | Adopt **semantic versioning** (e.g., `Post_v2`) or **optional fields**.                          |

---

## **6. Related Patterns**
| **Pattern Name**               | **Description**                                                                                     | **When to Use**                                                                                  |
|---------------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **[Event-Driven Architecture]**  | Decouple components via pub/sub (e.g., Kafka, WebSockets) for real-time updates.                  | Social interactions (e.g., live reactions, DMs).                                               |
| **[GraphQL for Social Data]**    | Query-specific fields/relations to reduce over-fetching.                                             | Frontends needing flexible data shapes (e.g., mobile apps).                                     |
| **[Content Moderation Pipeline]**| Automate flagging (e.g., ML + keyword filters) + manual review.                                    | High-volume platforms (e.g., YouTube comments).                                                 |
| **[Gossip Protocols]**          | Peer-to-peer content discovery (e.g., "Your friends liked this").                                   | Offline-first apps or decentralized social networks.                                            |
| **[API Versioning]**             | Separate endpoints for breaking changes (e.g., `/v1/posts`, `/v2/posts`).                           | Long-lived APIs requiring schema evolution.                                                     |

---
## **7. Example Workflow: Post Creation**
1. **Client** sends `POST /api/posts` with `userId`, `content`, and `mediaUrls`.
2. **Server**:
   - Validates input (length, attachments).
   - Generates `Post` record + `DirectMessage` to `userId` (e.g., "Your post was published!").
   - Triggers `post_created` event for WebSocket subscribers.
3. **Moderation**:
   - Checks `content` against a spam keywords list.
   - If flagged, creates `ModerationFlag` with `status: pending`.
4. **Frontend**:
   - Fetches updated `Post` via `GET /api/posts/{id}?include=reactions`.
   - Displays real-time reactions via WebSocket.

---
**Tools to Consider**:
- **ORM**: Sequelize, Prisma (for schema enforcement).
- **Event Bus**: Apache Kafka, AWS SNS.
- **Search**: Elasticsearch (for post/comment indexing).
- **Auth**: OAuth 2.0 + JWT for API security.