---

# **[Pattern] Offline-First Reference Guide**

---

## **Overview**
The **Offline-First** pattern prioritizes user experience (UX) by ensuring core functionality remains available even when connectivity is unreliable or absent. This approach involves caching critical data, synchronizing changes asynchronously, and providing seamless transitions between offline and online modes.

Unlike traditional progressive enhancement models, Offline-First assumes connectivity failures are common and designs systems to handle them proactively. Key use cases include **mobile apps, field applications, and geographies with poor network reliability** (e.g., rural areas or remote work). This pattern is particularly valuable for **mission-critical workflows** (e.g., healthcare, logistics) where downtime cannot be tolerated.

Implementing Offline-First requires balancing **data consistency** (conflict resolution) with **user perceived performance** (minimizing sync waits). It combines techniques like **local storage optimizations, differential sync, and versioning** to maintain data integrity across devices.

---

## **Schema Reference**

| **Component**               | **Description**                                                                                     | **Key Considerations**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Cache Layer**             | Stores data locally (e.g., SQLite, IndexedDB, LevelDB).                                              | - Selective caching (prioritize high-value data).                                                       |
|                             |                                                                                                     | - Cache invalidation/TTL policies to prevent stale data.                                                |
| **Sync Engine**             | Handles conflict resolution (e.g., last-write-wins, custom rules).                                | - Conflict resolution must be deterministic (avoid ambiguity).                                           |
|                             |                                                                                                     | - Batch sync for efficiency (reduce network overhead).                                                  |
| **Local Database**          | Embedded or client-side database (e.g., Realm, PouchDB).                                              | - Schema design for offline queries (denormalize or use M2M relations).                                   |
| **Offline UI**              | Display cached/submitted data without connectivity.                                                   | - Clear feedback (e.g., "Offline Mode," sync indicators).                                               |
| **Sync Metadata**           | Track changes (e.g., createdAt, modifiedAt, syncStatus).                                             | - Versioning or sequence numbers for incremental syncs.                                                 |
| **Data Partitioning**       | Segment data into "critical" vs. "nice-to-have" (e.g., user profiles vs. analytics).                | - Critical data must sync first; non-critical can wait.                                                 |
| **Connection State Handler**| Detects online/offline status and triggers actions (e.g., auto-retry, queue sync).                     | - Handle flaky networks (e.g., exponential backoff).                                                   |
| **Delta Sync**              | Only sync changes since last sync (reduces payload size).                                             | - Requires versioning or timestamps.                                                                    |
| **Progressive Sync**        | Sync in the background without blocking UI (e.g., Web Workers).                                      | - User must opt-in to avoid bandwidth overuse.                                                           |

---

## **Implementation Details**

### **1. Cache Strategy**
- **Selective Caching**: Cache only data required for core workflows. Example: In a task-management app, cache tasks but not user analytics.
  ```javascript
  // Pseudocode: Cache only "active" tasks
  if (task.status === "active") {
    db.put("tasks", task);
  }
  ```
- **Cache Invalidation**:
  - **Time-based TTL**: Delete cached data after 24 hours (e.g., news articles).
  - **Explicit Invalidation**: Clear cache when data is updated server-side (e.g., via API `purgeCache` endpoint).

### **2. Conflict Resolution**
**Last-Write-Wins (LWW)**: Default for most CRUD operations. Use metadata like `syncTimestamp` to determine winners.
```sql
-- Example SQL for LWW conflict resolution
UPDATE tasks
SET syncStatus = 'resolved'
WHERE id = ?
  AND syncTimestamp < (SELECT MAX(syncTimestamp) FROM tasks WHERE id = ?);
```

**Custom Rules**:
- For medical records, prioritize **physician updates** over patient self-updates.
- Use a `priority` field to override defaults:
  ```json
  {
    "id": 123,
    "conflictResolution": {
      "strategy": "custom",
      "rules": [
        { "field": "status", "winner": "server" },
        { "field": "notes", "winner": "clientIfNewerThan": 10 }
      ]
    }
  }
  ```

### **3. Sync Patterns**
| **Pattern**               | **Use Case**                          | **Implementation Notes**                                                                               |
|---------------------------|---------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Delta Sync**            | Large datasets (e.g., CRM records).   | Track `lastSyncTime` in metadata; only sync changes since then.                                         |
| **Batch Sync**            | High-frequency updates (e.g., IoT).   | Group changes into batches (e.g., every 10 mins) to reduce payload size.                                |
| **Priority Sync**         | Critical updates (e.g., alerts).      | Sync alerts first; queue others. Use a `syncPriority` field.                                          |
| **Conditional Sync**      | Offline edits (e.g., form submissions). | Sync only if the client-side version is "dirty" (has changes).                                        |

### **4. Offline UI/UX**
- **Visual Indicators**:
  - Add a "Sync in Progress" loading spinner.
  - Highlight unsynced changes with a badge (e.g., "2 updates pending").
- **Fallback Behavior**:
  - Allow offline data entry with a "sync later" option.
  - Provide a "Download Now" button for critical data (e.g., medical records).

### **5. Connection Handling**
- **Detect Offline State**:
  - Use `navigator.onLine` (web) or `ConnectivityManager` (mobile).
  - Example (JavaScript):
    ```javascript
    window.addEventListener('offline', () => {
      localStorage.setItem('offlineMode', 'true');
      queueSync(); // Trigger background sync
    });
    ```
- **Retry Logic**:
  - Exponential backoff for sync failures:
    ```javascript
    let retryCount = 0;
    async function syncWithRetry() {
      try {
        await syncData();
      } catch (error) {
        if (retryCount < 3) {
          await new Promise(resolve => setTimeout(resolve, 1000 * 2 ** retryCount));
          retryCount++;
          syncWithRetry();
        } else {
          logError("Sync failed after retries");
        }
      }
    }
    ```

### **6. Data Partitioning**
- **Critical vs. Non-Critical Data**:
  - **Critical**: User profiles, task lists, invoices.
  - **Non-Critical**: Analytics, cacheable assets (images).
- **Example Schema**:
  ```sql
  CREATE TABLE data_partitions (
    id TEXT PRIMARY KEY,
    partition_type TEXT CHECK (partition_type IN ('critical', 'non_critical')),
    data JSON
  );
  ```

---

## **Query Examples**

### **1. Retrieve Cached Data (Offline)**
```sql
-- SQLite: Query active tasks from local cache
SELECT * FROM tasks
WHERE status = 'active'
  AND syncStatus = 'synced';
```

### **2. Delta Sync (Only New/Changed Data)**
```javascript
// Pseudocode: Find records updated since last sync
const lastSyncTime = localStorage.getItem('lastSyncTime');
const changes = await db.query("tasks", {
  where: `modifiedAt > ?`,
  params: [lastSyncTime]
});
changes.forEach(record => {
  record.syncStatus = 'pending';
  db.put('tasks', record);
});
```

### **3. Conflict Detection**
```sql
-- Find conflicting records (out-of-sync)
SELECT t1.id
FROM tasks t1
JOIN tasks t2 ON t1.id = t2.id
WHERE t1.syncTimestamp < t2.syncTimestamp
  AND t1.clientId = 'device_a'
  AND t2.clientId = 'device_b';
```

### **4. Sync Metadata Update**
```javascript
// Mark records as synced after successful API call
await db.bulkPut(tasksToSync.map(task => ({
  ...task,
  syncStatus: 'synced',
  syncTimestamp: new Date().toISOString()
})));
```

### **5. Priority Sync (Critical First)**
```javascript
// Sort records by sync priority (critical first)
const pendingSync = await db.query("tasks", {
  orderBy: "syncPriority DESC"
});
// Sync in order
for (const task of pendingSync) {
  await syncTask(task);
}
```

---

## **Related Patterns**

| **Pattern**               | **Connection**                                                                 | **When to Use**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Progressive Enhancement** | Offline-First is a stricter version; assumes no connectivity.                 | Use Progressive Enhancement for gradual feature rollouts; Offline-First for critical workflows.    |
| **Optimistic UI**         | Both handle offline scenarios but differ in conflict resolution timing.        | Optimistic UI updates UI immediately; Offline-First queues changes for later sync.                   |
| **Event Sourcing**        | Complements Offline-First by providing an audit trail for changes.            | Combine with Offline-First to track all edits (e.g., healthcare records).                           |
| **CQRS (Read/Write Models)** | Offline-First can use separate read/write models for offline data.           | Use CQRS to decouple query performance from write consistency during offline periods.                 |
| **Versioned Data**        | Offline-First relies on versioning for delta syncs.                           | Versioned data ensures incremental syncs work correctly.                                            |
| **Service Workers**       | Can cache assets/APIs for Offline-First apps.                                  | Use SWs to cache API responses or fallbacks for critical resources.                                  |
| **GraphQL Subscriptions** | Not directly related, but both involve async data handling.                   | Use GraphQL Subscriptions for real-time syncs when connectivity improves.                              |

---
**Note**: For distributed systems, pair Offline-First with **CRDTs (Conflict-Free Replicated Data Types)** for stronger consistency guarantees.