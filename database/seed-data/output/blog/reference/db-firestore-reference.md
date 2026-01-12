# **[Pattern] Firestore Database Patterns – Reference Guide**

---

## **Overview**
Firestore Database Patterns provide structured approaches to organizing, querying, and scaling data in **Google Cloud Firestore**, a NoSQL document database. This guide outlines key implementation strategies, schema design principles, query optimization techniques, and common anti-patterns to ensure efficient and maintainable database operations. Whether building a **CRUD-heavy app**, handling **complex relationships**, or optimizing for **scalability**, these patterns help avoid pitfalls like inefficient queries, data duplication, or suboptimal security rules.

---

## **Key Concepts**
Firestore follows a **document-centric model** where data is stored as JSON-like documents in collections. Unlike relational databases, it lacks joins, so **flattening data** and **leveraging collections** is critical. Key concepts include:

| Concept | Description |
|---------|------------|
| **Collections & Documents** | Collections are like tables; documents are rows with JSON fields. |
| **Composite Keys** | Combining fields (e.g., `user/{uid}/posts/{postId}`) for hierarchical data. |
| **Subcollections** | Nested collections under a parent document (e.g., `users/{uid}/orderHistory`). |
| **Security Rules** | Fine-grained access control via JavaScript-like rules. |
| **Offline Persistence** | Caching data locally for offline access. |
| **Composite Indexes** | Explicit indexes for queries on multiple fields. |
| **Batch Writes** | Atomic operations on multiple documents. |

---

## **Schema Reference**
Use this table to design schemas based on your app’s needs.

| **Pattern**               | **Use Case**                          | **Schema Structure**                                                                 | **Query Example**                          | **Notes**                                                                                     |
|---------------------------|----------------------------------------|--------------------------------------------------------------------------------------|--------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Flattened Documents**   | Storing simple data (users, posts).   | `users/{uid}` → `{ name, email, profilePic }`                                        | `db.collection("users").doc(uid).get()`     | Avoids joins; duplicate data when needed.                                                    |
| **Composite Keys**        | Hierarchical data (e.g., chats).      | `chats/{chatId}/messages/{messageId}`                                              | `db.collectionGroup("messages").get()`      | Enables querying across subcollections.                                                     |
| **Subcollections**        | One-to-many relationships.            | `users/{uid}/posts/{postId}` → `{ title, content }`                                 | `db.collection("users/{uid}/posts").get()`  | Parent-child references; atomic deletes via `delete()` on parent.                             |
| **Array Fields**          | Small, ordered lists (e.g., tags).     | `post/{postId}` → `{ tags: ["tag1", "tag2"] }`                                      | Filter via `array-contains()`               | Not for large arrays (>1MB); use separate collections instead.                               |
| **Timestamp Fields**      | Logging events/activity.               | `events/{eventId}` → `{ timestamp: Firestore.Timestamp }`                           | `orderBy("timestamp")`                     | Use `Firestore.FieldValue.serverTimestamp()` for server-side timestamps.                     |
| **Geofire/Geopoint**      | Location-based queries.                | `locations/{locationId}` → `{ geopoint: { latitude, longitude } }`                  | `where("geopoint", "near", { lat, lon })`   | Requires composite indexes for geographic queries.                                            |
| **Denormalized Data**     | Performance-critical reads.           | Duplicate data (e.g., copy `user` data into a `post` document).                      | `db.collection("posts").where("authorId", "==", uid).get()` | Tradeoff: writes increase; reads decrease.                                                    |

---

## **Query Examples**
### **1. Basic Queries**
```javascript
// Get a single document
const doc = await db.collection("users").doc(uid).get();

// Query a collection (with pagination)
const querySnapshot = await db.collection("posts")
  .where("published", "==", true)
  .orderBy("timestamp")
  .limit(10)
  .get();
```

### **2. Composite Queries**
```javascript
// Query across subcollections (requires index)
const messages = await db.collectionGroup("messages")
  .where("readingStatus", "==", false)
  .get();
```

### **3. Batch Operations**
```javascript
const batch = db.batch();
batch.update(docRef1, { field: "newValue" });
batch.delete(docRef2);
await batch.commit();
```

### **4. Security-Restricted Queries**
```javascript
// Rules: allow read if user matches uid
"users/{uid}": {
  allow read: if request.auth != null && request.auth.uid == uid;
}
```

### **5. Offline Persistence**
```javascript
import { enableIndexedDbPersistence } from "firebase/firestore";
enableIndexedDbPersistence(db);
```

---

## **Best Practices**
1. **Avoid Unnecessary Joins**
   - Firestore lacks joins; **denormalize** or use subcollections for relationships.
   - Example: Store `user.email` in every `post` document if frequently accessed.

2. **Optimize Queries**
   - **Limit fields** in queries to reduce payloads:
     ```javascript
     db.collection("users").doc(uid).get().then(doc => doc.data(["name", "email"]));
     ```
   - Use **composite indexes** for queries on multiple fields.

3. **Batch Writes for Atoms**
   - Use `batch()` for related operations (e.g., updating a user’s post count and their profile).

4. **Leverage Subcollections for Hierarchy**
   - Example: `users/{uid}/orders/{orderId}` for one-to-many relationships.

5. **Minimize Array Fields**
   - Arrays >1MB are inefficient; use separate collections (e.g., `posts/{postId}/tags/{tagId}`).

6. **Use Composite Keys for Scalability**
   - Example: `chats/{chatId}/messages/{timestamp}` ensures even distribution.

7. **Security Rules First**
   - Design rules before schema to enforce access constraints early.

8. **Monitor Queries**
   - Use **Firestore’s Admin SDK** or **Cloud Logging** to detect expensive queries.

---

## **Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------|
| **Over-fetching data**               | Use `.select()` or stream only needed fields.                               |
| **Missing composite indexes**        | Run `db.collectionGroup("collection").get()` to identify missing indexes.    |
| **Excessive writes (denormalization)** | Batch writes; consider caching.                                             |
| **Offline conflicts**                | Use `onSnapshot` with conflict resolution logic.                            |
| **Large array fields**               | Split into separate documents (e.g., `tags/{tagId}`).                      |
| **Unbounded queries**                | Always use `.limit()` and paginate.                                          |

---

## **Related Patterns**
1. **[Flattened Data Pattern]**
   - Best for apps with simple, independent data (e.g., user profiles).
   - *See also:* [Denormalized Data Pattern](#denormalized-data).

2. **[Composite Keys Pattern]**
   - Ideal for hierarchical data (e.g., forum threads/replies).
   - *Anti-pattern:* Avoid deep nesting (>3 levels) for performance.

3. **[Subcollection Pattern]**
   - For one-to-many relationships (e.g., user posts, order items).
   - *Tradeoff:* Deletes require recursive operations.

4. **[Geospatial Queries Pattern]**
   - Use `geohash` or `geopoint` for location-based apps.
   - *Note:* Requires composite indexes for `near` queries.

5. **[Event Sourcing Pattern]**
   - Append-only logs (e.g., audit trails) using `events/{eventId}`.

6. **[Offline-First Pattern]**
   - Combine with Firestore’s persistence for mobile apps.

7. **[Security Rules Pattern]**
   - Enforce permissions at the database level (e.g., `allow read: if request.auth != null`).

---
## **Further Reading**
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Composite Indexes Guide](https://firebase.google.com/docs/firestore/manage-data/index-composite)
- [Best Practices for Scaling](https://firebase.google.com/docs/firestore/solutions/scale)