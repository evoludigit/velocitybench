# **Debugging CQRS & Event Sourcing: A Troubleshooting Guide**

## **Introduction**
CQRS (Command Query Responsibility Segregation) and Event Sourcing (ES) are powerful patterns for managing complex stateful systems. However, they introduce complexity that can lead to subtle bugs, performance issues, and hard-to-track problems.

This guide focuses on **practical debugging techniques** for common CQRS/ES issues, with actionable fixes and prevention strategies.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these symptoms:

| **Symptom**                     | **Possible Cause**                          |
|---------------------------------|--------------------------------------------|
| Events are missing or duplicated | Event store corruption, RPC failures       |
| Query model not matching command model | projection lag, event reprocessing failures |
| High latency in read queries      | Unoptimized projections, slow event replay  |
| State inconsistency              | Event reordering, race conditions, lost events |
| Audit trail incomplete or wrong   | Event logging disabled, incorrect projection |
| Scaling issues                   | Event store bottlenecks, projection contention |

---

## **2. Common Issues and Fixes**

### **Issue 1: Missing or Duplicated Events**
**Symptoms:**
- Event log shows gaps or duplicates.
- Replaying events fails with missing IDs or conflicting versions.
- Query model and command model diverge.

**Root Causes:**
- Network failures during RPC calls.
- Event store commit race conditions.
- Idempotency not enforced.

**Fixes:**
#### **a) Ensure Idempotency**
```typescript
// Store command in cache if already processed
const commandCache = new Map<string, boolean>();

async function handleCommand(commandId: string, command: Command) {
  if (commandCache.has(commandId)) return;
  commandCache.set(commandId, true);
  await processCommand(command);
}
```

#### **b) Use Transactional Outbox Pattern**
```typescript
// Database-backed outbox for atomic event publishing
await db.transaction(async (tx) => {
  await tx.execute('INSERT INTO outbox(event) VALUES($1)', [event]);
  await publishEvent(event);
});
```

#### **c) Validate Event Store Integrity**
```python
# Check for duplicates using a Bloom filter
from pybloom_live import ScalableBloomFilter

bloom = ScalableBloomFilter(initial_capacity=1_000_000, error_rate=0.001)

for event in event_store.read():
    if bloom.is_possible(event.id):
        raise Error("Duplicate event detected!")
    bloom.add(event.id)
```

---

### **Issue 2: Projection Lag**
**Symptoms:**
- Query model lags behind command model.
- Inconsistent reads, especially under high load.

**Root Causes:**
- Projections not kept up-to-date.
- Event replay failing silently.

**Fixes:**
#### **a) Use Event Sourcing Projection Libraries**
```csharp
// C# Example with EventStoreDB Projections
ProjectionDefinition projection = Projections.Define<MyEventProjection>()
    .InStartUp()
    .OnEvent<MyEvent>((s, ev) => s.EventStore.AppendToStreamAsync("order-projection", EventData.JsonFragment<Event>(ev)));
```

#### **b) Lease-Based Replay for Fault Tolerance**
```typescript
// Retry with exponential backoff
async function replayEvents() {
  let attempts = 0;
  while (attempts < 5) {
    try {
      await projectionProcessors.process();
      break;
    } catch (err) {
      attempts++;
      await delay(1000 * attempts);
    }
  }
}
```

---

### **Issue 3: Race Conditions in Event Processing**
**Symptoms:**
- State corruption in concurrent scenarios.
- Events processed out of order.

**Root Causes:**
- No event sequencing enforcement.
- Event handlers not thread-safe.

**Fixes:**
#### **a) Enforce Event Ordering**
```java
// Java using Event Sourcing library with stream ordering
public class OrderProcessor {
    private final EventStore eventStore;

    public void process(Event<EventType> event) {
        eventStore.getEventStore().appendToStream(
            event.getStreamId(),
            Collections.singletonList(event)
        );
    }
}
```

#### **b) Use Optimistic Concurrency Control**
```typescript
async function updateOrder(orderId: string, newState: OrderState) {
  const current = await findOrder(orderId);
  if (current.version !== newState.expectedVersion) {
    throw new Error("Stale state detected!");
  }
  await saveOrder(newState);
}
```

---

### **Issue 4: Audit Trail Missing or Incorrect**
**Symptoms:**
- Cannot track who modified what and when.
- Projections don’t reflect changes.

**Root Causes:**
- Missing event metadata (user, timestamp).
- Projections not capturing audit events.

**Fixes:**
#### **a) Log Audit Events Explicitly**
```typescript
// Add user metadata to every event
const auditEvent = {
  eventType: "AUDIT",
  userId: "user-123",
  timestamp: new Date(),
  meta: originalEvent
};

await eventStore.append(auditEvent);
```

#### **b) Ensure Projections Process All Events**
```python
# Project all events, including audit logs
class AuditProjection:
    def handle(self, event):
        if event.type == "AUDIT":
            self.log_event_to_db(event)
        # Handle other events...
```

---

## **3. Debugging Tools & Techniques**

### **Tool 1: Event Store Monitoring**
- Use **EventStoreDB’s EventViewer** to inspect event streams.
- Check for gaps, duplicates, or failed writes.

### **Tool 2: Projection Health Checks**
```bash
# Query Projector status in EventStoreDB
curl -X GET http://localhost:2113/shell/projections/my-projection
```

### **Tool 3: Distributed Tracing**
- Integrate **OpenTelemetry** to track event flow across services.
- Example:
  ```typescript
  const tracer = new Tracer("event-processing");
  tracer.addSpan("processEvent", async (span) => {
    await projection.process(event);
  });
  ```

### **Debugging Technique: Replay from Known Good State**
1. Take a snapshot of a known-good state.
2. Replay events from that point to verify consistency.

```bash
# Replay events from a specific version
eventstore-cli replay --start 100 --end 200 --stream my-event-stream
```

---

## **4. Prevention Strategies**

### **a) Enforce Event Serialization & Validation**
```typescript
// Validate events before storing
async function storeEvent(event: Event) {
  if (!event.id || !event.type || !event.timestamp) {
    throw new Error("Invalid event structure!");
  }
  await eventStore.append(event);
}
```

### **b) Use Infrastructure as Code (IaC)**
- Define event stores, projections, and streams via Terraform/Pulumi.

### **c) Automated Testing for Event Processing**
```typescript
// Test event replay correctness
it("replays events correctly", async () => {
  const initialState = await projection.getState();
  await eventStore.processEvents([event1, event2]);
  expect(projection.getState()).toEqual(expectedState);
});
```

### **d) Beginner’s Checklist**
1. **Always track every state change** as an event.
2. **Replay events periodically** to catch projection drifts.
3. **Monitor event store health** (e.g., disk space, latency).
4. **Test failure scenarios** (network drops, timeouts).

---

## **Final Tips**
- **Start small**: Implement CQRS/ES incrementally for one subsystem.
- **Monitor projections**: Alert on lag or failures.
- **Document event schemas**: Ensure backward/forward compatibility.

By following these structured debugging steps, you can quickly identify and resolve CQRS/ES issues while maintaining reliability. 🚀