```markdown
---
title: "Streaming Conventions: Building Robust APIs for Real-Time Data"
date: "2023-09-15"
author: "Alex Carter"
description: "Learn how streaming conventions help manage real-time data efficiently. This guide covers challenges, solutions, and implementation tips for real-time applications."
tags: ["backend", "API design", "streaming", "real-time", "database patterns"]
---

# **Streaming Conventions: Building Robust APIs for Real-Time Data**

Real-time applications—from chat apps to live sports scores—rely on **streaming data**. But without proper design, streaming APIs can become messy, inefficient, or even crash under load. That’s where **streaming conventions** come in.

These are standardized ways to handle data in real-time, balancing performance, readability, and scalability. Whether you're building a server-sent events (SSE) endpoint, WebSocket API, or a Kafka-based pipeline, streaming conventions help you avoid common pitfalls while keeping your code maintainable.

In this guide, I’ll show you:
- The pain points of improper streaming design
- How conventions solve real-world problems
- Practical code examples (Node.js, Python, and SQL)
- Common mistakes to avoid

By the end, you’ll have a clear, actionable strategy for designing streaming APIs.

---

## **The Problem: Why Streaming APIs Can Go Wrong**

Before diving into solutions, let’s look at what happens when you skip proper streaming conventions.

### **1. Inconsistent Data Delivery**
Imagine a live stock ticker where price updates arrive out of order or get duplicated. Users see erratic behavior, leading to frustration.

```json
// Example: Unreliable streaming event
// First event (normal)
{"symbol": "AAPL", "price": 150.25, "timestamp": 1694501234}

// Later event (duplicate)
{"symbol": "AAPL", "price": 150.25, "timestamp": 1694501234}

// THEN the correct update (out of order)
{"symbol": "AAPL", "price": 150.50, "timestamp": 1694501235}
```

This happens when:
- No sequence tracking is implemented
- Clients reprocess unacknowledged messages
- The backend doesn’t handle buffering properly

### **2. Performance Bottlenecks**
If your API sends raw data without proper chunking or compression, clients may struggle with high latency.

```javascript
// Bad: Sending unstructured JSON blobs
socket.send(JSON.stringify({ data: hugeArray, id: "123", timestamp: Date.now() }));
```

This causes:
- Memory overload on the client
- Slow connections due to large payloads
- Harder debugging (no clear structure)

### **3. Client-Side Chaos**
Without clear conventions, clients must guess:
- How to parse incoming data
- When a message is complete
- How to handle errors

This leads to fragile client implementations that break under edge cases.

---

## **The Solution: Streaming Conventions**

Streaming conventions are **agreed-upon rules** that govern how:
- Data is formatted
- Messages are sequenced
- Clients consume streams
- Errors are handled

We’ll focus on **three key conventions**:
1. **Message Structure** – How data is packaged
2. **Message Sequencing** – Ensuring order and reliability
3. **Error Handling** – Graceful recovery

---

## **Components/Solutions**

### **1. Message Structure: Schema & Format**
Use a **standardized JSON schema** for all events to ensure consistency.

#### **Example: JSON Schema for Real-Time Events**
```json
// This schema ensures all events follow a predictable format
{
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "timestamp": { "type": "integer" },
    "data": {
      "type": "object",
      "properties": {
        "symbol": { "type": "string" },
        "price": { "type": "number" },
        "metadata": { "type": "object" }
      },
      "required": ["symbol", "price"]
    }
  },
  "required": ["id", "timestamp", "data"]
}
```

#### **Why This Matters**
- Clients can validate incoming data without parsing errors
- Backend can enforce consistency
- Easier to debug with structured logs

### **2. Message Sequencing: Ensuring Order**
Use **sequence numbers** or **timestamps** to track message order.

#### **Example: Sequenced Events**
```json
// Event 1 (in order)
{"id": "1", "seq": 1, "data": { "price": 150.25 }}

// Event 2 (next in sequence)
{"id": "2", "seq": 2, "data": { "price": 150.30 }}

// Event 3 (duplicate seq - client should ignore)
{"id": "3", "seq": 2, "data": { "price": 150.35 }}
```

**Implementation (Python with FastAPI):**
```python
from fastapi import FastAPI, WebSocket
from typing import Dict, List

app = FastAPI()

class Message:
    def __init__(self, seq: int, data: Dict):
        self.seq = seq
        self.data = data

last_seq = 0

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        global last_seq
        last_seq += 1
        await websocket.send_json({"seq": last_seq, "data": {"price": 150 + (last_seq % 5)}})
```

### **3. Error Handling: Graceful Recovery**
Streaming APIs should **never crash** on malformed data. Instead, they should:
- Log errors
- Send **acknowledgments (ACKs)**
- Support **reconnection**

#### **Example: WebSocket Error Handling**
```javascript
// Client-side code (JavaScript)
const ws = new WebSocket("wss://api.example.com/stream");

ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    if (data.seq && data.data) {
      console.log("Processed:", data.data);
    } else {
      console.error("Invalid message format");
    }
  } catch (err) {
    console.error("Failed to parse:", err);
  }
};

ws.onerror = (err) => {
  console.error("WebSocket error:", err);
  // Auto-reconnect logic here
};
```

---

## **Implementation Guide**

### **Step 1: Define Your Event Schema**
Before coding, agree on:
- Required fields (`id`, `timestamp`, `data`)
- Optional fields (`metadata`, `source`)

**Example Schema (JSON):**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StreamEvent",
  "type": "object",
  "properties": {
    "event_id": { "type": "string", "format": "uuid" },
    "timestamp": { "type": "integer" },
    "data": { "type": "object" },
    "status": { "type": "string", "enum": ["ok", "error", "partial"] }
  },
  "required": ["event_id", "timestamp", "data", "status"]
}
```

### **Step 2: Implement Sequencing on the Backend**
Use **sequence counters** or **unique IDs** to track messages.

**Node.js Example (Express + WebSocket):**
```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

let seq = 0;

wss.on('connection', (ws) => {
  setInterval(() => {
    seq++;
    ws.send(JSON.stringify({
      seq,
      event: "price_update",
      data: { symbol: "AAPL", price: Math.random() * 50 }
    }));
  }, 1000);
});
```

### **Step 3: Client-Side Validation & ACKs**
Clients should:
1. Validate incoming data
2. Acknowledge receipt
3. Handle disconnections gracefully

**Python Client Example (with `websockets`):**
```python
import asyncio
import json
import websockets

async def consumer():
    uri = "ws://localhost:8080"
    async with websockets.connect(uri) as ws:
        seq = 0
        while True:
            try:
                msg = json.loads(await ws.recv())
                if msg["seq"] != seq:
                    print(f"Out of order: expected {seq}, got {msg['seq']}")
                else:
                    print(f"Received: {msg['data']}")
                    seq += 1
                    await ws.send(json.dumps({"ack": seq}))
            except Exception as e:
                print(f"Error: {e}")
                break

asyncio.get_event_loop().run_until_complete(consumer())
```

---

## **Common Mistakes to Avoid**

### **1. Skipping Message Validation**
❌ **Bad:**
```javascript
socket.onmessage = (e) => socket.send(e.data); // Echo raw data
```
✅ **Good:**
Always validate messages against your schema.

### **2. No Sequence Numbers = Chaos**
❌ **Bad:**
```python
# No seq tracking → clients may reprocess old events
ws.send({"data": new_update})
```
✅ **Good:**
```python
seq += 1
ws.send({"seq": seq, "data": new_update})
```

### **3. Ignoring Reconnection Logic**
❌ **Bad:**
```javascript
const ws = new WebSocket(url); // No retry logic
```
✅ **Good:**
```javascript
let reconnectAttempts = 0;
const reconnect = () => {
  if (reconnectAttempts < 5) {
    reconnectAttempts++;
    ws = new WebSocket(url);
  }
};
ws.onclose = reconnect;
```

### **4. Sending Uncompressed Large Data**
❌ **Bad:**
```python
ws.send(JSON.stringify(very_large_dataset));
```
✅ **Good:**
Use **chunking** or **compression** (e.g., `gzip` in WebSocket).

---

## **Key Takeaways**

✔ **Define a strict schema** for all events to ensure consistency.
✔ **Use sequence numbers** to track message order and detect duplicates.
✔ **Validate on both client & server** to catch malformed data early.
✔ **Implement ACKs** to confirm message receipt.
✔ **Handle reconnections gracefully** (exponential backoff is best).
✔ **Optimize performance** with chunking, compression, or binary protocols (e.g., Protocol Buffers).

---

## **Conclusion**

Streaming APIs are powerful but fragile without proper conventions. By following patterns like **structured messaging, sequencing, and error handling**, you can build scalable, reliable real-time systems.

### **Next Steps**
- Experiment with **WebSockets vs. SSE** (which fits your use case better?)
- Explore **Kafka or RabbitMQ** for high-throughput event streaming.
- Test under load using tools like **Locust** or **k6**.

Now go build something amazing—with conventions!

---
**Want to dive deeper?**
- [JSON Schema Official Docs](https://json-schema.org/)
- [WebSocket RFC](https://datatracker.ietf.org/doc/html/rfc6455)
- [Kafka Streams Guide](https://kafka.apache.org/documentation/streams/)

🚀 **Happy streaming!**
```