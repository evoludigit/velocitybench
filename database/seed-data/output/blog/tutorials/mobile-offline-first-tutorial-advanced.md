```markdown
---
title: "Offline-First Patterns: Building Resilient APIs for the Unreliable Web"
date: "2023-11-15"
author: "Alex Thompson"
tags: ["backend", "database", "api-design", "offline-first", "resilience"]
description: "Learn how to design APIs and backend systems that work reliably in connectivity-challenged environments—with practical patterns, tradeoffs, and code examples."
---

# **Offline-First Patterns: Building Resilient APIs for the Unreliable Web**

In today’s connected world, users expect apps to work—even when the internet doesn’t. Whether it’s a field technician in a remote location, a passenger on a plane, or a user with patchy cellular coverage, offline resilience is no longer a nice-to-have; it’s an expectation. Yet, most APIs are designed with a *connected-first* mindset, failing spectacularly when connectivity drops.

As a backend engineer, you’re often tasked with enabling offline functionality—not just for frontends (with PWA or service workers), but for the entire system. This means designing APIs, databases, and synchronization logic that work reliably in *three distinct modes*:
1. **Online-only** (full connectivity)
2. **Partial connectivity** (intermittent or slow)
3. **Offline** (no connectivity at all)

This post explores **offline-first design patterns** for backend systems, focusing on practical tradeoffs, database strategies, and API patterns that balance reliability with performance. We’ll dive into real-world implementations using PostgreSQL, Redis, and GraphQL, with clear code examples.

---

## **The Problem: Why Offline-First is Harder Than It Seems**

Offline-first systems face three core challenges:

### 1. **State Synchronization is Complex**
   - When a user works offline, their changes must be stored locally and later reconciled with the server. This introduces:
     - **Conflict resolution** (e.g., who wins if two users edit the same record?)
     - **Version tracking** (how do we know if a cached record is stale?)
     - **Delta sync** (only syncing changed data to save bandwidth)

   Example: A sales app where offline notes on a lead must merge with server data without overwriting critical fields.

### 2. **Database Schema Mismatches**
   - Offline databases (like SQLite or IndexedDB) often use simpler schemas than server databases (PostgreSQL, MongoDB). Migrating between them requires:
     - **Schema translation** (e.g., converting a rich JSON field in the backend to a flat table in the frontend)
     - **Partial writes** (saving a subset of fields offline, then syncing later)
   - Example: A backend might store `user_profile` as a JSONB column, but an offline app needs a flattened schema for faster local queries.

### 3. **API Design Fails Under Stress**
   - Traditional REST APIs assume latency is zero and bandwidth is infinite. Offline-first APIs must:
     - Support **batch operations** (async updates that queue instead of failing)
     - Handle **idempotency** (replaying updates safely after reconnecting)
     - Provide **status polling** (how does the client know if changes were synced?)

   Example: A mobile app’s "Save Draft" button should work even if the API is down, but later reconcile with server state without losing data.

### 4. **Performance vs. Consistency Tradeoffs**
   - Offline systems often sacrifice **strong consistency** for **availability**. You’ll need to choose:
     - **Eventual consistency** (accept temporary stale data)
     - **Conflict-free replicated data types (CRDTs)** (for collaborative editing)
     - **Manual resolution** (let users merge changes later)

   Example: A collaborative whiteboard app where two offline users draw on the same canvas—how do you merge their strokes without losing work?

---

## **The Solution: Offline-First Patterns**

To build resilient systems, we’ll use a combination of **database patterns**, **API strategies**, and **synchronization techniques**. Here’s the high-level architecture we’ll implement:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│             │     │             │     │                 │
│  Client     ├──┐   │  Offline   ├──┐   │  Server         │
│  (PWA/Web)   │ │   │  Database  │ │   │  (PostgreSQL)   │
└─────────────┘ │ └─────────────┘ │   └─────────────────┘
                 │                 │
                 ▼                 ▼
┌───────────────────────────────────────────────────┐
│               Synchronization Layer               │
│  (Queue, Conflict Resolution, Delta Sync)         │
└───────────────────────────────────────────────────┘
```

Key components:
1. **Offline Datastore**: SQLite, LevelDB, or IndexedDB (for local persistence).
2. **Conflict Resolution**: Operational Transform (OT) or CRDTs for collaborate editing.
3. **Sync Protocol**: Optimistic updates with version vectors or timestamps.
4. **API Design**: Idempotent endpoints with status tracking.
5. **Queueing System**: Redis or Kafka for deferred operations.

---

## **Components/Solutions**

### 1. **Offline Database Design**
Offline databases must support:
- Fast CRUD operations (no heavy joins).
- Conflict detection (e.g., `last_updated_at` or vector clocks).
- Partial writes (save only changed fields).

#### **Example: SQLite Schema for Offline Notes**
```sql
-- Server database (PostgreSQL)
CREATE TABLE server_notes (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    user_id INT REFERENCES users(id),
    last_updated_at TIMESTAMP,
    version INT  -- For conflict resolution
);

-- Offline database (SQLite)
CREATE TABLE offline_notes (
    id INTEGER PRIMARY KEY,
    content TEXT,
    user_id INTEGER,
    last_updated_at TIMESTAMP,
    version INTEGER,
    is_conflicted BOOLEAN DEFAULT FALSE,
    conflict_resolution TEXT  -- JSON: {"server": "...", "local": "..."}
);
```
**Tradeoff**: SQLite lacks transactions and JSON support natively, so we simplify schemas.

---

### 2. **Conflict Resolution: Version Vectors**
Use **version vectors** or **last-write-wins (LWW)** with timestamps to detect conflicts.

#### **Example: Updating a Note with Conflict Detection**
```javascript
// Pseudocode for offline update
async function saveNoteLocally(note) {
    const existing = await db.get(`offline_notes`, { id: note.id });

    if (!existing) {
        // New note: Save as-is
        await db.put(`offline_notes`, { ...note, version: 1 });
    } else if (existing.version === note.version) {
        // No conflict: Update
        await db.put(`offline_notes`, { ...note, last_updated_at: new Date() });
    } else {
        // Conflict: Mark and store both versions
        await db.put(`offline_notes`, {
            ...note,
            is_conflicted: true,
            conflict_resolution: JSON.stringify({
                local: note,
                server: existing
            }),
            version: Math.max(existing.version, note.version) + 1
        });
    }
}
```

**Tradeoff**: Version vectors add overhead. For simple apps, LWW with timestamps may suffice.

---

### 3. **Delta Sync: Only Sync Changed Data**
Instead of transferring entire records, sync only:
- Changed fields (`delta`).
- Metadata (`last_updated_at`, `version`).

#### **Example: GraphQL API for Delta Sync**
```graphql
# Request: Fetch changes since last sync
query NoteUpdates($syncToken: String!) {
    notes(since: $syncToken) {
        id
        content
        last_updated_at
        version
    }
}

# Response: Only returns modified notes
{
    "data": {
        "notes": [
            { "id": 1, "content": "Updated offline...", "last_updated_at": "2023-11-15T12:00:00Z" }
        ]
    }
}
```

**Server-side implementation (PostgreSQL)**:
```sql
-- Only return rows updated after syncToken
SELECT id, content, last_updated_at, version
FROM server_notes
WHERE last_updated_at > (SELECT last_updated_at FROM sync_tokens WHERE user_id = $userId)
ORDER BY last_updated_at;
```

**Tradeoff**: Requires client-side tracking of `last_updated_at`. Complexity increases with collaborative edits.

---

### 4. **Idempotent API Endpoints**
Offline-first APIs must handle retryable operations safely. Use:
- **Idempotency keys** (unique per operation).
- **Retry-after headers** (for rate-limiting).

#### **Example: Idempotent POST Endpoint (Fastify)**
```javascript
// Fastify route with idempotency
app.post('/notes', { idempotency: true }, async (req, reply) => {
    const { idempotencyKey } = req.headers;
    const existing = await db.get('idempotency_keys', idempotencyKey);

    if (existing) {
        return reply.status(200).json(existing.response);
    }

    // Process request
    const note = await createNote(req.body);
    await db.put('idempotency_keys', {
        idempotencyKey,
        response: note,
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24h
    });

    reply.status(201).json(note);
});
```

**Tradeoff**: Idempotency keys add storage overhead. Use Redis for short-lived keys.

---

### 5. **Queueing System for Offline Operations**
When offline, queue updates and sync when back online. Use Redis Streams or Kafka.

#### **Example: Queueing Updates with Redis**
```javascript
// Client-side: Queue an update
async function queueUpdate(update) {
    const queueKey = `user:${userId}:updates`;
    await redis.xAdd(queueKey, '*', update);
}

// Server-side: Process queue
async function processQueue() {
    const queueKey = `user:${userId}:updates`;
    const messages = await redis.xRead({ KEYS: [queueKey], COUNT: 10 });

    for (const msg of messages) {
        await applyUpdate(msg.message);
    }
}
```

**Tradeoff**: Queues add latency. Prioritize critical updates (e.g., payments > notes).

---

## **Implementation Guide**

### Step 1: Design the Offline Schema
- Start with a **simplified schema** (e.g., no joins, flat fields).
- Add **conflict fields** (`is_conflicted`, `conflict_resolution`).
- Use **timestamps** for LWW or **version vectors** for advanced sync.

### Step 2: Implement Delta Sync
- Track `last_updated_at` on all records.
- Use GraphQL or REST with `since:`/`until:` parameters.
- Example:
  ```graphql
  query NotesSince($since: DateTime!) {
      notes(since: $since) {
          id
          content
      }
  }
  ```

### Step 3: Add Conflict Resolution
- For simple apps: Use `last_updated_at` + LWW.
- For collaborative apps: Implement Operational Transform (OT) or CRDTs.
- Example OT for a text editor:
  ```javascript
  function applyOp(op) {
      // Transform local state based on server's last op
      return transform(localState, op, serverLastOp);
  }
  ```

### Step 4: Build Idempotent APIs
- Add `idempotency-key` header to all writes.
- Store responses in Redis with TTL.
- Example Fastify plugin:
  ```javascript
  const idempotencyPlugin = (app) => {
      app.addHook('onRequest', async (req, reply) => {
          const key = req.headers['idempotency-key'];
          if (key) {
              const cached = await redis.get(key);
              if (cached) return reply.status(200).send(JSON.parse(cached));
          }
      });

      app.addHook('onSend', async (req, reply, payload) => {
          const key = req.headers['idempotency-key'];
          if (key) await redis.setex(key, 86400, JSON.stringify(payload));
      });
  };
  ```

### Step 5: Handle Reconnection
- When online, sync changes **atomically**:
  1. Fetch server state (`notes?since=<last_sync>`).
  2. Apply local changes to server.
  3. Merge conflicts manually or via CRDTs.
  4. Update `last_updated_at`.

### Step 6: Test Offline Scenarios
- Simulate **network drops** (use `nohup` + `curl --fail`).
- Test **conflict scenarios** (edit offline, then reconnect).
- Example script to test offline sync:
  ```bash
  # Simulate offline mode
  curl --fail http://localhost:3000/notes -d '{"content": "Offline note"}'

  # Reconnect and sync
  curl http://localhost:3000/notes/sync
  ```

---

## **Common Mistakes to Avoid**

1. **Ignoring Conflict Resolution**
   - *Problem*: Assuming "last write wins" is always correct.
   - *Fix*: Design conflict merges early (e.g., "last update wins" for notes, but "manual resolve" for critical data).

2. **Not Tracking Delta Changes**
   - *Problem*: Syncing entire records wastes bandwidth.
   - *Fix*: Use `last_updated_at` or version vectors to sync only deltas.

3. **Overcomplicating the Offline Schema**
   - *Problem*: Trying to mirror the server schema in SQLite.
   - *Fix*: Keep offline schemas flat and simple. Sync richness when online.

4. **Failing to Handle Retries Gracefully**
   - *Problem*: API rejects all offline requests on retry.
   - *Fix*: Use queues (Redis/Kafka) and idempotency keys.

5. **No Backoff for Slow Networks**
   - *Problem*: Clients spam the server when reconnecting.
   - *Fix*: Implement exponential backoff in sync logic.

6. **Assuming All Data is Equal**
   - *Problem*: Treating a draft note the same as a payment.
   - *Fix*: Prioritize critical data (e.g., payments) over optional data (e.g., preferences).

---

## **Key Takeaways**

- **Offline-first requires tradeoffs**: Balance consistency, performance, and user experience.
- **Schema matters**: Offline databases need simpler schemas than server databases.
- **Conflict resolution is non-negotiable**: Plan for it early (LWW, OT, or CRDTs).
- **Delta sync saves bandwidth**: Track `last_updated_at` or versions to sync only changes.
- **Idempotency is essential**: Ensure APIs work safely on retry.
- **Queue offline updates**: Use Redis/Kafka to batch and sync later.
- **Test offline scenarios**: Simulate network issues early in development.

---

## **Conclusion**

Offline-first design isn’t just about making apps work without internet—it’s about building systems that **adapt to unreliable connectivity** while keeping data consistent and user experience smooth. The patterns we’ve covered (delta sync, conflict resolution, idempotent APIs, and queuing) provide a robust foundation, but the key is to **start simple and iterate**.

Start with **last-write-wins for simple data**, then add ** Operational Transform for collaborative editing**, and finally **CRDTs for highly concurrent scenarios**. Always test with **network throttling** and **offline modes** to catch edge cases early.

By designing for offline resilience upfront, you’ll create APIs that work *wherever the user goes*—not just where the internet does.

---
**Further Reading**:
- [CouchDB’s Conflict Resolution Guide](https://docs.couchdb.org/en/stable/couchapp/conflicts.html)
- [Operational Transformation (OT) Paper](https://www.-iggi.de/papers/ot-survey.pdf)
- [Protocol Buffers for Delta Sync](https://developers.google.com/protocol-buffers/docs/proto3#json)
- [Redis Streams for Queuing](https://redis.io/topics/streams-intro)
```