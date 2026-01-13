# **Debugging Hospitality Domain Patterns: A Troubleshooting Guide**
*Hospitality Domain Patterns* refer to architectural best practices for building scalable, reliable, and high-performance systems for hospitality applications (e.g., hotel bookings, reservations, guest management). This guide focuses on diagnosing and resolving common issues in **reservation systems, payment processing, and guest experience workflows**.

---

## **Symptom Checklist**
Before diving into fixes, confirm which symptoms align with your issue:

| **Symptom**                     | **Possible Cause**                          | **Severity** |
|----------------------------------|---------------------------------------------|--------------|
| Slow reservation processing      | Inefficient booking service calls             | High         |
| Failed payment transactions      | Payment gateway timeouts or API failures     | Critical     |
| Unavailable room availability     | Cached or stale data in inventory service   | Medium       |
| High latency in real-time updates| Slow event streaming (Kafka, WebSockets)    | High         |
| Duplicate bookings               | Optimistic concurrency conflicts            | Critical     |
| Guest checkout failures          | Database locks or transaction deadlocks     | High         |
| High API call latency            | Poor caching strategy (e.g., Redis misconfig) | Medium       |
| Inconsistent UI state            | Asynchronous operations not handled properly | Low          |

---
## **Common Issues & Fixes**

### **1. Performance Bottlenecks in Reservation Systems**
**Symptom:** High latency when querying room availability or processing bookings.
**Root Cause:**
- Excessive database queries (N+1 problem).
- No caching for frequent lookups (e.g., room availability).
- Blocking I/O operations (e.g., synchronous calls to external services).

**Fixes:**
#### **A. Implement Caching (Redis/Memcached)**
```javascript
// Before: Query database directly
const rooms = await database.query("SELECT * FROM rooms WHERE availability = true");

// After: Use Redis cache with TTL (cache invalidation on updates)
const cachedRooms = await redis.get("available_rooms");
if (!cachedRooms) {
  const rooms = await database.query("SELECT * FROM rooms WHERE availability = true");
  await redis.set("available_rooms", JSON.stringify(rooms), "EX", 60); // Cache for 60s
}
return JSON.parse(cachedRooms);
```
**Key Fixes:**
✔ Use **TTL-based invalidation** (e.g., cache invalidates on room updates).
✔ Avoid **cache stampedes** with locks (e.g., Redis `SETNX`).

#### **B. Optimize Database Queries**
```sql
-- Bad: Multiple queries for availability
SELECT * FROM rooms WHERE id = 123; -- Room details
SELECT * FROM reservations WHERE room_id = 123; -- Existing bookings

-- Good: Single query with JOIN
SELECT r.*, COUNT(DISTINCT res.id) as booked_count
FROM rooms r
LEFT JOIN reservations res ON r.id = res.room_id
WHERE r.id = 123 GROUP BY r.id;
```
**Key Fixes:**
✔ Use **indexed columns** (`room_id`, `availability_status`).
✔ Replace `SELECT *` with **specific columns**.

#### **C. Asynchronous Processing (Queue-Based)**
```javascript
// Before: Blocking call
const booking = await processBooking(guestId, roomId);

// After: Use a queue (Bull, RabbitMQ)
await queue.add("create_booking", { guestId, roomId });
```
**Key Fixes:**
✔ Offload **non-critical workflows** (e.g., sending confirmation emails).
✔ Use **event sourcing** for critical transactions.

---

### **2. Payment Failures & Transaction Issues**
**Symptom:** Payment gateways (Stripe, PayPal) returning failures or timeouts.
**Root Causes:**
- No **retries with exponential backoff**.
- **No idempotency keys** → duplicate payments.
- **Long-lived transactions** → deadlocks.

**Fixes:**
#### **A. Implement Retries with Backoff**
```javascript
const retryPayment = async (paymentId, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await stripe.charges.create({ ... });
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
};
```
**Key Fixes:**
✔ **Retry failed payments** (but avoid infinite loops).
✔ Use **circuit breakers** (e.g., `opossum` library) to stop cascading failures.

#### **B. Enforce Idempotency**
```javascript
// Add idempotency key to Stripe payload
const charge = await stripe.charges.create({
  amount: 1000,
  currency: "usd",
  idempotency_key: `payment_${requestId}`,
});
```
**Key Fixes:**
✔ Prevents **duplicate payments** (critical for refunds).
✔ Use **UUIDs** for unique request IDs.

#### **C. Optimistic Concurrency Control**
```sql
-- Use PESSIMISTIC_READ for high-contention tables
BEGIN TRANSACTION;
SELECT * FROM payments WHERE id = 123 FOR UPDATE; -- Lock row
-- Process payment...
COMMIT;
```
**Key Fixes:**
✔ Avoid **deadlocks** with proper transaction isolation.
✔ Use **row-level locking** (`FOR UPDATE`) for critical operations.

---

### **3. Stale Room Inventory Data**
**Symptom:** Guests see "booked" rooms that are actually available.
**Root Causes:**
- **No real-time sync** between booking and inventory services.
- **Eventual consistency** without conflict resolution.

**Fixes:**
#### **A. Use Event-Driven Architecture (Kafka/RabbitMQ)**
```javascript
// When a booking is created, publish an event
await eventBus.publish("booking_created", { bookingId, roomId });

// Inventory service listens and updates
@Subscribe("booking_created")
async handleBookingCreated(event) {
  await database.updateRoomAvailability(event.roomId, false);
}
```
**Key Fixes:**
✔ **Atomic updates** via events (no polling).
✔ **Idempotent handlers** to avoid duplicate updates.

#### **B. Implement Conflict Resolution**
```javascript
// Check version on update
const updateBooking = async (bookingId, newData) => {
  const current = await database.getBooking(bookingId);
  if (current.version !== newData.version) {
    throw new Error("Conflict: Stale data");
  }
  await database.updateBooking(bookingId, {
    ...newData,
    version: current.version + 1,
  });
};
```
**Key Fixes:**
✔ **Optimistic concurrency** prevents overwrites.
✔ Use **versioning** or **timestamp-based retries**.

---

### **4. Scalability Issues with Real-Time Updates**
**Symptom:** WebSocket/EventSource delays in showing live status (e.g., check-in, cancellations).
**Root Causes:**
- **Buffering events** in a single subscriber.
- **No partitioning** in event queues.

**Fixes:**
#### **A. Use Partitioned Queues (Kafka)**
```javascript
// Partition events by roomId for parallel processing
await eventBus.publish(
  "room_status_update",
  { roomId: 123, status: "checked_in" },
  { partitionKey: "room_123" }
);
```
**Key Fixes:**
✔ **Parallel processing** of independent events.
✔ **Lower latency** for critical updates.

#### **B. Optimize WebSocket Connections**
```javascript
// Use connection pooling (e.g., Socket.io with rooms)
io.of("/bookings").adapters.Adapter.prototype.roomOf = (sessionId) => {
  return `room_${sessionId}`;
};
```
**Key Fixes:**
✔ **Efficient broadcasting** (only send to relevant clients).
✔ **Use room-based subscriptions** instead of broadcasting to all.

---

## **Debugging Tools & Techniques**
| **Tool/Technique**       | **Use Case**                          | **Example Command**                     |
|--------------------------|---------------------------------------|-----------------------------------------|
| **APM (New Relic, Datadog)** | Latency tracing in microservices       | `GET /api/reservations?trace=`          |
| **Redis Insight**        | Cache hit/miss analysis               | `INFO stats`                            |
| **Kafka Lag Monitor**    | Event processing delays               | `kafka-consumer-groups --bootstrap-server` |
| **PostgreSQL `pg_stat_activity`** | Blocking queries                  | `\x` (extend output in `psql`)         |
| **Stripe/PCI Compliance Logs** | Payment failures       | `stripe logs --from=now-1h`             |
| **Chaos Engineering (Gremlin)** | Test failure resilience | Simulate 50% latency spikes           |
| **Grafana + Prometheus**  | Monitoring scalability metrics        | `up{service="booking-service"}`         |

**Pro Tip:**
- **Redact sensitive data** (e.g., credit cards) in logs.
- **Use structured logging** (JSON) for easier parsing:
  ```javascript
  console.log(JSON.stringify({
    event: "booking_failed",
    bookingId: "123",
    error: { code: 429, message: "Rate limit exceeded" }
  }));
  ```

---

## **Prevention Strategies**
### **1. Design for Failure**
- **Circuit breakers:** Automatically fallback if a service fails (e.g., `Hystrix`).
- **Chaos testing:** Randomly kill nodes to test resilience.
- **Graceful degradation:** Show "coming soon" instead of crashing.

### **2. Observability First**
- **Centralized logging** (ELK Stack, Loki).
- **Distributed tracing** (Jaeger, OpenTelemetry).
- **SLOs/SLIs:** Define error budgets (e.g., "payment failures < 1%").

### **3. Automated Rollbacks**
- **Blue-green deployments** for critical services.
- **Canary releases** for new features (e.g., 5% traffic first).

### **4. Database Optimization**
- **Read replicas** for reporting queries.
- **Sharding** for high-traffic tables (e.g., `reservations`).
- **Connection pooling** (PgBouncer for PostgreSQL).

### **5. Idempotency & Compensating Transactions**
- **For payments:** If a booking fails, **refund automatically** if the room is still available.
- **For cancellations:** **Release inventory** even if the UI fails.

---
## **Final Checklist for Fixes**
| **Issue**               | **Quick Fix**                          | **Long-Term Fix**                     |
|-------------------------|----------------------------------------|----------------------------------------|
| Slow reservations       | Add Redis cache                        | Optimize DB queries + async processing |
| Payment failures        | Retry with backoff                     | Idempotency keys + circuit breakers   |
| Stale inventory         | Event-driven updates                   | Conflict resolution + versioning      |
| Scalability issues      | Partitioned queues                     | Horizontal scaling + auto-scaling     |
| UI inconsistencies      | Polling for updates                    |Real-time WebSockets + rooms           |

---
## **Conclusion**
Hospitality systems must **balance speed, reliability, and consistency**. Start with **caching, retries, and event-driven updates**, then scale horizontally. Use **observability tools** to detect issues early, and **automate rollbacks** to reduce downtime.

**Key Takeaways:**
1. **Cache aggressively** (but invalidate properly).
2. **Make transactions idempotent** (prevent duplicates).
3. **Decouple services** (use events, not direct DB calls).
4. **Monitor everything** (latency, errors, queue lag).

By following this guide, you can quickly diagnose and resolve common hospitality domain issues while building a **resilient, scalable system**. 🚀